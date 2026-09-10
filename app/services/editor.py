"""Topology editor -- change-request workflow (PROBIS_KONSEP.md).

Edits from the SLD are NOT applied straight to the canonical tables. They
become lines of a ChangeRequest:

    DRAFT -> SUBMITTED -> VALIDATED -> REVIEWED -> PUBLISHED
                                              `-> REJECTED

  * add_change(cr, ...)   one line (SET_STATUS / ADD_CIRCUIT / ...)
  * validate(cr)          automatic checks (no isolated GI, seed intact, ...)
  * impact(cr)            preview: apply on a savepoint, diff Tier + kerawanan,
                          roll back
  * publish(cr)           apply for real; create a TopologyVersion ACTIVE and
                          supersede the previous one; mark affected kerawanan
                          REASSESS

The mutation primitives (_apply_*) are shared by impact() and publish().
"""
from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    AnalyticalView,
    Bay,
    ChangeRequest,
    ChangeSet,
    Circuit,
    DiagramNodePosition,
    RiskRecord,
    Substation,
    Subsystem,
    SubsystemMembership,
    TopologyVersion,
    Transformer,
    ViewMembership,
)
from app.services.topology import calculate_tier, get_view_graph


class EditError(Exception):
    """A bad edit request."""


# ---------------------------------------------------------------------------
# lookups
# ---------------------------------------------------------------------------

def _view(db: Session, view_id: int) -> AnalyticalView:
    v = db.get(AnalyticalView, view_id)
    if not v:
        raise EditError(f"view {view_id} not found")
    return v


def _cr(db: Session, cr_id: int) -> ChangeRequest:
    cr = db.get(ChangeRequest, cr_id)
    if not cr:
        raise EditError(f"change request {cr_id} not found")
    return cr


def _sub(db: Session, code: str) -> Substation:
    s = db.query(Substation).filter(Substation.code == code).first()
    if not s:
        raise EditError(f"GI '{code}' tidak ada")
    return s


def _circ(db: Session, code: str) -> Circuit:
    c = db.query(Circuit).filter(Circuit.code == code).first()
    if not c:
        raise EditError(f"penghantar '{code}' tidak ada")
    return c


# ---------------------------------------------------------------------------
# change request lifecycle
# ---------------------------------------------------------------------------

def create_cr(db: Session, view_id: int, title: str, effective_date: str | None,
              source_ref: str | None, submitted_by: str | None,
              kind: str = "STRUCTURAL") -> ChangeRequest:
    v = _view(db, view_id)
    n = db.query(func.count(ChangeRequest.id)).scalar() or 0
    cr = ChangeRequest(
        cr_key=f"CR-{datetime.utcnow():%Y}-{n + 1:04d}",
        title=title, kind=kind, subsystem_id=v.subsystem_id, view_id=v.id,
        status="DRAFT", effective_date=effective_date, source_ref=source_ref,
        submitted_by=submitted_by,
    )
    db.add(cr)
    db.commit()
    return cr


_ACTIONS = {
    "SET_STATUS", "ADD_CIRCUIT", "REMOVE_CIRCUIT", "PATCH_CIRCUIT",
    "ADD_GI", "REMOVE_GI", "PATCH_GI", "MOVE_MEMBERSHIP", "ADD_SUBSYSTEM",
}


def add_change(db: Session, cr_id: int, action: str, target_kind: str | None,
               target_ref: str | None, payload: dict, description: str = "") -> ChangeSet:
    cr = _cr(db, cr_id)
    if cr.status not in ("DRAFT", "SUBMITTED"):
        raise EditError(f"CR sudah {cr.status}, tidak bisa ditambah baris")
    if action not in _ACTIONS:
        raise EditError(f"aksi '{action}' tidak dikenal")
    seq = (db.query(func.max(ChangeSet.seq)).filter(
        ChangeSet.change_request_id == cr.id).scalar() or 0) + 1
    cs = ChangeSet(
        change_key=f"{cr.cr_key}-{seq:02d}", change_request_id=cr.id, seq=seq,
        action=action, target_kind=target_kind, target_ref=target_ref,
        payload_json=json.dumps(payload, ensure_ascii=False),
        description=description, status="PROPOSED",
    )
    db.add(cs)
    cr.status = "SUBMITTED"
    cr.updated_at = datetime.utcnow()
    cr.validation_json = None
    cr.impact_json = None
    db.commit()
    return cs


