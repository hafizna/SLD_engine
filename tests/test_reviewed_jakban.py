"""Regression coverage for the reviewed single-view Jakarta/Banten inputs."""
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import AnalyticalView, ViewMembership, Substation, GeneratingUnit
from app.services import ingest
from app.services.ingest_parser import parse_upload
from scripts._reviewed_jakban import build_reviewed, RISK_PINS, SOURCES, ROOT, LBK_CODE_CORRECTIONS


@pytest.mark.parametrize("code", SOURCES)
def test_reviewed_regeneration_preserves_topology_and_full_membership(code, tmp_path):
    source = ROOT / "samples/sources" / SOURCES[code]
    original = parse_upload(source.read_bytes(), source.name)
    path = build_reviewed(code, tmp_path)
    parsed = parse_upload(path.read_bytes(), path.name)
    committed = ROOT / "samples" / path.name
    assert parsed == parse_upload(committed.read_bytes(), committed.name)
    assert parsed["subsystem"]["code"] == code
    assert parsed["meta"]["dropped_edges"] == []
    if code in RISK_PINS:
        # The reviewed LBK / PBRC books carry no risk table; the book's rows are
        # re-attached to the reviewed topology, each with a pin.
        assert not original["risks"]
        assert len(parsed["risks"]) == len(RISK_PINS[code])
        assert all(r["pin_key"] for r in parsed["risks"])
    else:
        assert parsed["risks"] == original["risks"]
    # The reviewed workbook may add explicit source/stub evidence to the
    # machine-readable sheets. Every row from the user's source must still be
    # present, while the supplemental rows are checked below by code.
    parsed_objects = {n["external_key"]: n for n in parsed["objects"]}
    remap = LBK_CODE_CORRECTIONS if code == 'SS_LBK' else {}
    assert {remap.get(n["external_key"], n["external_key"]) for n in original["objects"]} <= set(parsed_objects)
    parsed_edges = {(e["from_external_key"], e["to_external_key"],
                     e.get("relation_type", "CONNECTED_TO")) for e in parsed["connections"]}
    assert {(remap.get(e["from_external_key"], e["from_external_key"]),
             remap.get(e["to_external_key"], e["to_external_key"]),
             e.get("relation_type", "CONNECTED_TO")) for e in original["connections"]} <= parsed_edges
    if code != 'SS_LBK':
        assert all(not n["view_keys"] for n in parsed["objects"])
        assert all(not c["view_keys"] for c in parsed["connections"])
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        draft = ingest.build_draft(db, parsed)
        for n in draft["nodes"]:
            n.update(resolution="NEW", canonical_id=None,
                     confirmed_code=n["external_key"], confirmed_name=n["raw_label"])
        assert ingest.validate(db, draft)["ok"]
        ingest.publish(db, draft, code, parsed["subsystem"]["name"], None,
                       parsed["subsystem"]["apb"])
        if code == 'SS_LBK':
            assert {v.view_key for v in db.query(AnalyticalView)} == {
                'SS_LBK_KEMBANGAN', 'SS_LBK_BALARAJA', 'SS_LBK_GABUNGAN'}
            view = db.query(AnalyticalView).filter_by(view_key='SS_LBK_GABUNGAN').one()
        else:
            view = db.query(AnalyticalView).one()
            assert view.view_key == f"{code}_FULL"
        members = db.query(ViewMembership).filter_by(view_id=view.id).all()
        actual = {m.node_id for m in members if m.node_kind == "SUBSTATION"}
        assert actual == {n.id for n in db.query(Substation).all()}
        actual_gen = {m.node_id for m in members if m.node_kind == "GENERATING_UNIT"}
        assert actual_gen == {n.id for n in db.query(GeneratingUnit).all()}
    engine.dispose()


def test_gucl_reviewed_supply_relations():
    path = ROOT / "samples/ss_gucl_ingest.xlsx"
    d = parse_upload(path.read_bytes(), path.name)
    pairs = {frozenset((c["from_external_key"], c["to_external_key"])) for c in d["connections"]}
    for pair in [("LBUAN", "MENES"), ("SKETI", "RKBRU"), ("KRWTU", "SRANG")]:
        assert frozenset(pair) in pairs
    for pair in [("CLBRU", "MENES"), ("CLBRU", "LBUAN"), ("MENES", "SKETI")]:
        assert frozenset(pair) not in pairs


