"""Render a before/after review from a read-only copy of a local SQLite DB.

python scripts/review_sld.py --database mantaps.db --baseline HEAD
Open .render_tmp/sld-review/index.html. No app startup or seed runs here.
"""
import argparse
import html
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=ROOT / 'mantaps.db')
    parser.add_argument('--output', type=Path, default=ROOT / '.render_tmp/sld-review')
    parser.add_argument('--baseline', default='HEAD')
    args = parser.parse_args()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models import AnalyticalView
    from app.services.sld_renderer import render_view_svg

    # Read a consistent snapshot, never modify or seed the user's database.
    engine = create_engine('sqlite:///:memory:')
    source = sqlite3.connect(args.database.resolve().as_uri() + '?mode=ro', uri=True)
    connection = engine.raw_connection()
    try:
        source.backup(connection.driver_connection)
    finally:
        source.close()
        connection.close()
    old = types.ModuleType('baseline_sld_renderer')
    code = subprocess.run(['git', 'show', f'{args.baseline}:app/services/sld_renderer.py'],
                          cwd=ROOT, check=True, capture_output=True, encoding='utf-8').stdout
    exec(compile(code, f'{args.baseline}:app/services/sld_renderer.py', 'exec'), old.__dict__)
    args.output.mkdir(parents=True, exist_ok=True)
    panels = []
    with Session(engine) as db:
        for view in db.query(AnalyticalView).order_by(AnalyticalView.id):
            name = html.escape(view.view_key)
            before = old.render_view_svg(db, view)
            after = render_view_svg(db, view)
            stem = ''.join(c if c.isalnum() or c in '-_' else '_' for c in view.view_key)
            (args.output / f'{stem}-before.svg').write_text(before, encoding='utf-8')
            (args.output / f'{stem}-after.svg').write_text(after, encoding='utf-8')
            panels.append(f'<section><h2>{name}</h2><div class="pair">'
                          f'<article><h3>Sebelum</h3>{before}</article>'
                          f'<article><h3>Sesudah</h3>{after}</article></div></section>')
            print(view.view_key, 'rendered')
    document = '''<!doctype html><html lang="id"><meta charset="utf-8">
<title>Review generator SLD</title><style>
*{box-sizing:border-box}body{font:15px system-ui;margin:24px;color:#172b4d;background:#f1f4f8}
header{max-width:1100px;margin-bottom:24px}h1{font-size:24px}h2{font-size:18px;margin:32px 0 14px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}article{background:white;padding:16px;border:1px solid #dbe2ec;border-radius:8px;overflow:auto}
h3{font-size:14px;margin:0 0 12px}svg{width:100%;height:auto;min-width:540px}
button,select{font:inherit;padding:8px;margin-right:8px}body.large .pair{grid-template-columns:1fr}body.large svg{min-width:1200px}
@media(max-width:850px){.pair{grid-template-columns:1fr}}@media print{button{display:none}}
</style><header><h1>Review generator SLD</h1>
<p>Data yang sama, dua renderer. Bandingkan posisi GI, pasangan sirkit, port busbar, dan tap PLTD.
Celah putih pada persilangan menunjukkan ruas yang tidak tersambung.</p>
<button onclick="document.body.classList.toggle('large')">Ubah tampilan berdampingan / besar</button>
</header>''' + ''.join(panels) + '</html>'
    (args.output / 'index.html').write_text(document, encoding='utf-8')
    engine.dispose()
    print(args.output / 'index.html')


if __name__ == '__main__':
    main()
