"""Regression coverage for the reviewed single-view Jakarta/Banten inputs."""
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import AnalyticalView, ViewMembership, Substation, GeneratingUnit
from app.services import ingest
from app.services.ingest_parser import parse_upload
from scripts._reviewed_jakban import build_reviewed, SOURCES, ROOT


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
    assert parsed["risks"] == original["risks"]
    # Only interpretation of the source's view prose may change.
    def without_views(rows):
        return [{k: v for k, v in row.items()
                 if k not in {"view_keys", "bay_view_keys", "bay_appearances"}}
                for row in rows]
    assert without_views(parsed["objects"]) == without_views(original["objects"])
    assert without_views(parsed["connections"]) == without_views(original["connections"])
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
