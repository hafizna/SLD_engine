"""View projection + Tier calculation.

Tier matrix (Buku Kerawanan SJB 2026, PENDAHULUAN hal. xvi):

    Sistem 500 kV                          Sistem 150 kV
    ------------------------------------   ------------------------------------
T1  GITET Outlet Pembangkit 500 kV         GI dgn Bay Input langsung ke
                                           Pembangkit 150 kV dan/atau GITET (IBT)
T2  GITET kedua (Bay Input ~ GITET T1)     GI kedua (Bay Input ~ GI T1)
T3  GITET ketiga (Bay Input ~ GITET T2)    GI ketiga (Bay Input ~ GI T2)
T4  GITET keempat ...                      GI keempat ... dst

Key rule the starter engine got wrong and this one fixes:
    Tier progresses through the GI CORE network only. A load transformer
    (150/20) hanging off a GI does NOT make the 20 kV side "Tier n+1".
    Downstream load context != Tier progression.

So traversal:
    * nodes  = substations in the view that are NOT pure downstream-load
    * edges  = circuits between those substations (line + IBT links),
               restricted to the active scenario
    * seeds  = Tier-1 substations (explicit tier_seed, or role SOURCE /
               SOURCE_BOUNDARY, or a substation fed directly by a
               GeneratingUnit / an IBT from a GITET)
    * BFS hop count over that GI graph  ->  Tier
"""
from __future__ import annotations

from collections import defaultdict, deque

from sqlalchemy.orm import Session

from app.models import (
    AnalyticalView,
    Circuit,
    GeneratingUnit,
    Substation,
    Transformer,
    ViewMembership,
)

RULE_PROFILES = {
    "BACKBONE_500": {
        "seed_roles": {"SOURCE"},
        "tier_mode": "GI_HOPS",
        "downstream_roles": {"DOWNSTREAM_CONTEXT"},
    },
    "IBT_500_150": {
        "seed_roles": {"SOURCE"},
        "tier_mode": "NONE",  # inherits upstream 500 kV tier + IBT identity
        "downstream_roles": {"DOWNSTREAM_CONTEXT"},
    },
    "SUBSYSTEM_150": {
        "seed_roles": {"SOURCE", "SOURCE_BOUNDARY"},
        "tier_mode": "GI_HOPS",
        "downstream_roles": {"DOWNSTREAM_CONTEXT", "EXTERNAL_CONTEXT"},
    },
}

# Statuses that count as "in service" for the risk map.
# The map is the current-condition ideal snapshot from the Buku Kerawanan
# (non-dynamic). A GITET/GI that is not yet energised (NEW_NOT_ENERGIZED) or
# still on the drawing board (PLANNED) is kept as a node for information but is
# NOT part of the connectivity / Tier graph. When such a project is actually
# commissioned it is a structural change (new TopologyVersion, possibly a new
# Subsystem), modelled through a change request -- not a toggle here.
# OWNED_BY_CUSTOMER (a KTT asset drawn in a dashed box) IS in service -- it is a
# real connected load, just not a PLN asset.
LIVE_STATUSES = {"ENERGIZED", "DE_ENERGIZED", "OWNED_BY_CUSTOMER"}


def _is_live(status: str | None) -> bool:
    return (status or "ENERGIZED") in LIVE_STATUSES


def _members(db: Session, view: AnalyticalView):
    rows = db.query(ViewMembership).filter(ViewMembership.view_id == view.id).all()
    return rows