def remove_change(db: Session, cr_id: int, change_key: str) -> None:
    cr = _cr(db, cr_id)
    if cr.status not in ("DRAFT", "SUBMITTED"):
        raise EditError(f"CR sudah {cr.status}")
    cs = db.query(ChangeSet).filter(
        ChangeSet.change_request_id == cr.id, ChangeSet.change_key == change_key).first()
    if not cs:
        raise EditError("baris tidak ada")
    db.delete(cs)
    cr.validation_json = cr.impact_json = None
    db.commit()


def lines(db: Session, cr_id: int) -> list[ChangeSet]:
    return db.query(ChangeSet).filter(
        ChangeSet.change_request_id == cr_id).order_by(ChangeSet.seq).all()


# ---------------------------------------------------------------------------
# applying the lines  (shared by impact() and publish())
# ---------------------------------------------------------------------------

def _apply_line(db: Session, cr: ChangeRequest, cs: ChangeSet) -> None:
    pl = json.loads(cs.payload_json or "{}")
    a = cs.action
    v = db.get(AnalyticalView, cr.view_id) if cr.view_id else None

    if a == "SET_STATUS":
        kind = cs.target_kind or "SUBSTATION"
        if kind == "SUBSTATION":
            _sub(db, cs.target_ref).status = pl["status"]
        elif kind == "CIRCUIT":
            _circ(db, cs.target_ref).status = pl["status"]

    elif a == "ADD_GI":
        if db.query(Substation).filter(Substation.code == pl["code"]).first():
            raise EditError(f"kode GI '{pl['code']}' sudah ada")
        s = Substation(
            code=pl["code"], name=pl.get("name", pl["code"]),
            substation_type=pl.get("substation_type", "GI"),
            voltage_kv=pl.get("voltage_kv", 150.0), status=pl.get("status", "ENERGIZED"),
            busbar_config=pl.get("busbar_config", "UNKNOWN"),
            has_transformer=pl.get("has_transformer", True),
            has_shunt_capacitor=pl.get("has_shunt_capacitor", False),
            note=pl.get("note"), confidence=1.0,
        )
        db.add(s)
        db.flush()
        if cr.subsystem_id:
            db.add(SubsystemMembership(
                subsystem_id=cr.subsystem_id, node_kind="SUBSTATION", node_id=s.id,
                role=pl.get("role", "CORE"), display_order=pl.get("tier")))
        if v:
            db.add(ViewMembership(
                view_id=v.id, node_kind="SUBSTATION", node_id=s.id,
                role=pl.get("role", "CORE"), tier_seed=pl.get("tier"),
                display_order=pl.get("tier")))
        if pl.get("as_bay_of"):
            fd = _sub(db, pl["as_bay_of"])
            db.add(Bay(substation_id=s.id, feeder_substation_id=fd.id,
                       subsystem_id=cr.subsystem_id,
                       name=f"Bay {s.name} @ {fd.name}", bay_type="LINE",
                       drawing_side=(v.drawing_side if v else None),
                       status=s.status, note=f"via {cr.cr_key}"))

    elif a == "PATCH_GI":
        s = _sub(db, cs.target_ref)
        for f in ("name", "substation_type", "voltage_kv", "status",
                  "busbar_config", "busbar_note", "has_transformer",
                  "has_shunt_capacitor", "symbol_note", "note"):
            if f in pl and pl[f] is not None:
                setattr(s, f, pl[f])
        if v and ("tier" in pl or "role" in pl):
            vm = db.query(ViewMembership).filter(
                ViewMembership.view_id == v.id, ViewMembership.node_kind == "SUBSTATION",
                ViewMembership.node_id == s.id).first()
            if vm:
                if pl.get("tier") is not None:
                    vm.tier_seed = vm.display_order = pl["tier"]
                if pl.get("role"):
                    vm.role = pl["role"]

    elif a == "REMOVE_GI":
        s = _sub(db, cs.target_ref)
        n = db.query(Circuit).filter(
            (Circuit.from_substation_id == s.id) | (Circuit.to_substation_id == s.id)).count()
        if n:
            raise EditError(f"'{s.code}' masih punya {n} penghantar")
        db.query(Bay).filter(
            (Bay.substation_id == s.id) | (Bay.feeder_substation_id == s.id)).delete()
        db.query(ViewMembership).filter(
            ViewMembership.node_kind == "SUBSTATION", ViewMembership.node_id == s.id).delete()
        db.query(SubsystemMembership).filter(
            SubsystemMembership.node_kind == "SUBSTATION",
            SubsystemMembership.node_id == s.id).delete()
        db.query(DiagramNodePosition).filter(
            DiagramNodePosition.node_kind == "SUBSTATION",
            DiagramNodePosition.node_id == s.id).delete()
        for r in db.query(RiskRecord).filter(
                RiskRecord.attach_kind == "SUBSTATION", RiskRecord.attach_id == s.id).all():
            r.attach_kind = r.attach_id = None
        db.delete(s)

    elif a == "ADD_CIRCUIT":
        fr, to = _sub(db, pl["from_code"]), _sub(db, pl["to_code"])
        code = pl.get("code") or f"PHT_{fr.code}_{to.code}"
        if db.query(Circuit).filter(Circuit.code == code).first():
            raise EditError(f"kode penghantar '{code}' sudah ada")
        db.add(Circuit(
            code=code, name=pl.get("name") or f"{fr.name} - {to.name}",
            circuit_type=pl.get("circuit_type", "SUTT"),
            voltage_kv=pl.get("voltage_kv", 150.0),
            from_substation_id=fr.id, to_substation_id=to.id,
            subsystem_id=cr.subsystem_id,
            circuit_count=pl.get("circuit_count", 2),
            single_phi=pl.get("single_phi", False),
            status=pl.get("status", "ENERGIZED"), scenario_id="NORMAL",
            drawing_side=(v.drawing_side if v else None),
            note=pl.get("note") or f"via {cr.cr_key}", confidence=1.0))

    elif a == "PATCH_CIRCUIT":
        c = _circ(db, cs.target_ref)
        for f in ("name", "circuit_type", "voltage_kv", "circuit_count",
                  "single_phi", "status", "note"):
            if f in pl and pl[f] is not None:
                setattr(c, f, pl[f])

    elif a == "REMOVE_CIRCUIT":
        c = _circ(db, cs.target_ref)
        for r in db.query(RiskRecord).filter(
                RiskRecord.attach_kind == "CIRCUIT", RiskRecord.attach_id == c.id).all():
            r.attach_kind = r.attach_id = None
        db.delete(c)

    elif a == "MOVE_MEMBERSHIP":
        s = _sub(db, cs.target_ref)
        target_ss = db.query(Subsystem).filter(Subsystem.code == pl["to_subsystem"]).first()
        if not target_ss:
            raise EditError(f"subsistem '{pl['to_subsystem']}' tidak ada")
        m = db.query(SubsystemMembership).filter(
            SubsystemMembership.node_kind == "SUBSTATION", SubsystemMembership.node_id == s.id,
            SubsystemMembership.subsystem_id == target_ss.id).first()
        if not m:
            db.add(SubsystemMembership(
                subsystem_id=target_ss.id, node_kind="SUBSTATION", node_id=s.id,
                role=pl.get("role", "CORE")))
        else:
            m.role = pl.get("role", m.role)
        if pl.get("from_subsystem"):
            src = db.query(Subsystem).filter(Subsystem.code == pl["from_subsystem"]).first()
            if src:
                db.query(SubsystemMembership).filter(
                    SubsystemMembership.node_kind == "SUBSTATION",
                    SubsystemMembership.node_id == s.id,
                    SubsystemMembership.subsystem_id == src.id).delete()

    elif a == "ADD_SUBSYSTEM":
        if db.query(Subsystem).filter(Subsystem.code == pl["code"]).first():
            raise EditError(f"kode subsistem '{pl['code']}' sudah ada")
        db.add(Subsystem(code=pl["code"], name=pl["name"], apb=pl.get("apb"),
                         source_ref=pl.get("source_ref") or f"via {cr.cr_key}"))

    else:
        raise EditError(f"aksi '{a}' belum diimplementasi")

    db.flush()


