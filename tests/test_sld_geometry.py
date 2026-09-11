"""Electrical drawing invariants, rather than a snapshot of SVG formatting."""
import re
import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

from app.services.sld_layout import offset_path, layered_positions
from app.services.sld_renderer import _circuit_style, _sym_solar


@pytest.mark.parametrize(('kv', 'kind', 'expected'), [
    (500, 'SUTET', ('#0047AB', 'none')),
    (500, 'SKTT', ('#0047AB', '7 5')),
    (150, 'SUTT', ('#C00000', 'none')),
    (70, 'SUTT', ('#E6B800', 'none')),
    (66, 'SUTT', ('#E6B800', 'none')),
    (30, 'SUTT', ('#39C96B', 'none')),
    (20, 'SKTT', ('#E67300', '7 5')),
])
def test_energized_circuit_colour_is_bound_to_voltage(kv, kind, expected):
    circuit = SimpleNamespace(status='ENERGIZED', circuit_type=kind, voltage_kv=kv)
    assert _circuit_style(circuit) == expected


def test_circuit_status_overrides_voltage_colour():
    planned = SimpleNamespace(status='PLANNED', circuit_type='SUTET', voltage_kv=500)
    new = SimpleNamespace(status='NEW_NOT_ENERGIZED', circuit_type='SUTET', voltage_kv=500)
    off = SimpleNamespace(status='DE_ENERGIZED', circuit_type='SUTET', voltage_kv=500)
    assert _circuit_style(planned) == ('#9AA0A6', '3 6')
    assert _circuit_style(new) == ('#111111', '12 7')
    assert _circuit_style(off) == ('#9AA0A6', '2 5')


def test_plts_uses_panel_inverter_symbol():
    symbol = _sym_solar(20, 30, '#0a8a3a')
    assert '<rect ' in symbol and '<path d="M' in symbol
    assert '<circle ' not in symbol


def intersection(a, b, c, d):
    """Inclusive intersection: even touching another conductor is ambiguous."""
    if a[0] == b[0] and c[0] == d[0]:
        return a[0] == c[0] and max(min(a[1], b[1]), min(c[1], d[1])) <= min(max(a[1], b[1]), max(c[1], d[1]))
    if a[1] == b[1] and c[1] == d[1]:
        return a[1] == c[1] and max(min(a[0], b[0]), min(c[0], d[0])) <= min(max(a[0], b[0]), max(c[0], d[0]))
    if a[1] == b[1]:
        a, b, c, d = c, d, a, b
    return min(c[0], d[0]) <= a[0] <= max(c[0], d[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])


@pytest.mark.parametrize('points', [
    [(0, 0), (0, 100), (200, 100), (200, 200)],
    [(200, 0), (200, 100), (0, 100), (0, 200)],
    [(0, 0), (0, 100), (200, 100), (200, 0)],
    [(0, 200), (0, 100), (200, 100), (200, 0)],
    [(0, 0), (0, 100), (200, 100), (200, 300), (400, 300), (400, 400)],
])
def test_bundle_remains_parallel_through_turns(points):
    a, b = offset_path(points, -7), offset_path(points, 7)
    assert not any(intersection(u, v, w, z) for u, v in zip(a, a[1:]) for w, z in zip(b, b[1:]))
    for (u, v), (w, z) in zip(zip(a, a[1:]), zip(b, b[1:])):
        assert abs(u[0] - w[0] if u[0] == v[0] else u[1] - w[1]) == 14


def test_layout_does_not_depend_on_from_to_or_input_order():
    rows = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}
    edges = [(1, 4), (2, 3), (3, 5), (4, 5), (3, 4), (1, 5), (2, 5)]
    names = {n: str(n) for n in rows}
    a = layered_positions(rows, edges, lambda n: 55, names, lambda r: r * 240)
    b = layered_positions(rows, [(y, x) for x, y in reversed(edges)], lambda n: 55, names, lambda r: r * 240)
    assert a == b


