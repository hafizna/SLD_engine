"""HTTP API.

The JSON view contract (`/api/views/{id}/graph`) is what a web viewer should
consume instead of hard-coding nodes/edges: it returns canonical nodes with
computed Tier + role, canonical edges with type/status/confidence, and the
semantic overlays (risk / defense scheme) as separate blocks so the viewer can
toggle layers.
"""
from __future__ import annotations

import io
import json
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (
    AnalyticalView,
    Circuit,
    DefenseScheme,
    DiagramNodePosition,
    DSRelation,
    GeneratingUnit,
    ObservedObject,
    RiskRecord,
    Substation,
    Subsystem,
    Transformer,
)
from app.schemas import (
    CRCreateIn,
    CRLineIn,
    CRRejectIn,
    CRReviewIn,
    CreateViewIn,
    LayoutPatchIn,
    ObservationBatchIn,
    RiskIn,
    RiskPatch,
)
from app.services import editor, editor_risks
from app.services.editor import EditError
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
                "risk_key": r.risk_key, "seq_no": r.seq_no, "category": r.category,
                "title": r.title, "condition": r.condition, "impact": r.impact,
                "mitigation": r.mitigation, "follow_up": r.follow_up,
                "horizon": r.horizon, "priority": r.priority, "status": r.status,
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

    positions = [
        {"node_kind": p.node_kind, "node_id": p.node_id, "x": p.x, "y": p.y, "pinned": p.pinned}
        for p in db.query(DiagramNodePosition).filter(DiagramNodePosition.view_id == v.id).all()
    ]

    return {
        "view": {
            "id": v.id, "key": v.view_key, "name": v.name, "rule_profile": v.rule_profile,
            "scenario_id": v.scenario_id, "layout_hint": v.layout_hint,
        },
        "nodes": node_out,
        "edges": edge_out,
        "overlays": {"risk": risks, "defense_scheme": schemes},
        # manually-saved node positions for this view; the SVG carries the full
        # auto-layout coords as data-x / data-y on each <g class="sld-node">.
        "layout": {"positions": positions},
    }


@router.get("/views/{view_id}/sld.svg")
def view_svg(view_id: int, db: Session = Depends(get_db)):
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise HTTPException(404, "View not found")
    return Response(render_view_svg(db, v), media_type="image/svg+xml")


# ---- diagram layout: drag-and-drop persistence -----------------------
# The renderer's auto-layout is a seed. A viewer that lets a person drag
# nodes POSTs the new positions back here; the next render uses them.