# ---------------------------------------------------------------------------
# validate  (automatic checks -- PROBIS step 02)
# ---------------------------------------------------------------------------

_LIVE = {"ENERGIZED", "DE_ENERGIZED", "OWNED_BY_CUSTOMER"}


def _graph_snapshot(db: Session, view_id: int) -> dict:
    v = db.get(AnalyticalView, view_id)
    nodes, edges, roles, seeds, _ = get_view_graph(db, v)
    tier = calculate_tier(db, v)
    sub = {k[1]: o for k, o in nodes.items() if k[0] == "SUBSTATION"}
    live_edges = [c for c in edges if (c.status or "ENERGIZED") in _LIVE]
    return {
        "codes": {s.code for s in sub.values()},
        "codes_live": {s.code for s in sub.values() if (s.status or "ENERGIZED") in _LIVE},
        "tier": {sub[nid].code: tier.get(("SUBSTATION", nid))
                 for nid in sub if ("SUBSTATION", nid) in tier},
        "edges": {c.code for c in edges},
        "edges_live": {c.code for c in live_edges},
        "seeds": {k[1] for k in seeds if k[0] == "SUBSTATION"},
        "isolated": sorted(
            s.code for nid, s in sub.items()
            if (s.status or "ENERGIZED") in _LIVE
            and not any(nid in (c.from_substation_id, c.to_substation_id) for c in live_edges)
            and roles.get(("SUBSTATION", nid)) not in ("EXTERNAL_CONTEXT",)),
    }


