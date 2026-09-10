"""Kerawanan (risk-point) editor.

A kerawanan is a semantic OVERLAY on the topology, not the topology itself, so
it is edited directly -- it does not go through the ChangeRequest / version
workflow. It pins to a canonical object (GI / circuit / transformer) by code,
never to a pixel.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    AnalyticalView,
    Circuit,
    RiskRecord,
    Substation,
    Subsystem,
    Transformer,
)
from app.services.editor import EditError


def _resolve(db: Session, kind: str | None, code: str | None):
    if not kind or not code:
        return None, None
    model = {"SUBSTATION": Substation, "CIRCUIT": Circuit, "TRANSFORMER": Transformer}.get(kind)
    if not model:
        return None, code
    o = db.query(model).filter(model.code == code).first()
    return (o.id if o else None), code


def _next_seq(db: Session, subsystem_id):
    rows = db.query(RiskRecord).filter(RiskRecord.subsystem_id == subsystem_id).all()
    return max((r.seq_no or 0 for r in rows), default=0) + 1


def add_risk(db: Session, view_id: int, data) -> RiskRecord:
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise EditError(f"view {view_id} not found")
    seq = data.seq_no or _next_seq(db, v.subsystem_id)
    ss = db.get(Subsystem, v.subsystem_id) if v.subsystem_id else None
    attach_id, attach_label = _resolve(db, data.attach_kind, data.attach_code)
    r = RiskRecord(
        risk_key=f"RISK-{ss.code if ss else 'V' + str(v.id)}-{seq:02d}"
        f"-{int(datetime.utcnow().timestamp()) % 100000}",
        subsystem_id=v.subsystem_id, view_id=v.id, seq_no=seq,
        category=data.category, title=data.title, condition=data.condition,
        impact=data.impact, mitigation=data.mitigation, follow_up=data.follow_up,
        horizon=data.horizon, priority=data.priority, status=data.status,
        attach_kind=data.attach_kind, attach_id=attach_id, attach_label=attach_label,
        confidence=1.0,
    )
    db.add(r)
    db.commit()
    return r


def patch_risk(db: Session, risk_key: str, data) -> RiskRecord:
    r = db.query(RiskRecord).filter(RiskRecord.risk_key == risk_key).first()
    if not r:
        raise EditError(f"kerawanan '{risk_key}' tidak ada")
    for f in ("seq_no", "category", "title", "condition", "impact",
              "mitigation", "follow_up", "horizon", "priority", "status"):
        val = getattr(data, f, None)
        if val is not None:
            setattr(r, f, val)
    if data.attach_kind is not None or data.attach_code is not None:
        kind = data.attach_kind if data.attach_kind is not None else r.attach_kind
        code = data.attach_code if data.attach_code is not None else r.attach_label
        r.attach_kind = kind
        r.attach_id, r.attach_label = _resolve(db, kind, code)
    db.commit()
    return r


def delete_risk(db: Session, risk_key: str) -> None:
    r = db.query(RiskRecord).filter(RiskRecord.risk_key == risk_key).first()
    if not r:
        raise EditError(f"kerawanan '{risk_key}' tidak ada")
    db.delete(r)
    db.commit()