def test_lbk_restores_both_voltage_sources_and_ibt_units():
    path = ROOT / "samples/ss_lbk_ingest.xlsx"
    parsed = parse_upload(path.read_bytes(), path.name)
    objects = {n["external_key"]: n for n in parsed["objects"]}
    for bus in ("KMBGN", "NBRJA"):
        assert objects[bus]["voltage_hv_kv"] == 150
        assert objects[f"GITET_{bus}"]["voltage_hv_kv"] == 500
    ibt = {(e["from_external_key"], e["to_external_key"], e["unit_no"])
           for e in parsed["connections"] if e.get("relation_type") == "IBT_LINK"}
    assert ibt == {(f"GITET_{bus}", bus, unit)
                   for bus in ("KMBGN", "NBRJA") for unit in ("1", "2")}
    risk = next(r for r in parsed["risks"] if r["seq_no"] == 1)
    assert risk["pin_key"] == "GITET_KMBGN"
    assert objects['TGBRU3']['status_hint'] == 'NEW_NOT_ENERGIZED'
    assert objects['TGBRU3']['tier_hint'] == 2
    assert not objects['TGBRU3']['is_bay']
    assert objects['KIT_LTKNG']['view_keys'] == ['BALARAJA']
    assert objects['ULJMI']['raw_label'] == 'Ulujami'
    assert objects['SPTAN']['tier_hint'] == 4
    assert objects['SPTAN2']['tier_hint'] == 5
    assert {'KIT_LTKNG', 'PLTD SNY'} <= set(objects)
    assert objects['PLTD SNY']['tier_hint'] == objects['GIS PLTD SNY']['tier_hint'] == 3
    assert objects['ITS']['raw_label'] == 'KTT ITS'
    assert objects['JTKBR']['raw_label'] == 'Jatake Baru'
    assert set(objects['JTKBR']['view_keys']) == {'KEMBANGAN', 'BALARAJA'}
    assert not ({'IIS', 'JTKDR'} & set(objects))
    assert any(e['from_external_key'] == 'PLTD SNY' and e['to_external_key'] == 'GIS PLTD SNY'
               for e in parsed['connections'])
    assert not any(e['from_external_key'] == 'PLTD SNY' and e['to_external_key'] == 'SNYAN'
                   for e in parsed['connections'])
    planned = next(e for e in parsed['connections'] if e['to_external_key'] == 'TGBRU3')
    assert planned['from_external_key'] == 'LTKNG'
    assert planned['view_keys'] == ['BALARAJA']
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        draft = ingest.build_draft(db, parsed)
        for n in draft["nodes"]:
            n.update(resolution="NEW", canonical_id=None,
                     confirmed_code=n["external_key"], confirmed_name=n["raw_label"])
        assert ingest.validate(db, draft)["ok"]
        ingest.publish(db, draft, "SS_LBK", parsed["subsystem"]["name"], None,
                       parsed["subsystem"]["apb"])
        from app.services.sld_renderer import render_view_svg
        import xml.etree.ElementTree as ET
        root = ET.fromstring(render_view_svg(db, db.query(AnalyticalView).filter_by(view_key='SS_LBK_GABUNGAN').one()))
        ns = {"s": "http://www.w3.org/2000/svg"}
        bars = root.find("s:g[@id='busbars']", ns)
        assert bars is not None
        svg = ET.tostring(bars, encoding="unicode")
        assert "GITET_KMBGN" in svg and "GITET_NBRJA" in svg
        assert '#0047AB' in svg and '#C00000' in svg
    engine.dispose()


def test_future_boundary_does_not_poison_neighbouring_full_asset():
    from app.services.seed_xlsx_fixture import seed_xlsx_fixture
    from app.models import Bay
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_xlsx_fixture(db, ROOT / 'samples/ss_prbc_ingest.xlsx')
        ids = {s.code: s.id for s in db.query(Substation)
               if s.code in {'PDKLP', 'SKTNI', 'SMRCN'}}
        assert all(db.get(Substation, sid).status == 'NEW_NOT_ENERGIZED' for sid in ids.values())
        seed_xlsx_fixture(db, ROOT / 'samples/ss_bksi_cbng_ingest.xlsx')
        for key, sid in ids.items():
            assert db.query(Substation).filter_by(code=key).one().id == sid
            assert db.get(Substation, sid).status == 'ENERGIZED'
            assert db.query(Bay).filter_by(substation_id=sid).first().status == 'NEW_NOT_ENERGIZED'
        from app.models import Circuit
        bekasi = db.query(Substation).filter_by(code='BKASI').one()
        planned = db.query(Circuit).filter_by(from_substation_id=bekasi.id,
                                            to_substation_id=ids['SKTNI']).one()
        assert planned.status == 'PLANNED'
    engine.dispose()


def test_senayan_gis_and_generator_are_shared_across_subsystems():
    from app.services.seed_xlsx_fixture import seed_xlsx_fixture
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        seed_xlsx_fixture(db, ROOT / 'samples/ss_lbk_ingest.xlsx')
        seed_xlsx_fixture(db, ROOT / 'samples/ss_muarakarang_durikosambi_ingest.xlsx')
        gis = db.query(Substation).filter_by(code='GIS PLTD SNY').one()
        plant = db.query(GeneratingUnit).filter_by(code='PLTD SNY').one()
        assert plant.outlet_substation_id == gis.id
        assert gis.substation_type == 'GIS'
        for key, expected in [('SS_LBK_KEMBANGAN', 3), ('SS_MK_DURK_MUARAKARANG', 4)]:
            view = db.query(AnalyticalView).filter_by(view_key=key).one()
            for kind, nid in [('SUBSTATION', gis.id), ('GENERATING_UNIT', plant.id)]:
                member = db.query(ViewMembership).filter_by(view_id=view.id, node_kind=kind, node_id=nid).one()
                assert member.tier_seed == expected
    engine.dispose()


