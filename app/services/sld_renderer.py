"""Starter SLD renderer.

NOT the final engineering renderer (no bay stubs, no CB symbols on both circuit
ends, no orthogonal bus grammar yet). It draws the GI graph with:
    - one horizontal busbar per GI, coloured by voltage
    - GIs stacked into Tier bands (Tier computed by topology.calculate_tier)
    - orthogonal elbow routing between busbars
    - transformer / capacitor tick marks under a GI when the SLD shows them
    - status styling: energised (solid), new (black dashed), planned (grey dashed)
    - risk markers on objects that carry a RiskRecord in this view's subsystem

Overlays (Tier band label, risk pins) are drawn as separate <g> layers so a web
viewer can toggle them.
"""
from __future__ import annotations

import html
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import AnalyticalView, RiskRecord, Substation
from app.services.topology import calculate_tier, get_view_graph

VOLT_COLOR = {500: "#0047AB", 275: "#00A6D6", 150: "#C00000", 70: "#E6B800", 20: "#E67300"}
STATUS_STYLE = {
    "ENERGIZED": ("#C00000", "none"),
    "NEW_NOT_ENERGIZED": ("#111111", "10 6"),
    "PLANNED": ("#9AA0A6", "4 5"),
    "DE_ENERGIZED": ("#C0392B", "2 4"),
    "OWNED_BY_CUSTOMER": ("#7A5C00", "1 4"),
}


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def render_view_svg(db: Session, view: AnalyticalView) -> str:
    nodes, edges, roles, seeds, _ = get_view_graph(db, view)
    tier = calculate_tier(db, view)

    subs = {key[1]: n for key, n in nodes.items() if key[0] == "SUBSTATION"}
    if not subs:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120">' \
               '<text x="20" y="60" font-family="Arial" font-size="14">No substations in view</text></svg>'

    # risk lookup: substation_id / circuit_id -> [seq_no]
    risk_on: dict[tuple[str, int], list[int]] = defaultdict(list)
    if view.subsystem_id:
        for r in db.query(RiskRecord).filter(RiskRecord.subsystem_id == view.subsystem_id).all():
            if r.attach_kind and r.attach_id:
                risk_on[(r.attach_kind, r.attach_id)].append(r.seq_no or 0)

    # ---- layout: row = tier, column = display_order ----------------------
    rows: dict[int, list[Substation]] = defaultdict(list)
    max_tier = max([tier.get(("SUBSTATION", sid), 99) for sid in subs] + [1])
    fallback_tier = {}
    for sid, s in subs.items():
        t = tier.get(("SUBSTATION", sid))
        if t is None:
            # not reachable from a seed in this scenario -> park at the bottom
            t = max_tier + 1
        fallback_tier[sid] = t
        rows[t].append(s)

    COL_W, ROW_H, MARGIN_X, MARGIN_Y = 190, 150, 90, 90
    bar_half = 62
    ncols = max((len(v) for v in rows.values()), default=1)
    W = MARGIN_X * 2 + max(ncols, 1) * COL_W
    H = MARGIN_Y * 2 + (max(rows) if rows else 1) * ROW_H + 60

    pos: dict[int, tuple[float, float]] = {}
    for t, items in rows.items():
        items.sort(key=lambda s: (s.name or ""))
        for i, s in enumerate(items):
            x = MARGIN_X + (i + 0.5) * (W - 2 * MARGIN_X) / max(len(items), 1)
            y = MARGIN_Y + (t - 1) * ROW_H
            pos[s.id] = (x, y)

    p: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial, sans-serif">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="16" y="26" font-size="14" font-weight="700" fill="#0f274a">{esc(view.name)}</text>',
    ]

    # ---- tier band overlay ---------------------------------------------------
    p.append('<g id="overlay-tier" opacity="0.9">')
    for t in sorted(rows):
        y = MARGIN_Y + (t - 1) * ROW_H
        label = f"TIER-{t}" if t <= max_tier else "(tak terjangkau seed)"
        p.append(f'<line x1="20" y1="{y}" x2="{W-20}" y2="{y}" stroke="#c9d3df" '
                 f'stroke-width="1" stroke-dasharray="2 6"/>')
        p.append(f'<text x="24" y="{y-6}" font-size="11" fill="#8592a6" font-weight="700">{label}</text>')
    p.append('</g>')

    # ---- circuits (edges) --------------------------------------------------
    p.append('<g id="circuits">')
    for c in edges:
        a = pos.get(c.from_substation_id)
        b = pos.get(c.to_substation_id)
        if not a or not b:
            continue
        (x1, y1), (x2, y2) = a, b
        stroke, dash = STATUS_STYLE.get(c.status, STATUS_STYLE["ENERGIZED"])
        if c.circuit_type == "IBT_LINK":
            stroke = "#0047AB"
        ym = (y1 + y2) / 2
        da = f' stroke-dasharray="{dash}"' if dash != "none" else ""
        w = 1.4 if c.single_phi else 2.4
        p.append(f'<path d="M{x1:.1f},{y1:.1f} V{ym:.1f} H{x2:.1f} V{y2:.1f}" '
                 f'fill="none" stroke="{stroke}" stroke-width="{w}"{da}>'
                 f'<title>{esc(c.name)} ({esc(c.circuit_type)}, {esc(c.status)}'
                 f'{", single phi" if c.single_phi else ""}) conf={c.confidence}</title></path>')
    p.append('</g>')

    # ---- busbars (nodes) -------------------------------------------------
    p.append('<g id="busbars">')
    for sid, s in subs.items():
        x, y = pos[sid]
        color = VOLT_COLOR.get(int(s.voltage_kv or 150), "#C00000")
        bstroke, bdash = STATUS_STYLE.get(s.status, STATUS_STYLE["ENERGIZED"])
        if s.status == "ENERGIZED":
            bstroke = color
        da = f' stroke-dasharray="{bdash}"' if bdash != "none" else ""
        role = roles.get(("SUBSTATION", sid), "")
        p.append(f'<g><title>{esc(s.name)} [{esc(s.code)}] {esc(s.substation_type)} '
                 f'{esc(int(s.voltage_kv))}kV - {esc(s.status)} - role {esc(role)}</title>')
        p.append(f'<text x="{x:.1f}" y="{y-16:.1f}" font-size="11" font-weight="700" '
                 f'text-anchor="middle" fill="#0f274a">{esc(s.name)}</text>')
        p.append(f'<line x1="{x-bar_half:.1f}" x2="{x+bar_half:.1f}" y1="{y:.1f}" y2="{y:.1f}" '
                 f'stroke="{bstroke}" stroke-width="6"{da}/>')
        # transformer / capacitor tick under the bar
        marks = []
        if s.has_transformer:
            marks.append("T")
        if s.has_shunt_capacitor:
            marks.append("C")
        if marks:
            p.append(f'<text x="{x:.1f}" y="{y+16:.1f}" font-size="9" text-anchor="middle" '
                     f'fill="#8592a6">{esc("/".join(marks))}</text>')
        if role in ("BOUNDARY", "EXTERNAL_CONTEXT"):
            p.append(f'<text x="{x:.1f}" y="{y+28:.1f}" font-size="8" text-anchor="middle" '
                     f'fill="#b06a00">{esc(role)}</text>')
        p.append('</g>')
    p.append('</g>')

    # ---- risk overlay -----------------------------------------------------
    p.append('<g id="overlay-risk">')
    for sid, s in subs.items():
        seqs = risk_on.get(("SUBSTATION", sid))
        if not seqs:
            continue
        x, y = pos[sid]
        p.append(f'<circle cx="{x+bar_half+10:.1f}" cy="{y:.1f}" r="9" fill="#F6C000" '
                 f'stroke="#B8860B" stroke-width="1.5"/>')
        p.append(f'<text x="{x+bar_half+10:.1f}" y="{y+3:.1f}" font-size="9" font-weight="700" '
                 f'text-anchor="middle" fill="#5a4500">{esc(",".join(str(q) for q in sorted(seqs)))}</text>')
    for c in edges:
        seqs = risk_on.get(("CIRCUIT", c.id))
        if not seqs:
            continue
        a, b = pos.get(c.from_substation_id), pos.get(c.to_substation_id)
        if not a or not b:
            continue
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        p.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="9" fill="#F6C000" '
                 f'stroke="#B8860B" stroke-width="1.5"/>')
        p.append(f'<text x="{mx:.1f}" y="{my+3:.1f}" font-size="9" font-weight="700" '
                 f'text-anchor="middle" fill="#5a4500">{esc(",".join(str(q) for q in sorted(seqs)))}</text>')
    p.append('</g>')

    p.append('</svg>')
    return "".join(p)
