"""HTTP API.

The JSON view contract (`/api/views/{id}/graph`) is what a web viewer should
consume instead of hard-coding nodes/edges: it returns canonical nodes with
computed Tier + role, canonical edges with type/status/confidence, and the
semantic overlays (risk / defense scheme) as separate blocks so the viewer can
toggle layers.
"""
from __future__ import annotations

import io
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    AnalyticalView,
    Circuit,
    DefenseScheme,
    DSRelation,
    GeneratingUnit,
    ObservedObject,
    RiskRecord,
    Substation,
    Subsystem,
    Transformer,
)
from app.schemas import CreateViewIn, ObservationBatchIn
from app.services.excel_register import export_register
from app.services.ingestion import save_observation_batch
from app.services.reconciliation import classify, find_candidates
from app.services.sld_renderer import render_view_svg
from app.services.topology import calculate_tier, get_view_graph

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}


# ---- subsystems ----------------------------------------------------------

@router.get("/subsystems")
def list_subsystems(db: Session = Depends(get_db)):
    return [
        {"id": s.id, "code": s.code, "name": s.name, "apb": s.apb, "source_ref": s.source_ref}
        for s in db.query(Subsystem).filter(Subsystem.active.is_(True)).all()
    ]


# ---- analytical views --------------------------------------------------

@router.get("/views")
def list_views(db: Session = Depends(get_db)):
    return [
        {
            "id": v.id, "view_key": v.view_key, "view_type": v.view_type, "name": v.name,
            "rule_profile": v.rule_profile, "subsystem_id": v.subsystem_id,
            "scenario_id": v.scenario_id, "layout_hint": v.layout_hint,
        }
        for v in db.query(AnalyticalView).all()
    ]


@router.post("/views")
def create_view(payload: CreateViewIn, db: Session = Depends(get_db)):
    v = AnalyticalView(**payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return {"id": v.id, "view_key": v.view_key}


@router.get("/views/{view_id}/graph")
def view_graph(view_id: int, db: Session = Depends(get_db)):
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise HTTPException(404, "View not found")

    nodes, edges, roles, seeds, _ = get_view_graph(db, v)
    tier = calculate_tier(db, v)

    node_out = []
    for (kind, nid), obj in nodes.items():
        role = roles.get((kind, nid), "")
        entry = {
            "kind": kind, "id": nid, "role": role,
            "tier": tier.get((kind, nid)),
            "is_seed": (kind, nid) in seeds,
        }
        if kind == "SUBSTATION":
            entry.update({
                "code": obj.code, "name": obj.name, "type": obj.substation_type,
                "voltage_kv": obj.voltage_kv, "status": obj.status,
                "busbar_config": obj.busbar_config, "busbar_note": obj.busbar_note,
                "has_transformer": obj.has_transformer,
                "has_shunt_capacitor": obj.has_shunt_capacitor,
                "symbol_note": obj.symbol_note, "note": obj.note,
                "confidence": obj.confidence,
            })
        elif kind == "GENERATING_UNIT":
            entry.update({
                "code": obj.code, "name": obj.name, "unit_type": obj.unit_type,
                "rated_mw": obj.rated_mw, "unit_count": obj.unit_count,
                "outlet_substation_id": obj.outlet_substation_id, "status": obj.status,
            })
        elif kind == "TRANSFORMER":
            entry.update({
                "code": obj.code, "name": obj.name, "transformer_type": obj.transformer_type,
                "substation_id": obj.substation_id, "unit_no": obj.unit_no,
                "rating_mva": obj.rating_mva, "status": obj.status,
            })
        node_out.append(entry)

    edge_out = [
        {
            "id": c.id, "code": c.code, "name": c.name, "circuit_type": c.circuit_type,
            "voltage_kv": c.voltage_kv, "status": c.status,
            "from_substation_id": c.from_substation_id, "to_substation_id": c.to_substation_id,
            "circuit_count": c.circuit_count, "single_phi": c.single_phi,
            "scenario_id": c.scenario_id, "confidence": c.confidence, "note": c.note,
        }
        for c in edges
    ]

    risks = []
    schemes = []
    if v.subsystem_id:
        for r in db.query(RiskRecord).filter(RiskRecord.subsystem_id == v.subsystem_id).order_by(RiskRecord.seq_no).all():
            risks.append({
                "risk_key": r.risk_key, "seq_no": r.seq_no, "title": r.title,
                "condition": r.condition, "impact": r.impact, "mitigation": r.mitigation,
                "follow_up": r.follow_up, "priority": r.priority, "status": r.status,
                "attach_kind": r.attach_kind, "attach_id": r.attach_id, "attach_label": r.attach_label,
            })
        rel_by_scheme: dict[int, list] = {}
        for rel in db.query(DSRelation).filter(DSRelation.subsystem_id == v.subsystem_id).all():
            rel_by_scheme.setdefault(rel.scheme_id, []).append({
                "attach_kind": rel.attach_kind, "attach_id": rel.attach_id,
                "attach_label": rel.attach_label, "role": rel.role, "coverage_note": rel.coverage_note,
            })
        for d in db.query(DefenseScheme).filter(DefenseScheme.id.in_(rel_by_scheme.keys() or [-1])).all():
            schemes.append({
                "scheme_key": d.scheme_key, "name": d.name, "scheme_type": d.scheme_type,
                "status": d.status, "scope_level": d.scope_level, "target_mw": d.target_mw,
                "target_mw_planned": d.target_mw_planned, "stages": d.stages, "reference": d.reference,
                "relations": rel_by_scheme.get(d.id, []),
            })

    return {
        "view": {
            "id": v.id, "key": v.view_key, "name": v.name, "rule_profile": v.rule_profile,
            "scenario_id": v.scenario_id, "layout_hint": v.layout_hint,
        },
        "nodes": node_out,
        "edges": edge_out,
        "overlays": {"risk": risks, "defense_scheme": schemes},
    }


@router.get("/views/{view_id}/sld.svg")
def view_svg(view_id: int, db: Session = Depends(get_db)):
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise HTTPException(404, "View not found")
    return Response(render_view_svg(db, v), media_type="image/svg+xml")


# ---- observations / reconciliation -----------------------------------

@router.post("/observations/import")
def import_observations(batch: ObservationBatchIn, db: Session = Depends(get_db)):
    doc = save_observation_batch(db, batch)
    return {"document_id": doc.id, "filename": doc.filename}


@router.get("/register.xlsx")
def download_register(db: Session = Depends(get_db)):
    """Export the canonical model as the Corporate Topology Register workbook."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        export_register(db, tmp.name)
        tmp.seek(0)
        data = open(tmp.name, "rb").read()
    return Response(
        data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Corporate_Topology_Register.xlsx"'},
    )


@router.get("/observations/{observed_id}/candidates")
def candidates(observed_id: int, db: Session = Depends(get_db)):
    obs = db.get(ObservedObject, observed_id)
    if not obs:
        raise HTTPException(404, "Observed object not found")
    rows = find_candidates(db, obs)
    return [
        {
            "substation_id": r["substation"].id, "code": r["substation"].code,
            "name": r["substation"].name, "score": round(r["score"], 3),
            "classification": classify(r["score"]), "evidence": r["evidence"],
        }
        for r in rows
    ]
