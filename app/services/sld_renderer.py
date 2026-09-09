"""SLD renderer -- follows the Buku Kerawanan drawing convention.

Line grammar (from the book's SLDs):
  * busbar                -> SOLID bold line, coloured by voltage
  * inter-GI circuit      -> DASHED red line between two busbars, CB box each end
  * IBT 500/150 link      -> SOLID thin line, triple-circle symbol, CB each end
  * GI output bay / load  -> SOLID thin SHORT stub down from the busbar to a
                             transformer / capacitor symbol
  * CB (PMT)              -> small filled square where a circuit meets a busbar
  * bus coupler           -> small open square in the middle of the busbar

The point the starter got wrong and this fixes: an inter-GI circuit (dashed) is
visually distinct from a GI's own output bay (solid short stub), and a
downstream/boundary dead-end GI is drawn as a stub under its feeder, not as a
full Tier row.

Busbars are not named in the book, so no bus names are drawn.
Deterministic: row = Tier, column = name order.
"""
from __future__ import annotations

import html
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import AnalyticalView, RiskRecord
from app.services.topology import calculate_tier, classify_layout, get_view_graph

VOLT_COLOR = {500: "#0047AB", 275: "#00A6D6", 150: "#C00000", 70: "#E6B800", 20: "#E67300"}
STATUS_DASH = {
    "ENERGIZED": "none",
    "NEW_NOT_ENERGIZED": "10 6",
    "PLANNED": "4 5",
    "DE_ENERGIZED": "2 4",
    "OWNED_BY_CUSTOMER": "1 4",
}
STATUS_STROKE = {
    "ENERGIZED": None,          # -> voltage colour
    "NEW_NOT_ENERGIZED": "#111111",
    "PLANNED": "#9AA0A6",
    "DE_ENERGIZED": "#C0392B",
    "OWNED_BY_CUSTOMER": "#7A5C00",
}

BUS_HALF = 66
ROW_H = 168
COL_MIN = 200
MARGIN_X = 110
MARGIN_Y = 110


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def _volt_color(kv) -> str:
    return VOLT_COLOR.get(int(kv or 150), "#C00000")


def _bus_style(sub) -> tuple[str, str]:
    stroke = STATUS_STROKE.get(sub.status) or _volt_color(sub.voltage_kv)
    dash = STATUS_DASH.get(sub.status, "none")
    return stroke, dash


# ---- symbol primitives (drawn hanging below a busbar at x, y) --------------

def _sym_transformer(x, y, color):
    """Double circle -- 150/20 load transformer."""
    r = 9
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.6">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+8:.1f}"/>'
        f'<circle cx="{x:.1f}" cy="{y+8+r:.1f}" r="{r}"/>'
        f'<circle cx="{x:.1f}" cy="{y+8+r+7:.1f}" r="{r}"/>'
        f"</g>"
    )


def _sym_ibt(x, y, color):
    """Triple circle hanging below a busbar at (x, y)."""
    r = 8
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.6">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+6:.1f}"/>'
        f'<circle cx="{x:.1f}" cy="{y+6+r:.1f}" r="{r}"/>'
        f'<circle cx="{x-5:.1f}" cy="{y+6+r+7:.1f}" r="{r}"/>'
        f'<circle cx="{x+5:.1f}" cy="{y+6+r+7:.1f}" r="{r}"/>'
        f"</g>"
    )


def _sym_ibt_inline(x, y):
    """Triple circle centred on a vertical link (for a GITET->GI IBT chain)."""
    r = 7
    return (
        f'<g stroke="#7A3D00" fill="#fff" stroke-width="1.6">'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'
        f'<circle cx="{x-4:.1f}" cy="{y+7:.1f}" r="{r}"/>'
        f'<circle cx="{x+4:.1f}" cy="{y+7:.1f}" r="{r}"/>'
        f"</g>"
    )


