"""SLD renderer -- follows the Buku Kerawanan drawing grammar.

What the book draws, and what this renders:

  GI in a Tier band (has a book Tier)
      SOLID bold busbar, coloured by voltage. A CB (small filled square) where
      each circuit meets it. Its own 150/20 load transformer hangs directly
      below as a double circle (no separate busbar, no big CB).

  Inter-GI circuit (busbar -> busbar, both in Tier bands)
      DASHED line, orthogonal, a CB at each busbar end. Not-yet-energised /
      planned circuits use a looser dash.

  IBT 500/150 link (GITET busbar -> GI busbar)
      One vertical chain PER transformer: CB (HV colour) -> triple circle ->
      CB (LV colour). Two IBTs -> two chains side by side.

  Spur / boundary bay (DKSBI, PKTGN, ABDGP, Mampang ... off the Kembangan bus)
      A short stub down from the feeder busbar + a CB + the GI name. NO busbar
      of its own -- it is a bay on the feeder, not a Tier node. This is the
      thing the earlier renderer got wrong.

Busbars are not named in the book, so no bus names are drawn.
Deterministic: row = book Tier, column = name order.
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
    "ENERGIZED": None,          # -> voltage colour
    "NEW_NOT_ENERGIZED": "#111111",
    "PLANNED": "#9AA0A6",
    "DE_ENERGIZED": "#C0392B",
    "OWNED_BY_CUSTOMER": "#7A5C00",
}

BUS_HALF = 70
ROW_H = 180
COL_MIN = 215
MARGIN_X = 120
MARGIN_Y = 120
CB = 10          # CB square side
CB_GAP = 11      # distance from the busbar to the CB centre


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def _vcol(kv) -> str:
    return VOLT_COLOR.get(int(kv or 150), "#C00000")


def _cb(x, y, color):
    return f'<rect x="{x - CB / 2:.1f}" y="{y - CB / 2:.1f}" width="{CB}" height="{CB}" fill="{color}"/>'


def _sym_transformer(x, y, color):
    """Double circle -- 150/20 load transformer, hanging below a busbar."""
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
    """Triple circle centred on a vertical link (a GITET -> GI IBT chain)."""
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

    # bays: a small GI drawn as a stub on a feeder busbar (no busbar of its own)
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

    # a GITET busbar feeds exactly one GI via IBT links
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

    # ---- rows: book Tier. GITET sits half a row above the GI it feeds -----
    #      GIs that are ONLY bays (drawn as stubs) never get a Tier row.
    tier_rows: dict[float, list[int]] = defaultdict(list)   # rk -> [sub_id]  (core only)
    for sid in core_ids:
        if sid in bay_gi_ids:
            continue
        s = subs[sid]
        if sid in gitet_feeds:
            ft = tier.get(("SUBSTATION", gitet_feeds[sid]))
            rk = (ft - 0.55) if ft else 0.45
        else:
            t = tier.get(("SUBSTATION", sid))
            if t is None:
                continue  # not-yet-energised core GI -> drawn as a note strip later
            rk = float(t)
        tier_rows[rk].append(sid)

    gen_rk: dict[int, float] = {}
    for g in gens.values():
        ft = tier.get(("SUBSTATION", g.outlet_substation_id))
        gen_rk[g.id] = (ft - 0.8) if ft else 0.2

    ncols = max((len(v) for v in tier_rows.values()), default=1)
    W = MARGIN_X * 2 + max(ncols, 1) * COL_MIN
    max_rk = max(list(tier_rows) + list(gen_rk.values()) + [1])
    H = MARGIN_Y * 2 + int(max_rk * ROW_H) + 160

    pos: dict[int, tuple[float, float]] = {}
    gen_pos: dict[int, tuple[float, float]] = {}
    for rk in sorted(tier_rows):
        ids = sorted(tier_rows[rk], key=lambda z: subs[z].name)
        for i, sid in enumerate(ids):
            x = MARGIN_X + (i + 0.5) * (W - 2 * MARGIN_X) / max(len(ids), 1)
            pos[sid] = (x, MARGIN_Y + rk * ROW_H)
    for gid, rk in gen_rk.items():
        outlet = pos.get(gens[gid].outlet_substation_id)
        gx = outlet[0] if outlet else MARGIN_X + (W - 2 * MARGIN_X) / 2
        gen_pos[gid] = (gx, MARGIN_Y + rk * ROW_H)

    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'font-family="Arial, Helvetica, sans-serif">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="18" y="26" font-size="14" font-weight="700" fill="#0f274a">{esc(view.name)}</text>',
    ]

    # ---- Tier band overlay ---------------------------------------------
    p.append('<g id="overlay-tier">')
    seen_bands = sorted({round(rk) for rk in tier_rows if rk == round(rk)})
    for t in seen_bands:
        y = MARGIN_Y + t * ROW_H
        p.append(f'<line x1="16" y1="{y}" x2="{W - 16}" y2="{y}" stroke="#d7e0ec" '
                 f'stroke-width="1" stroke-dasharray="2 7"/>')
        p.append(f'<text x="20" y="{y - 8}" font-size="11" fill="#8592a6" font-weight="700">TIER-{t}</text>')
    p.append('</g>')

    # ---- inter-GI circuits (DASHED, CB each end) ----------------------
    #      skip any circuit whose endpoint is only a bay -- it is drawn as a stub
    p.append('<g id="circuits">')
    for c in edges:
        if c.circuit_type == "IBT_LINK":
            continue
        if c.from_substation_id in bay_gi_ids or c.to_substation_id in bay_gi_ids:
            continue
        a = pos.get(c.from_substation_id)
        b = pos.get(c.to_substation_id)
        if not a or not b:
            continue
        (ux, uy), (lx, ly) = (a, b) if a[1] <= b[1] else (b, a)
        stroke = STATUS_STROKE.get(c.status) or "#C00000"
        dash = STATUS_DASH.get(c.status, "7 5")
        w = 1.4 if c.single_phi else 2.3
        ym = (uy + ly) / 2
        p.append(
            f'<path d="M{ux:.1f},{uy + CB_GAP:.1f} V{ym:.1f} H{lx:.1f} V{ly - CB_GAP:.1f}" fill="none" '
            f'stroke="{stroke}" stroke-width="{w}" stroke-dasharray="{dash}">'
            f'<title>{esc(c.name)} - {esc(c.circuit_type)}, {esc(c.status)}'
            f'{", single phi" if c.single_phi else ""}'
            f'{", " + str(c.circuit_count) + " sirkit" if c.circuit_count else ""} '
            f'(conf {c.confidence})</title></path>'
        )
        p.append(_cb(ux, uy + CB_GAP, stroke))
        p.append(_cb(lx, ly - CB_GAP, stroke))
    p.append('</g>')

    # ---- IBT chains: one per transformer, side by side --------------
    p.append('<g id="ibt-links">')
    for (hv, lv), links in ibt_links_by_pair.items():
        hp, lp = pos.get(hv), pos.get(lv)
        if not hp or not lp:
            continue
        hv_col = _vcol(subs[hv].voltage_kv)
        lv_col = _vcol(subs[lv].voltage_kv)
        n = len(links)
        for i, c in enumerate(sorted(links, key=lambda z: z.code)):
            cx = lp[0] + (i - (n - 1) / 2) * 26
            hy, ly = hp[1], lp[1]
            mid = (hy + ly) / 2
            dash = STATUS_DASH.get(c.status, "none")
            da = f' stroke-dasharray="{dash}"' if c.status != "ENERGIZED" else ""
            p.append(f'<path d="M{cx:.1f},{hy:.1f} V{ly:.1f}" fill="none" stroke="#8a6a3a" '
                     f'stroke-width="1.6"{da}><title>{esc(c.name)} - {esc(c.status)}</title></path>')
            p.append(_cb(cx, hy + CB_GAP, hv_col))
            p.append(_sym_ibt_inline(cx, mid - 4))
            p.append(_cb(cx, ly - CB_GAP, lv_col))
            p.append(f'<text x="{cx:.1f}" y="{mid + 22:.1f}" font-size="8" text-anchor="middle" '
                     f'fill="#8a6a3a">{esc(c.transformer_id and _tx_label(db, c.transformer_id))}</text>')
    p.append('</g>')

    # ---- generators -------------------------------------------------
    p.append('<g id="generators">')
    for gid, g in gens.items():
        gx, gy = gen_pos[gid]
        outlet = pos.get(g.outlet_substation_id)
        col = "#0a8a3a"
        p.append(_sym_generator(gx, gy - 30, col))
        p.append(f'<text x="{gx:.1f}" y="{gy - 42:.1f}" font-size="10" text-anchor="middle" '
                 f'fill="#0a8a3a">{esc(g.name)}</text>')
        if outlet:
            p.append(f'<path d="M{gx:.1f},{gy:.1f} V{outlet[1] - 4:.1f}" fill="none" '
                     f'stroke="{col}" stroke-width="2"/>')
    p.append('</g>')

    # ---- busbars + own load transformer -----------------------------
    p.append('<g id="busbars">')
    for sid, s in subs.items():
        if sid not in pos:
            continue
        x, y = pos[sid]
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
        p.append(f'<line x1="{x - BUS_HALF:.1f}" x2="{x + BUS_HALF:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                 f'stroke="{bstroke}" stroke-width="6"{da}/>')
        if s.busbar_config in ("DOUBLE_1CB", "DOUBLE_SECTIONALIZED"):
            p.append(f'<rect x="{x - 5:.1f}" y="{y - 4:.1f}" width="10" height="8" '
                     f'fill="#ffffff" stroke="{bstroke}" stroke-width="1.6"/>')

        # own 150/20 load transformer -- only if this GI is NOT a GITET feeder
        # (a GITET's IBT is drawn by the ibt-links layer)
        if s.has_transformer and sid not in gitet_feeds:
            p.append(_sym_transformer(x - 18, y + 3, vcol))
        if s.has_shunt_capacitor:
            p.append(_sym_capacitor(x + 20, y + 3, vcol))
        if role in ("BOUNDARY", "EXTERNAL_CONTEXT"):
            p.append(f'<text x="{x:.1f}" y="{y - 27:.1f}" font-size="8" text-anchor="middle" '
                     f'fill="#b06a00" font-weight="700">{esc(role)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- bays: a GI drawn as a stub on its feeder busbar, NO busbar --
    p.append('<g id="bays">')
    # merge the topology-derived spurs with the explicit Bay rows
    spur_as_bays: dict[int, list] = defaultdict(list)
    for spur_id, feeder_id in spur.items():
        if spur_id not in bay_gi_ids:
            spur_as_bays[feeder_id].append(("spur", subs[spur_id], subs[spur_id].status,
                                            roles.get(("SUBSTATION", spur_id), "")))
    for feeder_id, blist in bays_by_feeder.items():
        for b in blist:
            spur_as_bays[feeder_id].append(("bay", subs[b.substation_id], b.status, b.note or ""))

    for feeder_id, items in spur_as_bays.items():
        fp = pos.get(feeder_id)
        if not fp:
            continue
        fx, fy = fp
        items = sorted(items, key=lambda it: it[1].name)
        n = len(items)
        for i, (kind, gi, status, meta) in enumerate(items):
            sx = fx + (i - (n - 1) / 2) * 34
            sy = fy + 42
            col = STATUS_STROKE.get(status) or _vcol(gi.voltage_kv)
            dash = STATUS_DASH.get(status, "7 5")
            p.append(f'<g><title>{esc(gi.name)} [{esc(gi.code)}] - bay di bus {esc(subs[feeder_id].name)} '
                     f'({esc(status)}){" - " + esc(meta) if meta else ""}</title>')
            p.append(f'<path d="M{fx:.1f},{fy:.1f} V{fy + 10:.1f} H{sx:.1f} V{sy:.1f}" fill="none" '
                     f'stroke="{col}" stroke-width="1.8" stroke-dasharray="{dash}"/>')
            p.append(_cb(fx, fy + CB_GAP, col))
            p.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="3" fill="{col}"/>')
            p.append(f'<text x="{sx:.1f}" y="{sy + 13:.1f}" font-size="8.5" text-anchor="middle" '
                     f'fill="#6b7787">{esc(gi.name)}</text>')
            p.append('</g>')
    p.append('</g>')

    # ---- not-yet-energised core GIs: a note strip at the bottom -----
    dead = [sid for sid in core_ids
            if tier.get(("SUBSTATION", sid)) is None and sid not in spur]
    if dead:
        y0 = MARGIN_Y + (max(seen_bands) + 1) * ROW_H if seen_bands else H - 80
        p.append('<g id="not-energised">')
        p.append(f'<text x="20" y="{y0 - 6:.1f}" font-size="10" fill="#8592a6" font-weight="700">'
                 f'Belum energize / perencanaan (tidak dihitung Tier):</text>')
        for i, sid in enumerate(sorted(dead, key=lambda z: subs[z].name)):
            s = subs[sid]
            x = 24 + i * 190
            p.append(f'<line x1="{x:.1f}" x2="{x + 40:.1f}" y1="{y0:.1f}" y2="{y0:.1f}" '
                     f'stroke="#111" stroke-width="4" stroke-dasharray="10 6"/>')
            p.append(f'<text x="{x:.1f}" y="{y0 + 14:.1f}" font-size="9" fill="#555">'
                     f'{esc(s.name)}</text>')
        p.append('</g>')

    # ---- risk overlay --------------------------------------------
    p.append('<g id="overlay-risk">')

    def _pin(cx, cy, seqs):
        return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#F6C000" '
                f'stroke="#B8860B" stroke-width="1.5"/>'
                f'<text x="{cx:.1f}" y="{cy + 3:.1f}" font-size="9" font-weight="700" '
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


_TX_LABEL_CACHE: dict[int, str] = {}


def _tx_label(db: Session, tx_id: int) -> str:
    if tx_id not in _TX_LABEL_CACHE:
        t = db.get(Transformer, tx_id)
        _TX_LABEL_CACHE[tx_id] = (t.unit_no or "") if t else ""
    return _TX_LABEL_CACHE[tx_id]