def validate(db: Session, cr_id: int) -> dict:
    cr = _cr(db, cr_id)
    before = _graph_snapshot(db, cr.view_id) if cr.view_id else {}
    problems: list[str] = []
    warnings: list[str] = []
    sp = db.begin_nested()
    try:
        for cs in lines(db, cr.id):
            _apply_line(db, cr, cs)
        after = _graph_snapshot(db, cr.view_id) if cr.view_id else {}
    except EditError as e:
        sp.rollback()
        cr.validation_json = json.dumps({"ok": False, "problems": [str(e)], "warnings": []})
        cr.updated_at = datetime.utcnow()
        db.commit()
        return json.loads(cr.validation_json)
    sp.rollback()

    if after:
        new_iso = set(after["isolated"]) - set(before.get("isolated", []))
        if new_iso:
            problems.append(f"GI jadi terisolasi: {', '.join(sorted(new_iso))}")
        if not after["seeds"]:
            problems.append("tidak ada seed Tier-1 tersisa di view ini")
        moved = [c for c in after["tier"]
                 if c in before.get("tier", {}) and before["tier"][c] != after["tier"][c]]
        if moved:
            warnings.append(f"{len(moved)} GI berubah Tier: "
                            + ", ".join(f"{c} {before['tier'][c]}->{after['tier'][c]}"
                                        for c in sorted(moved)))
        gone = set(before.get("codes_live", [])) - set(after.get("codes_live", []))
        if gone:
            warnings.append(f"{len(gone)} GI keluar dari jaringan aktif: {', '.join(sorted(gone))}")

    res = {"ok": not problems, "problems": problems, "warnings": warnings}
    cr.validation_json = json.dumps(res, ensure_ascii=False)
    if res["ok"]:
        cr.status = "VALIDATED"
    cr.updated_at = datetime.utcnow()
    db.commit()
    return res


# ---------------------------------------------------------------------------
# impact preview  (PROBIS step 03)  -- apply on a savepoint, diff, roll back
# ---------------------------------------------------------------------------

def impact(db: Session, cr_id: int) -> dict:
    cr = _cr(db, cr_id)
    if not cr.view_id:
        raise EditError("CR tidak terikat ke view")
    before = _graph_snapshot(db, cr.view_id)
    risks_before = {r.risk_key: (r.seq_no, r.category, r.attach_label, r.status)
                    for r in db.query(RiskRecord).filter(
                        RiskRecord.subsystem_id == cr.subsystem_id).all()}

    sp = db.begin_nested()
    try:
        for cs in lines(db, cr.id):
            _apply_line(db, cr, cs)
        after = _graph_snapshot(db, cr.view_id)
        tier_changes = [
            {"code": c, "from": before["tier"].get(c), "to": after["tier"].get(c)}
            for c in sorted(set(before["tier"]) | set(after["tier"]))
            if before["tier"].get(c) != after["tier"].get(c)
        ]
        moved = {tc["code"] for tc in tier_changes}
        # kerawanan to re-assess: object edited, gone, or its Tier moved
        touched = {cs.target_ref for cs in lines(db, cr.id) if cs.target_ref}
        alive = ({s.code for s in db.query(Substation).all()}
                 | {c.code for c in db.query(Circuit).all()}
                 | {t.code for t in db.query(Transformer).all()})
        risk_reassess = []
        for r in db.query(RiskRecord).filter(
                RiskRecord.subsystem_id == cr.subsystem_id).all():
            lab = r.attach_label
            if lab and (lab in touched or lab not in alive or lab in moved):
                why = ("objek diedit" if lab in touched else
                       "objek hilang" if lab not in alive else "Tier berubah")
                risk_reassess.append({"risk_key": r.risk_key, "seq_no": r.seq_no,
                                      "title": r.title, "attach": lab, "why": why})
    finally:
        sp.rollback()
    res = {
        # "added" = new object OR an existing one that became energised
        "gi_added": sorted(after["codes_live"] - before["codes_live"]),
        "gi_removed": sorted(before["codes_live"] - after["codes_live"]),
        "circuit_added": sorted(after["edges_live"] - before["edges_live"]),
        "circuit_removed": sorted(before["edges_live"] - after["edges_live"]),
        "tier_changes": tier_changes,
        "risk_reassess": risk_reassess,
        "isolated_after": after["isolated"],
    }
    cr.impact_json = json.dumps(res, ensure_ascii=False)
    cr.updated_at = datetime.utcnow()
    db.commit()
    return res


