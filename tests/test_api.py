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
