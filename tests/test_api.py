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
                 "app.services.seed_ss_lbk", "app.services.seed", "app.api.routes",
                 "app.main"):
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


def test_view_graph_contract(client):
    views = client.get("/api/views").json()
    full = next(v for v in views if v["view_key"] == "SS_LBK_FULL")
    g = client.get(f"/api/views/{full['id']}/graph").json()

    assert g["view"]["rule_profile"] == "SUBSYSTEM_150"
    assert len(g["nodes"]) > 30
    assert len(g["edges"]) > 30
    assert len(g["overlays"]["risk"]) == 6
    assert len(g["overlays"]["defense_scheme"]) == 3

    kmbgn = next(n for n in g["nodes"] if n.get("code") == "KMBGN")
    assert kmbgn["tier"] == 1
    assert kmbgn["role"] == "SOURCE"

    nckupa = next(n for n in g["nodes"] if n.get("code") == "NCKUPA")
    assert nckupa["status"] == "NEW_NOT_ENERGIZED"
    assert nckupa["tier"] is None


def test_sld_svg_renders(client):
    views = client.get("/api/views").json()
    full = next(v for v in views if v["view_key"] == "SS_LBK_FULL")
    r = client.get(f"/api/views/{full['id']}/sld.svg")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in r.content
    assert b"overlay-risk" in r.content