def get_view_graph(db: Session, view: AnalyticalView):
    """Return (nodes, edges, roles, seeds, seed_override) for a view.

    nodes: {("SUBSTATION", id): Substation}  and generating units / transformers
    edges: list[Circuit] restricted to the view's substations + scenario,
           filtered to in-service status
    roles: {(kind, id): role}
    seeds: set[(kind, id)] tier-1 seeds (energised only)
    """
    profile = RULE_PROFILES.get(view.rule_profile, RULE_PROFILES["SUBSYSTEM_150"])
    members = _members(db, view)

    roles: dict[tuple[str, int], str] = {}
    tier_seed_override: dict[tuple[str, int], int] = {}
    sub_ids: set[int] = set()
    gen_ids: set[int] = set()
    tx_ids: set[int] = set()
    for m in members:
        key = (m.node_kind, m.node_id)
        roles[key] = m.role
        if m.tier_seed:
            tier_seed_override[key] = m.tier_seed
        if m.node_kind == "SUBSTATION":
            sub_ids.add(m.node_id)
        elif m.node_kind == "GENERATING_UNIT":
            gen_ids.add(m.node_id)
        elif m.node_kind == "TRANSFORMER":
            tx_ids.add(m.node_id)

    nodes: dict[tuple[str, int], object] = {}
    if sub_ids:
        for s in db.query(Substation).filter(Substation.id.in_(sub_ids)).all():
            nodes[("SUBSTATION", s.id)] = s
    if gen_ids:
        for g in db.query(GeneratingUnit).filter(GeneratingUnit.id.in_(gen_ids)).all():
            nodes[("GENERATING_UNIT", g.id)] = g
    if tx_ids:
        for t in db.query(Transformer).filter(Transformer.id.in_(tx_ids)).all():
            nodes[("TRANSFORMER", t.id)] = t

    edges: list[Circuit] = []
    if sub_ids:
        q = db.query(Circuit).filter(
            Circuit.from_substation_id.in_(sub_ids),
            Circuit.to_substation_id.in_(sub_ids),
            Circuit.active.is_(True),
        )
        for c in q.all():
            if c.scenario_id not in ("NORMAL", view.scenario_id):
                continue
            if view.drawing_side and c.drawing_side and c.drawing_side != view.drawing_side:
                continue
            if not _is_live(c.status):
                continue
            edges.append(c)

    live_sub = {
        key for key, obj in nodes.items()
        if key[0] == "SUBSTATION" and _is_live(obj.status)
    }

    # ---- determine tier-1 seeds -------------------------------------------
    seeds: set[tuple[str, int]] = set()
    for key, role in roles.items():
        if role in profile["seed_roles"] and (key[0] != "SUBSTATION" or key in live_sub):
            seeds.add(key)
    for key in tier_seed_override:
        if tier_seed_override[key] == 1 and (key[0] != "SUBSTATION" or key in live_sub):
            seeds.add(key)

    # a substation fed directly by a generating unit in this view is a seed
    for (_, gid) in [k for k in nodes if k[0] == "GENERATING_UNIT"]:
        g = nodes[("GENERATING_UNIT", gid)]
        if g.outlet_substation_id and ("SUBSTATION", g.outlet_substation_id) in live_sub:
            seeds.add(("SUBSTATION", g.outlet_substation_id))

    # a substation with a live IBT (500/150 step-down) present in the view is a seed
    if sub_ids:
        for t in db.query(Transformer).filter(
            Transformer.substation_id.in_(sub_ids),
            Transformer.transformer_type == "IBT",
            Transformer.active.is_(True),
        ).all():
            if ("SUBSTATION", t.substation_id) in live_sub and _is_live(t.status):
                seeds.add(("SUBSTATION", t.substation_id))

    return nodes, edges, roles, seeds, tier_seed_override


def calculate_tier(db: Session, view: AnalyticalView) -> dict[tuple[str, int], int]:
    """Tier per substation for this view.

    The Buku Kerawanan already assigns every GI on its SLD a Tier band
    (TIER-1..6). That is the authority for the risk map -- we reproduce the
    book, we do not recompute it. `ViewMembership.tier_seed` and, failing that,
    `ViewMembership.display_order` carry the book's Tier. Only substations with
    no book Tier fall back to a BFS hop count from the seeds.

    `validate_tier` (separate) flags where a BFS hop count disagrees with the
    book -- e.g. a "bay panjang" that crosses tiers -- for field review.
    """
    profile = RULE_PROFILES.get(view.rule_profile, RULE_PROFILES["SUBSYSTEM_150"])
    if profile["tier_mode"] == "NONE":
        return {}

    nodes, edges, roles, seeds, seed_override = get_view_graph(db, view)

    members = {(m.node_kind, m.node_id): m for m in _members(db, view)}
    live_sub_ids = {
        k[1] for k, obj in nodes.items()
        if k[0] == "SUBSTATION" and _is_live(obj.status)
    }

    tier: dict[tuple[str, int], int] = {}
    no_book: list[int] = []
    for (kind, nid), obj in nodes.items():
        if kind != "SUBSTATION":
            continue
        if nid not in live_sub_ids:
            continue  # not-yet-energised -> no Tier
        m = members.get((kind, nid))
        book_t = (m.tier_seed if m and m.tier_seed else
                  (m.display_order if m and m.display_order else None))
        if book_t is not None:
            tier[(kind, nid)] = int(book_t)
        else:
            no_book.append(nid)

    if not no_book:
        return tier

    # BFS fallback only for the GIs with no book Tier
    adj: dict[int, set[int]] = defaultdict(set)
    for c in edges:
        adj[c.from_substation_id].add(c.to_substation_id)
        adj[c.to_substation_id].add(c.from_substation_id)
    q = deque(sid for (k, sid) in tier if k == "SUBSTATION")
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v in no_book and ("SUBSTATION", v) not in tier:
                tier[("SUBSTATION", v)] = tier[("SUBSTATION", u)] + 1
                q.append(v)
    return tier


