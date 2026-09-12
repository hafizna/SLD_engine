"""SLD renderer -- Buku Kerawanan symbols and layered orthogonal layout.

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
  * shunt capacitor                standard symbols, explicit inventory counts

Layout: row = book Tier band. The complete graph determines row order;
busbar widths and endpoint ports determine final alignment. Route bundles
around bus/symbol obstacles, then offset their conductors at right angles.
Semicircular bridges mark crossings between unrelated circuits.
"""
from __future__ import annotations

import html
import re
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import AnalyticalView, Bay, Circuit, DiagramNodePosition, RiskRecord, Subsystem, Transformer
from app.services.sld_layout import (layered_positions, route_bundles, offset_path,
                                      path_d, WIRE_PITCH, BUS_TOP, BUS_BOTTOM)
from app.services.topology import _is_live, calculate_tier, classify_layout, get_view_graph
from app.services.sld_symbols import symbol_count, capacitor_is_off


def _view_title(db: Session, view: AnalyticalView) -> str:
    """Diagram heading: 'SS <subsystem> -- <POV>'. The view name is now just
    the point of view ('Sisi Kembangan'); the SS name gives it context. When
    the SS has only one view, the POV label adds nothing -> just the SS name."""
    ss = db.get(Subsystem, view.subsystem_id) if view.subsystem_id else None
    if not ss:
        return view.name or "SLD"
    siblings = (db.query(AnalyticalView)
                  .filter(AnalyticalView.subsystem_id == ss.id).count())
    if siblings > 1 and view.name:
        return f"SS {ss.name} — {view.name}"
    return f"SS {ss.name}"

VOLT_COLOR = {
    500: "#0047AB", 275: "#00A6D6", 150: "#C00000",
    70: "#E6B800", 66: "#E6B800", 30: "#39C96B", 20: "#E67300",
}

