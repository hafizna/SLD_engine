"""Electrical behavior through parse -> draft -> publish -> API graph -> SLD."""
import json
import subprocess
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base, upgrade_bus_section_schema
from app.models import AnalyticalView, Bay, Circuit, Device, Substation
from app.services.bus_sections import electrical_graph, simulate_connectivity, electrical_tiers
from app.services.ingest_parser import normalise, IngestParseError
from app.services import ingest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def section_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
    engine.dispose()


def payload(state='OPEN'):
    return normalise({
        'subsystem': {'code': 'SS_SECTIONS', 'name': 'Section test'},
        'objects': [
            {'external_key': 'SRC', 'raw_label': 'Source', 'tier_hint': 1, 'voltage_hv_kv': 150},
            {'external_key': 'SPLIT', 'raw_label': 'Sectioned GI', 'tier_hint': 2,
             'voltage_hv_kv': 150, 'bus_sections': ['A', 'B']},
            {'external_key': 'LOAD', 'raw_label': 'Load GI', 'tier_hint': 3, 'voltage_hv_kv': 150},
        ],
        'connections': [
            {'from_external_key': 'SRC', 'to_external_key': 'SPLIT', 'to_bus_section': 'A', 'circuit_count': 1, 'confidence': 1},
            {'from_external_key': 'SPLIT', 'to_external_key': 'LOAD', 'from_bus_section': 'B', 'circuit_count': 1, 'confidence': 1},
            {'from_external_key': 'SPLIT', 'to_external_key': 'SPLIT',
             'from_bus_section': 'A', 'to_bus_section': 'B',
             'circuit_type_hint': 'BUS_COUPLER', 'switch_state': state,
             'unit_no': 'KOP1', 'circuit_count': 1, 'confidence': 1},
        ],
        'risks': [{'seq_no': 1, 'pin_kind': 'CIRCUIT', 'pin_key': 'SPLIT-SPLIT:KOP1'}],
    })


def publish(db, data):
    draft = ingest.build_draft(db, data)
    for n in draft['nodes']:
        n['resolution'] = 'NEW'
    assert ingest.validate(db, draft)['ok']
    result = ingest.publish(db, draft, data['subsystem']['code'], data['subsystem']['name'], None, None)
    return db.get(AnalyticalView, result['view_id'])


def test_open_coupler_does_not_join_sections_or_fake_two_gis(section_db):
    db = section_db
    view = publish(db, payload())
    graph = electrical_graph(db, view)
    result = simulate_connectivity(graph)
    assert result['complete']
    keys = {(n['substation_id'], n['section_name']): n['key'] for n in graph['nodes']}
    split = db.query(Substation).filter_by(code='SPLIT').one()
    load = db.query(Substation).filter_by(code='LOAD').one()
    assert keys[(split.id, 'A')] in result['reached']
    assert keys[(split.id, 'B')] in result['unreached']
    assert keys[(load.id, None)] in result['unreached']
    assert db.query(Substation).count() == 3
    assert db.query(Device).one().normal_state == 'OPEN'
    assert all(b.bus_section_id for b in db.query(Bay).all())
    assert ('SUBSTATION', load.id) not in electrical_tiers(graph)


def test_closing_coupler_changes_reachability_without_changing_source(section_db):
    db = section_db
    view = publish(db, payload())
    graph = electrical_graph(db, view)
    coupler = db.query(Circuit).filter_by(circuit_type='BUS_COUPLER').one()
    closed = simulate_connectivity(graph, switch_overrides={coupler.id: 'CLOSED'})
    assert not closed['unreached']
    assert coupler.switch_state == 'OPEN'
    reopened = simulate_connectivity(graph)
    assert len(reopened['unreached']) == 2
    feeder = db.query(Circuit).filter(Circuit.to_substation_id == db.query(Substation).filter_by(code='SPLIT').one().id,
                                      Circuit.circuit_type != 'BUS_COUPLER').one()
    failed = simulate_connectivity(graph, switch_overrides={coupler.id: 'CLOSED'}, removed_edges=[feeder.id])
    assert len(failed['unreached']) == 3


@pytest.mark.parametrize('field,value', [('from_bus_section', 'X'), ('to_bus_section', 'A'), ('switch_state', 'maybe')])
def test_invalid_coupler_is_rejected(field, value):
    # API fixtures reload parser modules; use the currently active exception class.
    from app.services.ingest_parser import IngestParseError
    data = payload()
    data['connections'][-1][field] = value
    with pytest.raises(IngestParseError):
        normalise(data)


