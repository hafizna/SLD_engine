"""SLD renderer -- Buku Kerawanan drawing grammar, fixed-grid layout.

Line grammar (from the book's legend):
  * SUTT / SUTET         SOLID line
  * SKTT / SKLT          DASHED red line
  * RENCANA (not energised)   DASHED black line
  * OFF / tidak beroperasi    solid GREY line
  * 2 sirkit             two parallel lines; 1 sirkit / single phi -> one, thinner
  * busbar               SOLID bold, coloured by voltage
                         (black busbar = planned / not yet energised)
  * a CB box where a circuit meets a busbar
  * cross-tier feed: a penghantar whose two GIs are NOT in adjacent Tier
    bands, or that runs against the normal downward Tier flow (e.g. Curug T5
    fed from Cikupa T4). The book draws these stretched across Tier bands --
    that is a drawing-spacing artefact, NOT a real distance. Here it is just
    an edge routed cleanly around/through the grid; it never changes a Tier.
  * IBT 500/150 link     one vertical chain per transformer: CB(HV) -> triple
                         circle -> CB(LV)
  * bay (a small GI drawn only as a stub on a feeder busbar -- Durikosambi,
    Petukangan, AGP, Mampang off Kembangan): stub + CB + name, NO busbar. A GI
    can be a bay on several busbars.
  * GI 150/20 load transformer  double circle under the busbar
  * shunt capacitor / bus coupler   standard symbols

Layout: row = book Tier band; each GI gets a fixed lane; busbar width scales
with the number of attachments (own port per attachment); child GIs nudged
toward their parent's x.
"""
from __future__ import annotations

import html
import re
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import AnalyticalView, Bay, Circuit, DiagramNodePosition, RiskRecord, Transformer
from app.services.topology import _is_live, calculate_tier, classify_layout, get_view_graph

VOLT_COLOR = {500: "#0047AB", 275: "#00A6D6", 150: "#C00000", 70: "#E6B800", 20: "#E67300"}

# busbar styling by status (colour, dash)
STATUS_STROKE = {
    "ENERGIZED": None,               # -> voltage colour
    "NEW_NOT_ENERGIZED": "#111111",  # black busbar = planned / not yet energised
    "PLANNED": "#9AA0A6",
    "DE_ENERGIZED": "#C0392B",
    "OWNED_BY_CUSTOMER": "#7A5C00",
}
STATUS_DASH = {
    "ENERGIZED": "none",
    "NEW_NOT_ENERGIZED": "12 7",
    "PLANNED": "3 6",
    "DE_ENERGIZED": "2 5",
    "OWNED_BY_CUSTOMER": "5 4",
}


def _circuit_style(c):
    """(stroke, dash) for a circuit, from its type first, then its status."""
    if c.status in ("NEW_NOT_ENERGIZED", "PLANNED"):
        return "#111111", "3 6"            # RENCANA = black dashed
    if c.status == "DE_ENERGIZED":
        return "#9AA0A6", "none"           # OFF = grey solid
    ct = (c.circuit_type or "SUTT").upper()
    if ct in ("SKTT", "SKLT"):
        return "#C00000", "7 5"            # cable = red dashed
    if ct == "IBT_LINK":
        return "#8a6a3a", "none"
    return "#C00000", "none"               # SUTT / SUTET = solid

BAY_SLOT = 46          # horizontal space per attachment (bay / circuit / trafo)
BUS_MIN_HALF = 55      # minimum busbar half-length
GUTTER = 70            # clear space between one GI's lane and the next
ROW_H = 200
MARGIN_X = 150
MARGIN_Y = 120
CB = 10
CB_GAP = 12
EDGE_MARGIN = 54       # width of the outer channel a cross-tier feed routes in


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def _vcol(kv) -> str:
    return VOLT_COLOR.get(int(kv or 150), "#C00000")


def _cb(x, y, color):
    return f'<rect x="{x - CB / 2:.1f}" y="{y - CB / 2:.1f}" width="{CB}" height="{CB}" fill="{color}"/>'


HOP_R = 4.5   # radius of the little arc where one line hops over another


def _ortho_path(x1, y1, yb, x2, y3):
    """A square Z path: vertical from (x1,y1) to yb, horizontal to x2, vertical
    to y3. Returned as (verticals, horizontal) segment tuples for hop testing.
      verticals: [(x, ya, yb), ...]   horizontal: (y, xa, xb)
    """
    verts = [(x1, min(y1, yb), max(y1, yb)), (x2, min(yb, y3), max(yb, y3))]
    horiz = (yb, min(x1, x2), max(x1, x2))
    return verts, horiz


def _emit_hopped(x1, y1, yb, x2, y3, cross_xs):
    """SVG path 'd' for the square Z, with a small arc where the horizontal run
    at height yb passes each x in cross_xs (a crossing vertical of another
    line)."""
    xs = sorted(x for x in cross_xs if min(x1, x2) + HOP_R < x < max(x1, x2) - HOP_R)
    d = [f"M{x1:.1f},{y1:.1f} V{yb:.1f}"]
    left_to_right = x2 >= x1
    cur = x1
    seq = xs if left_to_right else list(reversed(xs))
    for cx in seq:
        if left_to_right:
            d.append(f"H{cx - HOP_R:.1f} A{HOP_R} {HOP_R} 0 0 1 {cx + HOP_R:.1f} {yb:.1f}")
        else:
            d.append(f"H{cx + HOP_R:.1f} A{HOP_R} {HOP_R} 0 0 0 {cx - HOP_R:.1f} {yb:.1f}")
        cur = cx
    d.append(f"H{x2:.1f} V{y3:.1f}")
    return " ".join(d)


def _cbs(x, y, color, n, dx=None):
    """n CB squares stacked horizontally (one per sirkit)."""
    dx = dx if dx is not None else (CB + 3)
    x0 = x - (n - 1) * dx / 2
    return "".join(_cb(x0 + i * dx, y, color) for i in range(n))


def _sym_transformer(x, y, hv_color, lv_color="#E67300"):
    """150/20 kV load transformer: top circle in the HV (busbar) colour, bottom
    circle in the LV colour (20 kV = orange)."""
    r = 9
    return (
        f'<g fill="none" stroke-width="1.7">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 7:.1f}" stroke="{hv_color}"/>'
        f'<circle cx="{x:.1f}" cy="{y + 7 + r:.1f}" r="{r}" stroke="{hv_color}"/>'
        f'<circle cx="{x:.1f}" cy="{y + 7 + r + 8:.1f}" r="{r}" stroke="{lv_color}"/>'
        f"</g>"
    )


def _sym_capacitor(x, y, color):
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.7">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 10:.1f}"/>'
        f'<line x1="{x - 8:.1f}" y1="{y + 10:.1f}" x2="{x + 8:.1f}" y2="{y + 10:.1f}"/>'
        f'<line x1="{x - 8:.1f}" y1="{y + 15:.1f}" x2="{x + 8:.1f}" y2="{y + 15:.1f}"/>'
        f'<line x1="{x:.1f}" y1="{y + 15:.1f}" x2="{x:.1f}" y2="{y + 22:.1f}"/>'
        f'<path d="M{x - 6:.1f},{y + 22:.1f} h12 M{x - 4:.1f},{y + 25:.1f} h8 M{x - 2:.1f},{y + 28:.1f} h4"/>'
        f"</g>"
    )


def _sym_ibt_inline(x, y, hv_color="#0047AB", lv_color="#C00000"):
    """IBT 500/150: top circle HV colour (blue 500), lower two LV colour
    (red 150)."""
    r = 7.5
    return (
        f'<g fill="#ffffff" stroke-width="1.7">'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" stroke="{hv_color}"/>'
        f'<circle cx="{x - 4.5:.1f}" cy="{y + 8:.1f}" r="{r}" stroke="{lv_color}"/>'
        f'<circle cx="{x + 4.5:.1f}" cy="{y + 8:.1f}" r="{r}" stroke="{lv_color}"/>'
        f"</g>"
    )