def _sym_capacitor(x, y, color):
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.6">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+10:.1f}"/>'
        f'<line x1="{x-8:.1f}" y1="{y+10:.1f}" x2="{x+8:.1f}" y2="{y+10:.1f}"/>'
        f'<line x1="{x-8:.1f}" y1="{y+15:.1f}" x2="{x+8:.1f}" y2="{y+15:.1f}"/>'
        f'<line x1="{x:.1f}" y1="{y+15:.1f}" x2="{x:.1f}" y2="{y+22:.1f}"/>'
        f'<line x1="{x-6:.1f}" y1="{y+22:.1f}" x2="{x+6:.1f}" y2="{y+22:.1f}"/>'
        f'<line x1="{x-3:.1f}" y1="{y+25:.1f}" x2="{x+3:.1f}" y2="{y+25:.1f}"/>'
        f"</g>"
    )


def _sym_generator(x, y, color):
    r = 12
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.6">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+6:.1f}"/>'
        f'<circle cx="{x:.1f}" cy="{y+6+r:.1f}" r="{r}"/>'
        f'<path d="M{x-6:.1f},{y+6+r:.1f} q3,-6 6,0 q3,6 6,0" />'
        f"</g>"
    )


def _cb(x, y, color):
    """Small square where a circuit meets a busbar."""
    return f'<rect x="{x-3:.1f}" y="{y-3:.1f}" width="6" height="6" fill="{color}"/>'