def test_longitude_is_a_soft_order_hint_without_changing_tier():
    rows = {1: 1, 2: 1, 3: 1}
    names = {1: "WEST-NAME-Z", 2: "CENTRE", 3: "EAST-NAME-A"}
    pos = layered_positions(rows, [], lambda _: 20, names, lambda r: r * 200,
                            order_hints={1: 106.0, 2: 108.0, 3: 112.0})
    assert pos[1][0] < pos[2][0] < pos[3][0]
    assert {xy[1] for xy in pos.values()} == {200}


def geometry_errors(svg):
    ns = {'s': 'http://www.w3.org/2000/svg'}
    root = ET.fromstring(svg)
    bars = []
    for group in root.findall('.//s:g[@id="busbars"]/s:g', ns):
        line = group.find('s:line', ns)
        if line is not None:
            bars.append((group.get('data-code'), float(line.get('x1')), float(line.get('x2')), float(line.get('y1'))))
    errors = []
    bundles = {}
    by_id = {}
    for group in root.findall('.//s:g[@id="circuits"]/s:g', ns):
        code = group.get('data-circuit-code')
        paths = []
        for path in group.findall('s:path[@class="sld-wire"]', ns):
            xy = list(map(float, re.findall(r'-?\d+(?:\.\d+)?', path.get('d'))))
            pts = list(zip(xy[::2], xy[1::2]))
            paths.append(pts)
            for a, b in zip(pts, pts[1:]):
                if (a[0] == b[0]) == (a[1] == b[1]):
                    errors.append(f'{code}: diagonal or zero segment {a} {b}')
                for name, l, r, y in bars:
                    # Allow only the first/last point to meet a busbar.
                    if any(abs(pt[1] - y) < 0.2 and l <= pt[0] <= r for pt in (pts[0], pts[-1])):
                        if a[0] == b[0] and min(a[1], b[1]) < y < max(a[1], b[1]) and l <= a[0] <= r:
                            errors.append(f'{code}: crosses its endpoint bus {name}')
                        continue
                    if intersection(a, b, (l, y), (r, y)):
                        errors.append(f'{code}: hits unrelated bus {name}')
            for endpoint in (pts[0], pts[-1]):
                if not any(abs(endpoint[1] - y) < 0.2 and l <= endpoint[0] <= r for _, l, r, y in bars):
                    errors.append(f'{code}: disconnected endpoint {endpoint}')
        for i, wire in enumerate(paths):
            for other in paths[i + 1:]:
                if any(intersection(a, b, c, d) for a, b in zip(wire, wire[1:]) for c, d in zip(other, other[1:])):
                    errors.append(f'{code}: conductors intersect')
        bundles.setdefault(group.get('data-bundle-code'), []).extend(paths)
        by_id[group.get('data-circuit-id')] = paths
    for code, paths in bundles.items():
        for i, wire in enumerate(paths):
            for other in paths[i + 1:]:
                if any(intersection(a, b, c, d) for a, b in zip(wire, wire[1:]) for c, d in zip(other, other[1:])):
                    errors.append(f'{code}: separate circuit records intersect within one bundle')
                for (a, b), (c, d) in zip(zip(wire, wire[1:]), zip(other, other[1:])):
                    spacing = abs(a[0] - c[0] if a[0] == b[0] else a[1] - c[1])
                    if spacing < 13.8:
                        errors.append(f'{code}: bundle spacing is only {spacing}')
    def endpoints(paths):
        return {name for wire in paths for pt in (wire[0], wire[-1])
                for name, l, r, y in bars if abs(pt[1]-y) < .2 and l <= pt[0] <= r}
    items = list(bundles.items())
    for i, (code, paths) in enumerate(items):
        for other_code, other_paths in items[i+1:]:
            for wire in paths:
                for other in other_paths:
                    for a, b in zip(wire, wire[1:]):
                        for c, d in zip(other, other[1:]):
                            if (a[0] == b[0]) != (c[0] == d[0]):
                                continue
                            axis = 0 if a[0] == b[0] else 1
                            span = 1-axis
                            gap = max(min(a[span], b[span]), min(c[span], d[span])) - min(max(a[span], b[span]), max(c[span], d[span]))
                            spacing = abs(a[axis]-c[axis])
                            if gap < 0 and spacing < 1:
                                errors.append(f'{code}/{other_code}: unrelated wires overlap')
                            if (axis == 1 and 0 <= gap < 40 and spacing < 40
                                    and abs(a[0]-b[0]) > 120 and abs(c[0]-d[0]) > 120
                                    and not endpoints(paths) & endpoints(other_paths)):
                                errors.append(f'{code}/{other_code}: near-continuation ({spacing=}, {gap=})')
    for tap in root.findall('.//s:g[@class="sld-tap"]', ns):
        point = float(tap.get('data-tap-x')), float(tap.get('data-tap-y'))
        target = by_id.get(tap.get('data-tap-circuit-id'), [])
        if not any(intersection(a, b, point, point) for wire in target for a, b in zip(wire, wire[1:])):
            errors.append(f'{tap.get("data-code")}: tap is not on its circuit')
        if target:
            segments = list(zip(target[0], target[0][1:]))
            total = sum(abs(b[0]-a[0])+abs(b[1]-a[1]) for a, b in segments)
            walked = 0
            for a, b in segments:
                if intersection(a, b, point, point):
                    walked += abs(point[0]-a[0])+abs(point[1]-a[1])
                    break
                walked += abs(b[0]-a[0])+abs(b[1]-a[1])
            if abs(walked-total/2) > .3:
                errors.append(f'{tap.get("data-code")}: tap is not halfway along the wire')
    expected = set()
    ids = list(by_id)
    for i, cid in enumerate(ids):
        for other_id in ids[i+1:]:
            for wire in by_id[cid]:
                for other in by_id[other_id]:
                    for a, b in zip(wire, wire[1:]):
                        for c, d in zip(other, other[1:]):
                            if (a[0] == b[0]) == (c[0] == d[0]):
                                continue
                            v, w, h, k = (a, b, c, d) if a[0] == b[0] else (c, d, a, b)
                            if min(v[1], w[1]) < h[1] < max(v[1], w[1]) and min(h[0], k[0]) < v[0] < max(h[0], k[0]):
                                expected.add((v[0], h[1]))
    actual = {(float(p.get('data-crossing-x')), float(p.get('data-crossing-y')))
              for p in root.findall('.//s:path[@class="sld-bridge"]', ns)}
    if actual != expected:
        errors.append(f'crossing bridges missing/spurious: {expected ^ actual}')
    senayan = root.findall('.//s:g[@data-circuit-code="SKTT_SNYAN_DNYSA_SP"]/s:path[@class="sld-wire"]', ns)
    direct = root.findall('.//s:g[@data-circuit-code="SKTT_SNYAN_DNYSA_DIRECT"]/s:path[@class="sld-wire"]', ns)
    if senayan and direct and senayan[0].get('stroke-width') != direct[0].get('stroke-width'):
        errors.append('Senayan-Danayasa conductors have different stroke widths')
    return errors