# busbar styling by status (colour, dash)
STATUS_STROKE = {
    "ENERGIZED": None,               # -> voltage colour
    "NEW_NOT_ENERGIZED": "#111111",  # black busbar = planned / not yet energised
    "PLANNED": "#9AA0A6",
    "DE_ENERGIZED": "#9AA0A6",
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
    """Return a P2B-compatible (stroke, dash) for a circuit.

    Colour carries the electrical voltage while dash carries the conductor
    type.  Operational status may override both, matching the busbar legend.
    """
    if c.status == "NEW_NOT_ENERGIZED":
        return STATUS_STROKE["NEW_NOT_ENERGIZED"], STATUS_DASH["NEW_NOT_ENERGIZED"]
    if c.status == "PLANNED":
        return STATUS_STROKE["PLANNED"], STATUS_DASH["PLANNED"]
    if c.status == "DE_ENERGIZED":
        return "#9AA0A6", STATUS_DASH["DE_ENERGIZED"]
    ct = (c.circuit_type or "SUTT").upper()
    if ct in ("SKTT", "SKLT"):
        return _vcol(c.voltage_kv), "7 5"   # cable = dashed, voltage still owns colour
    if ct == "IBT_LINK":
        return "#8a6a3a", "none"
    return _vcol(c.voltage_kv), "none"       # SUTT / SUTET = solid

BAY_SLOT = 46          # horizontal space per attachment (bay / circuit / trafo)
BUS_MIN_HALF = 55      # minimum busbar half-length
MARGIN_X = 150
CB = 10
CB_GAP = 12
EDGE_MARGIN = 54       # width of the outer channel a cross-tier feed routes in


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def _vcol(kv) -> str:
    return VOLT_COLOR.get(int(kv or 150), "#C00000")


def _cb(x, y, color):
    return f'<rect x="{x - CB / 2:.1f}" y="{y - CB / 2:.1f}" width="{CB}" height="{CB}" fill="{color}"/>'


def _perp_crossing(a, b, c, d):
    """Return the strict crossing and whether the first segment is vertical."""
    first_vertical = a[0] == b[0]
    if first_vertical == (c[0] == d[0]):
        return None
    v, w, h, k = (a, b, c, d) if first_vertical else (c, d, a, b)
    x, y = v[0], h[1]
    if min(v[1], w[1]) < y < max(v[1], w[1]) and min(h[0], k[0]) < x < max(h[0], k[0]):
        return x, y, first_vertical
    return None


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


def _sym_ibt_inline(x, y, hv_color="#0047AB", lv_left="#C00000", lv_right="#E0A400"):
    """IBT 500/150: top circle HV; lower pair identifies left/right LV sides."""
    r = 7.5
    return (
        f'<g fill="#ffffff" stroke-width="1.7">'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" stroke="{hv_color}"/>'
        f'<circle cx="{x - 4.5:.1f}" cy="{y + 8:.1f}" r="{r}" stroke="{lv_left}"/>'
        f'<circle cx="{x + 4.5:.1f}" cy="{y + 8:.1f}" r="{r}" stroke="{lv_right}"/>'
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


def _sym_solar(x, y, color):
    """PLTS/PV source: inverter panel symbol used by the P2B SLD."""
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.7">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 5:.1f}"/>'
        f'<rect x="{x - 10:.1f}" y="{y + 5:.1f}" width="20" height="24"/>'
        f'<path d="M{x - 7:.1f},{y + 26:.1f} L{x:.1f},{y + 9:.1f} '
        f'L{x + 7:.1f},{y + 26:.1f} Z"/>'
        f'</g>'
    )


def _conductor_offsets(counts):
    """Keep pairs legible even when four circuits occupy one input record."""
    groups, cursor = [], 0.0
    for count in counts:
        offsets = []
        for i in range(count):
            if i:
                cursor += WIRE_PITCH * (2 if i % 2 == 0 else 1)
            offsets.append(cursor)
        groups.append(offsets)
        cursor += WIRE_PITCH * 2
    midpoint = (cursor - WIRE_PITCH * 2) / 2
    return [[x - midpoint for x in group] for group in groups]


def render_view_svg(db: Session, view: AnalyticalView) -> str:
    nodes, edges, roles, seeds, _ = get_view_graph(db, view)
    tier = calculate_tier(db, view)
    core_ids, spur = classify_layout(db, view)

    subs = {k[1]: n for k, n in nodes.items() if k[0] == "SUBSTATION"}
    gens = {k[1]: n for k, n in nodes.items() if k[0] == "GENERATING_UNIT"}
    if not subs:
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 120">'
                '<text x="20" y="60" font-family="Arial" font-size="14">No substations in view</text></svg>')

    # A generator outlet is an actual source busbar even when it has only one
    # transmission neighbour. Leaf classification must not collapse it into a
    # hanging bay; otherwise the generator symbol survives but its lead has no
    # bus position to connect to.
    generator_outlets = {g.outlet_substation_id for g in gens.values() if g.outlet_substation_id in subs}
    core_ids.update(generator_outlets)
    for sid in generator_outlets:
        spur.pop(sid, None)

    # The backbone contains dozens of same-voltage GITETs. It needs a denser
    # drawing grid than an operational subsystem SLD, while retaining enough
    # room for two-circuit bundles and bridge arcs.
    compact_500 = view.rule_profile == "BACKBONE_500"
    bay_slot = BAY_SLOT
    bus_min_half = BUS_MIN_HALF
    layout_gutter = 54 if compact_500 else 110
    margin_x = 88 if compact_500 else MARGIN_X
    edge_margin = 44 if compact_500 else EDGE_MARGIN

    loads = {sid: symbol_count(s.symbol_note, 'transformer', s.has_transformer) for sid, s in subs.items()}
    capacitors = {sid: symbol_count(s.symbol_note, 'capacitor', s.has_shunt_capacitor) for sid, s in subs.items()}

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

    def _bay_note_count(b):
        m = re.search(r"circuit_count\s*=\s*(\d+)", b.note or "", re.I)
        return max(1, int(m.group(1))) if m else 1

    bay_counts = {b.id: _bay_note_count(b) for b in bay_rows}

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
    # (hv, lv) -> circuit, for IBTs whose HV side is a normal bus rather than a
    # GITET (150/70, 150/30). Both buses keep their own rows; only the chain is
    # drawn between them.
    _ibt_step_down: dict[tuple[int, int], object] = {}
    ibt_links_by_pair: dict[tuple[int, int], list] = defaultdict(list)
    _ibt_as_line: set[int] = set()   # circuit ids to route like a normal line
    for c in edges:
        if c.circuit_type != "IBT_LINK":
            continue
        a, b = c.from_substation_id, c.to_substation_id
        hv = a if (subs.get(a) and subs[a].voltage_kv >= subs.get(b, subs[a]).voltage_kv) else b
        lv = b if hv == a else a
        if not subs.get(hv):
            continue
        live = (_is_live(subs[hv].status)
                and _is_live(subs.get(lv, subs[hv]).status) and _is_live(c.status))
        if not live:
            _ibt_as_line.add(c.id)
            continue
        ibt_links_by_pair[(hv, lv)].append(c)
        if subs[hv].substation_type == "GITET":
            # A GITET is drawn floating directly above the LV bus it feeds; it
            # has no row of its own. `gitet_feeds` drives that placement.
            gitet_feeds[hv] = lv
        else:
            # A step-down inside the 150 kV network (150/70 at Cibinong,
            # Driyorejo, Kertosono; 150/30 further east) is the same transformer
            # structure, but its HV side is an ordinary bus that keeps its own
            # tier row and its own penghantar. Draw the chain without moving the
            # bus -- previously these links matched no branch at all, so the
            # lower-voltage network rendered as a floating island.
            _ibt_step_down[(hv, lv)] = c

    line_edges = [c for c in edges
                  if (c.circuit_type != "IBT_LINK" or c.id in _ibt_as_line)
                  and c.from_substation_id not in bay_gi_ids
                  and c.to_substation_id not in bay_gi_ids
                  and c.from_substation_id in subs and c.to_substation_id in subs]

    bundles = defaultdict(list)
    for c in line_edges:
        bundles[(tuple(sorted((c.from_substation_id, c.to_substation_id))),
                 c.circuit_type, c.status)].append(c)
    bundle_edges = [min(cs, key=lambda c: c.code) for cs in bundles.values()]
    representative = {c.id: min(cs, key=lambda c: c.code).id
                      for cs in bundles.values() for c in cs}
    bundle_members = {min(cs, key=lambda c: c.code).id: sorted(cs, key=lambda c: (not c.single_phi, c.code))
                      for cs in bundles.values()}

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
    # a GITET that feeds a drawn bus must be drawn too, even when classify_layout
    # filed it as a spur (happens when it has a single IBT link). Its IBT chain
    # is anchored to that GITET's own layout position.
    for _hv, _lv in gitet_feeds.items():
        if _hv not in drawn_ids and _lv in drawn_ids and _row_tier(_hv) is not None:
            drawn_ids.append(_hv)

    # count attachments -> busbar width. Every distinct thing that touches the
    # busbar takes one slot: incoming feed, each outgoing circuit, each bay,
    # own load transformer, own capacitor, each IBT chain.
    att: dict[int, int] = defaultdict(lambda: 2)
    for sid in drawn_ids:
        s = subs[sid]
        n = (loads[sid] if sid not in gitet_feeds else 0) + capacitors[sid]
        n += sum(bay_counts[b.id] for b in bays_by_feeder.get(sid, []))
        n += sum(max(1, c.circuit_count or 1) for spr, fd in spur.items()
                 for c in edges if fd == sid and spr not in bay_gi_ids and spr not in gitet_feeds
                 and {c.from_substation_id, c.to_substation_id} == {spr, fd})
        n += sum(1 for c in line_edges if sid in (c.from_substation_id, c.to_substation_id))
        n += sum(len(ls) for (hv, lv), ls in ibt_links_by_pair.items() if lv == sid)
        n += sum(1 for g in gens.values() if g.outlet_substation_id == sid)
        att[sid] = max(n, 2)

    def bus_half(sid: int) -> float:
        return max(bus_min_half, att[sid] * bay_slot / 2)

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
    # An in-network step-down (150/70, 150/30) draws its chain between two buses
    # that each keep their own tier row -- the book draws them exactly that way
    # (150 kV Semen Baru on Tier-2, 70 kV Semen Baru on Tier-3 beside Cileungsi).
    # Only force the LV bus down when the tiers would otherwise put it level with
    # or above its HV parent, which the chain cannot draw.
    for (_hv, _lv) in _ibt_step_down:
        if _hv in row_of and _lv in row_of and row_of[_lv] <= row_of[_hv]:
            row_of[_lv] = row_of[_hv] + 0.55
    gen_row: dict[int, float] = {}
    for g in gens.values():
        if not g.outlet_substation_id:
            continue  # tap-circuit generator: drawn on the circuit, not in a row
        ft = tier.get(("SUBSTATION", g.outlet_substation_id))
        gen_row[g.id] = (ft - 0.42) if ft else 0.45

    rows: dict[float, list[int]] = defaultdict(list)
    for sid, rk in row_of.items():
        rows[rk].append(sid)

    # Use all connections, not the first encountered feeder as a parent.
    layout_links = [(c.from_substation_id, c.to_substation_id) for c in line_edges
                    if c.from_substation_id in row_of and c.to_substation_id in row_of]
    # Allocate routing capacity per tier gap. A dense boundary can grow without
    # forcing every other pair of tiers to inherit its height.
    integer_tiers = list(range(1, max(1, int(max(row_of.values(), default=1))) + 1))
    gap_height = {}
    for t in integer_tiers[:-1]:
        crossing = sum(min(row_of[a], row_of[b]) <= t < max(row_of[a], row_of[b])
                       for a, b in layout_links)
        gap_height[t] = (max(210, 120 + crossing * 20) if compact_500
                         else max(220, 130 + crossing * 24))
    tier_y = {1: 210.0}
    for t in integer_tiers[:-1]:
        tier_y[t + 1] = tier_y[t] + gap_height[t]

    def y_at(rk):
        # Tier-0 is a compact, fixed source strip above the first GI row.
        # It is not routing space for inter-GI conductors.
        if rk <= 0:
            return 70.0
        lo = max(1, int(rk))
        if rk == lo or lo not in gap_height:
            return tier_y.get(lo, 210.0)
        return tier_y[lo] + (rk - lo) * gap_height[lo]
    regular_rows = {sid: rk for sid, rk in row_of.items() if sid not in gitet_feeds}
    regular_links = [(a, b) for a, b in layout_links if a in regular_rows and b in regular_rows]
    pos = layered_positions(regular_rows, regular_links, bus_half,
                            {sid: subs[sid].code for sid in regular_rows}, y_at,
                            gutter=layout_gutter,
                            virtual_gutter=18 if compact_500 else 24,
                            order_hints={sid: subs[sid].lon for sid in regular_rows})
    # Virtual ordering nodes may leave a completely empty vertical strip.
    # Collapse such strips globally, moving every row on the right together so
    # parent/child alignment remains intact and real busbar clearances remain.
    target_strip = layout_gutter + (80 if compact_500 else 100)
    while True:
        intervals = sorted((x - bus_half(sid), x + bus_half(sid)) for sid, (x, y) in pos.items())
        merged = []
        for left, right in intervals:
            if merged and left <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], right))
            else:
                merged.append((left, right))
        gap = next(((a[1], b[0]) for a, b in zip(merged, merged[1:])
                    if b[0] - a[1] > target_strip + 1e-6), None)
        if not gap:
            break
        cut_left, cut_right = gap
        shift = cut_right - cut_left - target_strip
        pos = {sid: ((x - shift if x >= cut_right else x), y) for sid, (x, y) in pos.items()}
    for hv, lv in gitet_feeds.items():
        if hv in row_of and lv in pos:
            pos[hv] = (pos[lv][0], pos[lv][1] - 130)
    W = max((x + bus_half(sid) for sid, (x, y) in pos.items()), default=800) + margin_x
    gen_pos = {gid: (pos.get(gens[gid].outlet_substation_id, (W / 2, 0))[0],
                     pos.get(gens[gid].outlet_substation_id, (0, 210))[1] - 85)
               for gid, rk in gen_row.items()}

    # Normalise automatic positions before applying saved coordinates. A saved
    # node must not be translated because an unrelated automatic node is < 0.
    auto_left = min((x - bus_half(sid) for sid, (x, y) in pos.items()), default=0)
    auto_shift = margin_x + edge_margin - auto_left
    pos = {sid: (x + auto_shift, y) for sid, (x, y) in pos.items()}
    gen_pos = {gid: (x + auto_shift, y) for gid, (x, y) in gen_pos.items()}

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

    # a GITET busbar sits directly above the LV bus it feeds (its IBT chains
    # rise straight into that bus); the DFS cursor placed it as a loose root.
    # Skip any GITET the user has explicitly placed.
    for hv, lv in gitet_feeds.items():
        if hv in pos and lv in pos and ("SUBSTATION", hv) not in saved:
            pos[hv] = (pos[lv][0], pos[lv][1] - 130)

    # A manual position is a fixed obstacle. Move automatic neighbours away
    # before allocating ports instead of translating the saved node itself.
    pinned = {nid for kind, nid in saved if kind == "SUBSTATION" and nid in pos}
    if pinned:
        fixed = set(pinned)
        for sid in sorted(set(pos) - pinned, key=lambda n: (pos[n][1], pos[n][0])):
            x, y = pos[sid]
            for _ in range(len(pos) + 1):
                obstacles = [n for n in fixed if abs(pos[n][1] - y) < 145 and
                             abs(pos[n][0] - x) < bus_half(n) + bus_half(sid) + 100]
                if not obstacles:
                    break
                x = max(pos[n][0] + bus_half(n) + bus_half(sid) + 100 for n in obstacles)
            pos[sid] = (x, y)
            fixed.add(sid)

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
        target_left = margin_x + edge_margin
        shift = (target_left - left) if not saved else max(0.0, target_left - left)
        if abs(shift) > 0.5:
            pos = {sid: (x + shift, y) for sid, (x, y) in pos.items()}
            gen_pos = {gid: (x + shift, y) for gid, (x, y) in gen_pos.items()}
        right = max([_right_edge(sid) for sid in pos] + [p[0] + 20 for p in gen_pos.values()])
        W = right + margin_x + edge_margin

    all_y = [p[1] for p in pos.values()] + [p[1] for p in gen_pos.values()]
    H = max(all_y, default=210) + 180

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
    # Collect attachment keys per side, ordered by opposite endpoint position.
    PORT: dict[tuple[int, str], float] = {}   # (sub_id, key) -> x

    def _order_key(sid, kind, other_x):
        return (other_x if other_x is not None else pos[sid][0], kind)

    def side(sid, other):
        # From/To is an undirected physical relation, not measured power flow.
        # A connection to a higher row exits above; same-row ties exit below.
        return -1 if pos[other][1] < pos[sid][1] else 1

    bus_attach: dict[int, list] = defaultdict(list)
    for c in bundle_edges:
        a, b = c.from_substation_id, c.to_substation_id
        for sid, oth in ((a, b), (b, a)):
            if sid not in pos:
                continue
            if oth not in pos:
                continue
            kind = "in" if side(sid, oth) == -1 else "out"
            bus_attach[sid].append((f"c{c.id}", kind, pos.get(oth, (pos[sid][0],))[0]))
    for hv, lv in gitet_feeds.items():
        if lv in pos and hv in pos:
            bus_attach[lv].append(("ibt", "ibt", pos[hv][0]))
    for g in gens.values():
        if g.outlet_substation_id in pos:
            bus_attach[g.outlet_substation_id].append((f"gen{g.id}", "gen", None))
    for sid in drawn_ids:
        s = subs[sid]
        if sid not in gitet_feeds:
            for unit in range(loads[sid]):
                bus_attach[sid].append((f"load{unit}", "load", None))
        for unit in range(capacitors[sid]):
            bus_attach[sid].append((f"cap{unit}", "cap", None))
    for feeder_id, blist in bays_by_feeder.items():
        if feeder_id in pos:
            for b in blist:
                bus_attach[feeder_id].append((f"bay{b.id}", "bay", None))
    for spur_id, feeder_id in spur.items():
        if spur_id not in bay_gi_ids and spur_id not in gitet_feeds and feeder_id in pos:
            bus_attach[feeder_id].append((f"spur{spur_id}", "bay", None))

    top_port_x: dict[int, list[float]] = defaultdict(list)   # x of each top attachment
    for sid, items in bus_attach.items():
        cx, cy = pos[sid]
        bh = bus_half(sid)
        # Each side has its own ordered ports. Sorting by the opposite bus
        # keeps siblings in the same order at both ends; sources do not consume
        # all left-hand slots and force unrelated children to cross them.
        for top in (True, False):
            group = [it for it in items if (it[1] in ("in", "ibt", "gen")) == top]
            # Load transformers conventionally sit at the left edge of a bus;
            # this keeps the equipment symbol out of the middle of a dense bay row.
            rank = {"load": 0, "cap": 1, "ibt": 2, "gen": 3, "in": 4, "out": 5}
            group.sort(key=lambda it: (rank.get(it[1], 9), *_order_key(sid, it[1], it[2]), it[0]))
            weights = []
            for key, _, _ in group:
                if key == "ibt":
                    weight = max(1, sum(len(ls) for (hv, lv), ls in ibt_links_by_pair.items() if lv == sid))
                elif key.startswith("bay") and key[3:].isdigit():
                    weight = bay_counts.get(int(key[3:]), 1)
                elif key.startswith("spur") and key[4:].isdigit():
                    spr = int(key[4:])
                    weight = sum(max(1, c.circuit_count or 1) for c in edges
                                 if {c.from_substation_id, c.to_substation_id} == {sid, spr}) or 1
                else:
                    weight = 1
                weights.append(weight)
            total = sum(weights)
            pitch = min(bay_slot, (2 * bh - 32) / max(total, 1))
            cursor = cx - total * pitch / 2
            for (key, kind, _), weight in zip(group, weights):
                px = cursor + weight * pitch / 2
                cursor += weight * pitch
                PORT[(sid, key)] = px
                if top:
                    top_port_x[sid].append(px)

    def port(sid, key, fallback_x=None):
        if key.startswith("c") and key[1:].isdigit():
            key = f"c{representative.get(int(key[1:]), int(key[1:]))}"
        return PORT.get((sid, key), fallback_x if fallback_x is not None else pos[sid][0])

    # A radial child can align its incoming bay with the parent outgoing bay,
    # not merely its bus centre. This removes the repeated tiny Z on a chain.
    for sid in sorted(pos, key=lambda n: (pos[n][1], pos[n][0])):
        if ("SUBSTATION", sid) in saved or sid in gitet_feeds:
            continue
        incoming = [(c, c.to_substation_id if c.from_substation_id == sid else c.from_substation_id)
                    for c in bundle_edges if sid in (c.from_substation_id, c.to_substation_id)]
        incoming = [(c, other) for c, other in incoming if other in pos and pos[other][1] < pos[sid][1]]
        if len(incoming) != 1:
            continue
        c, parent = incoming[0]
        dx = port(parent, f"c{c.id}") - port(sid, f"c{c.id}")
        x, y = pos[sid]
        if any(other != sid and abs(oy - y) < 80 and
               abs(ox - (x + dx)) < bus_half(sid) + bus_half(other) + 80
               for other, (ox, oy) in pos.items()):
            continue
        pos[sid] = (x + dx, y)
        for key in list(PORT):
            if key[0] == sid:
                PORT[key] += dx
        top_port_x[sid] = [px + dx for px in top_port_x[sid]]
    W = max(W, max((x + bus_half(sid) for sid, (x, y) in pos.items()), default=0) + margin_x)

    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" '
        f'data-layout-density="{"compact-500" if compact_500 else "standard"}" '
        f'font-family="Arial, Helvetica, sans-serif">',
        f'<rect width="{W:.0f}" height="{H}" fill="#ffffff"/>',
        f'<text x="18" y="26" font-size="14" font-weight="700" fill="#0f274a">'
        f'{esc(_view_title(db, view))}</text>',
    ]

    # ---- Tier band overlay -----------------------------------------
    # A semantic overlay (never baked in): the boundary line between two Tier
    # rows plus a left-edge label. Kept light so it does not compete with the
    # conductors, but clearly readable -- a dashed rule at the mid-y between
    # this row and the next, and a pale pill behind the "TIER-n" label.
    p.append('<g id="overlay-tier">')
    bands = sorted({int(round(rk)) for rk in rows if abs(rk - round(rk)) < 1e-6})
    for idx, t in enumerate(bands):
        y = y_at(t)
        # boundary rule sits half a row ABOVE this tier's busbars (between it
        # and the tier above); the first tier's rule sits just above it.
        previous_gap = y - y_at(t - 1) if t > 1 else 120
        by = y - (previous_gap / 2 if idx else 60)
        p.append(f'<line x1="16" y1="{by:.0f}" x2="{W - 16:.0f}" y2="{by:.0f}" '
                 f'stroke="#b9c6d8" stroke-width="1.2" stroke-dasharray="6 5"/>')
        p.append(f'<rect x="14" y="{by - 9:.0f}" width="54" height="17" rx="3" '
                 f'fill="#eef2f7" stroke="#c9d4e2" stroke-width="0.8"/>')
        p.append(f'<text x="41" y="{by + 3:.0f}" font-size="10.5" fill="#5a6b80" '
                 f'font-weight="700" text-anchor="middle">TIER {t}</text>')
    p.append('</g>')

    # ---- route bundles before emitting individual conductors ------------
    specs = []
    for c in bundle_edges:
        a, b = c.from_substation_id, c.to_substation_id
        if a not in pos or b not in pos:
            continue
        # Canonical geometry does not depend on which end was entered as From.
        if (pos[a][1], pos[a][0], subs[a].code) > (pos[b][1], pos[b][0], subs[b].code):
            a, b = b, a
        da, db_ = side(a, b), side(b, a)
        ax, bx = port(a, f"c{c.id}"), port(b, f"c{c.id}")
        ay, by = pos[a][1], pos[b][1]
        start = (ax, ay + (BUS_BOTTOM if da > 0 else -BUS_TOP))
        end = (bx, by + (BUS_BOTTOM if db_ > 0 else -BUS_TOP))
        specs.append((c, (ax, ay), start, end, (bx, by)))
    symbol_obstacles = []
    for (hv, lv), links in ibt_links_by_pair.items():
        if hv in pos and lv in pos:
            base = port(lv, "ibt")
            radius = (len(links) - 1) * 46 / 2 + 20
            symbol_obstacles.append((base - radius, pos[hv][1], base + radius, pos[lv][1] - 20))
    for gid, (gx, gy) in gen_pos.items():
        outlet = gens[gid].outlet_substation_id
        if outlet in pos:
            gx = port(outlet, f"gen{gid}")
            symbol_obstacles.append((gx - 24, gy - 42, gx + 24, pos[outlet][1] - 20))
    routes = []
    # Within a tier gap, reserve the long runs before shorter local ties.
    specs.sort(key=lambda z: (abs(z[2][1] - z[3][1]), -abs(z[2][0] - z[3][0]), z[0].code))
    # The strip above Tier-1 belongs to sources and their short outlet leads.
    # Inter-GI routes must enter the channel below Tier-1, even when a cheaper
    # same-row detour exists above the busbars.
    route_floor = (tier_y.get(1, 210.0) + BUS_BOTTOM) if not saved else None
    offsets_by_bundle = {c.id: _conductor_offsets([
        1 if m.single_phi else max(1, m.circuit_count or 1) for m in bundle_members[c.id]])
        for c, *_ in specs}
    centres = (route_bundles(pos, bus_half, specs, symbol_obstacles,
                             min_route_y=route_floor,
                             wire_offsets={cid: [off for group in groups for off in group]
                                           for cid, groups in offsets_by_bundle.items()}) if specs else {})
    for c, first, start, end, last in specs:
        centre = centres[c.id]
        members = bundle_members[c.id]
        # Separate distinct parallel line groups more clearly than the
        # conductors inside one group.  Example: SKLT 1-2 | 3-4 must read as
        # two pairs, not four equally spaced, ambiguous strokes.
        lane_offsets = offsets_by_bundle[c.id]
        for member, offsets in zip(members, lane_offsets):
            paths = [offset_path(centre, off) for off in offsets]
            stroke, dash = _circuit_style(member)
            routes.append({"cid": member.id, "code": member.code, "paths": paths, "centre": centre,
                           "bundle": c.code,
                           "stroke": stroke, "dash": dash, "w": 2.2,
                           "title": f"{member.name} - {member.circuit_type}, {member.status}",
                           "ctype": member.circuit_type, "status": member.status})
    route_by_cid = {r["cid"]: r for r in routes}
    p.append('<g id="circuits">')
    crossings = {}
    for r in routes:
        p.append(f'<g data-circuit-id="{r["cid"]}" data-circuit-code="{esc(r["code"])}" '
                 f'data-bundle-code="{esc(r["bundle"])}" '
                 f'data-circuit-type="{esc(r["ctype"])}" data-status="{esc(r["status"])}">')
        for wire in r["paths"]:
            d = path_d(wire)
            # A narrow halo separates strokes; explicit bridges below mark
            # perpendicular crossings without erasing adjacent conductors.
            p.append(f'<path class="wire-clearance" d="{d}" fill="none" stroke="white" '
                     f'stroke-width="7" stroke-linejoin="round"/>')
            p.append(f'<path class="sld-wire" d="{d}" fill="none" stroke="{r["stroke"]}" '
                     f'stroke-width="{r["w"]}" stroke-dasharray="{r["dash"]}"><title>{esc(r["title"])}</title></path>')
            for endpoint, inner in ((wire[0], wire[1]), (wire[-1], wire[-2])):
                direction = 1 if inner[1] > endpoint[1] else -1
                p.append(_cb(endpoint[0], endpoint[1] + direction * CB_GAP, r["stroke"]))
        p.append('</g>')
    # Detect every perpendicular crossing regardless of route order. The
    # vertical conductor always owns the bridge, including its colour/width.
    for i, ra in enumerate(routes):
        for rb in routes[i + 1:]:
            for wa in ra["paths"]:
                for wb in rb["paths"]:
                    for a, b in zip(wa, wa[1:]):
                        for c, d in zip(wb, wb[1:]):
                            crossing = _perp_crossing(a, b, c, d)
                            if crossing:
                                x, y, first_vertical = crossing
                                vr, hr = (ra, rb) if first_vertical else (rb, ra)
                                crossings[(round(x, 3), round(y, 3))] = (vr, hr)
    # Replace just the local vertical stroke, preserving the horizontal wire
    # underneath. A disk erases neighbouring conductors at the 14-unit pitch.
    radius = 5.5
    for (x, y), (vr, hr) in sorted(crossings.items()):
        p.append(f'<path d="M{x:.1f},{y-radius:.1f} V{y+radius:.1f}" stroke="white" stroke-width="{vr["w"]+2}"/>')
        p.append(f'<path d="M{x-4:.1f},{y:.1f} H{x+4:.1f}" stroke="{hr["stroke"]}" stroke-width="{hr["w"]}"/>')
    for (x, y), (vr, hr) in sorted(crossings.items()):
        d = f'M{x:.1f},{y-radius:.1f} A{radius},{radius} 0 0 1 {x:.1f},{y+radius:.1f}'
        p.append(f'<path class="bridge-clearance" d="{d}" fill="none" stroke="white" stroke-width="{vr["w"]+3}"/>')
        p.append(f'<path class="sld-bridge" data-crossing-x="{x:.1f}" data-crossing-y="{y:.1f}" '
                 f'data-over-circuit-id="{vr["cid"]}" d="{d}" fill="none" stroke="{vr["stroke"]}" stroke-width="{vr["w"]}"/>')
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
        # A GITET sits directly above the bus it feeds, so its chain is a plain
        # vertical drop. An in-network step-down (150/70) keeps both buses on
        # their own rows and they are usually offset horizontally, so the chain
        # has to step across to the HV busbar instead of hanging in mid-air.
        hv_x_span = (hp[0] - bus_half(hv), hp[0] + bus_half(hv))
        for i, c in enumerate(slinks):
            cx = base + (i - (n - 1) / 2) * IBT_DX
            hy, ly = hp[1], lp[1]
            mid = (hy + ly) / 2
            hx = min(max(cx, hv_x_span[0] + 6), hv_x_span[1] - 6)
            da = f' stroke-dasharray="{STATUS_DASH.get(c.status, "none")}"' if c.status != "ENERGIZED" else ""
            p.append(f'<g data-circuit-id="{c.id}" data-circuit-code="{esc(c.code)}" '
                     f'data-circuit-type="IBT_LINK" data-status="{esc(c.status)}">')
            if abs(hx - cx) < 0.5:
                d = f"M{cx:.1f},{hy:.1f} V{ly:.1f}"
            else:
                # down from the HV bar, across in the gap, then down to the LV bar
                d = (f"M{hx:.1f},{hy:.1f} V{mid - 16:.1f} "
                     f"H{cx:.1f} V{ly:.1f}")
            p.append(f'<path d="{d}" fill="none" stroke="#8a6a3a" '
                     f'stroke-width="1.6"{da}><title>{esc(c.name)} - {esc(c.status)}</title></path>')
            p.append(_cb(hx, hy + CB_GAP, hv_col))
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
        if not g.tap_circuit_id and gid not in gen_pos:
            continue
        standby = (g.status or "").upper() in ("STANDBY", "OFF")
        col = "#7c9a6a" if standby else "#0a8a3a"
        is_solar = "PLTS" in f"{g.unit_type or ''} {g.name or ''}".upper()
        if g.tap_circuit_id:
            # a small plant that is NOT a GI (no in/out busbar) -- it sits ON an
            # existing circuit. Draw a node tapped ONTO a real segment of that
            # circuit's routed path (the horizontal run), with a short dashed
            # lead out to the labelled node.
            c = next((e for e in line_edges if e.id == g.tap_circuit_id), None)
            rt = route_by_cid.get(g.tap_circuit_id) if c else None
            lx_ = ly_ = None
            tap_horizontal = False
            if rt and rt["paths"]:
                wire = rt["paths"][0]
                segments = list(zip(wire, wire[1:]))
                remaining = sum(abs(b[0]-a[0]) + abs(b[1]-a[1]) for a, b in segments) / 2
                for a, b in segments:
                    length = abs(b[0]-a[0]) + abs(b[1]-a[1])
                    if remaining <= length:
                        lx_ = a[0] + (b[0]-a[0]) * remaining / length
                        ly_ = a[1] + (b[1]-a[1]) * remaining / length
                        tap_horizontal = a[1] == b[1]
                        break
                    remaining -= length
            elif c:
                a = pos.get(c.from_substation_id)
                b = pos.get(c.to_substation_id)
                if a and b:
                    fx = port(c.from_substation_id, f"c{c.id}")
                    tx = port(c.to_substation_id, f"c{c.id}")
                    ly_ = (a[1] + b[1]) / 2
                    lx_ = fx + (tx - fx) * 0.5
            if lx_ is None:
                continue
            # A tap lead must leave its conductor, even when the midpoint is
            # on a horizontal segment rather than a vertical descent.
            nx, ny = (lx_, ly_ + 34) if tap_horizontal else (lx_ + 34, ly_)
            p.append(f'<g class="sld-tap" data-node-kind="GENERATING_UNIT" data-node-id="{gid}" '
                     f'data-code="{esc(g.code)}" data-tap-circuit-id="{g.tap_circuit_id}" '
                     f'data-tap-x="{lx_:.1f}" data-tap-y="{ly_:.1f}"><title>{esc(g.name)} ({esc(g.unit_type)}) - {esc(g.status)} - '
                     f'tap ruas {esc(c.name) if c else ""}</title>')
            p.append(f'<circle cx="{lx_:.1f}" cy="{ly_:.1f}" r="2.5" fill="{col}"/>')
            p.append(f'<path d="M{lx_:.1f},{ly_:.1f} L{nx:.1f},{ny:.1f}" stroke="{col}" stroke-width="1.4" '
                     f'stroke-dasharray="4 3"/>')
            if is_solar:
                p.append(_sym_solar(nx, ny - 14, col))
            else:
                p.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="4" fill="#ffffff" '
                         f'stroke="{col}" stroke-width="2"/>')
            p.append(f'<text x="{nx + 13 if is_solar else nx + 8:.1f}" y="{ny + 3:.1f}" font-size="9" '
                     f'fill="{col}">{esc(g.name)}{" (standby)" if standby else ""}</text>')
            p.append('</g>')
            continue
        outlet = pos.get(g.outlet_substation_id)
        gx = port(g.outlet_substation_id, f"gen{g.id}", gen_pos[gid][0]) if outlet else gen_pos[gid][0]
        gy = gen_pos[gid][1]
        _gp = "1" if ("GENERATING_UNIT", gid) in saved else "0"
        p.append(f'<g class="sld-node" data-node-kind="GENERATING_UNIT" data-node-id="{gid}" '
                 f'data-code="{esc(g.code)}" data-x="{gx:.1f}" data-y="{gy:.1f}" data-pinned="{_gp}">')
        p.append(_sym_solar(gx, gy - 30, col) if is_solar else _sym_generator(gx, gy - 30, col))
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
        display_code = s.code.removeprefix("GITET_") if compact_500 else s.code
        blabel = esc(display_code)
        est_w = 7 * len(display_code) + 12          # rough label width
        left_room = gap_left - bh - bus_half(row_order[idx - 1] if idx > 0 else sid) > est_w
        right_room = gap_right - bh - bus_half(row_order[idx + 1] if idx < len(row_order) - 1 else sid) > est_w
        left_top_clear = not any(px < left_lim for px in tps)
        right_top_clear = not any(px > right_lim for px in tps)
        has_left_pin = any(risk_on.get(("TRANSFORMER", t.id)) for t in tx_by_sub.get(sid, []))

        label_size = 10.5 if compact_500 else 12.5
        label_halo = 'paint-order="stroke" stroke="#ffffff" stroke-width="3" stroke-linejoin="round"'
        if is_gitet:
            p.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" font-size="{label_size}" font-weight="700" {label_halo} '
                     f'text-anchor="middle" fill="#0f274a">{blabel}</text>')
        elif centre_clear:
            p.append(f'<text x="{x:.1f}" y="{y - 26:.1f}" font-size="{label_size}" font-weight="700" {label_halo} '
                     f'text-anchor="middle" fill="#0f274a">{blabel}</text>')
        elif right_room and right_top_clear:
            p.append(f'<text x="{x + bh + 6:.1f}" y="{y + 3:.1f}" font-size="{label_size}" '
                     f'font-weight="700" {label_halo} text-anchor="start" fill="#0f274a">{blabel}</text>')
        elif left_room and left_top_clear and not has_left_pin:
            p.append(f'<text x="{x - bh - 6:.1f}" y="{y + 3:.1f}" font-size="{label_size}" '
                     f'font-weight="700" {label_halo} text-anchor="end" fill="#0f274a">{blabel}</text>')
        else:
            p.append(f'<text x="{x:.1f}" y="{y - 34:.1f}" font-size="{label_size}" font-weight="700" {label_halo} '
                     f'text-anchor="middle" fill="#0f274a">{blabel}</text>')
        p.append(f'<line x1="{x - bh:.1f}" x2="{x + bh:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                 f'stroke="{bstroke}" stroke-width="6"{da}/>')
        # busbar_config remains metadata. Without bay-to-section connectivity
        # and an operating scenario, drawing a coupler implies unknown state.
        if sid not in gitet_feeds:
            for unit in range(loads[sid]):
                p.append(f'<g class="load-transformer" data-symbol-unit="{unit+1}">'
                         + _sym_transformer(port(sid, f"load{unit}", x), y + 3, vcol) + '</g>')
        for unit in range(capacitors[sid]):
            cap_color = '#9AA0A6' if capacitor_is_off(s.symbol_note) else vcol
            p.append(f'<g class="shunt-capacitor" data-symbol-unit="{unit+1}">'
                     + _sym_capacitor(port(sid, f"cap{unit}", x), y + 3, cap_color) + '</g>')
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
        # a GITET spur is drawn as its own busbar + IBT chain, not a hanging stub
        if spur_id not in bay_gi_ids and spur_id not in gitet_feeds and feeder_id in pos:
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
    bay_circuits: dict[tuple[int, int], list] = defaultdict(list)
    _stub_gi_ids = bay_gi_ids | set(spur)
    for c in edges:   # not line_edges -- those exclude bay/spur-GI endpoints
        a, b = c.from_substation_id, c.to_substation_id
        for sid, oth in ((a, b), (b, a)):
            if sid in _stub_gi_ids and oth in subs:
                bay_feed_style[sid] = _circuit_style(c)
                bay_circuits[(oth, sid)].append(c)

    def _stub_x(it):
        fid, k = it[0], it[1]
        return port(fid, k, pos[fid][0]) if fid in pos else 0.0

    STUB_LEN = 42   # every bay stub is exactly this long -- consistent, per the book
    stub_pin_by_circuit = {}

    for feeder_id, key, gi, status, meta in sorted(stub_items, key=lambda it: (it[0], _stub_x(it))):
        fx, fy = pos[feeder_id]
        sx = port(feeder_id, key, fx)
        source_boundary = meta == "SOURCE_BOUNDARY"
        direction = -1 if source_boundary else 1
        sy = fy + direction * STUB_LEN
        stroke, dash = bay_feed_style.get(gi.id, ("#C00000", "7 5"))
        if status in ("NEW_NOT_ENERGIZED", "PLANNED"):
            stroke, dash = "#111111", "3 6"
        elif status == "DE_ENERGIZED":
            stroke, dash = "#9AA0A6", "none"
        da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        _bcs = sorted(bay_circuits.get((feeder_id, gi.id), []), key=lambda c: c.code)
        _bc = _bcs[0] if _bcs else None
        if _bc:
            stub_pin_by_circuit[_bc.id] = (sx + 16, (fy + sy) / 2)
        _bc_attr = (f' data-circuit-id="{_bc.id}" data-circuit-code="{esc(_bc.code)}"'
                    if _bc else "")
        bay_row = next((b for b in bay_rows if b.substation_id == gi.id and b.feeder_substation_id == feeder_id), None)
        group_counts = [max(1, c.circuit_count or 1) for c in _bcs]
        circuit_count = (sum(group_counts) if group_counts else
                         max(1, bay_counts.get(bay_row.id, 1) if bay_row else 1))
        p.append(f'<g class="sld-bay" data-node-kind="SUBSTATION" data-node-id="{gi.id}" '
                 f'data-code="{esc(gi.code)}" data-circuit-count="{circuit_count}"{_bc_attr}>'
                 f'<title>{esc(gi.name)} [{esc(gi.code)}] - bay di bus {esc(subs[feeder_id].name)} '
                 f'({esc(status)}){" - " + esc(meta) if meta else ""}</title>')
        offsets = [x for group in _conductor_offsets(group_counts or [circuit_count]) for x in group]
        for off in offsets:
            px = sx + off
            p.append(f'<path d="M{px:.1f},{fy:.1f} V{sy:.1f}" fill="none" '
                     f'stroke="{stroke}" stroke-width="2.1"{da}/>')
            p.append(_cb(px, fy + direction * CB_GAP, stroke))
        # A bay is ALWAYS just stub + CB + endpoint dot + code. It never gets a
        # transformer -- that is only for a GI with its own busbar. The code
        # (singkatan) is written below the dot, exactly as the book does it.
        for off in offsets:
            p.append(f'<circle cx="{sx + off:.1f}" cy="{sy:.1f}" r="3" fill="{stroke}"/>')
        label_y = sy - 10 if source_boundary else sy + 15
        p.append(f'<text x="{sx:.1f}" y="{label_y:.1f}" font-size="10" font-weight="700" '
                 f'paint-order="stroke" stroke="#ffffff" stroke-width="3" '
                 f'text-anchor="middle" fill="#334155">{esc(gi.code)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- mapping-audit strip (list computed earlier) -----------------
    if audit:
        y0 = max(all_y, default=210) + 140
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
        values = ",".join(str(q) for q in sorted(seqs))
        return (f'<g class="risk-pin" data-risk-seqs="{esc(values)}">'
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#F6C000" '
                f'stroke="#B8860B" stroke-width="1.5"/>'
                f'<text x="{cx:.1f}" y="{cy + 3:.1f}" font-size="9" font-weight="700" '
                f'text-anchor="middle" fill="#5a4500">'
                f'{esc(values)}</text></g>')

    for sid in drawn_ids:
        seqs = risk_on.get(("SUBSTATION", sid))
        if seqs:
            x, y = pos[sid]
            p.append(_pin(x + bus_half(sid) + 12, y + 22, seqs))
    for c in line_edges:
        seqs = risk_on.get(("CIRCUIT", c.id))
        a, b = pos.get(c.from_substation_id), pos.get(c.to_substation_id)
        if seqs and a and b:
            route = route_by_cid.get(c.id)
            if route:
                wire = route["paths"][0]
                u, v = max(zip(wire, wire[1:]), key=lambda e: abs(e[0][0] - e[1][0]) + abs(e[0][1] - e[1][1]))
                px, py = (u[0] + v[0]) / 2, (u[1] + v[1]) / 2
                p.append(_pin(px + (22 if u[0] == v[0] else 0), py - (20 if u[1] == v[1] else 0), seqs))
    for cid, (px, py) in stub_pin_by_circuit.items():
        seqs = risk_on.get(("CIRCUIT", cid))
        if seqs:
            p.append(_pin(px, py, seqs))
    for sid, tx_list in tx_by_sub.items():
        for t in tx_list:
            seqs = risk_on.get(("TRANSFORMER", t.id))
            if seqs and sid in pos:
                x, y = pos[sid]
                p.append(_pin(x - bus_half(sid) - 12, y, seqs))
    p.append('</g>')

    p.append('</svg>')
    route_points = [pt for r in routes for wire in r["paths"] for pt in wire]
    if route_points:
        left = min(0, min(x for x, y in route_points) - 40)
        top = min(0, min(y for x, y in route_points) - 40)
        right = max(W, max(x for x, y in route_points) + 80)
        bottom = max(H, max(y for x, y in route_points) + 80)
        p[0] = (f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="{left:.1f} {top:.1f} {right-left:.1f} {bottom-top:.1f}" '
                f'data-layout-density="{"compact-500" if compact_500 else "standard"}" '
                f'font-family="Arial, Helvetica, sans-serif">')
        p[1] = f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="#ffffff"/>'
    return "".join(p)
