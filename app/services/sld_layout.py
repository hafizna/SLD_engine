"""Geometry for SLDs, independent of SQL and SVG.

Electrical edges are not a parent/child tree. Order the complete layered graph,
then route bundles in free space. A bundle is offset only after routing, so its
two conductors stay parallel through every orthogonal bend.
"""
from collections import defaultdict
from heapq import heappop, heappush
from itertools import count
from statistics import median

WIRE_PITCH = 14.0
CHANNEL_PITCH = 32.0
BUNDLE_CLEAR = 40.0
COLLINEAR_TOUCH_PENALTY = 22
# How far past a route's own span its discouraged band reaches. Two long
# horizontal runs sitting end-to-end at a similar height read as one conductor
# even with no x-overlap; this mirrors the near-continuation gap the geometry
# invariant in tests/test_sld_geometry.py rejects.
NEAR_CONT_GAP = 40.0
BUS_TOP = 52.0
BUS_BOTTOM = 80.0


def layered_positions(row_of, links, half, names, y_at, gutter=110,
                      virtual_gutter=24, order_hints=None):
    """Order and place a layered graph.

    Long edges get virtual ordering nodes on intermediate rows.  Those markers
    preserve crossing order but must not consume the same gutter as a real GI.
    """
    def gap(a, b):
        return virtual_gutter if isinstance(a, tuple) or isinstance(b, tuple) else gutter
    layers = defaultdict(list)
    rank = {r: i for i, r in enumerate(sorted(set(row_of.values())))}
    node_rank = {n: rank[r] for n, r in row_of.items()}
    widths = {n: half(n) for n in row_of}
    order_hints = order_hints or {}
    has_geo = sum(v is not None for v in order_hints.values()) >= 2
    keys = ({n: (order_hints.get(n) is None, order_hints.get(n) or 0, names[n]) for n in row_of}
            if has_geo else {n: names[n] for n in row_of})
    adjacent = defaultdict(list)
    segments = []
    ties = []
    for n, r in node_rank.items():
        layers[r].append(n)
    # Virtual nodes reserve order for a long edge at every intervening layer.
    canonical_links = [tuple(sorted(e, key=names.get)) for e in links]
    for idx, (a, b) in enumerate(sorted(canonical_links, key=lambda e: (names[e[0]], names[e[1]]))):
        if a not in node_rank or b not in node_rank:
            continue
        if node_rank[a] == node_rank[b]:
            ties.append((a, b))
            continue
        if node_rank[a] > node_rank[b]:
            a, b = b, a
        chain = [a]
        for r in range(node_rank[a] + 1, node_rank[b]):
            dummy = ('edge', idx, r)
            node_rank[dummy] = r
            widths[dummy] = 12
            keys[dummy] = ((True, 0, f'~{names[a]}:{names[b]}:{r}') if has_geo
                           else f'~{names[a]}:{names[b]}:{r}')
            layers[r].append(dummy)
            chain.append(dummy)
        chain.append(b)
        for u, v in zip(chain, chain[1:]):
            adjacent[u].append(v)
            adjacent[v].append(u)
            segments.append((u, v))
    for r in layers:
        layers[r].sort(key=keys.get)

    def indices():
        return {n: i for row in layers.values() for i, n in enumerate(row)}

    def score():
        ix = indices()
        crossings = 0
        by_rank = defaultdict(list)
        for a, b in segments:
            by_rank[node_rank[a]].append((a, b))
        for edges in by_rank.values():
            for i, (a, b) in enumerate(edges):
                for c, d in edges[i + 1:]:
                    crossings += (ix[a] - ix[c]) * (ix[b] - ix[d]) < 0
        geo_inversions = 0
        if has_geo:
            for nodes in layers.values():
                known = [n for n in nodes if order_hints.get(n) is not None]
                for i, a in enumerate(known):
                    geo_inversions += sum(order_hints[a] > order_hints[b] for b in known[i + 1:])
        return (crossings, sum(abs(ix[a] - ix[b]) for a, b in ties),
                geo_inversions, sum(abs(ix[a] - ix[b]) for a, b in segments))

    best_score = score()
    best = {r: list(ns) for r, ns in layers.items()}
    for sweep in range(16):
        downward = sweep % 2 == 0
        for r in sorted(layers, reverse=not downward):
            ix = indices()
            def bary(n):
                nb = [ix[v] for v in adjacent[n]
                      if (node_rank[v] < r if downward else node_rank[v] > r)]
                return median(nb) if nb else ix[n]
            layers[r].sort(key=lambda n: (bary(n), ix[n]))
        # Only accept adjacent swaps which improve the whole graph, including
        # same-layer ties; arbitrary row reorder can undo a previous good pass.
        for r in sorted(layers):
            for i in range(len(layers[r]) - 1):
                before = score()
                layers[r][i:i + 2] = reversed(layers[r][i:i + 2])
                if score() >= before:
                    layers[r][i:i + 2] = reversed(layers[r][i:i + 2])
        candidate = score()
        if candidate < best_score:
            best_score = candidate
            best = {r: list(ns) for r, ns in layers.items()}
    layers = best
    xs = {}
    for r, ns in layers.items():
        cursor = 0
        for idx, n in enumerate(ns):
            xs[n] = cursor + widths[n]
            cursor += 2 * widths[n] + (gap(n, ns[idx + 1]) if idx + 1 < len(ns) else gutter)
        for n in ns:
            xs[n] -= cursor / 2
    # Project barycentres onto the ordered, non-overlapping row constraints.
    # Centre each packed row on its neighbours instead of accumulating a
    # one-sided push to the right on every iteration.
    for sweep in range(20):
        for r in sorted(layers, reverse=bool(sweep % 2)):
            ns = layers[r]
            wants = {n: median([xs[v] for v in adjacent[n]]) if adjacent[n] else xs[n] for n in ns}
            packed = []
            for n in ns:
                x = 0.5 * xs[n] + 0.5 * wants[n]
                if packed:
                    prev, px = packed[-1]
                    x = max(x, px + widths[prev] + widths[n] + gap(prev, n))
                packed.append((n, x))
            shift = sum(wants[n] - x for n, x in packed) / max(1, len(packed))
            for n, x in packed:
                xs[n] = x + shift
    return {n: (xs[n], y_at(row_of[n])) for n in row_of}


