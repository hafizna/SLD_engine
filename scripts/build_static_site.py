"""Render every analytical view to a static bundle for GitHub Pages.

Output (default: ./site/):
    index.html                 - viewer shell (view switcher, SLD, overlays)
    data/views.json            - list of views
    data/view-<id>.json        - full graph contract per view
    data/view-<id>.svg         - starter SLD per view
    data/register.xlsx         - Corporate Topology Register export

The data is a frozen snapshot -- no live API. It mirrors how the sister
dashboard is hosted, but the topology comes from the canonical engine.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"


def build() -> None:
    # fresh in-memory-ish DB in a temp file
    tmp = tempfile.mkdtemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/snapshot.db"

    from app.db import Base, SessionLocal, engine
    from app.models import AnalyticalView
    from app.services.excel_register import export_register
    from app.services.seed import seed_demo
    from app.services.seed_backbone_500 import seed_backbone_500
    from app.services.seed_ss_cwd import seed_ss_cwd
    from app.services.seed_xlsx_fixture import seed_xlsx_fixture
    from app.services.sld_renderer import render_view_svg
    from fastapi.testclient import TestClient

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo(db)
        # SS Cawang 2,3-Depok 1 (Sec 2.7): authored via /ingest in the live
        # engine, seeded straight into the snapshot here. Kept out of seed_demo
        # so the /ingest test suite can still publish under code SS_CWD.
        seed_ss_cwd(db)
        # Give the product-level 500 kV navigation a real projection. This
        # stress fixture stays out of seed_demo while its geometry findings
        # remain visible in the workbook audit.
        seed_backbone_500(db)
        # Remaining reviewed workbook fixtures. LBK/BLL/CWD use dedicated
        # seeders above; shared physical GI rows are reused across SS.
        for name in (# UP2B Jakarta & Banten
                     "ss_dkgd_ingest.xlsx", "ss_gucl_ingest.xlsx",
                     "ss_prbc_ingest.xlsx", "ss_slcg_ingest.xlsx",
                     "ss_muarakarang_durikosambi_ingest.xlsx",
                     "ss_plbratu_ingest.xlsx", "ss_bksi_cbng_ingest.xlsx",
                     "ss_gndul24_ingest.xlsx",
                     # UP2B Jawa Barat
                     "ss_cirata_ingest.xlsx", "ss_cbatu12_dltms_ingest.xlsx",
                     "ss_tasik_ingest.xlsx", "ss_ntmbn_ingest.xlsx",
                     "ss_sktni_ingest.xlsx",
                     # UP2B Jawa Tengah & DIY
                     "ss_pmlng_ingest.xlsx", "ss_byoli_ingest.xlsx",
                     "ss_ksghn_ingest.xlsx",
                     # UP2B Jawa Timur
                     "ss_krian3456_ingest.xlsx", "ss_kediri12_ingest.xlsx",
                     "ss_paiton123_ingest.xlsx",
                     # UP2B Bali
                     "ss_bali_ingest.json"):
            seed_xlsx_fixture(db, ROOT / "samples" / name)

    from app.main import app  # imports after DB is ready

    OUT.mkdir(parents=True, exist_ok=True)
    data_dir = OUT / "data"
    data_dir.mkdir(exist_ok=True)

    with TestClient(app) as client, SessionLocal() as db:
        views = client.get("/api/views").json()
        (data_dir / "views.json").write_text(json.dumps(views, indent=2), encoding="utf-8")
        subs = client.get("/api/subsystems").json()
        (data_dir / "subsystems.json").write_text(json.dumps(subs, indent=2), encoding="utf-8")
        summary = client.get("/api/dashboard/summary").json()
        (data_dir / "dashboard-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        for v in views:
            vid = v["id"]
            graph = client.get(f"/api/views/{vid}/graph").json()
            (data_dir / f"view-{vid}.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")

            av = db.get(AnalyticalView, vid)
            (data_dir / f"view-{vid}.svg").write_text(render_view_svg(db, av), encoding="utf-8")

        export_register(db, data_dir / "register.xlsx")

    # One shell for FastAPI and the frozen snapshot prevents the product flow
    # from drifting between deployments.  The flag only changes data URLs.
    shell = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
    shell = shell.replace("<script>\nconst API", "<script>\nwindow.STATIC_SNAPSHOT = true;\nconst API", 1)
    (OUT / "index.html").write_text(shell, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    # Map backdrop: FastAPI serves it from /static, the snapshot keeps it next
    # to index.html. Absent, the map simply draws no coastline.
    outline = ROOT / "app" / "static" / "jamali_outline.json"
    if outline.exists():
        shutil.copyfile(outline, OUT / outline.name)

    print(f"static site -> {OUT}")
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(OUT)}  ({p.stat().st_size} B)")


if __name__ == "__main__":
    build()
