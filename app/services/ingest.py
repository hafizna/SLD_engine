"""`/ingest` -- bootstrap a subsystem from an uploaded SLD + kerawanan table.

The flow the user asked for:

    upload  ->  build relations  ->  ASK THE USER TO CONFIRM  ->  build version  ->  render

STATELESS by design: the draft is a single JSON blob that round-trips between
the browser (localStorage) and these endpoints. NOTHING is written to the
database -- not even the staging tables -- until the user hits *Terbitkan*.
That makes the page safe to demo to anyone: they can upload any SLD, watch it
render and validate, and walk away leaving no trace.

    build_draft(payload)             parser output -> a draft blob (+ candidates,
                                     + verdicts, + validation), no DB write
    validate(db, draft)              checks; returns {ok, problems}
    render_draft_svg(db, draft)      materialise into a SAVEPOINT, render with the
                                     real renderer, roll back  (canon untouched)
    publish(db, draft, code, ...)    the ONE DB write: Subsystem + Substations +
                                     Circuits + Bays + Risks + a view +
                                     a TopologyVersion

`_materialise` is the single promotion function, shared by render + publish.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    AnalyticalView,
    Bay,
    ChangeSet,
    Circuit,
    GeneratingUnit,
    ObservedObject,
    RiskRecord,
    SourceDocument,
    Substation,
    Subsystem,
    SubsystemMembership,
    TopologyVersion,
    Transformer,
    TransformerWinding,
    ViewMembership,
)
from app.services.reconciliation import classify, find_candidates
from app.services.sld_renderer import render_view_svg

_LIVE = {"ENERGIZED", "DE_ENERGIZED", "OWNED_BY_CUSTOMER"}


class IngestError(Exception):
    """A bad ingest request."""


# ---------------------------------------------------------------------------
# build a draft blob from parser output  (no DB write)
# ---------------------------------------------------------------------------

def build_draft(db: Session, payload: dict) -> dict:
    """`payload` is the dict from `ingest_parser.parse_upload` / `.normalise`.
    Returns the editable draft blob, enriched with reconciliation candidates and
    a validation result. The blob is what the client keeps and re-sends."""
    nodes = []
    for o in payload["objects"]:
        n = {
            "external_key": o["external_key"],
            "object_type": o["object_type"],
            "raw_label": o["raw_label"],
            "site_name": o.get("site_name"),
            "voltage_hv_kv": o.get("voltage_hv_kv"),
            "voltage_lv_kv": o.get("voltage_lv_kv"),
            "unit_no": o.get("unit_no"),
            "tier_hint": o.get("tier_hint"),
            "status_hint": o.get("status_hint") or "ENERGIZED",
            "confidence": o.get("confidence", 1.0),
            "is_bay": bool(o.get("is_bay")),
            "bay_feeder_key": o.get("bay_feeder_key"),
            "has_transformer": bool(o.get("has_transformer")),
            "has_capacitor": bool(o.get("has_capacitor")),
            "resolution": "NEW",
            "confirmed_code": o["external_key"],
            "confirmed_name": o.get("site_name") or o["raw_label"],
            "canonical_id": None,
        }
        _auto_match(db, n)
        nodes.append(n)

    edges = []
    for c in payload["connections"]:
        conf = c.get("confidence", 0.5)
        edges.append({
            "from_key": c["from_external_key"],
            "to_key": c["to_external_key"],
            "relation_type": c.get("relation_type") or "CONNECTED_TO",
            "circuit_type_hint": c.get("circuit_type_hint") or "SUTT",
            "status_hint": c.get("status_hint") or "ENERGIZED",
            "circuit_count": c.get("circuit_count") or 2,
            "unit_no": c.get("unit_no"),
            "confidence": conf,
            "confirmed": conf >= 0.9,
            "note": c.get("note"),
        })

    draft = {
        "meta": payload["meta"],
        "subsystem": payload["subsystem"],
        "nodes": nodes,
        "edges": edges,
        "risks": [dict(r) for r in payload["risks"]],
    }
    draft["existing"] = _detect_existing(db, nodes)
    return decorate(db, draft)


def _detect_existing(db: Session, nodes: list[dict]) -> dict | None:
    """If most of the parsed GIs already sit in ONE existing subsystem, this
    upload is very likely that subsystem, not a new one -- the user should edit
    it via /editor, not bootstrap a duplicate."""
    from app.models import Subsystem, SubsystemMembership
    codes = {(n.get("confirmed_code") or n["external_key"]).strip().upper()
             for n in nodes if not n.get("is_bay")}
    if not codes:
        return None
    hit_by_ss: dict[int, int] = {}
    sub_by_code = {s.code: s for s in db.query(Substation).filter(Substation.code.in_(codes)).all()}
    for s in sub_by_code.values():
        for m in db.query(SubsystemMembership).filter(
                SubsystemMembership.node_kind == "SUBSTATION",
                SubsystemMembership.node_id == s.id).all():
            hit_by_ss[m.subsystem_id] = hit_by_ss.get(m.subsystem_id, 0) + 1
    if not hit_by_ss:
        return None
    ss_id, hits = max(hit_by_ss.items(), key=lambda kv: kv[1])
    frac = hits / len(codes)
    if frac < 0.6:
        return None
    ss = db.get(Subsystem, ss_id)
    view = (db.query(AnalyticalView)
            .filter(AnalyticalView.subsystem_id == ss_id).first())
    return {
        "subsystem_code": ss.code, "subsystem_name": ss.name,
        "view_id": view.id if view else None,
        "matched": hits, "of": len(codes), "fraction": round(frac, 2),
    }


def decorate(db: Session, draft: dict) -> dict:
    """Re-attach the derived bits (candidates, needs_review, validation) that the
    client does not persist. Called on every round-trip."""
    draft = _clean(draft)
    draft["existing"] = _detect_existing(db, draft["nodes"])
    for n in draft["nodes"]:
        obs = _as_observed(n)
        n["candidates"] = [
            {"substation_id": r["substation"].id, "code": r["substation"].code,
             "name": r["substation"].name, "score": round(r["score"], 3),
             "verdict": classify(r["score"])}
            for r in find_candidates(db, obs, limit=4)
        ]
        n["needs_review"] = (n.get("confidence") or 1) < 0.9
    for e in draft["edges"]:
        e["needs_review"] = (e.get("confidence") or 1) < 0.9
    draft["node_keys"] = [n["external_key"] for n in draft["nodes"]]
    draft["validation"] = validate(db, draft)
    return draft


def _auto_match(db: Session, n: dict) -> None:
    obs = _as_observed(n)
    cands = find_candidates(db, obs)
    top = cands[0]["substation"] if cands else None
    type_ok = top is not None and (
        (n["object_type"] in ("GITET", "GISTET")) == (top.substation_type in ("GITET", "GISTET"))
    )
    if top is not None and type_ok and not n["is_bay"] and classify(cands[0]["score"]) == "AUTO_MATCH":
        n["resolution"] = "MATCH"
        n["canonical_id"] = top.id
        n["confirmed_code"] = top.code
        n["confirmed_name"] = top.name


def _as_observed(n: dict) -> ObservedObject:
    return ObservedObject(
        external_key=n["external_key"], object_type=n["object_type"],
        raw_label=n["raw_label"], site_name=n.get("site_name"),
        normalized_name=None,
        voltage_hv_kv=n.get("voltage_hv_kv"), voltage_lv_kv=n.get("voltage_lv_kv"),
        unit_no=n.get("unit_no"),
    )


_ALLOWED_NODE = {"external_key", "object_type", "raw_label", "site_name",
                 "voltage_hv_kv", "voltage_lv_kv", "unit_no", "tier_hint",
                 "status_hint", "confidence", "is_bay", "bay_feeder_key",
                 "has_transformer", "has_capacitor", "resolution",
                 "confirmed_code", "confirmed_name", "canonical_id"}
_ALLOWED_EDGE = {"from_key", "to_key", "relation_type", "circuit_type_hint",
                 "status_hint", "circuit_count", "unit_no", "confidence",
                 "confirmed", "note"}
_ALLOWED_RISK = {"seq_no", "uit", "category", "priority", "title", "condition",
                 "impact", "mitigation", "follow_up", "pin_kind", "pin_key"}


def _clean(draft: dict) -> dict:
    """Strip anything the client should not be able to inject; keep only known
    fields. Defensive -- the blob comes back from the browser."""
    if not isinstance(draft, dict):
        raise IngestError("draft harus objek JSON")
    ss = draft.get("subsystem") or {}
    return {
        "meta": draft.get("meta") or {},
        "subsystem": {"code": ss.get("code"), "name": ss.get("name"), "apb": ss.get("apb")},
        "nodes": [{k: v for k, v in (n or {}).items() if k in _ALLOWED_NODE}
                  for n in (draft.get("nodes") or [])],
        "edges": [{k: v for k, v in (e or {}).items() if k in _ALLOWED_EDGE}
                  for e in (draft.get("edges") or [])],
        "risks": [{k: v for k, v in (r or {}).items() if k in _ALLOWED_RISK}
                  for r in (draft.get("risks") or [])],
        "effective_date": (draft.get("meta") or {}).get("effective_date"),
        "source_ref": (draft.get("meta") or {}).get("source_ref"),
    }


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def validate(db: Session, draft: dict) -> dict:
    draft = _clean(draft)
    nodes = [n for n in draft["nodes"] if n.get("resolution") != "SKIP"]
    edges = draft["edges"]
    keys = {n["external_key"] for n in nodes}
    problems: list[str] = []

    ex = _detect_existing(db, nodes)
    if ex:
        problems.append(
            f"{ex['matched']} dari {ex['of']} GI sudah tercatat di subsistem "
            f"'{ex['subsystem_code']}' ({ex['subsystem_name']}). /ingest hanya "
            f"untuk subsistem BARU -- untuk mengubah yang sudah ada, pakai "
            f"/editor (Change Request). Kalau ini benar-benar subsistem lain "
            f"yang kebetulan berbagi GI, lanjutkan lewat /editor juga.")

    seen: dict[str, str] = {}
    for n in nodes:
        if n.get("resolution") == "MATCH" and not n.get("canonical_id"):
            problems.append(f"{n['external_key']}: MATCH tapi belum pilih GI kanonik")
        if n.get("resolution") == "NEW" and not (n.get("confirmed_code") or "").strip():
            problems.append(f"{n['external_key']}: GI baru belum diberi kode")
        code = (n.get("confirmed_code") or "").strip().upper()
        if code:
            if code in seen and seen[code] != n["external_key"]:
                problems.append(f"kode '{code}' dipakai dua node ({seen[code]} & {n['external_key']})")
            seen[code] = n["external_key"]

    for e in edges:
        if e["from_key"] not in keys or e["to_key"] not in keys:
            problems.append(f"penghantar {e['from_key']}-{e['to_key']} menempel ke node yang di-SKIP")

    if not any((n.get("tier_hint") or 99) == 1 for n in nodes):
        problems.append("tidak ada GI Tier-1 (sumber) -- Tier tidak bisa dihitung")

    adj: dict[str, set[str]] = {n["external_key"]: set() for n in nodes}
    for e in edges:
        if e["from_key"] in adj and e["to_key"] in adj:
            adj[e["from_key"]].add(e["to_key"])
            adj[e["to_key"]].add(e["from_key"])
    for n in nodes:
        if n.get("is_bay"):
            continue
        if not adj.get(n["external_key"]) and (n.get("tier_hint") or 99) != 1:
            problems.append(f"{n['external_key']}: tidak terhubung ke penghantar mana pun (terisolasi)")

    for r in draft["risks"]:
        if not _resolve_pin(r.get("pin_kind"), r.get("pin_key"), keys):
            problems.append(
                f"kerawanan #{r.get('seq_no')}: "
                + ("belum ditautkan ke objek" if not r.get("pin_key")
                   else f"tautan '{r.get('pin_key')}' tidak cocok objek mana pun"))

    return {"ok": not problems, "problems": problems,
            "node_count": len(nodes), "edge_count": len(edges),
            "risk_count": len(draft["risks"])}


def _resolve_pin(kind: str | None, key: str | None, keys: set[str]):
    if not key:
        return None
    if kind == "CIRCUIT" or (kind != "SUBSTATION" and "-" in key and ":" not in key):
        a, _, b = key.partition("-")
        return ("CIRCUIT", key) if a in keys and b in keys else None
    if kind == "TRANSFORMER" or ":" in key:
        gk = key.partition(":")[0]
        return ("TRANSFORMER", key) if gk in keys else None
    return ("SUBSTATION", key) if key in keys else None


# ---------------------------------------------------------------------------
# materialise  (shared by publish + dry-run render)
# ---------------------------------------------------------------------------

def _materialise(db: Session, draft: dict, code: str, name: str,
                 effective_date: str | None, *, for_publish: bool) -> AnalyticalView:
    draft = _clean(draft)
    nodes = [n for n in draft["nodes"] if n.get("resolution") != "SKIP"]
    edges = draft["edges"]
    by_key = {n["external_key"]: n for n in nodes}
    apb = draft["subsystem"].get("apb") or "UP2B Jakarta & Banten"
    src_ref = draft.get("source_ref")
    fname = (draft["meta"] or {}).get("filename") or f"{code}.json"

    doc = SourceDocument(
        filename=fname, document_type="SLD_HANDOFF_JSON",
        analytical_hint="SUBSYSTEM_150", source_ref=src_ref,
        effective_date=effective_date,
    )
    db.add(doc)
    db.flush()

    ss = db.query(Subsystem).filter(Subsystem.code == code).first()
    if ss is None:
        ss = Subsystem(code=code, name=name, apb=apb, source_ref=src_ref)
        db.add(ss)
        db.flush()

    date = effective_date or draft.get("effective_date") or datetime.utcnow().strftime("%Y-%m-%d")
    nreview = sum(1 for e in edges if (e.get("confidence") or 1) < 0.9)
    tv = TopologyVersion(
        version_key=f"TV-{code}-{date}-{doc.id}", status="ACTIVE",
        effective_date=date,
        description=f"Bootstrap {name} via /ingest dari {fname}. {nreview} penghantar NEEDS_REVIEW.",
    )
    db.add(tv)
    db.flush()

    subs: dict[str, object] = {}
    kinds: dict[str, str] = {}
    _members: set[tuple[str, int]] = set()

    def _member(kind: str, node_id: int, role: str, order):
        if (kind, node_id) in _members:
            return
        if db.query(SubsystemMembership).filter_by(
                subsystem_id=ss.id, node_kind=kind, node_id=node_id).first():
            _members.add((kind, node_id))
            return
        db.add(SubsystemMembership(subsystem_id=ss.id, node_kind=kind,
                                   node_id=node_id, role=role, display_order=order))
        _members.add((kind, node_id))

    for n in nodes:
        ckey = (n.get("confirmed_code") or n["external_key"]).strip().upper()
        if n["object_type"] == "GENERATING_UNIT":
            g = db.query(GeneratingUnit).filter(GeneratingUnit.code == ckey).first()
            if g is None:
                g = GeneratingUnit(code=ckey, name=n.get("confirmed_name") or n["raw_label"],
                                   voltage_kv=n.get("voltage_hv_kv") or 150.0)
                db.add(g)
                db.flush()
            subs[n["external_key"]] = g
            kinds[n["external_key"]] = "GENERATING_UNIT"
            _member("GENERATING_UNIT", g.id, "SOURCE", n.get("tier_hint"))
            continue

        s = None
        if n.get("resolution") == "MATCH" and n.get("canonical_id"):
            s = db.get(Substation, n["canonical_id"])
        if s is None:
            s = db.query(Substation).filter(Substation.code == ckey).first()
        if s is None:
            s = Substation(
                code=ckey, name=n.get("confirmed_name") or n["raw_label"],
                substation_type=n["object_type"] if n["object_type"] in ("GI", "GITET", "GIS", "GISTET") else "GI",
                voltage_kv=n.get("voltage_hv_kv") or 150.0,
                status=n.get("status_hint") or "ENERGIZED",
                busbar_config="UNKNOWN",
                has_transformer=bool(n.get("has_transformer")),
                has_shunt_capacitor=bool(n.get("has_capacitor")),
                apb=apb, uit="JBB",
                note=f"Bootstrap via /ingest ({fname}).",
                confidence=n.get("confidence") or 1.0,
            )
            db.add(s)
            db.flush()
        subs[n["external_key"]] = s
        kinds[n["external_key"]] = "SUBSTATION"
        _member("SUBSTATION", s.id, _role(n), n.get("tier_hint"))

    txs: dict[str, Transformer] = {}

    def _make_tx(gi_key: str, unit: str | None):
        gi = subs.get(gi_key)
        if gi is None or kinds.get(gi_key) != "SUBSTATION":
            return None
        tcode = f"IBT_{(by_key[gi_key].get('confirmed_code') or gi_key).upper()}_{unit or '1'}"
        t = txs.get(tcode) or db.query(Transformer).filter(Transformer.code == tcode).first()
        if t is None:
            t = Transformer(code=tcode, name=f"IBT {unit or ''} {gi.name}".strip(),
                            transformer_type="IBT", substation_id=gi.id,
                            unit_no=unit, rating_mva=500.0, winding_count=2)
            db.add(t)
            db.flush()
            db.add(TransformerWinding(transformer_id=t.id, winding_no=1, voltage_kv=500, role="HV"))
            db.add(TransformerWinding(transformer_id=t.id, winding_no=2, voltage_kv=150, role="LV"))
        txs[tcode] = t
        _member("TRANSFORMER", t.id, "SOURCE_BOUNDARY", 1)
        return t

    circuits: dict[str, Circuit] = {}
    for e in edges:
        fk, tk = e["from_key"], e["to_key"]
        if fk not in subs or tk not in subs:
            continue
        conf = e.get("confidence", 0.5)
        is_ibt = (e.get("relation_type") == "IBT_LINK" or e.get("circuit_type_hint") == "IBT_LINK")
        if is_ibt:
            hv, lv = (fk, tk) if by_key[fk]["object_type"] in ("GITET", "GISTET") else (tk, fk)
            unit = e.get("unit_no")
            t = _make_tx(hv, unit)
            ccode = f"{(by_key[hv].get('confirmed_code') or hv).upper()}_{(by_key[lv].get('confirmed_code') or lv).upper()}_IBT{unit or ''}"
        else:
            a = (by_key[fk].get("confirmed_code") or fk).upper()
            b = (by_key[tk].get("confirmed_code") or tk).upper()
            ccode = f"{(e.get('circuit_type_hint') or 'SUTT')}_{a}_{b}"

        # a physical line can already exist (a GI-pair genuinely shared by two
        # real subsystems, e.g. New Balaraja - Balaraja). Reuse by code.
        c = db.query(Circuit).filter(Circuit.code == ccode).first()
        if c is not None:
            circuits[ccode] = c
            circuits[f"{fk}-{tk}"] = c
            circuits[f"{tk}-{fk}"] = c
            continue

        if is_ibt:
            c = Circuit(
                code=ccode, name=f"IBT {e.get('unit_no') or ''} {subs[hv].name} 500/150".strip(),
                circuit_type="IBT_LINK", voltage_kv=500,
                from_substation_id=subs[hv].id, to_substation_id=subs[lv].id,
                subsystem_id=ss.id, transformer_id=t.id if t else None,
                circuit_count=None, single_phi=False,
                status=e.get("status_hint") or "ENERGIZED", scenario_id="NORMAL",
                drawing_side=None, source_document_id=doc.id, confidence=1.0,
            )
        else:
            note = e.get("note") or f"traced dari SLD; confidence {conf:.1f}"
            c = Circuit(
                code=ccode, name=f"{subs[fk].name} - {subs[tk].name}",
                circuit_type=e.get("circuit_type_hint") or "SUTT",
                voltage_kv=by_key[fk].get("voltage_hv_kv") or 150,
                from_substation_id=subs[fk].id, to_substation_id=subs[tk].id,
                subsystem_id=ss.id, transformer_id=None,
                circuit_count=e.get("circuit_count") or 2, single_phi=False,
                status=e.get("status_hint") or "ENERGIZED", scenario_id="NORMAL",
                drawing_side=None, source_document_id=doc.id,
                note=("NEEDS_REVIEW; " + note) if conf < 0.9 else note,
                confidence=conf,
            )
        db.add(c)
        db.flush()
        circuits[ccode] = c
        circuits[f"{fk}-{tk}"] = c
        circuits[f"{tk}-{fk}"] = c

    for n in nodes:
        if not n.get("is_bay"):
            continue
        feeder = subs.get(n.get("bay_feeder_key"))
        if feeder is None or kinds.get(n.get("bay_feeder_key")) != "SUBSTATION":
            continue
        db.add(Bay(
            substation_id=subs[n["external_key"]].id,
            feeder_substation_id=feeder.id, subsystem_id=ss.id,
            name=f"Bay {subs[n['external_key']].name} @ {feeder.name}",
            bay_type="LINE", drawing_side=None,
            status=n.get("status_hint") or "ENERGIZED", note="Bootstrap via /ingest.",
        ))

    view = db.query(AnalyticalView).filter(AnalyticalView.view_key == f"{code}_FULL").first()
    if view is None:
        view = AnalyticalView(
            view_key=f"{code}_FULL", view_type="SUBSYSTEM", name="SLD lengkap",
            rule_profile="SUBSYSTEM_150", subsystem_id=ss.id,
            layout_hint="MERGED", drawing_side=None,
        )
        db.add(view)
        db.flush()
    _vm_seen: set[int] = set()
    for n in nodes:
        if kinds.get(n["external_key"]) != "SUBSTATION":
            continue
        nid = subs[n["external_key"]].id
        if nid in _vm_seen or db.query(ViewMembership).filter_by(
                view_id=view.id, node_kind="SUBSTATION", node_id=nid).first():
            _vm_seen.add(nid)
            continue
        db.add(ViewMembership(
            view_id=view.id, node_kind="SUBSTATION", node_id=nid,
            role=_role(n), tier_seed=n.get("tier_hint"), display_order=n.get("tier_hint"),
        ))
        _vm_seen.add(nid)

    for r in draft["risks"]:
        tag = _resolve_pin(r.get("pin_kind"), r.get("pin_key"), set(by_key))
        akind = aid = None
        if tag:
            akind, ref = tag
            if akind == "SUBSTATION":
                aid = subs[ref].id if ref in subs else None
            elif akind == "CIRCUIT":
                c = circuits.get(ref)
                aid = c.id if c else None
            elif akind == "TRANSFORMER":
                gk, _, unit = ref.partition(":")
                tcode = f"IBT_{(by_key[gk].get('confirmed_code') or gk).upper()}_{unit or '1'}"
                t = txs.get(tcode) or db.query(Transformer).filter(Transformer.code == tcode).first()
                aid = t.id if t else None
        seq = r.get("seq_no") or 0
        db.add(RiskRecord(
            risk_key=f"RISK-{code}-{seq:02d}",
            subsystem_id=ss.id, seq_no=seq, uit=r.get("uit") or "JBB",
            attach_kind=akind, attach_id=aid, attach_label=(r.get("pin_key") or None),
            title=r.get("title") or "", condition=r.get("condition") or "",
            impact=r.get("impact") or "", mitigation=r.get("mitigation") or "",
            follow_up=r.get("follow_up") or "",
            category=r.get("category") or "N-1", priority=r.get("priority") or "High",
            status="OPEN", source_document_id=doc.id,
        ))

    db.add(ChangeSet(
        change_key=f"CR-{code}-INGEST-{doc.id}", version_id=tv.id, action="MODEL",
        target_kind="SUBSYSTEM", target_ref=code,
        description=f"Bootstrap via /ingest. {len(nodes)} node, {len(edges)} penghantar, "
        f"{nreview} NEEDS_REVIEW.",
        status="APPLIED" if for_publish else "PROPOSED",
    ))
    db.flush()
    return view


def _role(n: dict) -> str:
    if (n.get("tier_hint") or 99) == 1:
        return "SOURCE"
    return "EXTERNAL_CONTEXT" if n.get("is_bay") else "CORE"


# ---------------------------------------------------------------------------
# render (savepoint) + publish (the one DB write)
# ---------------------------------------------------------------------------

def render_draft_svg(db: Session, draft: dict) -> str:
    """Dry-run: materialise into a SAVEPOINT, render with the real renderer, roll
    back. Nothing persists. A draft too broken to materialise renders a note."""
    draft = _clean(draft)
    code = (draft["subsystem"].get("code") or "DRAFT").strip().upper()
    name = draft["subsystem"].get("name") or "Draft"

    dup = _first_dup_code(draft)
    if dup:
        return _note_svg(f"Preview belum bisa dibuat: kode '{dup[0]}' dipakai dua node "
                         f"({dup[1]} & {dup[2]}). Perbaiki di panel review.")

    sp = db.begin_nested()
    try:
        view = _materialise(db, draft, code, name, draft.get("effective_date"),
                            for_publish=False)
        db.flush()
        svg = render_view_svg(db, view)
    except Exception as e:  # noqa: BLE001 - dry-run must never surface a 500
        svg = _note_svg(f"Preview gagal dirender: {e}")
    finally:
        sp.rollback()
    return svg


def publish(db: Session, draft: dict, code: str, name: str,
            effective_date: str | None) -> dict:
    draft = _clean(draft)
    code = (code or "").strip().upper()
    name = (name or "").strip()
    if not code or not name:
        raise IngestError("kode dan nama subsistem wajib diisi")
    v = validate(db, draft)
    if not v["ok"]:
        raise IngestError("validasi gagal: " + "; ".join(v["problems"]))
    if db.query(Subsystem).filter(Subsystem.code == code).first():
        raise IngestError(f"subsistem '{code}' sudah ada di basis data")

    view = _materialise(db, draft, code, name, effective_date, for_publish=True)
    db.commit()

    from app.services.topology import calculate_tier
    tiers = calculate_tier(db, view)
    return {
        "subsystem_code": code, "view_id": view.id, "view_key": view.view_key,
        "tier_count": len(set(tiers.values())),
    }


def _first_dup_code(draft: dict):
    seen: dict[str, str] = {}
    for n in draft["nodes"]:
        if n.get("resolution") == "SKIP":
            continue
        code = (n.get("confirmed_code") or n.get("external_key") or "").strip().upper()
        if code and code in seen and seen[code] != n["external_key"]:
            return (code, seen[code], n["external_key"])
        seen[code] = n["external_key"]
    return None


def _note_svg(msg: str) -> str:
    import html as _h
    words, cur, lines = msg.split(), "", []
    for w in words:
        if len(cur) + len(w) > 66:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    tspans = "".join(
        f'<tspan x="24" dy="{22 if i else 0}">{_h.escape(ln)}</tspan>'
        for i, ln in enumerate(lines))
    h = 60 + 22 * len(lines)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 {h}" '
            f'font-family="Arial, Helvetica, sans-serif">'
            f'<rect width="560" height="{h}" fill="#fffaf1"/>'
            f'<text x="24" y="34" font-size="12" fill="#b45309">{tspans}</text></svg>')
