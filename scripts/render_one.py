"""Render one workbook to SVG/PNG so a hand edit can be checked immediately.

    python scripts/render_one.py samples/ss_pedan34_ingest.xlsx

Edit the .xlsx by hand, run this, look at the picture. Nothing is written to
the project database and no other fixture is touched: the workbook is published
into a throwaway SQLite file under .render_tmp/render-one/.

Output (per analytical view):
    .render_tmp/render-one/<CODE>_<VIEW>.svg
    .render_tmp/render-one/<CODE>_<VIEW>.png      (if PyMuPDF is installed)
    .render_tmp/render-one/index.html             (all views on one page)

It also prints the tier actually used per asset, which is the quickest way to
see whether a tier problem comes from the workbook or from the engine:

    TIER  excel=2  used=2   KNTUG        Kanetug

`excel` is the `Tier (Mulai 0)` column as parsed; `used` is what the renderer
laid out. When the two differ the engine overrode the workbook -- that is an
engine question. When they match but the picture is wrong, the workbook is
wrong and the fix belongs in the .xlsx (or in scripts/make_ss_*.py, which
regenerates it).
"""
from __future__ import annotations

import argparse
import html
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook", type=Path,
                    help="samples/ss_xxx_ingest.xlsx (or .json)")
    ap.add_argument("--output", type=Path, default=ROOT / ".render_tmp/render-one")
    ap.add_argument("--zoom", type=float, default=2.0, help="PNG scale (default 2)")
    args = ap.parse_args()

    path = args.workbook if args.workbook.is_absolute() else ROOT / args.workbook
    if not path.exists():
        print(f"tidak ada: {path}")
        return 2

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app.models import AnalyticalView, GeneratingUnit, Substation, ViewMembership
    from app.services import ingest
    from app.services.ingest_parser import parse_upload
    from app.services.sld_renderer import render_view_svg

    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / f".db-{uuid.uuid4().hex[:8]}.sqlite"

    engine = create_engine(f"sqlite:///{tmp}", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    panels: list[str] = []
    try:
        with Session() as db:
            parsed = parse_upload(path.read_bytes(), path.name)
            draft = ingest.build_draft(db, parsed)
            # A throwaway database has nothing to reconcile against, so take
            # every node as new. This mirrors scripts/audit_sample_workbooks.py.
            for node in draft["nodes"]:
                node["resolution"] = "NEW"
                node["canonical_id"] = None
                node["confirmed_code"] = node.get("confirmed_code") or node["external_key"]
                node["confirmed_name"] = node.get("confirmed_name") or node["raw_label"]

            verdict = ingest.validate(db, draft)
            if not verdict["ok"]:
                print("VALIDASI GAGAL -- perbaiki dulu isi workbook:")
                for problem in verdict["problems"]:
                    print("  -", problem)
                return 1

            ingest.publish(db, draft, parsed["subsystem"]["code"],
                           parsed["subsystem"]["name"],
                           parsed["meta"].get("effective_date"),
                           parsed["subsystem"].get("apb"))

            code = parsed["subsystem"]["code"]
            excel_tier = {o["external_key"]: o.get("tier_hint") for o in parsed["objects"]}
            names = {o["external_key"]: o["raw_label"] for o in parsed["objects"]}
            sub_code = {s.id: s.code for s in db.query(Substation).all()}
            gen_code = {g.id: g.code for g in db.query(GeneratingUnit).all()}

            print(f"\n{code}: {len(parsed['objects'])} aset, "
                  f"{len(parsed['connections'])} ruas, {len(parsed['risks'])} kerawanan")

            for view in db.query(AnalyticalView).order_by(AnalyticalView.id):
                svg = render_view_svg(db, view)
                stem = f"{code}_{view.view_key}".replace("/", "_")
                svg_path = out / f"{stem}.svg"
                svg_path.write_text(svg, encoding="utf-8")
                print(f"\n  view {view.view_key}")

                mismatched = 0
                for m in (db.query(ViewMembership)
                          .filter(ViewMembership.view_id == view.id).all()):
                    if m.node_kind == "CIRCUIT":
                        continue
                    key = (sub_code if m.node_kind == "SUBSTATION" else gen_code).get(m.node_id)
                    want = excel_tier.get(key)
                    used = m.tier_seed
                    flag = "" if want == used else "   <-- BEDA"
                    if flag:
                        mismatched += 1
                    print(f"    TIER  excel={want!s:>4}  used={used!s:>4}   "
                          f"{key!s:<12} {names.get(key, '')}{flag}")
                if mismatched:
                    print(f"    ({mismatched} aset tidak memakai tier dari Excel -- "
                          f"itu pertanyaan untuk engine, bukan workbook)")

                panels.append(
                    f"<section><h2>{html.escape(view.view_key)}</h2>{svg}</section>")
                try:
                    import fitz
                    fitz.open(str(svg_path))[0].get_pixmap(
                        matrix=fitz.Matrix(args.zoom, args.zoom)
                    ).save(str(out / f"{stem}.png"))
                except Exception:
                    pass  # PNG is a convenience; the SVG is the real output
    finally:
        engine.dispose()
        tmp.unlink(missing_ok=True)

    page = ("""<!doctype html><meta charset="utf-8"><title>Render satu workbook</title>
<style>body{font:15px system-ui;margin:24px;background:#f1f4f8;color:#172b4d}
h1{font-size:22px}h2{font-size:16px;margin:28px 0 10px}
section{background:#fff;padding:16px;border:1px solid #dbe2ec;border-radius:8px;overflow:auto}
svg{width:100%;height:auto;min-width:900px}</style>
<h1>""" + html.escape(path.name) + "</h1>" + "".join(panels))
    (out / "index.html").write_text(page, encoding="utf-8")
    print(f"\n  -> {out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