def simplify(points):
    result = []
    for pt in points:
        if result and pt == result[-1]:
            continue
        if len(result) >= 2:
            a, b = result[-2:]
            if (a[0] == b[0] == pt[0]) or (a[1] == b[1] == pt[1]):
                result.pop()
        result.append(pt)
    return result


def offset_path(points, distance):
    """Miter an orthogonal polyline; offset is a normal, not an x/y nudge."""
    shifted = []
    for a, b in zip(points, points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = abs(dx) + abs(dy)
        nx, ny = -dy / length * distance, dx / length * distance
        shifted.append(((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)))
    out = [shifted[0][0]]
    for (a, b), (c, d) in zip(shifted, shifted[1:]):
        out.append((a[0], c[1]) if a[0] == b[0] else (c[0], a[1]))
    return out + [shifted[-1][1]]


def path_d(points):
    return ' '.join([f'M{points[0][0]:.1f},{points[0][1]:.1f}'] +
                    [f'L{x:.1f},{y:.1f}' for x, y in points[1:]])


class OrthogonalRouter:
    """Rectilinear visibility grid with bus/symbol obstacles and reserved lanes.

    Route a *bundle* centreline. Parallel overlap is forbidden; perpendicular
    crossings are expensive. Endpoints escape vertically through their own bay
    before joining the routing grid. Row spacing is allocated by the caller.
    """
    def __init__(self, pos, half, endpoints, extra_obstacles=(), min_route_y=None):
        self.min_route_y = min_route_y
        self.rects = [(x - half(n) - 20, y - 40, x + half(n) + 20, y + 64)
                      for n, (x, y) in pos.items()] + list(extra_obstacles)
        self.used = []
        self.soft_bands = []
        self.forbidden_runs = []
        xs = {round(x, 3) for x, y in endpoints}
        ys = {round(y, 3) for x, y in endpoints}
        for l, t, r, b in self.rects:
            xs.update((l - 24, r + 24))
            ys.update((t - 12, b + 16))
        lo, hi = min(xs) - 96, max(xs) + 96
        # Outer channels are distinct lanes, not one shared vertical trunk.
        for i in range(1, len(endpoints) // 2 + 2):
            xs.update((lo - i * CHANNEL_PITCH, hi + i * CHANNEL_PITCH))
        ylo, yhi = min(ys) - 100, max(ys) + 100
        ys.update((ylo, yhi))
        base = sorted(ys)
        for a, b in zip(base, base[1:]):
            k = 1
            while a + k * CHANNEL_PITCH < b:
                ys.add(a + k * CHANNEL_PITCH)
                k += 1
        if min_route_y is not None:
            # Generator symbols occupy the space above the highest bus row.
            # Transmission routing must stay below that hierarchy boundary.
            ys = {y for y in ys if y >= min_route_y} | {round(y, 3) for x, y in endpoints}
        self.xs, self.ys = sorted(xs), sorted(ys)
        self.blocked = set()
        for i, x in enumerate(self.xs):
            for j, y in enumerate(self.ys):
                if any(l < x < r and t < y < b for l, t, r, b in self.rects):
                    self.blocked.add((i, j))
        self.base_clear = {}

    def _clear(self, a, b):
        key = tuple(sorted((a, b)))
        if key not in self.base_clear:
            x1, y1 = a
            x2, y2 = b
            self.base_clear[key] = not any(
                (l < x1 < r and max(min(y1, y2), t) < min(max(y1, y2), bot))
                if x1 == x2 else
                (t < y1 < bot and max(min(x1, x2), l) < min(max(x1, x2), r))
                for l, t, r, bot in self.rects)
        return self.base_clear[key]

    def _cost(self, a, b):
        vertical = a[0] == b[0]
        if not vertical and any(bottom <= a[1] <= top and
                max(min(a[0], b[0]), left) < min(max(a[0], b[0]), right)
                for left, right, bottom, top in self.forbidden_runs):
            return None
        axis = 0 if vertical else 1
        span = 1 - axis
        low, high = sorted((a[span], b[span]))
        penalty = 0
        for c, d in self.used:
            other_vertical = c[0] == d[0]
            if vertical == other_vertical:
                # Reserve enough centreline clearance for the outer wires of
                # neighbouring two-conductor bundles (14-unit wire pitch).
                # Spans that merely touch (share one endpoint) still collide
                # once each bundle's own +/-7 wire offset is applied, so the
                # overlap test must not require strictly interior overlap.
                if (abs(a[axis] - c[axis]) < 32 and
                        max(low, min(c[span], d[span])) <= min(high, max(c[span], d[span])) + 0.01):
                    return None
                gap = max(low, min(c[span], d[span])) - min(high, max(c[span], d[span]))
                # <= CHANNEL_PITCH (not strictly less): a route sitting exactly
                # at the minimum legal clearance is still a near-continuation
                # risk for two long, unrelated parallel runs and must not be
                # the router's zero-penalty default.
                if abs(a[axis] - c[axis]) <= CHANNEL_PITCH and 0 <= gap < BUNDLE_CLEAR:
                    penalty += COLLINEAR_TOUCH_PENALTY
            elif (low - 0.01 <= c[span] <= high + 0.01 and
                  min(c[axis], d[axis]) <= a[axis] <= max(c[axis], d[axis])):
                # A crossing near another route's bend looks like a junction.
                near_bend = min(abs(a[axis] - c[axis]), abs(a[axis] - d[axis])) < 20
                penalty += 1200 if near_bend else 180
        for c, d in self.soft_bands:
            # Deliberately CHANNEL_PITCH, not NEAR_CONT_GAP: widening this to 40
            # re-routes fixtures that already satisfy the invariant (SS_KSGHN
            # regressed) for no net gain. The band WIDTH is widened instead --
            # see NEAR_CONT_GAP in route_bundles.
            if not vertical and abs(a[1] - c[1]) < CHANNEL_PITCH and max(low, c[0]) < min(high, d[0]):
                penalty += COLLINEAR_TOUCH_PENALTY
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + penalty

    def route(self, start, end):
        # Reserved trunks create new usable lanes. Without these coordinates,
        # a valid 32-unit gap can be absent from the original visibility grid.
        additions = {a[1] + off for a, b in self.used if a[1] == b[1]
                     for off in (-CHANNEL_PITCH, CHANNEL_PITCH)} - set(self.ys)
        if self.min_route_y is not None:
            additions = {y for y in additions if y >= self.min_route_y}
        x_additions = {a[0] + off for a, b in self.used if a[0] == b[0]
                       for off in (-CHANNEL_PITCH, CHANNEL_PITCH)} - set(self.xs)
        if additions or x_additions:
            self.ys = sorted(set(self.ys) | additions)
            self.xs = sorted(set(self.xs) | x_additions)
            self.blocked = {(i, j) for i, x in enumerate(self.xs)
                            for j, y in enumerate(self.ys)
                            if any(l < x < r and t < y < b for l, t, r, b in self.rects)}
        start = tuple(round(v, 3) for v in start)
        end = tuple(round(v, 3) for v in end)
        si = (self.xs.index(start[0]), self.ys.index(start[1]))
        ei = (self.xs.index(end[0]), self.ys.index(end[1]))
        sequence = count()
        heap = [(0, next(sequence), (*si, 1))]
        dist = {(*si, 1): 0}
        prev = {}
        costs = {}
        goal = None
        while heap:
            _, _, state = heappop(heap)
            i, j, direction = state
            if (i, j) == ei:
                goal = state
                break
            a = self.xs[i], self.ys[j]
            for ni, nj, nd in ((i - 1, j, 0), (i + 1, j, 0), (i, j - 1, 1), (i, j + 1, 1)):
                if not (0 <= ni < len(self.xs) and 0 <= nj < len(self.ys)):
                    continue
                if (ni, nj) in self.blocked:
                    continue
                b = self.xs[ni], self.ys[nj]
                key = tuple(sorted((a, b)))
                if key not in costs:
                    costs[key] = self._cost(a, b) if self._clear(a, b) else None
                cost = costs[key]
                if cost is None:
                    continue
                new = dist[state] + cost + (48 if nd != direction else 0)
                target = ni, nj, nd
                if new >= dist.get(target, float('inf')):
                    continue
                dist[target] = new
                prev[target] = state
                h = abs(b[0] - end[0]) + abs(b[1] - end[1])
                heappush(heap, (new + h, next(sequence), target))
        if goal is None:
            raise ValueError(f'No clear SLD channel from {start} to {end}')
        points = []
        while goal is not None:
            points.append((self.xs[goal[0]], self.ys[goal[1]]))
            goal = prev.get(goal)
        return simplify(list(reversed(points)))

    def reserve(self, points):
        self.used.extend(zip(points, points[1:]))


def _near_continuations(points, offsets, other_points, other_offsets):
    """Indices of complete horizontal runs ambiguous after wire offsets.

    Check the emitted one-decimal geometry, not visibility-grid fragments.
    Shared-bus connections are excluded by the caller.
    """
    bad = set()
    for offset in offsets:
        wire = [(round(x, 1), round(y, 1)) for x, y in offset_path(points, offset)]
        for other_offset in other_offsets:
            other = [(round(x, 1), round(y, 1)) for x, y in offset_path(other_points, other_offset)]
            for i, (a, b) in enumerate(zip(wire, wire[1:])):
                if a[1] != b[1] or abs(a[0] - b[0]) <= 120:
                    continue
                for c, d in zip(other, other[1:]):
                    if c[1] != d[1] or abs(c[0] - d[0]) <= 120:
                        continue
                    gap = max(min(a[0], b[0]), min(c[0], d[0])) - min(max(a[0], b[0]), max(c[0], d[0]))
                    if 0 <= gap < NEAR_CONT_GAP and abs(a[1] - c[1]) < NEAR_CONT_GAP:
                        bad.add(i)
    return bad


def route_bundles(pos, half, specs, extra_obstacles=(), min_route_y=None, wire_offsets=None):
    """Negotiate scarce channels: retry a blocked bundle before earlier routes.

    Greedy shortest-first routing alone can seal a later port, particularly
    after manual positioning. Rerouting releases those earlier reservations;
    it never relaxes the no-overlap or bus-obstacle constraints.
    """
    endpoints = [pt for _, _, start, end, _ in specs for pt in (start, end)]
    wire_offsets = wire_offsets or {c.id: [0] for c, *_ in specs}
    incident = {c.id: {c.from_substation_id, c.to_substation_id} for c, *_ in specs}
    order = list(specs)
    tried = set()
    last_error = None
    for _ in range(max(1, len(specs))):
        signature = tuple(c.id for c, *_ in order)
        if signature in tried:
            break
        tried.add(signature)
        router = OrthogonalRouter(pos, half, endpoints, extra_obstacles,
                                  min_route_y=min_route_y)
        results = {}
        for spec in order:
            c, first, start, end, last = spec
            committed = list(router.used)
            router.soft_bands = []
            router.forbidden_runs = []
            for other, ofirst, ostart, oend, olast in specs:
                if other.id == c.id:
                    continue
                osafe = (ostart[0], ostart[1] + (32 if ostart[1] > ofirst[1] else -32))
                esafe = (oend[0], oend[1] + (32 if oend[1] > olast[1] else -32))
                router.used.extend(((ofirst, osafe), (esafe, olast)))
                if other.id not in results and ostart[0] != oend[0]:
                    middle = (ostart[1] + oend[1]) / 2
                    left, right = sorted((ostart[0], oend[0]))
                    # Widen the discouraged band past the other route's own span.
                    # Two long horizontal runs that merely sit end-to-end at a
                    # similar height read as ONE conductor even though they never
                    # overlap in x -- the same "near-continuation" the geometry
                    # invariant rejects. NEAR_CONT_GAP mirrors that threshold so
                    # the router avoids the band instead of being corrected later.
                    router.soft_bands.append(((left - NEAR_CONT_GAP, middle),
                                              (right + NEAR_CONT_GAP, middle)))
            try:
                for attempt in range(16):
                    points = simplify([tuple(round(v, 3) for v in pt)
                                       for pt in [first] + router.route(start, end) + [last]])
                    bad = set()
                    for other_id, other_points in results.items():
                        if incident[c.id] & incident[other_id]:
                            continue
                        bad.update(_near_continuations(points, wire_offsets[c.id],
                                                      other_points, wire_offsets[other_id]))
                    if not bad:
                        break
                    for i in bad:
                        a, b = points[i:i + 2]
                        # Ban only the ambiguous horizontal corridor for this
                        # route. Reserve nothing until its full wires pass.
                        router.forbidden_runs.append((min(a[0], b[0]), max(a[0], b[0]),
                                                      a[1] - CHANNEL_PITCH, a[1] + CHANNEL_PITCH))
                else:
                    raise ValueError('No unambiguous horizontal SLD channel')
            except ValueError as exc:
                last_error = ValueError(f'{c.code}: {exc}')
                order = [spec] + [s for s in order if s[0].id != c.id]
                break
            router.used = committed
            router.reserve(points)
            results[c.id] = points
        else:
            return results
    raise last_error or ValueError('No clear SLD routing')
