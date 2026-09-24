"""Regression coverage for the reviewed single-view Jakarta/Banten inputs."""
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import AnalyticalView, ViewMembership, Substation, GeneratingUnit
from app.services import ingest
from app.services.ingest_parser import parse_upload
from scripts._reviewed_jakban import build_reviewed, RISK_PINS, SOURCES, ROOT


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
    assert {n["external_key"] for n in original["objects"]} <= set(parsed_objects)
    parsed_edges = {(e["from_external_key"], e["to_external_key"],
                     e.get("relation_type", "CONNECTED_TO")) for e in parsed["connections"]}
    assert {(e["from_external_key"], e["to_external_key"],
             e.get("relation_type", "CONNECTED_TO")) for e in original["connections"]} <= parsed_edges
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


def test_reviewed_boundary_evidence_is_explicit():
    expected = {
        "SS_LBK": {"NCKUPA": "CKUPA", "CKNN?": "DLRA", "TGBRU3": "SUJYA",
                    "JTKBR": "JTAKE", "BSH": "CKDRU"},
        "SS_GUCL": {"SARAN4": "SRANG", "RGKOT": "SARAN4", "BUNAR": "RGKOT",
                     "KRACAK": "BUNAR"},
        "SS_PRBC": {"PDKLP": "BKASI", "SKTNI": "BKASI", "SMRCN": "BKASI"},
    }
    for code, bays in expected.items():
        path = ROOT / "samples" / f"{code.lower()}_ingest.xlsx"
        parsed = parse_upload(path.read_bytes(), path.name)
        actual = {n["external_key"]: n.get("bay_feeder_key")
                  for n in parsed["objects"] if n.get("is_bay")}
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