def _legacy_bfs_tier(db: Session, view: AnalyticalView):
    profile = RULE_PROFILES.get(view.rule_profile, RULE_PROFILES["SUBSYSTEM_150"])
    if profile["tier_mode"] == "NONE":
        return {}
    nodes, edges, roles, seeds, seed_override = get_view_graph(db, view)

    downstream = {
        key for key, role in roles.items() if role in profile["downstream_roles"]
    }

    # adjacency over substation nodes only (the GI core network)
    adj: dict[int, set[int]] = defaultdict(set)
    for c in edges:
        a = ("SUBSTATION", c.from_substation_id)
        b = ("SUBSTATION", c.to_substation_id)
        if a in downstream or b in downstream:
            continue  # a load spur does not carry tier progression
        adj[c.from_substation_id].add(c.to_substation_id)
        adj[c.to_substation_id].add(c.from_substation_id)

    tier: dict[tuple[str, int], int] = {}
    q: deque[int] = deque()
    for key in seeds:
        if key[0] != "SUBSTATION":
            continue
        sid = key[1]
        start = seed_override.get(key, 1)
        if sid not in tier or start < tier[("SUBSTATION", sid)]:
            tier[("SUBSTATION", sid)] = start
            q.append(sid)

    while q:
        u = q.popleft()
        cur = tier[("SUBSTATION", u)]
        for v in adj[u]:
            cand = cur + 1
            if ("SUBSTATION", v) not in tier or cand < tier[("SUBSTATION", v)]:
                tier[("SUBSTATION", v)] = cand
                q.append(v)

    # downstream-load substations inherit their feeding GI's tier (no +1)
    for c in edges:
        a, b = ("SUBSTATION", c.from_substation_id), ("SUBSTATION", c.to_substation_id)
        if a in downstream and b in tier and a not in tier:
            tier[a] = tier[b]
        if b in downstream and a in tier and b not in tier:
            tier[b] = tier[a]

    return tier


def validate_tier(db: Session, view: AnalyticalView):
    """Compare the book's Tier (calculate_tier) with a pure BFS hop count and
    report where they disagree -- a "bay panjang" that crosses Tier bands, a
    missing feed, or a mis-traced edge. Returns a list of dicts for review.
    """
    book = calculate_tier(db, view)
    bfs = _legacy_bfs_tier(db, view)
    nodes, _, _, _, _ = get_view_graph(db, view)
    out = []
    for (kind, nid), obj in nodes.items():
        if kind != "SUBSTATION":
            continue
        bt = book.get((kind, nid))
        ft = bfs.get((kind, nid))
        if bt is not None and ft is not None and bt != ft:
            out.append({"code": obj.code, "name": obj.name, "book_tier": bt, "bfs_tier": ft})
    return sorted(out, key=lambda r: abs(r["bfs_tier"] - r["book_tier"]), reverse=True)


def classify_layout(db: Session, view: AnalyticalView):
    """Split the view's substations into 'core' (own Tier row + busbar) and
    'spur' (a bay hanging off one feeder busbar, drawn with NO busbar).

    In the book, a GI that is only a bay on a Tier-N busbar -- Durikosambi,
    Petukangan, Abadi Guna Papan, Mampang off the Kembangan bus -- is drawn as
    a short stub + a name, not as a Tier node. A spur here is a substation that:
      * has graph degree 1 (a single feeder), AND
      * either has a context role (BOUNDARY / EXTERNAL_CONTEXT / DOWNSTREAM_CONTEXT),
        OR has no book Tier of its own on this drawing,
        OR its lone feeder is a Tier-1 source busbar (a bay straight off it).

    Returns (core_ids, spur: {spur_sub_id: feeder_sub_id}).
    """
    nodes, edges, roles, _, _ = get_view_graph(db, view)
    sub_ids = {k[1] for k in nodes if k[0] == "SUBSTATION"}
    tier = calculate_tier(db, view)
    members = {(m.node_kind, m.node_id): m for m in _members(db, view)}

    deg: dict[int, int] = defaultdict(int)
    neigh: dict[int, list[int]] = defaultdict(list)
    for c in edges:
        deg[c.from_substation_id] += 1
        deg[c.to_substation_id] += 1
        neigh[c.from_substation_id].append(c.to_substation_id)
        neigh[c.to_substation_id].append(c.from_substation_id)

    context_roles = {"BOUNDARY", "EXTERNAL_CONTEXT", "DOWNSTREAM_CONTEXT"}
    spur: dict[int, int] = {}
    for sid in sub_ids:
        if deg.get(sid, 0) != 1:
            continue
        role = roles.get(("SUBSTATION", sid), "")
        feeder = neigh[sid][0]
        m = members.get(("SUBSTATION", sid))
        book_t = (m.tier_seed if m and m.tier_seed else
                  (m.display_order if m and m.display_order else None))
        feeder_t = tier.get(("SUBSTATION", feeder))
        is_bay_off_source = feeder_t == 1 and (book_t is None or book_t == 1)
        if role in context_roles or book_t is None or is_bay_off_source:
            spur[sid] = feeder

    core_ids = sub_ids - set(spur)
    return core_ids, spur
