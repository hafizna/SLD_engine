"""Optional section-level connectivity; physical GI identity never changes.

Unassigned terminals and unknown switch positions are reported explicitly.
They must not be used as a shortcut joining sections of the same GI.
"""
from collections import defaultdict, deque

from app.models import BusSection

SWITCH_TYPES = {'BUS_COUPLER', 'BUS_TIE'}
SWITCH_STATES = {'OPEN', 'CLOSED', 'UNKNOWN'}


def draft_section_problems(nodes, edges):
    by_key = {n['external_key']: n for n in nodes}
    problems, warnings = [], []
    for n in nodes:
        sections = n.get('bus_sections') or []
        if not isinstance(sections, list) or any(not isinstance(s, str) or not s.strip() for s in sections):
            problems.append(f"{n['external_key']}: seksi bus harus daftar nama")
        elif len(set(sections)) != len(sections):
            problems.append(f"{n['external_key']}: seksi bus ganda")
        if sections and (n.get('object_type') == 'GENERATING_UNIT' or n.get('is_bay')):
            problems.append(f"{n['external_key']}: seksi bus hanya untuk GI busbar")
        outlet = n.get('outlet_bus_section')
        if outlet and outlet not in (by_key.get(n.get('outlet_key'), {}).get('bus_sections') or []):
            problems.append(f"{n['external_key']}: seksi outlet pembangkit tidak dikenal")
    for e in edges:
        label = f"{e['from_key']}-{e['to_key']}:{e.get('unit_no') or ''}"
        ct = e.get('circuit_type_hint') or e.get('circuit_type')
        switch = ct in SWITCH_TYPES
        for side in ('from', 'to'):
            k = e[f'{side}_key']
            section = e.get(f'{side}_bus_section')
            sections = by_key.get(k, {}).get('bus_sections') or []
            if section and section not in sections:
                problems.append(f"{label}: seksi {side} {section} tidak dideklarasikan di {k}")
            elif sections and not section:
                warnings.append(f"{label}: terminal {k} belum dipetakan ke seksi bus; simulasi belum lengkap")
        if switch:
            if e['from_key'] != e['to_key']:
                problems.append(f"{label}: kopel bus harus di dalam satu GI")
            if not e.get('unit_no'):
                problems.append(f"{label}: kopel wajib memiliki ID unik")
            if not e.get('from_bus_section') or not e.get('to_bus_section') or e.get('from_bus_section') == e.get('to_bus_section'):
                problems.append(f"{label}: kopel harus menghubungkan dua seksi berbeda")
            state = e.get('switch_state') or 'UNKNOWN'
            if state not in SWITCH_STATES:
                problems.append(f"{label}: status kopel harus OPEN/CLOSED/UNKNOWN")
            elif state == 'UNKNOWN':
                warnings.append(f"{label}: posisi kopel belum diketahui; simulasi belum lengkap")
        elif e.get('switch_state') is not None:
            problems.append(f"{label}: switch_state hanya untuk kopel/tie bus")
        elif e['from_key'] == e['to_key']:
            problems.append(f"{label}: self-link hanya diperbolehkan untuk kopel antar seksi")
    return problems, warnings


def section_inventory(db, sub_ids):
    by_sub = defaultdict(list)
    if sub_ids:
        for s in db.query(BusSection).filter(BusSection.substation_id.in_(sub_ids), BusSection.active.is_(True)).all():
            by_sub[s.substation_id].append(s)
    for sections in by_sub.values():
        sections.sort(key=lambda s: (s.bus_order or 0, s.name, s.id))
    return by_sub


