"""SLD renderer -- Buku Kerawanan drawing grammar, fixed-grid layout.

Layout
  * Row  = book Tier band (from calculate_tier). GITET sits half a row above
    the GI its IBTs feed.
  * Each core GI gets a fixed-width lane. Its busbar width scales with the
    number of things attached to it (bays + own transformer/capacitor + child
    circuits), with a floor, so bays never get cramped.
  * Columns are packed left-to-right per row; a child GI is nudged toward its
    parent's x so the tree reads top-down.

Line grammar
  * busbar               SOLID bold, coloured by voltage
  * inter-GI circuit     DASHED, orthogonal, a CB box at each busbar end.
                         The horizontal elbow runs in the empty gap BETWEEN two
                         Tier bands -- never across a busbar it does not touch.
  * upward "bay panjang" (child Tier < feeder Tier, e.g. Curug T5 -> Cikupa T4)
                         routed around the OUTSIDE edge of the diagram.
  * IBT 500/150 link     one vertical chain per transformer: CB(HV) -> triple
                         circle -> CB(LV). Two IBTs -> two chains side by side.
  * bay (small GI drawn only as a stub on a feeder busbar -- Durikosambi,
    Petukangan, AGP, Mampang off Kembangan): short stub + CB + name, NO busbar.
    A GI can be a bay on several busbars (Petukangan: off Kembangan, and a
    broken feeder off Senayan).
  * GI 150/20 load transformer  double circle hanging under the busbar
  * shunt capacitor             standard symbol
  * bus coupler                 small open square mid-busbar
"""
from __future__ import annotations

import html
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import AnalyticalView, Bay, RiskRecord, Transformer
from app.services.topology import calculate_tier, classify_layout, get_view_graph

VOLT_COLOR = {500: "#0047AB", 275: "#00A6D6", 150: "#C00000", 70: "#E6B800", 20: "#E67300"}
STATUS_DASH = {
    "ENERGIZED": "7 5",
    "NEW_NOT_ENERGIZED": "12 7",
    "PLANNED": "3 6",
    "DE_ENERGIZED": "2 5",
    "OWNED_BY_CUSTOMER": "5 4",
}
STATUS_STROKE = {
    "ENERGIZED": None,
    "NEW_NOT_ENERGIZED": "#111111",
    "PLANNED": "#9AA0A6",
    "DE_ENERGIZED": "#C0392B",
    "OWNED_BY_CUSTOMER": "#7A5C00",
}

LANE_W = 190           # fixed lane width per GI
BAY_SLOT = 40          # horizontal space reserved per bay / attachment
BUS_MIN = 96           # minimum busbar half-not: actual = max(BUS_MIN, slots*BAY_SLOT)/2
ROW_H = 190
MARGIN_X = 140
MARGIN_Y = 120
CB = 10
CB_GAP = 12
EDGE_MARGIN = 46       # width of the outer routing channel for bay-panjang


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def _vcol(kv) -> str:
    return VOLT_COLOR.get(int(kv or 150), "#C00000")


def _cb(x, y, color):
    return f'<rect x="{x - CB / 2:.1f}" y="{y - CB / 2:.1f}" width="{CB}" height="{CB}" fill="{color}"/>'


def _sym_transformer(x, y, color):
    r = 9
    return (
        f'<g stroke="{color}" fill="none" stroke-width="1.7">'
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 7:.1f}"/>'
        f'<circle cx="{x:.1f}" cy="{y + 7 + r:.1f}" r="{r}"/>'
        f'<circle cx="{x:.1f}" cy="{y + 7 + r + 8:.1f}" r="{r}"/>'
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