def render_view_svg(db: Session, view: AnalyticalView) -> str:
    nodes, edges, roles, seeds, _ = get_view_graph(db, view)
    tier = calculate_tier(db, view)
    core_ids, spur = classify_layout(db, view)

    subs = {k[1]: n for k, n in nodes.items() if k[0] == "SUBSTATION"}
    gens = {k[1]: n for k, n in nodes.items() if k[0] == "GENERATING_UNIT"}
    if not subs:
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 120">'
                '<text x="20" y="60" font-family="Arial" font-size="14">No substations in view</text></svg>')

    # transformers per substation (for the IBT / trafo symbol)
    from app.models import Transformer
    tx_by_sub: dict[int, list] = defaultdict(list)
    for t in db.query(Transformer).filter(Transformer.substation_id.in_(subs)).all():
        tx_by_sub[t.substation_id].append(t)

    risk_on: dict[tuple[str, int], list[int]] = defaultdict(list)
    if view.subsystem_id:
        for r in db.query(RiskRecord).filter(RiskRecord.subsystem_id == view.subsystem_id).all():
            if r.attach_kind and r.attach_id:
                risk_on[(r.attach_kind, r.attach_id)].append(r.seq_no or 0)

    # ---- rows: fractional row keys so 500 kV GITET and generators sit
    #      ABOVE the 150 kV bus they feed --------------------------------
    max_tier = max([t for t in tier.values()] + [1])

    # which GI does each GITET / generator feed?
    gitet_feeds: dict[int, int] = {}
    for c in edges:
        if c.circuit_type == "IBT_LINK":
            hv = c.from_substation_id if subs.get(c.from_substation_id) and subs[c.from_substation_id].voltage_kv >= 500 else c.to_substation_id
            lv = c.to_substation_id if hv == c.from_substation_id else c.from_substation_id
            if subs.get(hv) and subs[hv].substation_type == "GITET":
                gitet_feeds[hv] = lv

    row_of: dict[int, float] = {}
    for sid in core_ids:
        s = subs[sid]
        if sid in gitet_feeds:
            fed_tier = tier.get(("SUBSTATION", gitet_feeds[sid]))
            row_of[sid] = (fed_tier - 0.55) if fed_tier else 0.45
        else:
            t = tier.get(("SUBSTATION", sid))
            row_of[sid] = float(t if t is not None else max_tier + 1)

    gen_row: dict[int, float] = {}
    for g in gens.values():
        fed_tier = tier.get(("SUBSTATION", g.outlet_substation_id))
        gen_row[g.id] = (fed_tier - 0.75) if fed_tier else 0.25

    rows: dict[float, list] = defaultdict(list)         # rk -> [("S", sub) | ("G", gen)]
    for sid, rk in row_of.items():
        rows[rk].append(("S", subs[sid]))
    for gid, rk in gen_row.items():
        rows[rk].append(("G", gens[gid]))

    ncols = max((len(v) for v in rows.values()), default=1)
    W = MARGIN_X * 2 + max(ncols, 1) * COL_MIN
    max_rk = max(rows) if rows else 1
    H = MARGIN_Y * 2 + int(max_rk * ROW_H) + 140

    pos: dict[int, tuple[float, float]] = {}          # substation id -> (x, y)
    gen_pos: dict[int, tuple[float, float]] = {}
    for rk in sorted(rows):
        items = sorted(rows[rk], key=lambda kv: getattr(kv[1], "name", ""))
        for i, (kind, o) in enumerate(items):
            x = MARGIN_X + (i + 0.5) * (W - 2 * MARGIN_X) / max(len(items), 1)
            y = MARGIN_Y + rk * ROW_H
            if kind == "G":
                gen_pos[o.id] = (x, y)
            else:
                pos[o.id] = (x, y)

    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="Arial, Helvetica, sans-serif">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="18" y="26" font-size="14" font-weight="700" fill="#0f274a">{esc(view.name)}</text>',
    ]

    # ---- Tier band overlay ---------------------------------------------
    p.append('<g id="overlay-tier">')
    for t in sorted(r for r in rows if r and r <= max_tier):
        y = MARGIN_Y + t * ROW_H
        p.append(f'<line x1="16" y1="{y}" x2="{W-16}" y2="{y}" stroke="#d7e0ec" '
                 f'stroke-width="1" stroke-dasharray="2 7"/>')
        p.append(f'<text x="20" y="{y-8}" font-size="11" fill="#8592a6" font-weight="700">TIER-{t}</text>')
    p.append('</g>')

    # ---- IBT links: bus(HV) -> CB -> IBT symbol -> CB -> bus(LV) ------
    p.append('<g id="ibt-links">')
    for c in edges:
        if c.circuit_type != "IBT_LINK":
            continue
        a = pos.get(c.from_substation_id)
        b = pos.get(c.to_substation_id)
        if not a or not b:
            continue
        hv_first = a[1] <= b[1]
        (hx, hy), (lx, ly) = (a, b) if hv_first else (b, a)
        hv_sub = subs.get(c.from_substation_id if hv_first else c.to_substation_id)
        lv_sub = subs.get(c.to_substation_id if hv_first else c.from_substation_id)
        hv_col = _volt_color(hv_sub.voltage_kv) if hv_sub else "#0047AB"
        lv_col = _volt_color(lv_sub.voltage_kv) if lv_sub else "#C00000"
        mid_y = (hy + ly) / 2
        # vertical chain at the HV busbar's x
        cx = hx
        dash = STATUS_DASH.get(c.status, "none")
        da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        p.append(f'<path d="M{cx:.1f},{hy:.1f} V{ly:.1f}" fill="none" stroke="#888" '
                 f'stroke-width="1.4"{da}><title>{esc(c.name)} - {esc(c.status)}</title></path>')
        p.append(_cb(cx, hy + 6, hv_col))                 # CB on the HV side
        p.append(_sym_ibt_inline(cx, mid_y))              # IBT triple-circle
        p.append(_cb(cx, ly - 6, lv_col))                 # CB on the LV side
    p.append('</g>')

    # ---- inter-GI circuits: DASHED, CB box each end ------------------
    p.append('<g id="circuits">')
    for c in edges:
        if c.circuit_type == "IBT_LINK":
            continue
        a = pos.get(c.from_substation_id)
        b = pos.get(c.to_substation_id)
        if not a or not b:
            continue
        (x1, y1), (x2, y2) = a, b
        stroke = STATUS_STROKE.get(c.status) or "#C00000"
        base_dash = "7 5"                       # inter-GI circuit = dashed
        w = 1.4 if c.single_phi else 2.2
        if c.status in ("NEW_NOT_ENERGIZED", "PLANNED", "DE_ENERGIZED"):
            base_dash = STATUS_DASH.get(c.status, base_dash)
        da = f' stroke-dasharray="{base_dash}"' if base_dash != "none" else ""
        (ux, uy), (lx, ly) = ((x1, y1), (x2, y2)) if y1 <= y2 else ((x2, y2), (x1, y1))
        ym = (uy + ly) / 2
        p.append(
            f'<path d="M{ux:.1f},{uy+3:.1f} V{ym:.1f} H{lx:.1f} V{ly-3:.1f}" fill="none" '
            f'stroke="{stroke}" stroke-width="{w}"{da}>'
            f'<title>{esc(c.name)} - {esc(c.circuit_type)}, {esc(c.status)}'
            f'{", single phi" if c.single_phi else ""}'
            f'{", " + str(c.circuit_count) + " sirkit" if c.circuit_count else ""} '
            f'(conf {c.confidence})</title></path>'
        )
        p.append(_cb(ux, uy + 3, stroke))
        p.append(_cb(lx, ly - 3, stroke))
    p.append('</g>')

    # ---- generator stems --------------------------------------------
    p.append('<g id="generators">')
    for gid, g in gens.items():
        gx, gy = gen_pos[g.id]
        outlet = pos.get(g.outlet_substation_id)
        col = "#0a8a3a"
        p.append(_sym_generator(gx, gy - 34, col))
        p.append(f'<text x="{gx:.1f}" y="{gy-46:.1f}" font-size="10" text-anchor="middle" '
                 f'fill="#0a8a3a">{esc(g.name)}</text>')
        if outlet:
            ox, oy = outlet
            p.append(f'<path d="M{gx:.1f},{gy:.1f} V{oy-4:.1f}" fill="none" stroke="{col}" stroke-width="2"/>')
    p.append('</g>')

    # ---- busbars + hanging symbols --------------------------------
    p.append('<g id="busbars">')
    for sid, s in subs.items():
        if sid not in pos:
            continue
        x, y = pos[sid]
        vcol = _volt_color(s.voltage_kv)
        bstroke, bdash = _bus_style(s)
        da = f' stroke-dasharray="{bdash}"' if bdash != "none" else ""
        role = roles.get(("SUBSTATION", sid), "")

        p.append(f'<g><title>{esc(s.name)} [{esc(s.code)}] {esc(s.substation_type)} '
                 f'{esc(int(s.voltage_kv))} kV - {esc(s.status)} - role {esc(role)}'
                 f'{" - " + esc(s.busbar_note) if s.busbar_note else ""}</title>')
        p.append(f'<text x="{x:.1f}" y="{y-14:.1f}" font-size="11" font-weight="700" '
                 f'text-anchor="middle" fill="#0f274a">{esc(s.name)}</text>')
        # busbar -- SOLID bold line
        p.append(f'<line x1="{x-BUS_HALF:.1f}" x2="{x+BUS_HALF:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                 f'stroke="{bstroke}" stroke-width="6"{da}/>')
        # bus coupler -- small open square mid-bar (double-busbar configs)
        if s.busbar_config in ("DOUBLE_1CB", "DOUBLE_SECTIONALIZED"):
            p.append(f'<rect x="{x-5:.1f}" y="{y-4:.1f}" width="10" height="8" '
                     f'fill="#ffffff" stroke="{bstroke}" stroke-width="1.5"/>')

        # GI output bay -- SOLID thin SHORT stub down to the 150/20 load
        # transformer. (IBTs are drawn by the ibt-links layer, not here.)
        if s.has_transformer:
            p.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+6:.1f}" '
                     f'stroke="{vcol}" stroke-width="1.6"/>')
            p.append(_cb(x, y + 4, vcol))
            p.append(_sym_transformer(x, y + 6, vcol))
        if s.has_shunt_capacitor:
            p.append(f'<line x1="{x+24:.1f}" y1="{y:.1f}" x2="{x+24:.1f}" y2="{y+6:.1f}" '
                     f'stroke="{vcol}" stroke-width="1.6"/>')
            p.append(_sym_capacitor(x + 24, y + 6, vcol))
        if role in ("BOUNDARY", "EXTERNAL_CONTEXT"):
            p.append(f'<text x="{x:.1f}" y="{y-26:.1f}" font-size="8" text-anchor="middle" '
                     f'fill="#b06a00" font-weight="700">{esc(role)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- spur substations (short stub under the feeder) -------------
    p.append('<g id="spurs">')
    # group spurs by feeder so several stack side by side
    by_feeder: dict[int, list[int]] = defaultdict(list)
    for spur_id, feeder_id in spur.items():
        by_feeder[feeder_id].append(spur_id)
    for feeder_id, spur_ids in by_feeder.items():
        fp = pos.get(feeder_id)
        if not fp:
            continue
        fx, fy = fp
        n = len(spur_ids)
        for i, sid in enumerate(sorted(spur_ids, key=lambda z: subs[z].name)):
            s = subs[sid]
            sx = fx + (i - (n - 1) / 2) * 40
            sy = fy + 44
            col = STATUS_STROKE.get(s.status) or _volt_color(s.voltage_kv)
            dash = STATUS_DASH.get(s.status, "none")
            da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
            p.append(f'<g><title>{esc(s.name)} [{esc(s.code)}] - spur / output-bay of feeder - '
                     f'role {esc(roles.get(("SUBSTATION", sid), ""))}</title>')
            p.append(f'<path d="M{fx:.1f},{fy:.1f} V{sy:.1f}" fill="none" stroke="{col}" '
                     f'stroke-width="1.6"{da}/>')
            p.append(_cb(fx, fy + 6, col))
            p.append(f'<line x1="{sx-16:.1f}" x2="{sx+16:.1f}" y1="{sy:.1f}" y2="{sy:.1f}" '
                     f'stroke="{col}" stroke-width="3.5"{da}/>')
            p.append(f'<text x="{sx:.1f}" y="{sy+12:.1f}" font-size="8.5" text-anchor="middle" '
                     f'fill="#7b8794">{esc(s.name)}</text>')
            p.append('</g>')
    p.append('</g>')

    # ---- risk overlay --------------------------------------------
    p.append('<g id="overlay-risk">')

    def _pin(cx, cy, seqs):
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#F6C000" '
                f'stroke="#B8860B" stroke-width="1.5"/>'
                f'<text x="{cx:.1f}" y="{cy+3:.1f}" font-size="9" font-weight="700" '
                f'text-anchor="middle" fill="#5a4500">'
                f'{esc(",".join(str(q) for q in sorted(seqs)))}</text>')

    for sid in subs:
        seqs = risk_on.get(("SUBSTATION", sid))
        if seqs and sid in pos:
            x, y = pos[sid]
            p.append(_pin(x + BUS_HALF + 10, y, seqs))
    for c in edges:
        seqs = risk_on.get(("CIRCUIT", c.id))
        a, b = pos.get(c.from_substation_id), pos.get(c.to_substation_id)
        if seqs and a and b:
            p.append(_pin((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, seqs))
    for sid, tx_list in tx_by_sub.items():
        for t in tx_list:
            seqs = risk_on.get(("TRANSFORMER", t.id))
            if seqs and sid in pos:
                x, y = pos[sid]
                p.append(_pin(x - BUS_HALF - 10, y, seqs))
    p.append('</g>')

    p.append('</svg>')
    return "".join(p)
