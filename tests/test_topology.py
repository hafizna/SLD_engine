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


def test_explicit_circuit_membership_overrides_owner_without_leaking_other_edges(db):
    from app.models import Subsystem, ViewMembership
    view = _view(db, 'SS_LBK_KEMBANGAN')
    edges = get_view_graph(db, view)[1]
    chosen, excluded = edges[:2]
    owner = Subsystem(code='OTHER_OWNER', name='Other source workbook')
    db.add(owner)
    db.flush()
    chosen.subsystem_id = owner.id
    chosen.drawing_side = 'OTHER'
    db.query(ViewMembership).filter_by(view_id=view.id, node_kind='CIRCUIT').delete()
    db.add(ViewMembership(view_id=view.id, node_kind='CIRCUIT', node_id=chosen.id, role='CORE'))
    db.flush()
    actual = {c.id for c in get_view_graph(db, view)[1]}
    assert actual == {chosen.id}
    assert excluded.id not in actual


def test_two_views_only_no_merged(db):
    from app.models import AnalyticalView
    keys = {v.view_key for v in db.query(AnalyticalView).all()}
    assert keys == {"SS_LBK_KEMBANGAN", "SS_LBK_BALARAJA"}


def test_sources_are_tier_1(db):
    t = _tier_by_code(db, _view(db, "SS_LBK_KEMBANGAN"))
    for code in ("KMBGN", "GITET_KMBGN"):
        assert t[code] == 1, f"{code} should be Tier 1, got {t[code]}"
    t = _tier_by_code(db, _view(db, "SS_LBK_BALARAJA"))
    for code in ("NBRJA", "LTKNG", "GITET_NBRJA"):
        assert t[code] == 1, f"{code} should be Tier 1, got {t[code]}"


def test_tier_increases_downstream(db):
    t = _tier_by_code(db, _view(db, "SS_LBK_KEMBANGAN"))
    # New Senayan (fed from Kembangan) then Senayan (fed from New Senayan)
    assert t["NSYAN"] == 2
    assert t["SNYAN"] == 3


def test_not_yet_energised_gitet_is_not_in_tier_graph(db):
    """GITET New Cikupa is NEW_NOT_ENERGIZED -> node exists, no Tier."""
    t = _tier_by_code(db, _view(db, "SS_LBK_BALARAJA"))
    assert "NCKUPA" in t
    assert t["NCKUPA"] is None
    assert t["TGBRU_3"] is None


def test_jatake_tier_is_context_dependent(db):
    """Jatake is drawn on BOTH SLDs at DIFFERENT Tiers (the book's own layout):
    Tier 5 on the Kembangan drawing (a Cikupa spur), Tier 6 on the Balaraja
    drawing (an output bay off Tier 6). This is why Tier is per-view, never a
    column on Substation."""
    t_bal = _tier_by_code(db, _view(db, "SS_LBK_BALARAJA"))
    t_kem = _tier_by_code(db, _view(db, "SS_LBK_KEMBANGAN"))
    assert t_kem["JTAKE"] == 5
    assert t_bal["JTAKE"] == 6
    assert not hasattr(Substation, "tier")


def test_suvarna_tier_differs_by_drawing(db):
    """Suvarna Sutra: Tier 5 on Kembangan (spur off Cikupa T4), Tier 3 on
    Balaraja (fed from Sindang Jaya / Balaraja)."""
    t_kem = _tier_by_code(db, _view(db, "SS_LBK_KEMBANGAN"))
    t_bal = _tier_by_code(db, _view(db, "SS_LBK_BALARAJA"))
    assert t_kem["SVRNA"] == 5
    assert t_bal["SVRNA"] == 3


def test_load_transformer_does_not_add_a_tier(db):
    """Ulujami is a dead-end GI (150/20 load only). It must not create a Tier-4
    '20 kV' node -- downstream load is not tier progression."""
    v = _view(db, "SS_LBK_KEMBANGAN")
    nodes, edges, _, _, _ = get_view_graph(db, v)
    ulj = db.query(Substation).filter_by(code="ULJMI").first()
    out = [c for c in edges if ulj.id in (c.from_substation_id, c.to_substation_id)]
    assert len(out) == 1  # only the feed from New Senayan


def test_single_phi_circuits_flagged(db):
    rows = db.query(Circuit).filter(Circuit.single_phi.is_(True)).all()
    names = {c.code for c in rows}
    assert "SUTT_PSKMS_PSKBR" in names
    assert "SUTT_PSKBR_GJTGL" in names