def test_crossing_is_independent_of_route_order():
    from app.services.sld_renderer import _perp_crossing
    vertical = ((10, 0), (10, 100))
    horizontal = ((0, 30), (90, 30))
    assert _perp_crossing(*vertical, *horizontal) == (10, 30, True)
    assert _perp_crossing(*horizontal, *vertical) == (10, 30, False)
    assert _perp_crossing(*vertical, (10, 30), (90, 30)) is None


def test_seeded_geometry(db):
    # Existing fixture isolates the DB. Include all three real subsystems,
    # including both LBK views, without touching the user's mantaps.db.
    from app.services.seed_ss_bll import seed_ss_bll
    from app.services.seed_ss_cwd import seed_ss_cwd
    from app.models import AnalyticalView
    from app.services.sld_renderer import render_view_svg
    seed_ss_bll(db)
    seed_ss_cwd(db)
    errors = []
    for view in db.query(AnalyticalView).all():
        svg = render_view_svg(db, view)
        errors.extend(f'{view.view_key}: {e}' for e in geometry_errors(svg))
        root = ET.fromstring(svg)
        ns = {'s': 'http://www.w3.org/2000/svg'}
        if view.view_key == 'SS_LBK_BALARAJA':
            assert 'class="sld-bridge"' in svg
            assert 'class="risk-pin" data-risk-seqs="5"' in svg
            # A tiered BOUNDARY is a full busbar in this view, not silently
            # collapsed into the Bay appearance used by another view.
            busbars = svg.split('<g id="bays">', 1)[0]
            assert 'data-code="DKSBI"' in busbars
        if view.view_key == 'SS_CWD_FULL':
            assert 'class="sld-bridge"' not in svg
        for bar in root.findall('.//s:g[@id="busbars"]/s:g', ns):
            assert bar.find('s:rect', ns) is None  # no implied coupler state
            name = bar.get('data-code')
            if name in ('MAXIM', 'JTAKE', 'LEGOK', 'CWANG'):
                expected = {'MAXIM': ('load-transformer', 3), 'JTAKE': ('shunt-capacitor', 2),
                            'LEGOK': ('shunt-capacitor', 2), 'CWANG': ('shunt-capacitor', 3)}[name]
                assert len(bar.findall(f's:g[@class="{expected[0]}"]', ns)) == expected[1], name
            if name == 'LKONG':
                cap = bar.find('s:g[@class="shunt-capacitor"]/s:g', ns)
                assert cap is not None and cap.get('stroke') == '#9AA0A6'
    assert not errors, '\n'.join(errors)


