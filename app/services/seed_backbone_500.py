"""Seed: 500 kV backbone (SUTET) risk view -- BACKBONE_500.

Source: Buku Kerawanan SJB 2026, Tabel 1.1.A (Kerawanan SUTET 500 kV N-1,
N-2, N-1 N-2 -- points 1-31) and Gambar 1.4 (Peta Kerawanan SUTET 500 kV).

The data lives in `samples/backbone_500_ingest.xlsx` (built by
`scripts/make_backbone_500_xlsx.py` straight from the kerawanan table). This
seeder just runs that workbook through the same ingest path a user would --
parse -> build_draft -> materialise -- so there is ONE source of truth.

*** STRESS-TEST FIXTURE for the layout engine: ~46 GITET across 6 Tier
bands, a mesh of 55 SUTET with many Timur-Barat crossings, a generating
unit on every Tier-1 GITET. NOT wired into seed.py. ***

Relations are read from the kerawanan TABLE, not guessed from the crossing
lines in the figure. GITET codes match the figure's labels; the figure only
fixes each GITET's Tier band.
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

_XLSX = Path(__file__).resolve().parents[2] / "samples" / "backbone_500_ingest.xlsx"


def seed_backbone_500(db: Session) -> dict:
    """Materialise the backbone 500 kV fixture from the ingest workbook.
    Returns the publish result ({subsystem_code, view_id, ...})."""
    from app.models import Subsystem
    if db.query(Subsystem).filter(Subsystem.code == "BACKBONE_500_JB").first():
        return {"subsystem_code": "BACKBONE_500_JB", "already": True}

    from app.services import ingest, ingest_parser

    payload = ingest_parser.parse_upload(_XLSX.read_bytes(), _XLSX.name)
    draft = ingest.build_draft(db, payload)
    # A 500 kV GITET and its 150 kV GI may share the short label used in the
    # book (for example CWANG).  They are different canonical substations.
    # Prefix the canonical GITET code so a previously seeded 150 kV GI cannot
    # donate its voltage, transformer, or capacitor attributes to this view.
    for n in draft["nodes"]:
        n["resolution"] = "NEW"
        n["confirmed_code"] = (
            f"GITET_{n['external_key']}"
            if n.get("object_type") in ("GITET", "GISTET")
            else n["external_key"]
        )
    return ingest.publish(
        db, draft,
        code="BACKBONE_500_JB",
        name="Backbone 500 kV Jawa-Madura-Bali",
        effective_date="2026-06-30",
        apb="UIP2B JAMALI",
    )