@router.get("/views/{view_id}/layout")
def get_layout(view_id: int, db: Session = Depends(get_db)):
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise HTTPException(404, "View not found")
    rows = db.query(DiagramNodePosition).filter(DiagramNodePosition.view_id == view_id).all()
    return {
        "view_id": view_id,
        "positions": [
            {
                "node_kind": p.node_kind, "node_id": p.node_id,
                "x": p.x, "y": p.y, "pinned": p.pinned,
                "updated_by": p.updated_by,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in rows
        ],
    }


@router.patch("/views/{view_id}/layout")
def patch_layout(view_id: int, payload: LayoutPatchIn, db: Session = Depends(get_db)):
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise HTTPException(404, "View not found")

    existing = {
        (p.node_kind, p.node_id): p
        for p in db.query(DiagramNodePosition).filter(DiagramNodePosition.view_id == view_id).all()
    }
    keep: set[tuple[str, int]] = set()
    for pos in payload.positions:
        key = (pos.node_kind, pos.node_id)
        keep.add(key)
        row = existing.get(key)
        if row is None:
            db.add(DiagramNodePosition(
                view_id=view_id, node_kind=pos.node_kind, node_id=pos.node_id,
                x=pos.x, y=pos.y, pinned=pos.pinned, updated_by=payload.updated_by,
            ))
        else:
            row.x, row.y, row.pinned = pos.x, pos.y, pos.pinned
            row.updated_by = payload.updated_by
            row.updated_at = datetime.utcnow()
    if payload.replace:
        for key, row in existing.items():
            if key not in keep:
                db.delete(row)
    db.commit()
    return {"view_id": view_id, "saved": len(payload.positions),
            "cleared": len([k for k in existing if payload.replace and k not in keep])}


@router.delete("/views/{view_id}/layout")
def reset_layout(view_id: int, db: Session = Depends(get_db)):
    """Drop all manual positions -> the view falls back to pure auto-layout."""
    n = db.query(DiagramNodePosition).filter(DiagramNodePosition.view_id == view_id).delete()
    db.commit()
    return {"view_id": view_id, "cleared": n}


# ---- topology change requests (PROBIS_KONSEP.md) --------------------
# Edits from the SLD do NOT touch the canonical tables directly. They become
# lines of a ChangeRequest that is validated, previewed, reviewed, then
# published as a new TopologyVersion.

def _cr_out(cr, db):
    return {
        "id": cr.id, "cr_key": cr.cr_key, "title": cr.title, "kind": cr.kind,
        "status": cr.status, "effective_date": cr.effective_date,
        "source_ref": cr.source_ref, "submitted_by": cr.submitted_by,
        "reviewed_by": cr.reviewed_by, "view_id": cr.view_id,
        "validation": json.loads(cr.validation_json) if cr.validation_json else None,
        "impact": json.loads(cr.impact_json) if cr.impact_json else None,
        "lines": [
            {"change_key": l.change_key, "seq": l.seq, "action": l.action,
             "target_kind": l.target_kind, "target_ref": l.target_ref,
             "payload": json.loads(l.payload_json or "{}"),
             "description": l.description, "status": l.status}
            for l in editor.lines(db, cr.id)
        ],
    }


@router.get("/change-requests")
def list_crs(db: Session = Depends(get_db)):
    from app.models import ChangeRequest
    return [_cr_out(cr, db) for cr in
            db.query(ChangeRequest).order_by(ChangeRequest.id.desc()).all()]


@router.get("/change-requests/{cr_id}")
def get_cr(cr_id: int, db: Session = Depends(get_db)):
    from app.models import ChangeRequest
    cr = db.get(ChangeRequest, cr_id)
    if not cr:
        raise HTTPException(404, "CR not found")
    return _cr_out(cr, db)


@router.post("/views/{view_id}/change-requests")
def open_cr(view_id: int, payload: CRCreateIn, db: Session = Depends(get_db)):
    try:
        cr = editor.create_cr(db, view_id, payload.title, payload.effective_date,
                              payload.source_ref, payload.submitted_by, payload.kind)
    except EditError as e:
        raise HTTPException(400, str(e))
    return _cr_out(cr, db)


@router.post("/change-requests/{cr_id}/lines")
def add_cr_line(cr_id: int, payload: CRLineIn, db: Session = Depends(get_db)):
    try:
        editor.add_change(db, cr_id, payload.action, payload.target_kind,
                          payload.target_ref, payload.payload, payload.description)
    except EditError as e:
        raise HTTPException(400, str(e))
    from app.models import ChangeRequest
    return _cr_out(db.get(ChangeRequest, cr_id), db)


@router.delete("/change-requests/{cr_id}/lines/{change_key}")
def del_cr_line(cr_id: int, change_key: str, db: Session = Depends(get_db)):
    try:
        editor.remove_change(db, cr_id, change_key)
    except EditError as e:
        raise HTTPException(400, str(e))
    from app.models import ChangeRequest
    return _cr_out(db.get(ChangeRequest, cr_id), db)


@router.post("/change-requests/{cr_id}/validate")
def validate_cr(cr_id: int, db: Session = Depends(get_db)):
    try:
        return editor.validate(db, cr_id)
    except EditError as e:
        raise HTTPException(400, str(e))


@router.post("/change-requests/{cr_id}/impact")
def impact_cr(cr_id: int, db: Session = Depends(get_db)):
    try:
        return editor.impact(db, cr_id)
    except EditError as e:
        raise HTTPException(400, str(e))


@router.post("/change-requests/{cr_id}/review")
def review_cr(cr_id: int, payload: CRReviewIn, db: Session = Depends(get_db)):
    try:
        cr = editor.review(db, cr_id, payload.reviewed_by)
    except EditError as e:
        raise HTTPException(400, str(e))
    return _cr_out(cr, db)


@router.post("/change-requests/{cr_id}/publish")
def publish_cr(cr_id: int, payload: CRReviewIn, db: Session = Depends(get_db)):
    try:
        return editor.publish(db, cr_id, payload.reviewed_by)
    except EditError as e:
        raise HTTPException(400, str(e))


@router.post("/change-requests/{cr_id}/reject")
def reject_cr(cr_id: int, payload: CRRejectIn, db: Session = Depends(get_db)):
    try:
        cr = editor.reject(db, cr_id, payload.reason)
    except EditError as e:
        raise HTTPException(400, str(e))
    return _cr_out(cr, db)


# ---- kerawanan (risk points) -- direct edit; a kerawanan is an overlay,
#      not structural topology, so it does not need the version workflow.

def _risk_out(r):
    return {"risk_key": r.risk_key, "seq_no": r.seq_no, "category": r.category,
            "title": r.title, "condition": r.condition, "impact": r.impact,
            "mitigation": r.mitigation, "follow_up": r.follow_up,
            "horizon": r.horizon, "priority": r.priority, "status": r.status,
            "attach_kind": r.attach_kind, "attach_code": r.attach_label}


@router.get("/views/{view_id}/risks")
def list_risks(view_id: int, db: Session = Depends(get_db)):
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise HTTPException(404, "View not found")
    q = db.query(RiskRecord)
    if v.subsystem_id:
        q = q.filter(RiskRecord.subsystem_id == v.subsystem_id)
    else:
        q = q.filter(RiskRecord.view_id == v.id)
    return [_risk_out(r) for r in q.order_by(RiskRecord.seq_no).all()]


@router.post("/views/{view_id}/risks")
def create_risk(view_id: int, payload: RiskIn, db: Session = Depends(get_db)):
    try:
        r = editor_risks.add_risk(db, view_id, payload)
    except EditError as e:
        raise HTTPException(400, str(e))
    return _risk_out(r)


@router.patch("/risks/{risk_key}")
def update_risk(risk_key: str, payload: RiskPatch, db: Session = Depends(get_db)):
    try:
        r = editor_risks.patch_risk(db, risk_key, payload)
    except EditError as e:
        raise HTTPException(400, str(e))
    return _risk_out(r)


@router.delete("/risks/{risk_key}")
def remove_risk(risk_key: str, db: Session = Depends(get_db)):
    try:
        editor_risks.delete_risk(db, risk_key)
    except EditError as e:
        raise HTTPException(400, str(e))
    return {"deleted": risk_key}


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