def _sym_generator(x, y, color):
    r = 12
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.7">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 6:.1f}"/>'
        f'<circle cx="{x:.1f}" cy="{y + 6 + r:.1f}" r="{r}"/>'
        f'<path d="M{x - 6:.1f},{y + 6 + r:.1f} q3,-6 6,0 q3,6 6,0"/>'
        f"</g>"
    )


def render_view_svg(db: Session, view: AnalyticalView) -> str:
    nodes, edges, roles, seeds, _ = get_view_graph(db, view)
    tier = calculate_tier(db, view)
    core_ids, spur = classify_layout(db, view)

    subs = {k[1]: n for k, n in nodes.items() if k[0] == "SUBSTATION"}
    gens = {k[1]: n for k, n in nodes.items() if k[0] == "GENERATING_UNIT"}
    if not subs:
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 120">'
                '<text x="20" y="60" font-family="Arial" font-size="14">No substations in view</text></svg>')

    tx_by_sub: dict[int, list] = defaultdict(list)
    for t in db.query(Transformer).filter(Transformer.substation_id.in_(subs)).all():
        tx_by_sub[t.substation_id].append(t)

    bay_rows = db.query(Bay).filter(Bay.substation_id.in_(subs), Bay.active.is_(True)).all()
    # a Bay row scoped to another subsystem does not apply to this view
    bay_rows = [b for b in bay_rows
                if b.subsystem_id is None or b.subsystem_id == view.subsystem_id]
    if view.drawing_side:
        bay_rows = [b for b in bay_rows if not b.drawing_side or b.drawing_side == view.drawing_side]
    bays_by_feeder: dict[int, list] = defaultdict(list)
    bay_gi_ids: set[int] = set()
    for b in bay_rows:
        if b.feeder_substation_id:
            bays_by_feeder[b.feeder_substation_id].append(b)
            bay_gi_ids.add(b.substation_id)

    risk_on: dict[tuple[str, int], list[int]] = defaultdict(list)
    if view.subsystem_id:
        for r in db.query(RiskRecord).filter(RiskRecord.subsystem_id == view.subsystem_id).all():
            if r.attach_kind and r.attach_id:
                risk_on[(r.attach_kind, r.attach_id)].append(r.seq_no or 0)

    # ---- IBT structure --------------------------------------------------
    # An IBT chain (triple circle + CBs) is only drawn for a LIVE GITET feeding
    # a LIVE bus. A planned GITET's link is drawn as a plain black dashed line
    # and the GITET as a plain black busbar.
    gitet_feeds: dict[int, int] = {}
    ibt_links_by_pair: dict[tuple[int, int], list] = defaultdict(list)
    _ibt_as_line: set[int] = set()   # circuit ids to route like a normal line
    for c in edges:
        if c.circuit_type != "IBT_LINK":
            continue
        a, b = c.from_substation_id, c.to_substation_id
        hv = a if (subs.get(a) and subs[a].voltage_kv >= subs.get(b, subs[a]).voltage_kv) else b
        lv = b if hv == a else a
        if subs.get(hv) and subs[hv].substation_type == "GITET":
            if _is_live(subs[hv].status) and _is_live(subs.get(lv, subs[hv]).status) and _is_live(c.status):
                gitet_feeds[hv] = lv
                ibt_links_by_pair[(hv, lv)].append(c)
            else:
                _ibt_as_line.add(c.id)

    line_edges = [c for c in edges
                  if (c.circuit_type != "IBT_LINK" or c.id in _ibt_as_line)
                  and c.from_substation_id not in bay_gi_ids
                  and c.to_substation_id not in bay_gi_ids
                  and c.from_substation_id in subs and c.to_substation_id in subs]

    # book Tier band per GI (ViewMembership.tier_seed, else display_order) --
    # used to place a GI the Tier engine did not rank because it is not yet
    # energised. The book still drew it in a band; we honour that band.
    from app.models import ViewMembership as _VM
    _vm = {m.node_id: m for m in
           db.query(_VM).filter(_VM.view_id == view.id, _VM.node_kind == "SUBSTATION").all()}

    def _book_band(sid):
        m = _vm.get(sid)
        if not m:
            return None
        return m.tier_seed if m.tier_seed else m.display_order

    def _row_tier(sid):
        """Tier row for layout: the computed Tier if any, else the book band."""
        t = tier.get(("SUBSTATION", sid))
        return t if t is not None else _book_band(sid)

    # ---- which GIs get a busbar row: core (not bay-only) with either a
    #      computed Tier OR a book band (not-yet-energised planning objects
    #      stay on the diagram, drawn black, just not Tier-counted).
    drawn_ids = [sid for sid in core_ids
                 if sid not in bay_gi_ids and _row_tier(sid) is not None]

    # count attachments -> busbar width. Every distinct thing that touches the
    # busbar takes one slot: incoming feed, each outgoing circuit, each bay,
    # own load transformer, own capacitor, each IBT chain.
    att: dict[int, int] = defaultdict(lambda: 2)
    for sid in drawn_ids:
        s = subs[sid]
        n = (1 if s.has_transformer and sid not in gitet_feeds else 0) + (1 if s.has_shunt_capacitor else 0)
        n += len(bays_by_feeder.get(sid, []))
        n += sum(1 for spr, fd in spur.items() if fd == sid and spr not in bay_gi_ids)
        n += sum(1 for c in line_edges if sid in (c.from_substation_id, c.to_substation_id))
        n += sum(1 for (hv, lv) in gitet_feeds.items() if lv == sid)
        att[sid] = max(n, 2)

    def bus_half(sid: int) -> float:
        return max(BUS_MIN_HALF, att[sid] * BAY_SLOT / 2)

    # ---- rows keyed by fractional Tier --------------------------------
    # a GITET whose IBT chain feeds a LIVE bus sits just above that bus. A
    # GITET that is only planning info (NCKUPA, black bus) keeps its own book
    # band -- it is not really feeding anything yet.
    row_of: dict[int, float] = {}
    for sid in drawn_ids:
        if sid in gitet_feeds and _is_live(subs[sid].status) and _is_live(subs[gitet_feeds[sid]].status):
            ft = _row_tier(gitet_feeds[sid])
            row_of[sid] = (ft - 0.78) if ft else 0.35
        else:
            row_of[sid] = float(_row_tier(sid))
    gen_row: dict[int, float] = {}
    for g in gens.values():
        if not g.outlet_substation_id:
            continue  # tap-circuit generator: drawn on the circuit, not in a row
        ft = tier.get(("SUBSTATION", g.outlet_substation_id))
        gen_row[g.id] = (ft - 0.42) if ft else 0.45

    rows: dict[float, list[int]] = defaultdict(list)
    for sid, rk in row_of.items():
        rows[rk].append(sid)

    # parent (the node to sit above/below) for x-nudging. For a normal edge the
    # parent is the higher-Tier (upstream) end; for a cross-tier feed that runs
    # against the Tier flow (child Tier < feeder Tier) the child is nudged
    # toward its FEEDER instead, so e.g. Cikupa lands above Curug, not far away.
    # a single-phi edge is a weak link for layout -- don't derive parenthood
    # from it; a GI reachable only through single-phi edges is instead attached
    # next to a loop sibling that has a real feeder (Pasar Kemis <- Pasar Kemis
    # Baru).
    sp_nb: dict[int, set[int]] = defaultdict(set)
    all_nb: dict[int, set[int]] = defaultdict(set)
    for c in line_edges:
        all_nb[c.from_substation_id].add(c.to_substation_id)
        all_nb[c.to_substation_id].add(c.from_substation_id)
        if c.single_phi:
            sp_nb[c.from_substation_id].add(c.to_substation_id)
            sp_nb[c.to_substation_id].add(c.from_substation_id)

    parent: dict[int, int] = {}
    for c in line_edges:
        if c.single_phi:
            continue
        a, b = c.from_substation_id, c.to_substation_id
        ta, tb = tier.get(("SUBSTATION", a)), tier.get(("SUBSTATION", b))
        if ta is None or tb is None:
            continue
        if ta < tb:
            parent.setdefault(b, a)
        elif tb < ta:
            parent.setdefault(a, b)
            parent[b] = a
    for hv, lv in gitet_feeds.items():
        parent[hv] = lv

    for sid, nb in sp_nb.items():
        if sid in row_of and sid not in parent and nb == all_nb.get(sid):
            for sib in sorted(nb, key=lambda x: (x not in parent, x)):
                if sib in parent:
                    parent[sid] = sib
                    break

    # ---- tree layout: place each subtree as a contiguous block -----------
    pos: dict[int, tuple[float, float]] = {}

    def lane_w(sid):
        return bus_half(sid) * 2 + GUTTER

    # normalise the parent map: a node's parent must be strictly upstream
    # (lower row) OR a same-row loop sibling, so the graph stays a DAG.
    clean_parent: dict[int, int] = {}
    for cid, pid in parent.items():
        if cid not in row_of or pid not in row_of:
            continue
        if row_of[pid] < row_of[cid]:
            clean_parent[cid] = pid
        elif row_of[pid] == row_of[cid] and pid in clean_parent:
            # same-row sibling attach (loop members); safe only if pid already
            # has a real upstream parent
            clean_parent[cid] = pid
    # second pass: pick up same-row attaches whose pid was cleaned after them
    for cid, pid in parent.items():
        if (cid in row_of and pid in row_of and cid not in clean_parent
                and row_of[pid] == row_of[cid] and pid in clean_parent):
            clean_parent[cid] = pid
    children: dict[int, list[int]] = defaultdict(list)
    for cid, pid in clean_parent.items():
        children[pid].append(cid)
    roots = sorted((s for s in row_of if s not in clean_parent),
                   key=lambda s: (row_of[s], subs[s].name))

    cursor = [MARGIN_X + EDGE_MARGIN]
    placed: set[int] = set()

    def layout(sid: int) -> float:
        if sid in placed:
            return pos.get(sid, (cursor[0],))[0]
        placed.add(sid)
        pos[sid] = (cursor[0], MARGIN_Y + row_of[sid] * ROW_H)   # placeholder
        kids = sorted(children.get(sid, []), key=lambda k: (row_of[k], subs[k].name))
        if not kids:
            x = cursor[0] + lane_w(sid) / 2
            cursor[0] += lane_w(sid)
        else:
            kid_xs = [layout(k) for k in kids]
            x = sum(kid_xs) / len(kid_xs)
        pos[sid] = (x, MARGIN_Y + row_of[sid] * ROW_H)
        return x

    for r in roots:
        layout(r)
    for s in list(row_of):
        if s not in placed:
            layout(s)

    content_w = cursor[0] - (MARGIN_X + EDGE_MARGIN)
    W = MARGIN_X * 2 + EDGE_MARGIN * 2 + max(content_w, lane_w(roots[0]) if roots else 200)

    # ---- barycenter layer-sweep: pull every node toward the average x of its
    #      graph neighbours (parents, children, same-tier links), then push
    #      apart to clear overlap. This is what stops two subtrees whose only
    #      link is a same-tier tie (Balaraja <-> Sindang Jaya) from landing at
    #      opposite ends of the diagram.
    neighbours: dict[int, set[int]] = defaultdict(set)
    for c in line_edges:
        a, b = c.from_substation_id, c.to_substation_id
        if a in row_of and b in row_of:
            neighbours[a].add(b)
            neighbours[b].add(a)
    for hv, lv in gitet_feeds.items():
        if hv in row_of and lv in row_of:
            neighbours[hv].add(lv)
            neighbours[lv].add(hv)

    def _min_gap(a, b):
        return bus_half(a) + bus_half(b) + GUTTER * 0.9

    def _spread_row(order):
        for i in range(1, len(order)):
            prev, cur = order[i - 1], order[i]
            g = _min_gap(prev, cur)
            if pos[cur][0] - pos[prev][0] < g:
                pos[cur] = (pos[prev][0] + g, pos[cur][1])

    for _ in range(30):
        for rk in sorted(rows):
            order = sorted(rows[rk], key=lambda s: pos[s][0])
            for s in order:
                nb = [n for n in neighbours.get(s, ()) if n in pos]
                if nb:
                    want = sum(pos[n][0] for n in nb) / len(nb)
                    pos[s] = (0.55 * want + 0.45 * pos[s][0], pos[s][1])
            order = sorted(rows[rk], key=lambda s: pos[s][0])
            _spread_row(order)
            for i in range(len(order) - 2, -1, -1):
                nxt, cur = order[i + 1], order[i]
                g = _min_gap(cur, nxt)
                if pos[nxt][0] - pos[cur][0] < g:
                    pos[cur] = (pos[nxt][0] - g, pos[cur][1])

    # a degree-1 node whose only neighbour is on the SAME row (Jatake Baru <-
    # Jatake) belongs right next to it, not wherever the DFS cursor left it.
    for sid in list(row_of):
        nb = [n for n in neighbours.get(sid, ()) if n in pos]
        if len(nb) == 1 and row_of[nb[0]] == row_of[sid]:
            anchor = nb[0]
            g = _min_gap(anchor, sid)
            side = 1 if pos[sid][0] >= pos[anchor][0] else -1
            pos[sid] = (pos[anchor][0] + side * g, pos[sid][1])

    # authoritative final de-overlap: one left-to-right pass per row, no
    # barycenter tug afterwards, so nothing is left touching.
    for rk in sorted(rows):
        _spread_row(sorted(rows[rk], key=lambda s: pos[s][0]))

    gen_pos: dict[int, tuple[float, float]] = {}
    for gid, rk in gen_row.items():
        outlet = pos.get(gens[gid].outlet_substation_id)
        gx = outlet[0] if outlet else W / 2
        gen_pos[gid] = (gx, MARGIN_Y + rk * ROW_H)

    # ---- manual overrides: a saved (x, y) wins over auto-layout ----------
    # The auto-layout below is only a seed. Anything a person dragged in the
    # viewer is persisted per view in DiagramNodePosition and applied here,
    # so the diagram the engine emits is the one the user last arranged.
    saved = {
        (p.node_kind, p.node_id): (p.x, p.y)
        for p in db.query(DiagramNodePosition).filter(DiagramNodePosition.view_id == view.id).all()
    }
    for (kind, nid), (sx, sy) in saved.items():
        if kind == "SUBSTATION" and nid in pos:
            pos[nid] = (sx, sy)
        elif kind == "GENERATING_UNIT" and nid in gen_pos:
            gen_pos[nid] = (sx, sy)

    # ---- single-phi triangle: keep the three members as a tight cluster.
    #      In the book the Pasar Kemis / Pasar Kemis Baru / Gajah Tunggal loop
    #      is drawn compact -- the two upper buses side by side, the lower one
    #      centred just below them. Snap the lower member under the pair.
    _sp_adj0: dict[int, set[int]] = defaultdict(set)
    for c in line_edges:
        if c.single_phi:
            _sp_adj0[c.from_substation_id].add(c.to_substation_id)
            _sp_adj0[c.to_substation_id].add(c.from_substation_id)
    _tri = {n for n, nb in _sp_adj0.items() if len(nb) >= 2 and n in pos}
    if 2 <= len(_tri) <= 4:
        by_row: dict[float, list[int]] = defaultdict(list)
        for n in _tri:
            by_row[row_of[n]].append(n)
        if len(by_row) >= 2:
            top_rk = min(by_row)
            top = by_row[top_rk]
            cx_top = sum(pos[n][0] for n in top) / len(top)
            for rk, members in by_row.items():
                if rk == top_rk:
                    continue
                for j, n in enumerate(sorted(members, key=lambda m: pos[m][0])):
                    pos[n] = (cx_top + (j - (len(members) - 1) / 2) * 90, pos[n][1])

    # a GITET busbar sits directly above the LV bus it feeds (its IBT chains
    # rise straight into that bus); the DFS cursor placed it as a loose root.
    # Skip any GITET the user has explicitly placed.
    for hv, lv in gitet_feeds.items():
        if hv in pos and lv in pos and ("SUBSTATION", hv) not in saved:
            pos[hv] = (pos[lv][0], pos[hv][1])

    # ---- normalise the frame ------------------------------------------
    # The auto-layout puts nodes wherever the DFS cursor landed; that leaves a
    # dead band on the left and an over-wide canvas on the right. Translate the
    # whole drawing so its true left edge (leftmost busbar end, or a bay-panjang
    # routing channel) sits at a fixed margin, then size W/H to the real extent.
    def _left_edge(sid):
        return pos[sid][0] - bus_half(sid)

    def _right_edge(sid):
        return pos[sid][0] + bus_half(sid)

    if pos:
        left = min([_left_edge(sid) for sid in pos] + [p[0] - 20 for p in gen_pos.values()])
        # Once a person has arranged this view, don't translate their layout --
        # only clamp so nothing runs off the left edge. Pure auto-layout is
        # snapped to the margin to kill the dead gutter.
        target_left = MARGIN_X + EDGE_MARGIN
        shift = (target_left - left) if not saved else max(0.0, target_left - left)
        if abs(shift) > 0.5:
            pos = {sid: (x + shift, y) for sid, (x, y) in pos.items()}
            gen_pos = {gid: (x + shift, y) for gid, (x, y) in gen_pos.items()}
        right = max([_right_edge(sid) for sid in pos] + [p[0] + 20 for p in gen_pos.values()])
        W = right + MARGIN_X + EDGE_MARGIN

    all_y = [p[1] for p in pos.values()] + [p[1] for p in gen_pos.values()]
    max_rk = max(list(rows) + list(gen_row.values()) + [1])
    H = MARGIN_Y * 2 + int(max_rk * ROW_H) + 170
    if all_y:
        H = max(H, max(all_y) + MARGIN_Y + 170)

    # ---- mapping-audit list ------------------------------------------
    # GUARANTEE: nothing vanishes silently. This view draws ONE book page. The
    # canonical DB still holds every relation of the subsystem; a relation that
    # belongs to the OTHER page is listed here as "tersimpan, tergambar di
    # halaman <lain>" -- NOT dropped, NOT represented elsewhere. Removing it
    # would change the subsystem.
    drawn_sub_ids = set(drawn_ids)
    _ibt_drawn = {c.id for links in ibt_links_by_pair.values() for c in links}
    drawn_circ_ids = {c.id for c in line_edges} | _ibt_drawn
    drawn_bay_ids = {b.id for b in bay_rows if b.feeder_substation_id in pos}
    _pg = {"K": "sisi Balaraja (hal.70)", "B": "sisi Kembangan (hal.69)"}.get(view.drawing_side or "", "halaman lain")
    _pg_of = {"K": "sisi Kembangan (hal.69)", "B": "sisi Balaraja (hal.70)"}

    audit: list[tuple[str, str, str, str]] = []   # (kind, code, label, reason)
    for sid, s in subs.items():
        if sid in drawn_sub_ids or sid in bay_gi_ids or sid in spur:
            continue
        t = tier.get(("SUBSTATION", sid))
        if not _is_live(s.status):
            reason = f"status {s.status} -- info perencanaan, tidak dihitung Tier"
        elif t is None:
            reason = f"relasi GI ini tersimpan di DB, tergambar di {_pg}"
        else:
            reason = "tidak tergambar (cek layout)"
        audit.append(("GI/BUS", s.code, s.name, reason))

    _all_sub_ids = set(subs)
    for c in db.query(Circuit).filter(
        Circuit.from_substation_id.in_(_all_sub_ids),
        Circuit.to_substation_id.in_(_all_sub_ids),
        Circuit.active.is_(True),
    ).all():
        if c.id in drawn_circ_ids:
            continue
        if (c.subsystem_id is not None and view.subsystem_id is not None
                and c.subsystem_id != view.subsystem_id):
            continue   # belongs to another subsystem
        other_page = bool(view.drawing_side and c.drawing_side
                          and c.drawing_side != view.drawing_side)
        # a GI drawn as a stub -- a Bay row, or a degree-1 spur -- carries its
        # single feeding circuit as that stub.
        stub_gis = bay_gi_ids | set(spur)
        a_stub = c.from_substation_id in stub_gis
        b_stub = c.to_substation_id in stub_gis
        if (a_stub ^ b_stub) and _is_live(c.status) and not other_page:
            feeder = c.to_substation_id if a_stub else c.from_substation_id
            stub_gi = c.from_substation_id if a_stub else c.to_substation_id
            drawn_as_stub = feeder in pos and (
                any(bb.feeder_substation_id == feeder for bb in bay_rows)
                or spur.get(stub_gi) == feeder
            )
            if drawn_as_stub:
                continue
        fr, to = subs.get(c.from_substation_id), subs.get(c.to_substation_id)
        nm = c.name or (f"{fr.code}-{to.code}" if fr and to else c.code)
        if other_page:
            reason = (f"ruas ini tersimpan di DB, tergambar di "
                      f"{_pg_of.get(c.drawing_side, 'halaman ' + str(c.drawing_side))}")
        elif not _is_live(c.status):
            reason = f"status {c.status} -- info perencanaan, tidak dihitung Tier"
        elif a_stub and b_stub:
            reason = "ruas antara dua GI yang sama-sama digambar sebagai bay/spur"
        else:
            reason = "endpoint tidak tergambar sebagai busbar"
        audit.append(("IBT" if c.circuit_type == "IBT_LINK" else "PENGHANTAR", c.code, nm, reason))

    for b in bay_rows:
        if b.id in drawn_bay_ids:
            continue
        gi = subs.get(b.substation_id)
        fd = subs.get(b.feeder_substation_id) if b.feeder_substation_id else None
        code = gi.code if gi else str(b.substation_id)
        lbl = f"{gi.name if gi else b.substation_id}" + (f" @ {fd.name}" if fd else "")
        audit.append(("BAY", code, lbl,
                      "busbar feeder tidak tergambar" if b.feeder_substation_id
                      else "feeder tidak diketahui"))

    audit.sort()
    audit_h = (34 + 16 * len(audit)) if audit else 0
    H += audit_h

    # ---- port allocation: every attachment on a busbar gets its own x -----
    # Collect attachment keys per busbar, ordered so incoming feed is left,
    # own load in the middle, outgoing circuits to the right, bays after that.
    PORT: dict[tuple[int, str], float] = {}   # (sub_id, key) -> x

    def _order_key(sid, kind, other_x):
        # left -> right along the busbar: incoming feed & IBT, then own load /
        # capacitor, then outgoing circuits, then bays.
        base = {"in": 0, "ibt": 1, "gen": 1, "load": 3, "cap": 4, "out": 6, "bay": 8}[kind]
        return (base, other_x if other_x is not None else pos[sid][0])

    bus_attach: dict[int, list] = defaultdict(list)
    for c in line_edges:
        a, b = c.from_substation_id, c.to_substation_id
        for sid, oth in ((a, b), (b, a)):
            if sid not in pos:
                continue
            t_self = tier.get(("SUBSTATION", sid))
            t_oth = tier.get(("SUBSTATION", oth))
            kind = "in" if (t_oth is not None and t_self is not None and t_oth < t_self) else "out"
            bus_attach[sid].append((f"c{c.id}", kind, pos.get(oth, (pos[sid][0],))[0]))
    for hv, lv in gitet_feeds.items():
        if lv in pos:
            bus_attach[lv].append(("ibt", "ibt", pos[hv][0]))
    for g in gens.values():
        if g.outlet_substation_id in pos:
            bus_attach[g.outlet_substation_id].append((f"gen{g.id}", "gen", None))
    for sid in drawn_ids:
        s = subs[sid]
        if s.has_transformer and sid not in gitet_feeds:
            bus_attach[sid].append(("load", "load", None))
        if s.has_shunt_capacitor:
            bus_attach[sid].append(("cap", "cap", None))
    for feeder_id, blist in bays_by_feeder.items():
        if feeder_id in pos:
            for b in blist:
                bus_attach[feeder_id].append((f"bay{b.id}", "bay", None))
    for spur_id, feeder_id in spur.items():
        if spur_id not in bay_gi_ids and feeder_id in pos:
            bus_attach[feeder_id].append((f"spur{spur_id}", "bay", None))

    top_port_x: dict[int, list[float]] = defaultdict(list)   # x of each top attachment
    for sid, items in bus_attach.items():
        cx, cy = pos[sid]
        bh = bus_half(sid)
        items = sorted(items, key=lambda it: _order_key(sid, it[1], it[2]))
        n = len(items)
        usable = max(2 * bh - 20, 2 * bh * 0.7)
        for i, (key, kind, _) in enumerate(items):
            px = cx - usable / 2 + (i + 0.5) * usable / max(n, 1)
            PORT[(sid, key)] = px
            if kind in ("in", "ibt", "gen"):
                top_port_x[sid].append(px)

    def port(sid, key, fallback_x=None):
        return PORT.get((sid, key), fallback_x if fallback_x is not None else pos[sid][0])

    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" '
        f'font-family="Arial, Helvetica, sans-serif">',
        f'<rect width="{W:.0f}" height="{H}" fill="#ffffff"/>',
        f'<text x="18" y="26" font-size="14" font-weight="700" fill="#0f274a">{esc(view.name)}</text>',
    ]

    # ---- Tier band overlay -----------------------------------------
    p.append('<g id="overlay-tier">')
    bands = sorted({int(round(rk)) for rk in rows if abs(rk - round(rk)) < 1e-6})
    for t in bands:
        y = MARGIN_Y + t * ROW_H
        p.append(f'<line x1="16" y1="{y}" x2="{W - 16:.0f}" y2="{y}" stroke="#d7e0ec" '
                 f'stroke-width="1" stroke-dasharray="2 7"/>')
        p.append(f'<text x="20" y="{y - 8}" font-size="11" fill="#8592a6" font-weight="700">TIER-{t}</text>')
    p.append('</g>')

    # ---- circuits (each end enters its busbar at its own port x) ------
    #      2 sirkit  -> two parallel dashed lines
    #      1 sirkit / single phi -> one dashed line (single phi = thinner + note)
    left_ch = MARGIN_X + EDGE_MARGIN * 0.45
    right_ch = W - MARGIN_X - EDGE_MARGIN * 0.45
    CCT_OFF = 5     # half-separation between the two circuits of a 2-sirkit line

    # detect single-phi loops: a set of >=3 single-phi edges forming a cycle
    # (Pasar Kemis - Pasar Kemis Baru - Gajah Tunggal). The edge that closes
    # the loop (an upward single-phi edge inside the group) is routed as one
    # clean run just outside the group, not through the generic edge channel.
    sp_adj: dict[int, set[int]] = defaultdict(set)
    for c in line_edges:
        if c.single_phi:
            sp_adj[c.from_substation_id].add(c.to_substation_id)
            sp_adj[c.to_substation_id].add(c.from_substation_id)
    loop_members: set[int] = {n for n, nb in sp_adj.items() if len(nb) >= 2}
    loop_close_ids: set[int] = set()
    for c in line_edges:
        if (c.single_phi and c.from_substation_id in loop_members
                and c.to_substation_id in loop_members):
            ta_ = tier.get(("SUBSTATION", c.from_substation_id))
            tb_ = tier.get(("SUBSTATION", c.to_substation_id))
            if ta_ is not None and tb_ is not None and ta_ != tb_:
                loop_close_ids.add(c.id)   # the up/down edge closing the triangle
    # is the loop small & clustered enough to route locally? (Pasar Kemis
    # triangle after the cluster snap). If so, drop the far-right channel.
    loop_local = False
    if 2 <= len(loop_members) <= 4 and all(m in pos for m in loop_members):
        span = max(pos[m][0] for m in loop_members) - min(pos[m][0] for m in loop_members)
        loop_local = span < 320
    loop_x = None
    if loop_members and not loop_local:
        loop_x = max(pos[m][0] + bus_half(m) for m in loop_members if m in pos) + 34

    # Each edge is one clean Z: straight down from the source port, ONE
    # horizontal run at a height chosen NEAR the target (not a shared channel
    # -- that is what made parallel feeds overlap), straight down into the
    # target port. The turn height is staggered a little per circuit so two
    # edges between the same rows do not share one horizontal line.
    _turn_seq: dict[int, int] = {}
    for _i, _c in enumerate(sorted(line_edges, key=lambda z: z.id)):
        _turn_seq[_c.id] = _i

    def turn_y(af, at, cid):
        """Horizontal-run height for a normal downward edge: in the gap between
        the two rows, biased toward the target, stepped per circuit so siblings
        don't share a line. Kept clear of the target's label band (y-26..y).
        """
        ya, yb = pos[af][1], pos[at][1]
        lo, hi = min(ya, yb), max(ya, yb)
        span = hi - lo
        # 55%..80% of the way down, stepped
        frac = 0.55 + (_turn_seq.get(cid, 0) % 6) * 0.045
        y = lo + span * frac
        return min(y, hi - 40)   # never inside the target's label band

    # ---- phase 1: compute every circuit's ortho route as (x1,y1,yb,x2,y3) ---
    #      one route per sirkit; collect them so phase 2 can add hop arcs where
    #      a horizontal run passes over another circuit's vertical leg.
    routes: list[dict] = []   # {cid, code, ctype, status, stroke, dash, w, title,
                              #  segs:[(x1,y1,yb,x2,y3)], cbs:[(x,y,n)]}
    for c in line_edges:
        af, at = c.from_substation_id, c.to_substation_id
        if af not in pos or at not in pos:
            continue
        stroke, dash = _circuit_style(c)
        w = 1.3 if c.single_phi else 2.2
        # routing uses the row a GI sits on -- computed Tier, else book band --
        # so a not-yet-energised line still routes as a clean Z, not a diagonal
        ta = _row_tier(af)
        tb = _row_tier(at)
        key = f"c{c.id}"
        fx0, fy0 = port(af, key), pos[af][1]
        tx0, ty0 = port(at, key), pos[at][1]
        title = (f'<title>{esc(c.name)} - {esc(c.circuit_type)}, {esc(c.status)}'
                 f'{", single phi" if c.single_phi else ""}'
                 f'{", " + str(c.circuit_count) + " sirkit" if c.circuit_count else ""} '
                 f'(conf {c.confidence})</title>')
        n_cct = 1 if (c.single_phi or (c.circuit_count or 1) < 2) else 2
        offs = [0.0] if n_cct == 1 else [-CCT_OFF, CCT_OFF]

        same_tier = ta is not None and tb is not None and ta == tb
        # cross-tier feed that runs AGAINST the downward flow (feeder below the
        # GI it feeds -- Curug T5 -> Cikupa T4). Everything else that is not
        # same-tier is a normal downward edge, however many Tier bands it spans.
        against_flow = ta is not None and tb is not None and ta > tb

        entry = {"cid": c.id, "code": c.code, "ctype": c.circuit_type,
                 "status": c.status, "stroke": stroke, "dash": dash, "w": w,
                 "title": title, "segs": [], "cbs": []}

        if c.id in loop_close_ids and loop_x is not None:
            (ex, ey), (sx2, sy2) = ((fx0, fy0), (tx0, ty0)) if fy0 > ty0 else ((tx0, ty0), (fx0, fy0))
            entry["segs"].append((ex, ey + CB_GAP, ey + 24, loop_x, sy2 - CB_GAP))
            entry["segs"].append((loop_x, sy2 - CB_GAP, sy2 - CB_GAP, sx2, sy2 - CB_GAP))
            entry["cbs"].append((fx0, fy0 + (1 if fy0 > ty0 else -1) * CB_GAP, n_cct))
            entry["cbs"].append((tx0, ty0 + (1 if ty0 > fy0 else -1) * CB_GAP, n_cct))
            routes.append(entry)
            continue

        adjacent_tie = (same_tier and c.single_phi and abs(fx0 - tx0) < 300)
        if adjacent_tie:
            yb = fy0 + 24
            entry["segs"].append((fx0, fy0 + CB_GAP, yb, tx0, ty0 + CB_GAP))
            entry["cbs"].append((fx0, fy0 + CB_GAP, 1))
            entry["cbs"].append((tx0, ty0 + CB_GAP, 1))
            routes.append(entry)
            continue

        # CB direction: the line always LEAVES the source's bottom and ENTERS
        # the target from ABOVE, except a same-tier tie (both bottom) and an
        # against-flow feed (leaves feeder bottom, enters upper bus from below).
        if same_tier:
            fdir = tdir = -1
        elif against_flow:
            # af is deeper Tier here (ta > tb) -> af is the upper bus, at the
            # feeder below it. The feeder's line leaves its TOP; the upper bus
            # takes it from BELOW.
            fdir, tdir = 1, 1
        else:
            fdir, tdir = 1, -1

        # per-sirkit separation: shift BOTH legs in x by `off`, and nudge the
        # turn height by a hair so the two horizontal runs never merge
        for k, off in enumerate(offs):
            fx, tx = fx0 + off, tx0 + off
            hy_nudge = -3.0 if k == 0 else 3.0  # 2-cct: one run just above the other
            if same_tier:
                # inverted bracket ABOVE both buses
                yb = min(fy0, ty0) - 26 - abs(off) + hy_nudge
                entry["segs"].append((fx, fy0 - CB_GAP, yb, tx, ty0 - CB_GAP))
            elif against_flow:
                # feeder (lower Tier row) feeds a bus one or more Tiers ABOVE it
                # (Curug T5 -> Cikupa T4). Leave the feeder's TOP, rise a little,
                # run across just under the upper bus, rise into it from below.
                (ux, uy) = (fx, fy0)          # upper bus (deeper Tier value)
                (bx, by) = (tx, ty0)          # feeder, physically below
                if abs(bx - ux) < 90:
                    # roughly aligned: straight up through the midpoint
                    yb = (by + uy) / 2 + hy_nudge
                else:
                    yb = uy + 30 + (_turn_seq.get(c.id, 0) % 4) * 12 + hy_nudge
                    yb = min(yb, by - 20)
                entry["segs"].append((bx, by - CB_GAP, yb, ux, uy + CB_GAP))
            else:
                # normal downward: down from source, across in the gap, down in
                (ux, uy), (lx, ly) = ((fx, fy0), (tx, ty0)) if fy0 <= ty0 else ((tx, ty0), (fx, fy0))
                yb = turn_y(af if fy0 <= ty0 else at, at if fy0 <= ty0 else af, c.id) + hy_nudge
                yb = min(max(yb, uy + 20), ly - 40)
                entry["segs"].append((ux, uy + CB_GAP, yb, lx, ly - CB_GAP))
        entry["cbs"].append((fx0, fy0 + fdir * CB_GAP, n_cct))
        entry["cbs"].append((tx0, ty0 + tdir * CB_GAP, n_cct))
        routes.append(entry)

    # ---- phase 2: emit each route, hopping its horizontal run over the
    #      vertical legs of OTHER circuits it would otherwise cross ------------
    all_verts: list[tuple[float, float, float, int]] = []   # (x, y_lo, y_hi, cid)
    for r in routes:
        for (x1, y1, yb, x2, y3) in r["segs"]:
            all_verts.append((x1, min(y1, yb), max(y1, yb), r["cid"]))
            all_verts.append((x2, min(yb, y3), max(yb, y3), r["cid"]))

    p.append('<g id="circuits">')
    for r in routes:
        p.append(f'<g data-circuit-id="{r["cid"]}" data-circuit-code="{esc(r["code"])}" '
                 f'data-circuit-type="{esc(r["ctype"])}" data-status="{esc(r["status"])}">')
        for i, (x1, y1, yb, x2, y3) in enumerate(r["segs"]):
            cross_xs = [vx for (vx, vlo, vhi, vcid) in all_verts
                        if vcid != r["cid"] and vlo < yb - 1 < vhi
                        and min(x1, x2) + 6 < vx < max(x1, x2) - 6]
            d = _emit_hopped(x1, y1, yb, x2, y3, cross_xs)
            tt = r["title"] if i == 0 else ""
            p.append(f'<path d="{d}" fill="none" stroke="{r["stroke"]}" '
                     f'stroke-width="{r["w"]}" stroke-dasharray="{r["dash"]}">{tt}</path>')
        for (cx, cy, cn) in r["cbs"]:
            p.append(_cbs(cx, cy, r["stroke"], cn))
        p.append('</g>')
    p.append('</g>')

    # ---- IBT chains (each chain at the LV busbar's 'ibt' port) --------
    # We draw only the IBTs that belong to THIS view (New Balaraja shows IBT 3,4
    # in SS_BLL, IBT 1,2 in SS_LBK). Each chain is labelled with its unit no so
    # a reader can tell which transformer it is.
    _ibt_unit: dict[int, str] = {}
    _ibt_tx_ids = {c.transformer_id for links in ibt_links_by_pair.values()
                   for c in links if c.transformer_id}
    if _ibt_tx_ids:
        for t in db.query(Transformer).filter(Transformer.id.in_(_ibt_tx_ids)).all():
            _ibt_unit[t.id] = t.unit_no or ""

    def _ibt_label(c) -> str:
        u = _ibt_unit.get(c.transformer_id, "")
        if u:
            return f"IBT {u}"
        # fall back to a trailing number in the circuit name / code
        m = re.search(r"(\d+)", (c.name or c.code).split("-")[0])
        return f"IBT {m.group(1)}" if m else "IBT"

    p.append('<g id="ibt-links">')
    for (hv, lv), links in ibt_links_by_pair.items():
        hp, lp = pos.get(hv), pos.get(lv)
        if not hp or not lp:
            continue
        hv_col, lv_col = _vcol(subs[hv].voltage_kv), _vcol(subs[lv].voltage_kv)
        base = port(lv, "ibt")
        n = len(links)
        slinks = sorted(links, key=lambda z: (_ibt_unit.get(z.transformer_id, ""), z.code))
        IBT_DX = 46   # room for the inline symbol + a unit label per chain
        for i, c in enumerate(slinks):
            cx = base + (i - (n - 1) / 2) * IBT_DX
            hy, ly = hp[1], lp[1]
            mid = (hy + ly) / 2
            da = f' stroke-dasharray="{STATUS_DASH.get(c.status, "none")}"' if c.status != "ENERGIZED" else ""
            p.append(f'<g data-circuit-id="{c.id}" data-circuit-code="{esc(c.code)}" '
                     f'data-circuit-type="IBT_LINK" data-status="{esc(c.status)}">')
            p.append(f'<path d="M{cx:.1f},{hy:.1f} V{ly:.1f}" fill="none" stroke="#8a6a3a" '
                     f'stroke-width="1.6"{da}><title>{esc(c.name)} - {esc(c.status)}</title></path>')
            p.append(_cb(cx, hy + CB_GAP, hv_col))
            p.append(_sym_ibt_inline(cx, mid - 4))
            p.append(_cb(cx, ly - CB_GAP, lv_col))
            # unit label below the inline symbol (clear of both the circles and
            # the neighbouring chain)
            p.append(f'<text x="{cx:.1f}" y="{mid + 20:.1f}" font-size="8.5" '
                     f'fill="#8a6a3a" font-weight="700" text-anchor="middle">{esc(_ibt_label(c))}</text>')
            p.append('</g>')
    p.append('</g>')

    # ---- generators --------------------------------------------
    p.append('<g id="generators">')
    for gid, g in gens.items():
        standby = (g.status or "").upper() in ("STANDBY", "OFF")
        col = "#7c9a6a" if standby else "#0a8a3a"
        if g.tap_circuit_id:
            # a small plant tapping a circuit -> a NODE (point) + label, placed
            # ~1/3 along the circuit toward its downstream end (like the book:
            # the tap "cuts into" the existing line near one substation).
            c = next((e for e in line_edges if e.id == g.tap_circuit_id), None)
            a = pos.get(c.from_substation_id) if c else None
            b = pos.get(c.to_substation_id) if c else None
            if not a or not b:
                continue
            fx = port(c.from_substation_id, f"c{c.id}")
            tx = port(c.to_substation_id, f"c{c.id}")
            # a point ON the circuit line, ~60% toward the downstream end so it
            # clears the upstream bus's own bays, with a short dash out to the
            # node label
            f = 0.60
            ly_ = a[1] + (b[1] - a[1]) * f
            lx_ = fx + (tx - fx) * f
            nx = lx_ + 34                       # node sits a bit to the right
            p.append(f'<g><title>{esc(g.name)} ({esc(g.unit_type)}) - {esc(g.status)} - '
                     f'tap ruas {esc(c.name)}</title>')
            p.append(f'<circle cx="{lx_:.1f}" cy="{ly_:.1f}" r="2.5" fill="{col}"/>')
            p.append(f'<path d="M{lx_:.1f},{ly_:.1f} h34" stroke="{col}" stroke-width="1.4" '
                     f'stroke-dasharray="4 3"/>')
            p.append(f'<circle cx="{nx:.1f}" cy="{ly_:.1f}" r="4" fill="#ffffff" '
                     f'stroke="{col}" stroke-width="2"/>')
            p.append(f'<text x="{nx + 8:.1f}" y="{ly_ + 3:.1f}" font-size="9" '
                     f'fill="{col}">{esc(g.name)}{" (standby)" if standby else ""}</text>')
            p.append('</g>')
            continue
        outlet = pos.get(g.outlet_substation_id)
        gx = port(g.outlet_substation_id, f"gen{g.id}", gen_pos[gid][0]) if outlet else gen_pos[gid][0]
        gy = gen_pos[gid][1]
        _gp = "1" if ("GENERATING_UNIT", gid) in saved else "0"
        p.append(f'<g class="sld-node" data-node-kind="GENERATING_UNIT" data-node-id="{gid}" '
                 f'data-code="{esc(g.code)}" data-x="{gx:.1f}" data-y="{gy:.1f}" data-pinned="{_gp}">')
        p.append(_sym_generator(gx, gy - 30, col))
        p.append(f'<text x="{gx:.1f}" y="{gy - 42:.1f}" font-size="10" text-anchor="middle" '
                 f'fill="{col}">{esc(g.name)}</text>')
        if outlet:
            p.append(f'<path d="M{gx:.1f},{gy:.1f} V{outlet[1] - CB_GAP:.1f}" fill="none" '
                     f'stroke="{col}" stroke-width="2"/>')
            p.append(_cb(gx, outlet[1] - CB_GAP, col))
        p.append('</g>')
    p.append('</g>')

    # ---- busbars ---------------------------------------------
    p.append('<g id="busbars">')
    for sid in drawn_ids:
        s = subs[sid]
        x, y = pos[sid]
        bh = bus_half(sid)
        # a GITET busbar is centred exactly over its IBT chains (nothing else
        # attaches to it here), so it can't overrun the rest of the diagram
        if sid in gitet_feeds:
            lv = gitet_feeds[sid]
            base = port(lv, "ibt")
            n = len(ibt_links_by_pair.get((sid, lv), [1]))
            x = base
            bh = max((n - 1) * 46 / 2 + 26, 40)
        vcol = _vcol(s.voltage_kv)
        bstroke = STATUS_STROKE.get(s.status) or vcol
        bdash = STATUS_DASH.get(s.status, "none")
        da = f' stroke-dasharray="{bdash}"' if s.status not in ("ENERGIZED", "OWNED_BY_CUSTOMER") else ""
        role = roles.get(("SUBSTATION", sid), "")
        _pinned = "1" if ("SUBSTATION", sid) in saved else "0"
        p.append(f'<g class="sld-node" data-node-kind="SUBSTATION" data-node-id="{sid}" '
                 f'data-code="{esc(s.code)}" data-x="{x:.1f}" data-y="{y:.1f}" '
                 f'data-bus-half="{bh:.1f}" data-pinned="{_pinned}">'
                 f'<title>{esc(s.name)} [{esc(s.code)}] {esc(s.substation_type)} '
                 f'{esc(int(s.voltage_kv))} kV - {esc(s.status)} - role {esc(role)}'
                 f'{" - " + esc(s.busbar_note) if s.busbar_note else ""}</title>')
        # label placement: put the name where the top of the busbar is CLEAR.
        # GITET -> just above (nothing up there). Otherwise look at where the
        # incoming feeds / IBT / generator meet this bar:
        #   * left third clear  -> label off the left end
        #   * right third clear -> label off the right end
        #   * centre clear      -> centred, well above the CBs
        #   * nothing clear     -> above-left, lifted clear of everything
        is_gitet = sid in gitet_feeds
        tps = top_port_x.get(sid, [])
        left_lim, right_lim = x - bh * 0.34, x + bh * 0.34
        centre_clear = not any(left_lim <= px <= right_lim for px in tps)
        # room to the neighbouring bus on this same Tier row?
        row_order = sorted(rows[row_of[sid]], key=lambda z: pos[z][0])
        idx = row_order.index(sid)
        gap_left = (pos[sid][0] - pos[row_order[idx - 1]][0]) if idx > 0 else 9e9
        gap_right = (pos[row_order[idx + 1]][0] - pos[sid][0]) if idx < len(row_order) - 1 else 9e9
        # the label on the diagram is the SLD CODE (singkatan), like the book;
        # the full name lives in the <title> tooltip and the Excel register.
        blabel = esc(s.code)
        est_w = 7 * len(s.code) + 12          # rough label width
        left_room = gap_left - bh - bus_half(row_order[idx - 1] if idx > 0 else sid) > est_w
        right_room = gap_right - bh - bus_half(row_order[idx + 1] if idx < len(row_order) - 1 else sid) > est_w
        left_top_clear = not any(px < left_lim for px in tps)
        right_top_clear = not any(px > right_lim for px in tps)
        has_left_pin = any(risk_on.get(("TRANSFORMER", t.id)) for t in tx_by_sub.get(sid, []))

        if is_gitet:
            p.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" font-size="11" font-weight="700" '
                     f'text-anchor="middle" fill="#0f274a">{blabel}</text>')
        elif centre_clear:
            p.append(f'<text x="{x:.1f}" y="{y - 26:.1f}" font-size="11" font-weight="700" '
                     f'text-anchor="middle" fill="#0f274a">{blabel}</text>')
        elif right_room and right_top_clear:
            p.append(f'<text x="{x + bh + 6:.1f}" y="{y + 3:.1f}" font-size="11" '
                     f'font-weight="700" text-anchor="start" fill="#0f274a">{blabel}</text>')
        elif left_room and left_top_clear and not has_left_pin:
            p.append(f'<text x="{x - bh - 6:.1f}" y="{y + 3:.1f}" font-size="11" '
                     f'font-weight="700" text-anchor="end" fill="#0f274a">{blabel}</text>')
        else:
            p.append(f'<text x="{x:.1f}" y="{y - 34:.1f}" font-size="11" font-weight="700" '
                     f'text-anchor="middle" fill="#0f274a">{blabel}</text>')
        p.append(f'<line x1="{x - bh:.1f}" x2="{x + bh:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                 f'stroke="{bstroke}" stroke-width="6"{da}/>')
        if s.busbar_config in ("DOUBLE_1CB", "DOUBLE_SECTIONALIZED"):
            p.append(f'<rect x="{x - 5:.1f}" y="{y - 4:.1f}" width="10" height="8" '
                     f'fill="#ffffff" stroke="{bstroke}" stroke-width="1.6"/>')
        if s.has_transformer and sid not in gitet_feeds:
            p.append(_sym_transformer(port(sid, "load", x), y + 3, vcol))
        if s.has_shunt_capacitor:
            p.append(_sym_capacitor(port(sid, "cap", x), y + 3, vcol))
        if role in ("BOUNDARY", "EXTERNAL_CONTEXT"):
            # small tag under the left end of the bar -- never stacked on the name
            p.append(f'<text x="{x - bh:.1f}" y="{y + 15:.1f}" font-size="7.5" '
                     f'text-anchor="start" fill="#b06a00" font-weight="700">{esc(role)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- bays (stub + CB + name, no busbar; at their own port) -------
    p.append('<g id="bays">')
    stub_items: list[tuple[int, str, object, str, str]] = []
    for spur_id, feeder_id in spur.items():
        if spur_id not in bay_gi_ids and feeder_id in pos:
            stub_items.append((feeder_id, f"spur{spur_id}", subs[spur_id],
                               subs[spur_id].status, roles.get(("SUBSTATION", spur_id), "")))
    for feeder_id, blist in bays_by_feeder.items():
        if feeder_id in pos:
            for b in blist:
                stub_items.append((feeder_id, f"bay{b.id}", subs[b.substation_id],
                                   b.status, b.note or ""))
    # a bay stub is drawn in its feeding circuit's style (SKTT = red dashed,
    # SUTT = solid); it ends in a transformer symbol if the bay GI is a
    # radial load (Ulujami), otherwise a small dot. The stub IS the circuit on
    # the diagram, so carry its circuit id/code for the mapping audit.
    bay_feed_style: dict[int, tuple[str, str]] = {}
    bay_circuit: dict[tuple[int, int], object] = {}   # (feeder_id, stub_gi_id) -> Circuit
    _stub_gi_ids = bay_gi_ids | set(spur)
    for c in edges:   # not line_edges -- those exclude bay/spur-GI endpoints
        a, b = c.from_substation_id, c.to_substation_id
        for sid, oth in ((a, b), (b, a)):
            if sid in _stub_gi_ids and oth in subs:
                bay_feed_style[sid] = _circuit_style(c)
                bay_circuit[(oth, sid)] = c

    def _stub_x(it):
        fid, k = it[0], it[1]
        return port(fid, k, pos[fid][0]) if fid in pos else 0.0

    STUB_LEN = 42   # every bay stub is exactly this long -- consistent, per the book

    for feeder_id, key, gi, status, meta in sorted(stub_items, key=lambda it: (it[0], _stub_x(it))):
        fx, fy = pos[feeder_id]
        sx = port(feeder_id, key, fx)
        sy = fy + STUB_LEN
        stroke, dash = bay_feed_style.get(gi.id, ("#C00000", "7 5"))
        if status in ("NEW_NOT_ENERGIZED", "PLANNED"):
            stroke, dash = "#111111", "3 6"
        elif status == "DE_ENERGIZED":
            stroke, dash = "#9AA0A6", "none"
        da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        _bc = bay_circuit.get((feeder_id, gi.id))
        _bc_attr = (f' data-circuit-id="{_bc.id}" data-circuit-code="{esc(_bc.code)}"'
                    if _bc else "")
        p.append(f'<g class="sld-bay" data-node-kind="SUBSTATION" data-node-id="{gi.id}" '
                 f'data-code="{esc(gi.code)}"{_bc_attr}>'
                 f'<title>{esc(gi.name)} [{esc(gi.code)}] - bay di bus {esc(subs[feeder_id].name)} '
                 f'({esc(status)}){" - " + esc(meta) if meta else ""}</title>')
        p.append(f'<path d="M{sx:.1f},{fy:.1f} V{sy:.1f}" fill="none" '
                 f'stroke="{stroke}" stroke-width="1.8"{da}/>')
        p.append(_cb(sx, fy + CB_GAP, stroke))
        # A bay is ALWAYS just stub + CB + endpoint dot + code. It never gets a
        # transformer -- that is only for a GI with its own busbar. The code
        # (singkatan) is written below the dot, exactly as the book does it.
        p.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="{stroke}"/>')
        p.append(f'<text x="{sx:.1f}" y="{sy + 13:.1f}" font-size="8" '
                 f'text-anchor="middle" fill="#6b7787">{esc(gi.code)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- mapping-audit strip (list computed earlier) -----------------
    if audit:
        y0 = (MARGIN_Y + (max(bands) + 1) * ROW_H) if bands else (H - audit_h + 20)
        p.append('<g id="mapping-audit">')
        p.append(f'<text x="20" y="{y0 - 8:.1f}" font-size="11" fill="#8592a6" font-weight="700">'
                 f'Objek hasil mapping yang TIDAK masuk gambar utama '
                 f'({len(audit)}) &#8212; konfirmasi tidak ada yang terlewat:</text>')
        for i, (kind, code, label, reason) in enumerate(audit):
            yy = y0 + 10 + i * 16
            p.append(f'<g data-audit-kind="{esc(kind)}" data-audit-code="{esc(code)}">')
            p.append(f'<text x="24" y="{yy:.1f}" font-size="9" fill="#7a5c00" font-weight="700">'
                     f'{esc(kind)}</text>')
            p.append(f'<text x="110" y="{yy:.1f}" font-size="9" fill="#333">'
                     f'{esc(label)} [{esc(code)}]</text>')
            p.append(f'<text x="470" y="{yy:.1f}" font-size="9" fill="#8592a6">&#8212; {esc(reason)}</text>')
            p.append('</g>')
        p.append('</g>')

    # ---- risk overlay ---------------------------------------
    p.append('<g id="overlay-risk">')

    def _pin(cx, cy, seqs):
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#F6C000" '
                f'stroke="#B8860B" stroke-width="1.5"/>'
                f'<text x="{cx:.1f}" y="{cy + 3:.1f}" font-size="9" font-weight="700" '
                f'text-anchor="middle" fill="#5a4500">'
                f'{esc(",".join(str(q) for q in sorted(seqs)))}</text>')

    for sid in drawn_ids:
        seqs = risk_on.get(("SUBSTATION", sid))
        if seqs:
            x, y = pos[sid]
            p.append(_pin(x + bus_half(sid) + 12, y, seqs))
    for c in line_edges:
        seqs = risk_on.get(("CIRCUIT", c.id))
        a, b = pos.get(c.from_substation_id), pos.get(c.to_substation_id)
        if seqs and a and b:
            p.append(_pin((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, seqs))
    for sid, tx_list in tx_by_sub.items():
        for t in tx_list:
            seqs = risk_on.get(("TRANSFORMER", t.id))
            if seqs and sid in pos:
                x, y = pos[sid]
                p.append(_pin(x - bus_half(sid) - 12, y, seqs))
    p.append('</g>')

    p.append('</svg>')
    return "".join(p)