# ---------------------------------------------------------------------------
# review + publish  (PROBIS steps 04-06)
# ---------------------------------------------------------------------------

def review(db: Session, cr_id: int, reviewed_by: str | None) -> ChangeRequest:
    cr = _cr(db, cr_id)
    if cr.status != "VALIDATED":
        raise EditError("CR harus VALIDATED dulu (jalankan validate)")
    cr.status = "REVIEWED"
    cr.reviewed_by = reviewed_by
    cr.updated_at = datetime.utcnow()
    db.commit()
    return cr


def reject(db: Session, cr_id: int, reason: str | None) -> ChangeRequest:
    cr = _cr(db, cr_id)
    if cr.status in ("PUBLISHED",):
        raise EditError("CR sudah terbit, tidak bisa ditolak")
    cr.status = "REJECTED"
    cr.updated_at = datetime.utcnow()
    if reason:
        cr.validation_json = json.dumps({"ok": False, "problems": [f"REJECTED: {reason}"]})
    db.commit()
    return cr


def publish(db: Session, cr_id: int, approver: str | None) -> dict:
    cr = _cr(db, cr_id)
    if cr.status not in ("REVIEWED", "VALIDATED"):
        raise EditError("CR harus VALIDATED/REVIEWED sebelum diterbitkan")

    # supersede the current ACTIVE version for this subsystem, if any
    prev = (db.query(TopologyVersion)
            .filter(TopologyVersion.status == "ACTIVE",
                    TopologyVersion.version_key.like(
                        f"TV-{_ss_code(db, cr) or 'SYS'}-%"))
            .first())
    tv = TopologyVersion(
        version_key=f"TV-{_ss_code(db, cr) or 'SYS'}-{cr.cr_key}",
        status="ACTIVE", effective_date=cr.effective_date,
        description=f"{cr.title} ({cr.cr_key})", approver=approver,
        reviewer=cr.reviewed_by,
    )
    db.add(tv)
    db.flush()
    if prev:
        prev.status = "SUPERSEDED"

    tier_before = _graph_snapshot(db, cr.view_id)["tier"] if cr.view_id else {}

    # apply the lines for real
    applied = 0
    for cs in lines(db, cr.id):
        _apply_line(db, cr, cs)
        cs.status = "APPLIED"
        cs.version_id = tv.id
        applied += 1

    # kerawanan to re-assess: its pinned object was edited, disappeared, or its
    # (or its endpoint's) Tier moved
    reassessed = []
    if cr.view_id:
        after = _graph_snapshot(db, cr.view_id)
        touched = {cs.target_ref for cs in lines(db, cr.id) if cs.target_ref}
        moved = {c for c in after["tier"] if tier_before.get(c) != after["tier"].get(c)}
        alive = ({s.code for s in db.query(Substation).all()}
                 | {c.code for c in db.query(Circuit).all()}
                 | {t.code for t in db.query(Transformer).all()})
        for r in db.query(RiskRecord).filter(
                RiskRecord.subsystem_id == cr.subsystem_id).all():
            if r.status not in ("OPEN", "MATERIALIZED"):
                continue
            lab = r.attach_label
            if lab and (lab in touched or lab not in alive or lab in moved):
                r.status = "REASSESS"
                reassessed.append(r.risk_key)

    cr.status = "PUBLISHED"
    cr.published_version_id = tv.id
    cr.updated_at = datetime.utcnow()
    db.commit()
    return {"cr_key": cr.cr_key, "version": tv.version_key, "applied": applied,
            "superseded": prev.version_key if prev else None,
            "kerawanan_reassess": reassessed}


def _ss_code(db: Session, cr: ChangeRequest) -> str | None:
    if not cr.subsystem_id:
        return None
    ss = db.get(Subsystem, cr.subsystem_id)
    return ss.code if ss else None
