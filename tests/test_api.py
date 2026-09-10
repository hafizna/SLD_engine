"""API contract tests -- what a web viewer consumes."""
import importlib
import os
import tempfile

import pytest


@pytest.fixture()
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"
    import app.db as db_mod
    importlib.reload(db_mod)
    for name in ("app.models", "app.services.topology", "app.services.reconciliation",
                 "app.services.sld_renderer", "app.services.ingestion",
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


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_subsystems_lists_ss_lbk(client):
    data = client.get("/api/subsystems").json()
    assert any(s["code"] == "SS_LBK" for s in data)


def test_two_views_no_merged(client):
    keys = {v["view_key"] for v in client.get("/api/views").json()}
    # SS_LBK spans two book SLDs -> two per-side views, and no force-merged
    # "SS_LBK_FULL" view.
    ss_lbk_keys = {k for k in keys if k.startswith("SS_LBK")}
    assert ss_lbk_keys == {"SS_LBK_KEMBANGAN", "SS_LBK_BALARAJA"}


def test_ss_bll_single_view_two_sources(client):
    views = client.get("/api/views").json()
    bll = next(v for v in views if v["view_key"] == "SS_BLL_FULL")
    g = client.get(f"/api/views/{bll['id']}/graph").json()
    # two independent Tier-1 busbars from two different GITETs
    t1 = sorted(n["code"] for n in g["nodes"] if n.get("tier") == 1 and n.get("role") == "SOURCE")
    assert {"NBRJA", "LKBRU"}.issubset(set(t1))
    # they are not tied at Tier-1
    id_to_code = {n["id"]: n.get("code") for n in g["nodes"] if n["kind"] == "SUBSTATION"}
    tied = {
        frozenset((id_to_code.get(e["from_substation_id"]), id_to_code.get(e["to_substation_id"])))
        for e in g["edges"]
    }
    assert frozenset(("NBRJA", "LKBRU")) not in tied
    # the one book kerawanan point lands on the Lengkong Baru - Serpong ruas
    assert len(g["overlays"]["risk"]) == 1
    srpng = next(n for n in g["nodes"] if n.get("code") == "SRPNG")
    assert srpng["tier"] == 2


def test_view_graph_contract(client):
    views = client.get("/api/views").json()
    bal = next(v for v in views if v["view_key"] == "SS_LBK_BALARAJA")
    g = client.get(f"/api/views/{bal['id']}/graph").json()

    assert g["view"]["rule_profile"] == "SUBSYSTEM_150"
    assert len(g["nodes"]) > 20
    assert len(g["edges"]) > 20
    assert len(g["overlays"]["risk"]) == 6
    assert len(g["overlays"]["defense_scheme"]) == 3

    nbrja = next(n for n in g["nodes"] if n.get("code") == "NBRJA")
    assert nbrja["tier"] == 1
    assert nbrja["role"] == "SOURCE"

    nckupa = next(n for n in g["nodes"] if n.get("code") == "NCKUPA")
    assert nckupa["status"] == "NEW_NOT_ENERGIZED"
    assert nckupa["tier"] is None


def test_kembangan_view_has_kmbgn_tier_1(client):
    views = client.get("/api/views").json()
    kem = next(v for v in views if v["view_key"] == "SS_LBK_KEMBANGAN")
    g = client.get(f"/api/views/{kem['id']}/graph").json()
    kmbgn = next(n for n in g["nodes"] if n.get("code") == "KMBGN")
    assert kmbgn["tier"] == 1


def test_sld_svg_renders(client):
    views = client.get("/api/views").json()
    full = next(v for v in views if v["view_key"] == "SS_LBK_BALARAJA")
    r = client.get(f"/api/views/{full['id']}/sld.svg")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in r.content
    assert b"overlay-risk" in r.content


def test_svg_accounts_for_every_mapped_object(client):
    """Nothing from the parse may vanish: every substation, circuit and bay is
    either drawn (data-node / a circuit path / a bay stub) or listed in the
    mapping-audit strip with a reason."""
    import re

    views = client.get("/api/views").json()
    for v in views:
        vid = v["id"]
        svg = client.get(f"/api/views/{vid}/sld.svg").content.decode()
        g = client.get(f"/api/views/{vid}/graph").json()

        drawn_node_ids = set(map(int, re.findall(r'data-node-id="(\d+)"', svg)))
        audit_codes = set(re.findall(r'data-audit-code="([^"]+)"', svg))
        stub_names = set(re.findall(r'font-size="8.5" text-anchor="middle"[^>]*>([^<]+)</text>', svg))

        for n in g["nodes"]:
            if n["kind"] != "SUBSTATION":
                continue
            drawn = n["id"] in drawn_node_ids
            stub = n["name"] in stub_names          # bay-only GI: drawn as a stub
            listed = n.get("code") in audit_codes   # accounted for in the audit strip
            assert drawn or stub or listed, (
                f"view {v['view_key']}: {n.get('code')} ({n['name']}) "
                f"neither drawn nor stubbed nor audited"
            )

        # every circuit is either a drawn path or in the audit strip
        drawn_circ_ids = set(map(int, re.findall(r'data-circuit-id="(\d+)"', svg)))
        for e in g["edges"]:
            assert e["id"] in drawn_circ_ids or e["code"] in audit_codes, (
                f"view {v['view_key']}: circuit {e['code']} neither drawn nor audited"
            )


def test_layout_roundtrip(client):
    import re

    views = client.get("/api/views").json()
    vid = views[0]["id"]
    g = client.get(f"/api/views/{vid}/graph").json()
    # a plain GI (not a GITET -- those get snapped above their LV bus)
    sub = next(n for n in g["nodes"]
               if n["kind"] == "SUBSTATION" and n.get("type") not in ("GITET", "GISTET")
               and n.get("tier"))

    assert client.get(f"/api/views/{vid}/layout").json()["positions"] == []
    r = client.patch(f"/api/views/{vid}/layout", json={
        "positions": [{"node_kind": "SUBSTATION", "node_id": sub["id"], "x": 900.0, "y": 640.0}],
        "updated_by": "tester",
    })
    assert r.json()["saved"] == 1
    saved = client.get(f"/api/views/{vid}/layout").json()["positions"]
    assert saved and saved[0]["x"] == 900.0 and saved[0]["y"] == 640.0

    # the saved position appears in the rendered SVG (frame may only clamp, not
    # translate, once a layout is saved)
    svg = client.get(f"/api/views/{vid}/sld.svg").content.decode()
    m = re.search(rf'data-node-id="{sub["id"]}"[^>]*data-x="([\d.]+)"[^>]*data-y="([\d.]+)"', svg)
    assert m
    assert abs(float(m.group(1)) - 900.0) < 5
    assert abs(float(m.group(2)) - 640.0) < 5
    assert client.delete(f"/api/views/{vid}/layout").json()["cleared"] == 1


def test_change_request_workflow(client):
    """PROBIS_KONSEP.md: a structural change is a ChangeRequest -> validate ->
    impact preview -> review -> publish (new TopologyVersion, old superseded)."""
    views = client.get("/api/views").json()
    vid = next(v["id"] for v in views if v["view_key"] == "SS_LBK_BALARAJA")

    # NCKUPA is NEW_NOT_ENERGIZED -> not in the graph; edit does not touch canon yet
    g0 = client.get(f"/api/views/{vid}/graph").json()
    n0 = next((n for n in g0["nodes"] if n.get("code") == "NCKUPA"), None)
    assert n0 is not None and n0["status"] == "NEW_NOT_ENERGIZED"

    cr = client.post(f"/api/views/{vid}/change-requests", json={
        "title": "COD GITET New Cikupa", "effective_date": "2026-11-01",
        "source_ref": "RUPTL 2025-2034",
    }).json()
    crid = cr["id"]
    assert cr["status"] == "DRAFT"

    client.post(f"/api/change-requests/{crid}/lines", json={
        "action": "SET_STATUS", "target_kind": "SUBSTATION", "target_ref": "NCKUPA",
        "payload": {"status": "ENERGIZED"}})
    client.post(f"/api/change-requests/{crid}/lines", json={
        "action": "SET_STATUS", "target_kind": "CIRCUIT", "target_ref": "PHT_NCKUPA_JTAKE",
        "payload": {"status": "ENERGIZED"}})

    # canon unchanged until publish
    assert next(n for n in client.get(f"/api/views/{vid}/graph").json()["nodes"]
                if n.get("code") == "NCKUPA")["status"] == "NEW_NOT_ENERGIZED"

    val = client.post(f"/api/change-requests/{crid}/validate").json()
    assert val["ok"] is True

    imp = client.post(f"/api/change-requests/{crid}/impact").json()
    assert "PHT_NCKUPA_JTAKE" in imp["circuit_added"]
    assert any(t["code"] == "NCKUPA" for t in imp["tier_changes"])

    client.post(f"/api/change-requests/{crid}/review", json={"reviewed_by": "tester"})
    pub = client.post(f"/api/change-requests/{crid}/publish", json={"reviewed_by": "tester"}).json()
    assert pub["version"].startswith("TV-SS_LBK-CR-")
    assert pub["superseded"] == "TV-SS_LBK-2026-06"
    assert pub["applied"] == 2

    # now the canon reflects it
    nf = next(n for n in client.get(f"/api/views/{vid}/graph").json()["nodes"]
              if n.get("code") == "NCKUPA")
    assert nf["status"] == "ENERGIZED"
    assert nf["tier"] is not None


def test_cr_validation_blocks_isolating_a_gi(client):
    views = client.get("/api/views").json()
    vid = next(v["id"] for v in views if v["view_key"] == "SS_BLL_FULL")
    crid = client.post(f"/api/views/{vid}/change-requests", json={"title": "bad"}).json()["id"]
    # de-energise the only feed into Tigaraksa -> it should become isolated
    client.post(f"/api/change-requests/{crid}/lines", json={
        "action": "REMOVE_CIRCUIT", "target_kind": "CIRCUIT", "target_ref": "SUTT_CITRA_TGRSA"})
    val = client.post(f"/api/change-requests/{crid}/validate").json()
    assert val["ok"] is False
    assert any("terisolasi" in p for p in val["problems"])


def test_kerawanan_category_dropdown(client):
    views = client.get("/api/views").json()
    vid = next(v["id"] for v in views if v["view_key"] == "SS_BLL_FULL")
    r = client.post(f"/api/views/{vid}/risks", json={
        "category": "N-1-1", "title": "uji", "condition": "x",
        "mitigation": "y", "follow_up": "z", "priority": "High",
        "attach_kind": "CIRCUIT", "attach_code": "SUTT_LKBRU_SRPNG"}).json()
    assert r["category"] == "N-1-1"
    rk = r["risk_key"]
    r2 = client.patch(f"/api/risks/{rk}", json={"category": "N-0"}).json()
    assert r2["category"] == "N-0"
    assert client.delete(f"/api/risks/{rk}").json()["deleted"] == rk
