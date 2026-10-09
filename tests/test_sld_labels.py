"""Asset names remain readable without losing their original identity."""
import xml.etree.ElementTree as ET

from app.services.sld_renderer import _plant_label


def test_long_plant_name_wraps_without_losing_words_or_shrinking():
    name = 'PLTU Celukan Bawang Unit 1-3 & Pembangkit Cadangan'
    label = ET.fromstring(_plant_label(name, 100, 50, '#C00000', code='KIT_CB'))
    lines = list(label)
    assert len(lines) > 1
    assert ' '.join(line.text for line in lines) == name
    assert all(len(line.text) <= 24 for line in lines)
    assert label.get('font-size') == '12.5'
    assert label.get('data-short-label').startswith('PLTU Celukan Bawang')
    assert float(label.get('y')) + (len(lines) - 1) * 15 == 50


def test_stub_gi_labels_have_busbar_typography_and_full_title(db):
    from app.models import AnalyticalView
    from app.services.sld_renderer import render_view_svg
    ns = {'s': 'http://www.w3.org/2000/svg'}
    labels = []
    for view in db.query(AnalyticalView).all():
        root = ET.fromstring(render_view_svg(db, view))
        for group in root.findall('.//s:g[@id="bays"]/s:g', ns):
            label = group.find('s:text', ns)
            if label is None or 'gi-label' not in label.get('class', ''):
                continue
            labels.append(label)
            assert label.get('font-size') == '12.5'
            assert label.get('font-weight') == '700'
            assert group.find('s:title', ns).text
    assert labels, 'Expected actual stub GI labels in the seeded fixture'
