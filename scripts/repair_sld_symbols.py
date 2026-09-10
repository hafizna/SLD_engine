"""Repair missing legacy ingest symbol flags from reviewed PLN references.

Print the exact field diff by default. --apply backs up SQLite before applying
only the listed symbol fields. Connectivity, Tier and operating state are not
part of this repair. Existing nonempty notes are kept after the correction.
"""
import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=ROOT / 'mantaps.db')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    payload = json.loads((ROOT / 'samples/sld_symbol_corrections.json').read_text(encoding='utf-8'))
    conn = sqlite3.connect(args.database.resolve().as_uri() + ('?mode=rw' if args.apply else '?mode=ro'), uri=True)
    conn.row_factory = sqlite3.Row
    changes = []
    for correction in payload['substations']:
        row = conn.execute('SELECT * FROM substation WHERE code=?', (correction['code'],)).fetchone()
        if row is None:
            continue
        for field in ('has_transformer', 'has_shunt_capacitor', 'symbol_note'):
            if field not in correction:
                continue
            value = correction[field]
            if field == 'symbol_note' and row[field]:
                if value in row[field]:
                    continue
                value += ' ' + row[field]
            if row[field] != value:
                changes.append((row['code'], field, row[field], value))
    print(json.dumps(changes, indent=2, ensure_ascii=False))
    if args.apply and changes:
        backup = ROOT / '.render_tmp' / f'symbols-before-{datetime.now():%Y%m%d-%H%M%S-%f}.db'
        backup.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(backup) as target:
            conn.backup(target)
        with conn:
            for code, field, before, after in changes:
                # field is selected from the fixed allowlist above.
                conn.execute(f'UPDATE substation SET {field}=? WHERE code=?', (after, code))
        print(f'Applied {len(changes)} field corrections. Backup: {backup}')
    conn.close()


if __name__ == '__main__':
    main()