def test_reviewed_boundary_evidence_is_explicit():
    expected = {
        "SS_LBK": {"NCKUPA": "CKUPA", "CKNDE": "BLRJA",
                    "JTKBR": "JTAKE", "BSH": "CKBRU"},
        "SS_GUCL": {"SARAN4": "SRANG", "RGKOT": "SARAN4", "BUNAR": "RGKOT",
                     "KRACAK": "BUNAR"},
        "SS_PRBC": {"PDKLP": "BKASI", "SKTNI": "BKASI", "SMRCN": "BKASI"},
    }
    for code, bays in expected.items():
        path = ROOT / "samples" / f"{code.lower()}_ingest.xlsx"
        parsed = parse_upload(path.read_bytes(), path.name)
        actual = {n["external_key"]: n.get("bay_feeder_key")
                  for n in parsed["objects"] if n.get("bay_appearances")}
        assert {key: actual[key] for key in bays} == bays


def test_reviewed_pbrc_generator_and_gitet_relations():
    path = ROOT / "samples/ss_prbc_ingest.xlsx"
    parsed = parse_upload(path.read_bytes(), path.name)
    objects = {n["external_key"]: n for n in parsed["objects"]}
    assert {"KIT_MKR_ST30", "KIT_PRIOK_B12", "KIT_PRIOK_B3"} <= set(objects)
    assert {"GITET_BKASI", "GITET_MTWAR", "GITET_CWBRU"} <= set(objects)
    pairs = {(e["from_external_key"], e["to_external_key"]) for e in parsed["connections"]}
    assert {("KIT_MKR_ST30", "MKLMA"), ("KIT_PRIOK_B12", "PRBRT"),
            ("KIT_PRIOK_B3", "PRTRU")} <= pairs
    ibt = {(e["from_external_key"], e["to_external_key"], e["unit_no"])
           for e in parsed["connections"] if e.get("relation_type") == "IBT_LINK"}
    assert {("GITET_BKASI", "BKASI", "2"), ("GITET_BKASI", "BKASI", "4"),
            ("GITET_MTWAR", "MTWAR", "1"), ("GITET_MTWAR", "MTWAR", "2"),
            ("GITET_CWBRU", "CWBRU", "1")} <= ibt


def test_legacy_labels_are_carried_by_stable_codes():
    checks = {
        "SS_LBK": {"KMBGN": "Kembangan (bus 150 kV)", "MTLAN": "Metland",
                    "NCKUPA": "GITET New Cikupa (rencana)"},
        "SS_GUCL": {"RGKOT": "Rangkasbitung Kota", "LBUAN": "Labuan"},
        "SS_PRBC": {"BKASI": "Bekasi (bus 150 kV)",
                    "GITET_BKASI": "GITET Bekasi", "CNANG": "Cinang / Cawang Baru bawah"},
    }
    for code, expected in checks.items():
        path = ROOT / "samples" / f"{code.lower()}_ingest.xlsx"
        parsed = parse_upload(path.read_bytes(), path.name)
        names = {n["external_key"]: n["raw_label"] for n in parsed["objects"]}
        assert {key: names[key] for key in expected} == expected


def test_a_pin_on_a_plant_row_lands_on_its_outlet_bus():
    """PRBC #5 (power swing trips Priok generation) is written on the two Priok
    plant rows. It used to publish as a SUBSTATION pin carrying the plant's
    GeneratingUnit id, so it drew on whichever GI shared that id."""
    path = ROOT / "samples/ss_prbc_ingest.xlsx"
    parsed = parse_upload(path.read_bytes(), path.name)
    risk = next(r for r in parsed["risks"] if r["seq_no"] == 5)
    pins = {risk["pin_key"], *(key for _kind, key in risk["extra_pins"])}
    assert pins == {"PRTRU", "PRBRT"}           # outlets of Priok Blok 3 and Blok 1&2
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        draft = ingest.build_draft(db, parsed)
        for n in draft["nodes"]:
            n.update(resolution="NEW", canonical_id=None,
                     confirmed_code=n["external_key"], confirmed_name=n["raw_label"])
        ingest.publish(db, draft, "SS_PRBC", parsed["subsystem"]["name"], None,
                       parsed["subsystem"]["apb"])
        from app.models import RiskRecord
        record = db.query(RiskRecord).filter_by(seq_no=5).one()
        assert db.get(Substation, record.attach_id).code == record.attach_label
    engine.dispose()