def test_backbone_500_compacts_layout_and_keeps_routes_below_generators(db):
    from app.models import AnalyticalView, Substation
    from app.services.seed_backbone_500 import seed_backbone_500
    from app.services.sld_renderer import render_view_svg

    result = seed_backbone_500(db)
    view = db.get(AnalyticalView, result['view_id'])
    # Short book labels overlap with 150 kV GI codes in subsystem fixtures.
    # The 500 kV projection must own distinct canonical GITET objects, or SS
    # capacitor/transformer attributes leak into the backbone.
    for code in ('BLRJA', 'CWANG', 'DEPOK', 'DKSBI'):
        s = db.query(Substation).filter(Substation.code == f'GITET_{code}').one()
        assert s.voltage_kv == 500
        assert not s.has_transformer and not s.has_shunt_capacitor
    svg = render_view_svg(db, view)
    root = ET.fromstring(svg)
    ns = {'s': 'http://www.w3.org/2000/svg'}
    width = float(root.get('viewBox').split()[2])
    nodes = {g.get('data-code'): float(g.get('data-x'))
             for g in root.findall('.//s:g[@class="sld-node"]', ns)
             if g.get('data-node-kind') == 'SUBSTATION'}

    assert root.get('data-layout-density') == 'compact-500'
    assert width < 5000
    ordered_x = sorted(nodes.values())
    assert max(b - a for a, b in zip(ordered_x, ordered_x[1:])) < width * .2
    assert root.findall('.//s:path[@class="sld-bridge"]', ns)
    assert not [e for e in geometry_errors(svg) if 'crossing bridges' in e]
    generators = root.findall('.//s:g[@id="generators"]/s:g[@class="sld-node"]', ns)
    assert len(generators) == 18
    assert all(g.find('s:path', ns) is not None for g in generators)
    top_bus_y = min(float(g.get('data-y')) for g in root.findall('.//s:g[@class="sld-node"]', ns)
                    if g.get('data-node-kind') == 'SUBSTATION')
    wires = root.findall('.//s:g[@id="circuits"]//s:path[@class="sld-wire"]', ns)
    wire_points = []
    for wire in wires:
        xy = list(map(float, re.findall(r'-?\d+(?:\.\d+)?', wire.get('d'))))
        wire_points.extend(zip(xy[::2], xy[1::2]))
    assert min(y for x, y in wire_points) >= top_bus_y


def test_symbol_counts_do_not_use_ratings():
    from app.services.sld_symbols import symbol_count, symbol_note
    assert symbol_count('50 MVAr', 'capacitor', True) == 1
    assert symbol_count('3x kapasitor 50 MVAr', 'capacitor', True) == 3
    assert symbol_count('3 trafo di SLD (perlu konfirmasi OSL)', 'transformer', True) == 3
    assert symbol_count(symbol_note({'transformer_count': 0, 'symbol_note': '3 trafo sebelumnya'}), 'transformer', True) == 0
