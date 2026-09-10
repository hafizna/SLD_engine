"""Drawing inventory from explicit counts or legacy SLD symbol notes.

These are counts of symbols observed in a drawing, not inferred engineering
asset registers. No count is inferred from an MVA/MVAr rating or a GI name.
"""
import re


def symbol_count(note, kind, present):
    words = r'(?:trafo|transformers?)' if kind == 'transformer' else r'(?:kapasitor|(?:shunt\s+)?capacitors?)'
    match = re.search(r'\b(\d+)\s*(?:x\s*)?' + words + r'\b', note or '', re.I)
    return int(match.group(1)) if match else int(bool(present))


def symbol_note(node):
    parts = []
    for key, label in (('transformer_count', 'trafo'), ('capacitor_count', 'kapasitor')):
        value = node.get(key)
        if value is not None:
            if isinstance(value, bool) or int(value) != float(value) or int(value) < 0:
                raise ValueError(f'{key} harus bilangan bulat non-negatif')
            parts.append(f'{int(value)} {label}')
    if node.get('symbol_note'):
        parts.append(node['symbol_note'])
    return '; '.join(parts) or None


def capacitor_is_off(note):
    return bool(re.search(r'(kapasitor|capacitor)[^;+.]*\b(non[- ]?aktif|off|non[- ]?active)',
                          note or '', re.I))
