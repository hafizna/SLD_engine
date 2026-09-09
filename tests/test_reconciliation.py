"""Reconciliation: an ObservedObject read from a drawing must resolve to the
one canonical Substation even when the label is written differently."""
from types import SimpleNamespace

from app.services.reconciliation import (
    classify,
    find_candidates,
    normalize_name,
    score_observed_to_substation,
)


def test_normalize_strips_noise():
    assert normalize_name("GI Pasar Kemis Baru") == "PASAR KEMIS"
    assert normalize_name("GITET Kembangan") == "KEMBANGAN"


def test_same_gi_different_label_scores_high(db):
    obs = SimpleNamespace(
        object_type="GI", site_name="Kembangan", raw_label="KMBGN",
        voltage_hv_kv=150, voltage_lv_kv=None, unit_no=None,
    )
    rows = find_candidates(db, obs)
    top = rows[0]
    assert top["substation"].code == "KMBGN"
    assert classify(top["score"]) in ("AUTO_MATCH", "REVIEW")


def test_wrong_site_not_auto_match(db):
    kembangan = next(
        s for s in [r["substation"] for r in find_candidates(
            db, SimpleNamespace(object_type="GI", site_name="Kembangan",
                                raw_label="Kembangan", voltage_hv_kv=150,
                                voltage_lv_kv=None, unit_no=None))]
        if s.code == "KMBGN"
    )
    obs = SimpleNamespace(
        object_type="GI", site_name="Gandul", raw_label="GI Gandul",
        voltage_hv_kv=150, voltage_lv_kv=None, unit_no=None,
    )
    score, _ = score_observed_to_substation(obs, kembangan)
    assert score < 0.85