def test_unassigned_terminal_and_unknown_position_are_explicit(section_db):
    data = payload('UNKNOWN')
    data['connections'][0]['to_bus_section'] = None
    db = section_db
    draft = ingest.build_draft(db, data)
    check = ingest.validate(db, draft)
    assert check['ok'] and not check['connectivity_complete']
    assert len(check['warnings']) == 2
    view = publish(db, data)
    graph = electrical_graph(db, view)
    assert not graph['complete']
    assert simulate_connectivity(graph)['complete'] is False


def test_svg_renders_separate_bars_switch_and_risk_pin(section_db):
    from app.services.sld_renderer import render_view_svg
    from xml.etree import ElementTree as ET
    view = publish(section_db, payload())
    svg = ET.fromstring(render_view_svg(section_db, view))
    assert len([n for n in svg.iter() if n.get('class') == 'bus-section']) == 2
    couplers = [n for n in svg.iter() if n.get('class') == 'bus-coupler']
    assert len(couplers) == 1 and couplers[0].get('data-switch-state') == 'OPEN'
    assert any(n.get('data-risk-seqs') == '1' for n in svg.iter())


def test_existing_database_migration_keeps_data_and_is_idempotent():
    from sqlalchemy import text, inspect
    engine = create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE circuit (id INTEGER PRIMARY KEY, name TEXT)'))
        conn.execute(text("INSERT INTO circuit VALUES (1, 'existing')"))
        conn.execute(text('CREATE TABLE generating_unit (id INTEGER PRIMARY KEY)'))
    upgrade_bus_section_schema(engine)
    upgrade_bus_section_schema(engine)
    assert {'from_bus_section_id', 'to_bus_section_id', 'switch_state'} <= {c['name'] for c in inspect(engine).get_columns('circuit')}
    with engine.connect() as conn:
        assert conn.execute(text('SELECT name FROM circuit WHERE id=1')).scalar() == 'existing'


def test_browser_and_backend_simulation_agree(section_db):
    db = section_db
    view = publish(db, payload())
    graph = electrical_graph(db, view)
    coupler = db.query(Circuit).filter_by(circuit_type='BUS_COUPLER').one()
    html = (ROOT / 'app/static/index.html').read_text(encoding='utf-8')
    js = html.split('// BEGIN ELECTRICAL REACHABILITY')[1].split('// END ELECTRICAL REACHABILITY')[0]
    js = js[js.index('function electricalReach'):]
    script = js + '\nconst graph = ' + json.dumps(graph) + ';\n'
    script += f'console.log(JSON.stringify(electricalReach(graph, [], {{{coupler.id}: "CLOSED"}})));'
    browser = json.loads(subprocess.check_output(['node', '-e', script], text=True))
    backend = simulate_connectivity(graph, switch_overrides={coupler.id: 'CLOSED'})
    assert set(browser['reached']) == set(backend['reached'])
    assert set(browser['unreached']) == set(backend['unreached'])


def test_section_port_layout_is_generic_and_independent_of_absolute_position():
    from app.services.sld_layout import section_port_layout
    terminals = [
        {'key': 'p1', 'section_id': 10, 'side': -1, 'order': 300},
        {'key': 'p2', 'section_id': 10, 'side': -1, 'order': 100},
        {'key': 'p3', 'section_id': 20, 'side': 1, 'order': 0},
        {'key': 'p4', 'section_id': None, 'side': -1, 'order': 0},
    ]
    spans, ports = section_port_layout(300, [10, 20, 30], terminals)
    assert ports['p2'] < ports['p1']  # order follows opposite buses
    assert set(spans) == {10, 20, 30, None}
    for t in terminals:
        lo, hi = spans[t['section_id']]
        assert lo < ports[t['key']] < hi
    for center in (0, 750, 10000):
        for t in terminals:
            lo, hi = spans[t['section_id']]
            assert center+lo < center+ports[t['key']] < center+hi


def test_krian_fixture_sections_and_incomplete_sawahan_are_preserved(section_db):
    from app.services.ingest_parser import parse_upload
    from app.services.sld_renderer import render_view_svg
    from scripts.audit_sample_workbooks import GEOMETRY_ERRORS
    path = ROOT / 'samples/ss_krian12_gresik_ingest.xlsx'
    data = parse_upload(path.read_bytes(), path.name)
    draft = ingest.build_draft(section_db, data)
    warnings = ingest.validate(section_db, draft)['warnings']
    assert len(warnings) == 5 and all('SWHAN' in w for w in warnings)
    view = publish(section_db, data)
    graph = electrical_graph(section_db, view)
    assert not graph['complete']
    assert len(graph['nodes']) == 50  # 47 GI nodes + three extra section vertices
    assert section_db.query(Circuit).filter_by(circuit_type='BUS_COUPLER').count() == 3
    assert section_db.query(Substation).count() == 47  # generator is separate
    assert not GEOMETRY_ERRORS(render_view_svg(section_db, view))
