"""Tier engine tests, exercised against the seeded SS_LBK fixture."""
from app.models import AnalyticalView, Circuit, Substation
from app.services.topology import RULE_PROFILES, calculate_tier, get_view_graph


def _view(db, key):
    return db.query(AnalyticalView).filter_by(view_key=key).first()


def _tier_by_code(db, view):
    nodes, _, _, _, _ = get_view_graph(db, view)
    tier = calculate_tier(db, view)
    code = {}
    for (kind, nid), obj in nodes.items():
        if kind == "SUBSTATION":
            code[obj.code] = tier.get((kind, nid))
    return code


def test_profiles_exist():
    assert {"BACKBONE_500", "IBT_500_150", "SUBSYSTEM_150"}.issubset(RULE_PROFILES)


def test_sources_are_tier_1(db):
    t = _tier_by_code(db, _view(db, "SS_LBK_FULL"))
    for code in ("KMBGN", "NBRJA", "LTKNG", "GITET_KMBGN", "GITET_NBRJA"):
        assert t[code] == 1, f"{code} should be Tier 1, got {t[code]}"


def test_tier_increases_downstream(db):
    t = _tier_by_code(db, _view(db, "SS_LBK_FULL"))
    # New Senayan (fed from Kembangan) then Senayan (fed from New Senayan)
    assert t["NSYAN"] == 2
    assert t["SNYAN"] == 3


def test_not_yet_energised_gitet_is_not_in_tier_graph(db):
    """GITET New Cikupa is NEW_NOT_ENERGIZED -> node exists, no Tier."""
    t = _tier_by_code(db, _view(db, "SS_LBK_FULL"))
    assert "NCKUPA" in t
    assert t["NCKUPA"] is None
    assert t["TGBRU_3"] is None


def test_jatake_tier_is_context_dependent(db):
    """Jatake appears in both SLDs; Tier differs by which seed reaches it.
    This is why Tier is computed per-view and never stored on Substation."""
    t_bal = _tier_by_code(db, _view(db, "SS_LBK_BALARAJA"))
    t_kem = _tier_by_code(db, _view(db, "SS_LBK_KEMBANGAN"))
    assert t_bal["JTAKE"] == 5              # reached via Cikupa on the Balaraja side
    assert t_kem["JTAKE"] is None           # the Kembangan SLD alone doesn't feed it
    assert not hasattr(Substation, "tier")  # tier is never a column


def test_load_transformer_does_not_add_a_tier(db):
    """Ulujami is a dead-end GI (150/20 load only). It must not create a Tier-4
    '20 kV' node -- downstream load is not tier progression."""
    v = _view(db, "SS_LBK_FULL")
    nodes, edges, _, _, _ = get_view_graph(db, v)
    # no circuit leaves Ulujami toward another substation
    ulj = db.query(Substation).filter_by(code="ULJMI").first()
    out = [c for c in edges if ulj.id in (c.from_substation_id, c.to_substation_id)]
    assert len(out) == 1  # only the feed from New Senayan


def test_single_phi_circuits_flagged(db):
    rows = db.query(Circuit).filter(Circuit.single_phi.is_(True)).all()
    names = {c.code for c in rows}
    assert "SUTT_PSKMS_PSKBR" in names
    assert "SUTT_PSKBR_GJTGL" in names
