"""/ingest -- stateless: upload -> draft blob -> review -> preview -> publish.

Nothing touches the DB until publish. The draft is a JSON blob the client
re-sends on every call.
"""
import importlib
import json
import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

SAMPLE_JSON = Path(__file__).resolve().parent.parent / "samples" / "ss_cwd_ingest.json"
SAMPLE_XLSX = Path(__file__).resolve().parent.parent / "samples" / "ss_cwd_ingest.xlsx"
LBK_XLSX = Path(__file__).resolve().parent.parent / "samples" / "ss_lbk_ingest.xlsx"


@pytest.fixture()
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    import app.db as db_mod
    import app.models
    importlib.reload(db_mod)
    for name in ("app.models", "app.services.topology", "app.services.reconciliation",
                 "app.services.sld_renderer", "app.services.ingestion",
                 "app.services.ingest_parser", "app.services.ingest",
                 "app.services.editor", "app.services.editor_risks",
                 "app.services.seed_ss_lbk", "app.services.seed_ss_bll",
                 "app.services.seed", "app.api.routes", "app.main"):
        importlib.reload(importlib.import_module(name))
    from fastapi.testclient import TestClient
    import app.main as main_mod
    with TestClient(main_mod.app) as c:
        yield c
    try:
        os.unlink(path)
    except OSError:
        pass


