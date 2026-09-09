"""Entity reconciliation: match an ObservedObject to a canonical Substation.

Scoring inputs (starter): object type, site/name similarity, HV voltage, LV
voltage, unit number. Production should also use connected bus, neighbouring
objects, asset ID / NIA / Maximo, topology signature, effective date.

Outcomes:
    AUTO_MATCH   score >= 0.85   -- safe to attach automatically
    REVIEW       0.65 - 0.85     -- human confirmation
    CREATE_NEW   score < 0.65    -- probably a new physical object
    CONFLICT     (topology says two drawings disagree -- flagged elsewhere)

Safety rule: a low-confidence engineering match must never silently merge topology.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from app.models import ObservedObject, Substation

AUTO_MATCH = 0.85
REVIEW = 0.65

_NOISE = re.compile(r"\b(GI|GITET|GIS|GISTET|IBT|TRF|TRAFO|UNIT|NO|KTT|BARU|LAMA|BUS)\b")


def normalize_name(value: str | None) -> str:
    v = (value or "").upper()
    v = _NOISE.sub(" ", v)
    v = re.sub(r"[^A-Z0-9]+", " ", v)
    return " ".join(v.split())


def _eq(a, b) -> bool:
    return a is not None and b is not None and str(a).strip().upper() == str(b).strip().upper()


def _near_voltage(a, b, tol: float = 1.0) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


def score_observed_to_substation(obs: ObservedObject, sub: Substation):
    points = 0.0
    evidence: dict = {}

    if _eq(obs.object_type, "SUBSTATION") or obs.object_type in ("GI", "GITET", "GIS"):
        points += 0.10
        evidence["type"] = True

    a = normalize_name(obs.site_name or obs.raw_label)
    b = normalize_name(sub.name)
    sim = SequenceMatcher(None, a, b).ratio() if a and b else 0.0
    points += 0.55 * sim
    evidence["name_similarity"] = round(sim, 3)

    if _eq(obs.raw_label, sub.code) or _eq(obs.site_name, sub.code):
        points += 0.15
        evidence["code_exact"] = True

    if _near_voltage(obs.voltage_hv_kv, sub.voltage_kv):
        points += 0.15
        evidence["hv"] = True
    if _near_voltage(obs.voltage_lv_kv, sub.voltage_kv):
        points += 0.05
        evidence["lv"] = True

    return min(points, 1.0), evidence


def find_candidates(db: Session, obs: ObservedObject, limit: int = 5):
    out = []
    for sub in db.query(Substation).filter(Substation.active.is_(True)).all():
        score, evidence = score_observed_to_substation(obs, sub)
        out.append({"substation": sub, "score": score, "evidence": evidence})
    return sorted(out, key=lambda x: x["score"], reverse=True)[:limit]


def classify(score: float) -> str:
    if score >= AUTO_MATCH:
        return "AUTO_MATCH"
    if score >= REVIEW:
        return "REVIEW"
    return "CREATE_NEW"