def _sym_ibt_inline(x, y):
    r = 7.5
    return (
        f'<g stroke="#7A3D00" fill="#ffffff" stroke-width="1.7">'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'
        f'<circle cx="{x - 4.5:.1f}" cy="{y + 8:.1f}" r="{r}"/>'
        f'<circle cx="{x + 4.5:.1f}" cy="{y + 8:.1f}" r="{r}"/>'
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
    gitet_feeds: dict[int, int] = {}
    ibt_links_by_pair: dict[tuple[int, int], list] = defaultdict(list)
    for c in edges:
        if c.circuit_type != "IBT_LINK":
            continue
        a, b = c.from_substation_id, c.to_substation_id
        hv = a if (subs.get(a) and subs[a].voltage_kv >= subs.get(b, subs[a]).voltage_kv) else b
        lv = b if hv == a else a
        if subs.get(hv) and subs[hv].substation_type == "GITET":
            gitet_feeds[hv] = lv
            ibt_links_by_pair[(hv, lv)].append(c)

    line_edges = [c for c in edges
                  if c.circuit_type != "IBT_LINK"
                  and c.from_substation_id not in bay_gi_ids
                  and c.to_substation_id not in bay_gi_ids
                  and c.from_substation_id in subs and c.to_substation_id in subs]

    # ---- which GIs get a row (core, energised, not bay-only) -----------
    drawn_ids = [sid for sid in core_ids
                 if sid not in bay_gi_ids and tier.get(("SUBSTATION", sid)) is not None]

    # count attachments -> busbar width
    att: dict[int, int] = defaultdict(lambda: 1)
    for sid in drawn_ids:
        s = subs[sid]
        n = 1 + (1 if s.has_transformer and sid not in gitet_feeds else 0) + (1 if s.has_shunt_capacitor else 0)
        n += len(bays_by_feeder.get(sid, []))
        for c in line_edges:
            if sid in (c.from_substation_id, c.to_substation_id):
                n += 1
        att[sid] = max(n, 2)

    def bus_half(sid: int) -> float:
        return max(BUS_MIN, att[sid] * BAY_SLOT) / 2

    # ---- rows keyed by fractional Tier --------------------------------
    row_of: dict[int, float] = {}
    for sid in drawn_ids:
        if sid in gitet_feeds:
            ft = tier.get(("SUBSTATION", gitet_feeds[sid]))
            row_of[sid] = (ft - 0.55) if ft else 0.45
        else:
            row_of[sid] = float(tier[("SUBSTATION", sid)])
    gen_row: dict[int, float] = {}
    for g in gens.values():
        ft = tier.get(("SUBSTATION", g.outlet_substation_id))
        gen_row[g.id] = (ft - 0.85) if ft else 0.2

    rows: dict[float, list[int]] = defaultdict(list)
    for sid, rk in row_of.items():
        rows[rk].append(sid)

    # parent (feeder) of each GI, for x-nudging
    parent: dict[int, int] = {}
    for c in line_edges:
        a, b = c.from_substation_id, c.to_substation_id
        ta, tb = tier.get(("SUBSTATION", a)), tier.get(("SUBSTATION", b))
        if ta is None or tb is None:
            continue
        if ta < tb:
            parent.setdefault(b, a)
        elif tb < ta:
            parent.setdefault(a, b)
    for hv, lv in gitet_feeds.items():
        parent[hv] = lv  # GITET nudged to its GI

    # ---- assign x per row: pack, then bias toward parent -------------
    pos: dict[int, tuple[float, float]] = {}
    # width first pass
    row_width = {}
    for rk, ids in rows.items():
        row_width[rk] = sum(max(LANE_W, bus_half(s) * 2 + 30) for s in ids)
    content_w = max(row_width.values()) if row_width else LANE_W
    W = MARGIN_X * 2 + EDGE_MARGIN * 2 + content_w

    for rk in sorted(rows):
        ids = rows[rk]
        # order by parent x if known, else by name
        ids.sort(key=lambda s: (pos.get(parent.get(s, -1), (1e9,))[0], subs[s].name))
        lanes = [max(LANE_W, bus_half(s) * 2 + 30) for s in ids]
        total = sum(lanes)
        x = MARGIN_X + EDGE_MARGIN + (content_w - total) / 2
        for s, lw in zip(ids, lanes):
            cx = x + lw / 2
            # bias toward parent
            pp = pos.get(parent.get(s, -1))
            if pp:
                cx = 0.55 * cx + 0.45 * pp[0]
            pos[s] = (cx, MARGIN_Y + rk * ROW_H)
            x += lw

    gen_pos: dict[int, tuple[float, float]] = {}
    for gid, rk in gen_row.items():
        outlet = pos.get(gens[gid].outlet_substation_id)
        gx = outlet[0] if outlet else W / 2
        gen_pos[gid] = (gx, MARGIN_Y + rk * ROW_H)

    max_rk = max(list(rows) + list(gen_row.values()) + [1])
    H = MARGIN_Y * 2 + int(max_rk * ROW_H) + 170

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

    # ---- circuits -------------------------------------------------
    left_ch = MARGIN_X + EDGE_MARGIN * 0.45
    right_ch = W - MARGIN_X - EDGE_MARGIN * 0.45
    p.append('<g id="circuits">')
    for c in line_edges:
        a = pos.get(c.from_substation_id)
        b = pos.get(c.to_substation_id)
        if not a or not b:
            continue
        stroke = STATUS_STROKE.get(c.status) or "#C00000"
        dash = STATUS_DASH.get(c.status, "7 5")
        w = 1.4 if c.single_phi else 2.3
        ta = tier.get(("SUBSTATION", c.from_substation_id))
        tb = tier.get(("SUBSTATION", c.to_substation_id))
        title = (f'<title>{esc(c.name)} - {esc(c.circuit_type)}, {esc(c.status)}'
                 f'{", single phi" if c.single_phi else ""}'
                 f'{", " + str(c.circuit_count) + " sirkit" if c.circuit_count else ""} '
                 f'(conf {c.confidence})</title>')

        if ta is not None and tb is not None and ta == tb:
            # same-tier tie: shallow bump below the bar
            (x1, y1), (x2, y2) = a, b
            yb = y1 + 30
            p.append(f'<path d="M{x1:.1f},{y1 + CB_GAP:.1f} V{yb:.1f} H{x2:.1f} V{y2 + CB_GAP:.1f}" '
                     f'fill="none" stroke="{stroke}" stroke-width="{w}" stroke-dasharray="{dash}">{title}</path>')
            p.append(_cb(x1, y1 + CB_GAP, stroke)); p.append(_cb(x2, y2 + CB_GAP, stroke))
            continue

        (ux, uy), (lx, ly) = (a, b) if a[1] <= b[1] else (b, a)
        upward = ta is not None and tb is not None and ta > tb  # child above its feeder

        if upward:
            # route around the nearer outer edge
            (fx, fy), (cx, cy) = (a, b) if a[1] > b[1] else (b, a)  # feeder is lower
            ch = left_ch if (fx + cx) / 2 < W / 2 else right_ch
            p.append(f'<path d="M{fx:.1f},{fy + CB_GAP:.1f} V{fy + 24:.1f} H{ch:.1f} V{cy - 24:.1f} '
                     f'H{cx:.1f} V{cy + CB_GAP:.1f}" fill="none" stroke="{stroke}" '
                     f'stroke-width="{w}" stroke-dasharray="{dash}">{title}</path>')
            p.append(_cb(fx, fy + CB_GAP, stroke)); p.append(_cb(cx, cy + CB_GAP, stroke))
            continue

        # normal parent->child: elbow in the gap between the two bands
        gap_y = (uy + ly) / 2
        p.append(f'<path d="M{ux:.1f},{uy + CB_GAP:.1f} V{gap_y:.1f} H{lx:.1f} V{ly - CB_GAP:.1f}" '
                 f'fill="none" stroke="{stroke}" stroke-width="{w}" stroke-dasharray="{dash}">{title}</path>')
        p.append(_cb(ux, uy + CB_GAP, stroke)); p.append(_cb(lx, ly - CB_GAP, stroke))
    p.append('</g>')

    # ---- IBT chains ----------------------------------------------
    p.append('<g id="ibt-links">')
    for (hv, lv), links in ibt_links_by_pair.items():
        hp, lp = pos.get(hv), pos.get(lv)
        if not hp or not lp:
            continue
        hv_col, lv_col = _vcol(subs[hv].voltage_kv), _vcol(subs[lv].voltage_kv)
        n = len(links)
        for i, c in enumerate(sorted(links, key=lambda z: z.code)):
            cx = lp[0] + (i - (n - 1) / 2) * 28
            hy, ly = hp[1], lp[1]
            mid = (hy + ly) / 2
            da = f' stroke-dasharray="{STATUS_DASH.get(c.status, "none")}"' if c.status != "ENERGIZED" else ""
            p.append(f'<path d="M{cx:.1f},{hy:.1f} V{ly:.1f}" fill="none" stroke="#8a6a3a" '
                     f'stroke-width="1.6"{da}><title>{esc(c.name)} - {esc(c.status)}</title></path>')
            p.append(_cb(cx, hy + CB_GAP, hv_col))
            p.append(_sym_ibt_inline(cx, mid - 4))
            p.append(_cb(cx, ly - CB_GAP, lv_col))
    p.append('</g>')

    # ---- generators --------------------------------------------
    p.append('<g id="generators">')
    for gid, g in gens.items():
        gx, gy = gen_pos[gid]
        outlet = pos.get(g.outlet_substation_id)
        col = "#0a8a3a"
        p.append(_sym_generator(gx, gy - 30, col))
        p.append(f'<text x="{gx:.1f}" y="{gy - 42:.1f}" font-size="10" text-anchor="middle" '
                 f'fill="#0a8a3a">{esc(g.name)}</text>')
        if outlet:
            p.append(f'<path d="M{gx:.1f},{gy:.1f} V{outlet[1] - CB_GAP:.1f}" fill="none" '
                     f'stroke="{col}" stroke-width="2"/>')
            p.append(_cb(gx, outlet[1] - CB_GAP, col))
    p.append('</g>')

    # ---- busbars ---------------------------------------------
    p.append('<g id="busbars">')
    for sid in drawn_ids:
        s = subs[sid]
        x, y = pos[sid]
        bh = bus_half(sid)
        vcol = _vcol(s.voltage_kv)
        bstroke = STATUS_STROKE.get(s.status) or vcol
        bdash = STATUS_DASH.get(s.status, "none")
        da = f' stroke-dasharray="{bdash}"' if s.status not in ("ENERGIZED", "OWNED_BY_CUSTOMER") else ""
        role = roles.get(("SUBSTATION", sid), "")
        p.append(f'<g><title>{esc(s.name)} [{esc(s.code)}] {esc(s.substation_type)} '
                 f'{esc(int(s.voltage_kv))} kV - {esc(s.status)} - role {esc(role)}'
                 f'{" - " + esc(s.busbar_note) if s.busbar_note else ""}</title>')
        p.append(f'<text x="{x:.1f}" y="{y - 15:.1f}" font-size="11" font-weight="700" '
                 f'text-anchor="middle" fill="#0f274a">{esc(s.name)}</text>')
        p.append(f'<line x1="{x - bh:.1f}" x2="{x + bh:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                 f'stroke="{bstroke}" stroke-width="6"{da}/>')
        if s.busbar_config in ("DOUBLE_1CB", "DOUBLE_SECTIONALIZED"):
            p.append(f'<rect x="{x - 5:.1f}" y="{y - 4:.1f}" width="10" height="8" '
                     f'fill="#ffffff" stroke="{bstroke}" stroke-width="1.6"/>')
        if s.has_transformer and sid not in gitet_feeds:
            p.append(_sym_transformer(x - bh + 20, y + 3, vcol))
        if s.has_shunt_capacitor:
            p.append(_sym_capacitor(x + bh - 18, y + 3, vcol))
        if role in ("BOUNDARY", "EXTERNAL_CONTEXT"):
            p.append(f'<text x="{x:.1f}" y="{y - 27:.1f}" font-size="8" text-anchor="middle" '
                     f'fill="#b06a00" font-weight="700">{esc(role)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- bays (stub + CB + name, no busbar) --------------------
    p.append('<g id="bays">')
    stub_targets: dict[int, list] = defaultdict(list)
    for spur_id, feeder_id in spur.items():
        if spur_id not in bay_gi_ids and feeder_id in pos:
            stub_targets[feeder_id].append(("spur", subs[spur_id], subs[spur_id].status,
                                            roles.get(("SUBSTATION", spur_id), "")))
    for feeder_id, blist in bays_by_feeder.items():
        if feeder_id not in pos:
            continue
        for b in blist:
            stub_targets[feeder_id].append(("bay", subs[b.substation_id], b.status, b.note or ""))

    for feeder_id, items in stub_targets.items():
        fx, fy = pos[feeder_id]
        bh = bus_half(feeder_id)
        items = sorted(items, key=lambda it: it[1].name)
        n = len(items)
        span = min(2 * bh - 24, max(1, n) * BAY_SLOT)
        for i, (kind, gi, status, meta) in enumerate(items):
            sx = fx - span / 2 + (i + 0.5) * span / max(n, 1)
            sy = fy + 44
            col = STATUS_STROKE.get(status) or _vcol(gi.voltage_kv)
            dash = STATUS_DASH.get(status, "7 5")
            p.append(f'<g><title>{esc(gi.name)} [{esc(gi.code)}] - bay di bus {esc(subs[feeder_id].name)} '
                     f'({esc(status)}){" - " + esc(meta) if meta else ""}</title>')
            p.append(f'<path d="M{sx:.1f},{fy:.1f} V{sy:.1f}" fill="none" '
                     f'stroke="{col}" stroke-width="1.8" stroke-dasharray="{dash}"/>')
            p.append(_cb(sx, fy + CB_GAP, col))
            p.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="{col}"/>')
            p.append(f'<text x="{sx:.1f}" y="{sy + 13:.1f}" font-size="8.5" text-anchor="middle" '
                     f'fill="#6b7787">{esc(gi.name)}</text>')
            p.append('</g>')
    p.append('</g>')

    # ---- not-yet-energised note strip -------------------------
    dead = [sid for sid in core_ids
            if tier.get(("SUBSTATION", sid)) is None and sid not in spur and sid not in bay_gi_ids]
    if dead:
        y0 = MARGIN_Y + (max(bands) + 1) * ROW_H if bands else H - 90
        p.append('<g id="not-energised">')
        p.append(f'<text x="20" y="{y0 - 6:.1f}" font-size="10" fill="#8592a6" font-weight="700">'
                 f'Belum energize / perencanaan (tidak dihitung Tier):</text>')
        for i, sid in enumerate(sorted(dead, key=lambda z: subs[z].name)):
            x = 24 + i * 210
            p.append(f'<line x1="{x:.1f}" x2="{x + 44:.1f}" y1="{y0:.1f}" y2="{y0:.1f}" '
                     f'stroke="#111" stroke-width="4" stroke-dasharray="10 6"/>')
            p.append(f'<text x="{x:.1f}" y="{y0 + 14:.1f}" font-size="9" fill="#555">'
                     f'{esc(subs[sid].name)}</text>')
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