def _draft(client, fmt="xlsx"):
    if fmt == "xlsx":
        r = client.post("/api/ingest/parse-file",
                        files={"file": ("ss_cwd_ingest.xlsx", SAMPLE_XLSX.read_bytes(),
                                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    else:
        payload = json.loads(SAMPLE_JSON.read_text(encoding="utf-8"))
        r = client.post("/api/ingest/parse", json={"payload": payload})
    assert r.status_code == 200, r.text
    return r.json()


def test_parse_xlsx_template_builds_draft(client):
    """The 3-sheet PLN template (Jalur_Transmisi + Gardu_Induk_dan_Aset +
    Data_Kerawanan_Detail) is the primary format."""
    d = _draft(client, "xlsx")
    assert d["subsystem"]["code"] == "SS_CWD"          # from the Info sheet
    assert len(d["nodes"]) == 15
    assert len(d["edges"]) == 13
    assert len(d["risks"]) == 4
    # GITET busbars are split from their 150 kV bus
    keys = {n["external_key"] for n in d["nodes"]}
    assert "GITET_DEPOK" in keys and "DEPOK" in keys
    # IBT links carry a unit number AND feed the right 150 kV bus:
    # GITET Cawang -> CWBRU (Cawang Baru), not CWANG (Cawang Lama, a Tier-2 GI)
    ibt = [e for e in d["edges"] if e["circuit_type_hint"] == "IBT_LINK"]
    assert len(ibt) == 3
    cwang_ibt = [e for e in ibt if e["from_key"] == "GITET_CWANG"]
    assert cwang_ibt and all(e["to_key"] == "CWBRU" for e in cwang_ibt)
    assert d["validation"]["ok"] is True


def test_zero_based_workbook_tiers_are_fully_converted(client):
    """Every value in `Tier (Mulai 0)` is zero-based, including tiers > 0."""
    d = _draft(client, "xlsx")
    tiers = {n["external_key"]: n["tier_hint"] for n in d["nodes"]}
    assert tiers["GITET_CWANG"] == 1
    assert tiers["CWBRU"] == 1
    assert tiers["CWANG"] == 2
    assert tiers["STBDI"] == 3


def test_lbk_template_preserves_single_phi_planned_ibt_and_view_scoped_boundary():
    from app.services.ingest_parser import parse_upload

    payload = parse_upload(LBK_XLSX.read_bytes(), LBK_XLSX.name)
    single = {(c["from_external_key"], c["to_external_key"])
              for c in payload["connections"] if c.get("single_phi")}
    assert {("SNYAN", "GISPD"), ("GISPD", "DNYSA"),
            ("PSKMS", "PSKBR"), ("PSKBR", "GJTGL"),
            ("GJTGL", "PSKMS")} <= single

    nckupa = next(c for c in payload["connections"]
                   if c["from_external_key"] == "NCKUPA" and c["relation_type"] == "IBT_LINK")
    assert nckupa["status_hint"] == "PLANNED"
    assert nckupa["view_keys"] == ["BALARAJA"]

    dksbi = next(o for o in payload["objects"] if o["external_key"] == "DKSBI")
    assert dksbi["role_hint"] == "BOUNDARY"
    assert dksbi["is_bay"] is False
    assert dksbi["bay_view_keys"] == ["KEMBANGAN"]


def test_ingest_multiple_ibt_links_do_not_collide(client):
    """A GITET with several IBT links -- and a hand-added extra one -- must
    materialise without a UNIQUE-constraint crash on subsystem_membership."""
    d = _draft(client, "xlsx")
    d["edges"].append({
        "from_key": "GITET_CWANG", "to_key": "CWBRU", "relation_type": "IBT_LINK",
        "circuit_type_hint": "IBT_LINK", "status_hint": "ENERGIZED",
        "circuit_count": 1, "unit_no": "4", "confidence": 1.0, "confirmed": True})
    r = client.post("/api/ingest/preview.svg", json=d)
    assert r.status_code == 200 and b"<svg" in r.content
    assert b"UNIQUE constraint" not in r.content

    pub = client.post("/api/ingest/publish", json={
        "draft": d, "subsystem_code": "SS_CWD", "subsystem_name": "Cawang 2,3 - Depok 1",
        "effective_date": "2026-06-30"})
    assert pub.status_code == 200, pub.text


def test_bay_stub_preserves_single_or_double_circuit_count(client):
    d = _draft(client, "xlsx")
    bay = next(n for n in d["nodes"] if n["external_key"] == "LKONG2")
    bay["bay_circuit_count"] = 2
    r = client.post("/api/ingest/preview.svg", json=d)
    assert r.status_code == 200, r.text
    root = ET.fromstring(r.text)
    ns = {"s": "http://www.w3.org/2000/svg"}
    stub = root.find('.//s:g[@class="sld-bay"][@data-code="LKONG2"]', ns)
    assert stub is not None and stub.get("data-circuit-count") == "2"
    assert len(stub.findall('s:path', ns)) == 2


def test_parse_json_handoff_still_works(client):
    d = _draft(client, "json")
    assert len(d["nodes"]) == 15 and len(d["edges"]) == 13
    dc = next(e for e in d["edges"] if e["from_key"] == "DEPOK" and e["to_key"] == "CWANG")
    assert dc["needs_review"] is False
    gd = next(n for n in d["nodes"] if n["external_key"] == "GITET_DEPOK")
    assert gd["resolution"] == "NEW"


def test_ingest_flags_an_existing_subsystem(client):
    """Uploading the datasheet of a subsystem that already exists (SS_BLL) must
    be blocked -- the user should edit it via /editor, not bootstrap a copy."""
    from app.services.ingest_parser import normalise
    from app.services import ingest as ingest_svc
    import app.db as db_mod

    # a tiny payload made of GIs that are already SS_BLL members
    payload = normalise({
        "subsystem": {"code": "SS_WHATEVER", "name": "x"},
        "objects": [
            {"external_key": "NBRJA", "object_type": "GI", "raw_label": "NBRJA", "tier_hint": 1},
            {"external_key": "LSTEL", "object_type": "GI", "raw_label": "LSTEL", "tier_hint": 2},
            {"external_key": "SPMIL", "object_type": "GI", "raw_label": "SPMIL", "tier_hint": 3},
        ],
        "connections": [
            {"from_external_key": "NBRJA", "to_external_key": "LSTEL"},
            {"from_external_key": "LSTEL", "to_external_key": "SPMIL"},
        ],
        "risks": [],
    })
    with db_mod.SessionLocal() as db:
        d = ingest_svc.build_draft(db, payload)
    assert d["existing"] is not None
    assert d["existing"]["subsystem_code"] == "SS_BLL"
    assert d["validation"]["ok"] is False
    assert any("SS_BLL" in p and "/editor" in p for p in d["validation"]["problems"])


def test_parse_writes_nothing_to_db(client):
    _draft(client)
    assert not any(s["code"] == "SS_CWD" for s in client.get("/api/subsystems").json())
    assert not any(v["view_key"] == "SS_CWD_FULL" for v in client.get("/api/views").json())


def test_coordinates_survive_draft_publish_and_graph(client):
    payload = {
        "subsystem": {"code": "SS_GEO", "name": "Geo fixture"},
        "objects": [
            {"external_key": "GEOW", "object_type": "GI", "raw_label": "Geo West",
             "tier_hint": 1, "latitude": -6.2, "longitude": 106.5},
            {"external_key": "GEOE", "object_type": "GI", "raw_label": "Geo East",
             "tier_hint": 2, "latitude": -6.3, "longitude": 107.5},
        ],
        "connections": [{"from_external_key": "GEOW", "to_external_key": "GEOE"}],
        "risks": [],
    }
    draft = client.post("/api/ingest/parse", json=payload).json()
    assert draft["nodes"][0]["latitude"] == -6.2
    published = client.post("/api/ingest/publish", json={
        "draft": draft, "subsystem_code": "SS_GEO", "subsystem_name": "Geo fixture",
    })
    assert published.status_code == 200, published.text
    graph = client.get(f"/api/views/{published.json()['view_id']}/graph").json()
    coords = {n["code"]: (n["latitude"], n["longitude"]) for n in graph["nodes"]
              if n["kind"] == "SUBSTATION"}
    assert coords == {"GEOW": (-6.2, 106.5), "GEOE": (-6.3, 107.5)}


def test_preview_renders_from_blob_and_rolls_back(client):
    d = _draft(client)
    r = client.post("/api/ingest/preview.svg", json=d)
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in r.content
    # canon still clean after a preview
    assert not any(s["code"] == "SS_CWD" for s in client.get("/api/subsystems").json())


def test_preview_never_500s_on_a_broken_draft(client):
    d = _draft(client)
    # duplicate a code -> materialise would hit the UNIQUE constraint
    d["nodes"][3]["confirmed_code"] = d["nodes"][2]["confirmed_code"]
    r = client.post("/api/ingest/preview.svg", json=d)
    assert r.status_code == 200
    assert b"<svg" in r.content
    assert "dipakai dua node".encode() in r.content


def test_validate_blocks_unresolved_node(client):
    d = _draft(client)
    for n in d["nodes"]:
        if n["external_key"] == "TRSNA":
            n["resolution"] = "NEW"
            n["confirmed_code"] = ""
    v = client.post("/api/ingest/validate", json=d).json()
    assert v["ok"] is False
    assert any("belum diberi kode" in p for p in v["problems"])


def test_publish_materialises_subsystem(client):
    d = _draft(client)
    pub = client.post("/api/ingest/publish", json={
        "draft": d, "subsystem_code": "SS_CWD",
        "subsystem_name": "Cawang 2,3 - Depok 1", "effective_date": "2026-06-30"})
    assert pub.status_code == 200, pub.text
    assert pub.json()["view_key"] == "SS_CWD_FULL"

    views = client.get("/api/views").json()
    cwd = next(v for v in views if v["view_key"] == "SS_CWD_FULL")
    g = client.get(f"/api/views/{cwd['id']}/graph").json()
    subs = {n["code"]: n for n in g["nodes"] if n["kind"] == "SUBSTATION"}
    assert len(subs) == 15
    # Tier bands match Buku Kerawanan Sec 2.7
    assert subs["DEPOK"]["tier"] == 1 and subs["CWBRU"]["tier"] == 1
    assert subs["CWANG"]["tier"] == 2 and subs["ABDGP"]["tier"] == 2
    assert subs["STBDI"]["tier"] == 3 and subs["DNYSA"]["tier"] == 3
    assert len(g["overlays"]["risk"]) == 4
    assert all(r["attach_kind"] for r in g["overlays"]["risk"])
    assert client.get(f"/api/views/{cwd['id']}/sld.svg").status_code == 200

    # a traced (0.5) ruas carries a NEEDS_REVIEW note on the canonical circuit
    import app.db as db_mod
    from app.models import Circuit
    with db_mod.SessionLocal() as db:
        c = db.query(Circuit).filter(Circuit.code == "SUTT_CWBRU_DRNTG").first()
        assert c is not None and (c.note or "").startswith("NEEDS_REVIEW")
        assert c.confidence < 0.9


def test_publish_refuses_duplicate_subsystem(client):
    d = _draft(client)
    body = {"draft": d, "subsystem_code": "SS_CWD",
            "subsystem_name": "x", "effective_date": None}
    assert client.post("/api/ingest/publish", json=body).status_code == 200
    r2 = client.post("/api/ingest/publish", json=body)
    assert r2.status_code == 400
    assert "sudah ada" in r2.json()["detail"]


def test_publish_refuses_invalid_draft(client):
    d = _draft(client)
    for n in d["nodes"]:
        if n["external_key"] == "MPLMA":
            n["confirmed_code"] = ""
    r = client.post("/api/ingest/publish", json={
        "draft": d, "subsystem_code": "SS_CWD", "subsystem_name": "x",
        "effective_date": None})
    assert r.status_code == 400
    assert "validasi gagal" in r.json()["detail"]


def test_parser_rejects_payload_without_subsystem(client):
    r = client.post("/api/ingest/parse", json={"payload": {"objects": []}})
    assert r.status_code == 400
    assert "wajib" in r.json()["detail"]


def test_explicit_symbol_counts_survive_excel_draft_preview_publish(client, monkeypatch):
    import openpyxl
    from app.services.ingest_parser import parse_xlsx

    class Sheet:
        def __init__(self, rows):
            self.rows = rows
        def iter_rows(self, values_only=True):
            return iter(self.rows)

    class Book(dict):
        @property
        def sheetnames(self):
            return list(self)

    book = Book({
        'Info': Sheet([('Kode Subsistem', 'SS_SYMBOLS'), ('Nama Subsistem', 'Symbol test')]),
        'Gardu_Induk_dan_Aset': Sheet([
            ('Kode', 'Tipe', 'Tier', 'Jumlah Trafo', 'Jumlah Kapasitor'),
            ('SYMSRC', 'Busbar GI', 1, 0, 0), ('SYMLOAD', 'Busbar GI', 2, 3, 2)]),
        'Jalur_Transmisi': Sheet([('Dari GI', 'Ke GI', 'Jumlah Sirkit'), ('SYMSRC', 'SYMLOAD', 2)]),
    })
    monkeypatch.setattr(openpyxl, 'load_workbook', lambda *a, **kw: book)
    payload = parse_xlsx(b'', 'symbols.xlsx')
    draft = client.post('/api/ingest/parse', json={'payload': payload}).json()
    load = next(n for n in draft['nodes'] if n['external_key'] == 'SYMLOAD')
    assert (load['transformer_count'], load['capacitor_count']) == (3, 2)
    response = client.post('/api/ingest/preview.svg', json=draft)
    assert response.status_code == 200
    assert response.text.count('class="load-transformer"') == 3
    assert response.text.count('class="shunt-capacitor"') == 2
    published = client.post('/api/ingest/publish', json={
        'draft': draft, 'subsystem_code': 'SS_SYMBOLS', 'subsystem_name': 'Symbol test'})
    assert published.status_code == 200, published.text
    svg = client.get(f'/api/views/{published.json()["view_id"]}/sld.svg').text
    assert svg.count('class="load-transformer"') == 3
    assert svg.count('class="shunt-capacitor"') == 2


def test_negative_symbol_count_is_not_published(client):
    draft = _draft(client, 'json')
    draft['nodes'][0]['capacitor_count'] = -1
    result = client.post('/api/ingest/validate', json=draft).json()
    assert not result['ok']
    assert any('jumlah simbol' in p for p in result['problems'])


def test_multiview_500kv_and_multi_risk_tags_publish(client, monkeypatch):
    import openpyxl
    from app.services.ingest_parser import parse_xlsx

    class Sheet:
        def __init__(self, rows): self.rows = rows
        def iter_rows(self, values_only=True): return iter(self.rows)
    class Book(dict):
        @property
        def sheetnames(self): return list(self)

    book = Book({
        'Info': Sheet([('Kode Subsistem', 'SS_500_MULTI'), ('Nama Subsistem', '500 kV multiview')]),
        'Views': Sheet([('Kode View', 'Nama View', 'Sumber Tier-1 (kode GI, pisah ;)'),
                        ('V1', 'View one', 'A'), ('V2', 'View two', 'B')]),
        'Gardu_Induk_dan_Aset': Sheet([
            ('Kode', 'Tipe', 'Tier', 'Tegangan', 'No Kerawanan', 'Sudut Pandang', 'Bus Terhubung'),
            ('A', 'Busbar GITET', 1, '500 kV', None, 'V1', None),
            ('X', 'Busbar GITET', 2, '500 kV', '5;7', 'V1', None),
            ('GEN', 'Pembangkit', 1, '500 kV', None, 'V1', 'A'),
            ('B', 'Busbar GITET', 1, '500 kV', None, 'V2', None),
            ('Y', 'Busbar GITET', 2, '500 kV', None, 'V2', None)]),
        'Jalur_Transmisi': Sheet([
            ('Dari GI', 'Ke GI', 'Jumlah Sirkit', 'No Kerawanan', 'Sudut Pandang'),
            ('A', 'X', 2, 7, 'V1'), ('B', 'Y', 2, None, 'V2')]),
        'Data_Kerawanan_Detail': Sheet([
            ('No', 'Kondisi / Permasalahan'), (5, 'Risk at X'), (7, 'Risk on A-X')]),
    })
    monkeypatch.setattr(openpyxl, 'load_workbook', lambda *a, **kw: book)
    payload = parse_xlsx(b'', 'multi.xlsx')
    assert [v['view_key'] for v in payload['subsystem']['views']] == ['V1', 'V2']
    assert next(o for o in payload['objects'] if o['external_key'] == 'GEN')['object_type'] == 'GENERATING_UNIT'
    assert [(r['seq_no'], r['pin_kind'], r['pin_key']) for r in payload['risks']] == [
        (5, 'SUBSTATION', 'X'), (7, 'CIRCUIT', 'A-X')]
    draft = client.post('/api/ingest/parse', json={'payload': payload}).json()
    assert draft['validation']['ok'], draft['validation']['problems']
    published = client.post('/api/ingest/publish', json={
        'draft': draft, 'subsystem_code': 'SS_500_MULTI', 'subsystem_name': '500 kV multiview'})
    assert published.status_code == 200, published.text
    assert {v['view_key'] for v in published.json()['views']} == {'SS_500_MULTI_V1', 'SS_500_MULTI_V2'}
    views = {v['view_key']: v for v in client.get('/api/views').json()}
    g1 = client.get(f"/api/views/{views['SS_500_MULTI_V1']['id']}/graph").json()
    g2 = client.get(f"/api/views/{views['SS_500_MULTI_V2']['id']}/graph").json()
    assert {n['code'] for n in g1['nodes']} >= {'A', 'X', 'GEN'}
    assert {n['code'] for n in g2['nodes']} >= {'B', 'Y'}
    assert all(n['code'] not in {'B', 'Y'} for n in g1['nodes'])