def electrical_graph(db, view, *, physical_graph=None):
    from app.services.topology import get_view_graph, _is_live
    physical_graph = physical_graph or get_view_graph(db, view)
    nodes, edges, roles, seeds, _ = physical_graph
    subs = {k[1]: s for k, s in nodes.items() if k[0] == 'SUBSTATION'}
    sections = section_inventory(db, set(subs))
    vertices, endpoints, issues = {}, {}, []
    for sid, s in subs.items():
        for section in sections.get(sid) or [None]:
            key = f'B:{section.id}' if section else f'S:{sid}'
            vertices[key] = {'key': key, 'substation_id': sid,
                             'bus_section_id': section.id if section else None,
                             'section_name': section.name if section else None,
                             'status': s.status}
    by_id = {s.id: s for group in sections.values() for s in group}

    def terminal(sid, section_id, label):
        if section_id:
            section = by_id.get(section_id)
            if not section or section.substation_id != sid:
                issues.append(f'{label}: seksi endpoint tidak sesuai GI')
                return None
            return f'B:{section_id}'
        if sections.get(sid):
            issues.append(f'{label}: terminal seksi bus belum dipetakan')
            return None
        return f'S:{sid}'

    links = []
    for c in edges:
        a = terminal(c.from_substation_id, c.from_bus_section_id, c.code + ' dari')
        b = terminal(c.to_substation_id, c.to_bus_section_id, c.code + ' ke')
        endpoints[c.id] = (a, b)
        if c.circuit_type in SWITCH_TYPES and c.switch_state not in {'OPEN', 'CLOSED'}:
            issues.append(f'{c.code}: posisi kopel UNKNOWN')
        links.append({'id': c.id, 'from_key': a, 'to_key': b,
                      'circuit_type': c.circuit_type, 'switch_state': c.switch_state,
                      'status': c.status, 'circuit_count': c.circuit_count or 1,
                      'single_phi': c.single_phi})
    electrical_seeds = set()
    for kind, sid in seeds:
        if kind != 'SUBSTATION' or sid not in subs:
            continue
        if not sections.get(sid):
            electrical_seeds.add(f'S:{sid}')
        else:
            # A sectioned source needs an actual injection terminal; GI role
            # alone must not energize every section across an open coupler.
            source_terms = set()
            for c in edges:
                if c.circuit_type == 'IBT_LINK' and c.to_substation_id == sid:
                    source_terms.add(endpoints[c.id][1])
            for (k, _gid), g in nodes.items():
                if k == 'GENERATING_UNIT' and g.outlet_substation_id == sid and _is_live(g.status):
                    source_terms.add(terminal(sid, g.outlet_bus_section_id, g.code))
            source_terms.discard(None)
            if not source_terms:
                issues.append(f'{subs[sid].code}: terminal sumber pada seksi bus belum ditetapkan')
            electrical_seeds.update(source_terms)
    return {'nodes': list(vertices.values()), 'edges': links,
            'seeds': sorted(electrical_seeds), 'complete': not issues,
            'issues': list(dict.fromkeys(issues))}


def simulate_connectivity(graph, *, removed_edges=(), switch_overrides=None):
    """Read-only reachability scenario; UNKNOWN/incomplete never gives a verdict."""
    overrides = switch_overrides or {}
    edge_map = {e['id']: e for e in graph['edges']}
    for cid, state in overrides.items():
        if cid not in edge_map or edge_map[cid]['circuit_type'] not in SWITCH_TYPES or state not in {'OPEN', 'CLOSED'}:
            raise ValueError('override harus menunjuk kopel dengan posisi OPEN/CLOSED')
    if not graph['complete']:
        return {'complete': False, 'issues': graph['issues'], 'reached': [], 'unreached': []}
    live = {n['key'] for n in graph['nodes'] if n['status'] in {'ENERGIZED', 'OWNED_BY_CUSTOMER'}}
    adj = defaultdict(set)
    for e in graph['edges']:
        if e['id'] in removed_edges or e['status'] not in {'ENERGIZED', 'OWNED_BY_CUSTOMER'}:
            continue
        if e['circuit_type'] in SWITCH_TYPES and overrides.get(e['id'], e['switch_state']) != 'CLOSED':
            continue
        a, b = e['from_key'], e['to_key']
        if a in live and b in live:
            adj[a].add(b)
            adj[b].add(a)
    reached = set(graph['seeds']) & live
    queue = deque(reached)
    while queue:
        for neighbour in adj[queue.popleft()] - reached:
            reached.add(neighbour)
            queue.append(neighbour)
    return {'complete': True, 'issues': [], 'reached': sorted(reached),
            'unreached': sorted(live - reached)}


def electrical_tiers(graph):
    """0-cost internal couplers, 1-hop external circuits; no GI shortcuts."""
    if not graph['complete']:
        return {}
    owners = {n['key']: n['substation_id'] for n in graph['nodes']}
    live = {n['key'] for n in graph['nodes'] if n['status'] in {'ENERGIZED', 'OWNED_BY_CUSTOMER'}}
    adj = defaultdict(list)
    for e in graph['edges']:
        if e['status'] not in {'ENERGIZED', 'OWNED_BY_CUSTOMER'} or e['from_key'] not in live or e['to_key'] not in live:
            continue
        if e['circuit_type'] in SWITCH_TYPES and e['switch_state'] != 'CLOSED':
            continue
        cost = 0 if owners[e['from_key']] == owners[e['to_key']] else 1
        adj[e['from_key']].append((e['to_key'], cost))
        adj[e['to_key']].append((e['from_key'], cost))
    distance = {k: 1 for k in graph['seeds'] if k in live}
    queue = deque(distance)
    while queue:
        u = queue.popleft()
        for v, cost in adj[u]:
            candidate = distance[u] + cost
            if candidate < distance.get(v, float('inf')):
                distance[v] = candidate
                (queue.appendleft if cost == 0 else queue.append)(v)
    out = {}
    for key, value in distance.items():
        sid = owners[key]
        out[('SUBSTATION', sid)] = min(out.get(('SUBSTATION', sid), value), value)
    return out
