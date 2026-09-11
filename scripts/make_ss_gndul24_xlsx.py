"""samples/ss_gndul24_ingest.xlsx -- Subsistem Gandul 2,4 (UP2B Jakarta & Banten).

Source: Buku Kerawanan SJB 2026 Sec 2.13, Gambar 2.12 (Peta Kerawanan, PDF
p.107) and Tabel 2.11 (PDF p.108-110). The per-subsistem Peta Kerawanan is the
trace source here rather than Lampiran-1: it already carries the tier bands, the
bay stubs and the risk pin, and is far more legible than the whole-region sheet.

Smallest subsistem in the book -- one injection, one risk:
GITET Gandul 500 kV -> IBT 2,4 -> GNDUL Tier-1, with SWGAN and CRNDE drawn as
bay stubs off Tier-1. Tier-2 is PNDAH and KMANG (KMANG has a bus coupler),
Tier-3 is ASARI plus the KTT-owned SAMBAS/CSW pair drawn inside an "Aset milik
KTT" box.

The single kerawanan is the SKTT 150 kV Gandul-Kemang nominal current (634 A
derating to 500 A), so it pins to the GNDUL-KMANG ruas.

Run: python scripts/make_ss_gndul24_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "DKI Jakarta"

ASSETS = [
    dict(code="GNDUL7", name="GITET Gandul", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 2 GNDUL7", name="IBT 2,4 Gandul 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="GNDUL7", bus_lv="GNDUL", trafo=2,
         simbol="2 IBT (unit 2,4)"),
    dict(code="GNDUL", name="Gandul (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section + kopel"),
    dict(code="PNDAH", name="Pondok Indah", type="Busbar GI", tier=2),
    dict(code="KMANG", name="Kemang", type="Busbar GI", tier=2,
         simbol="bus coupler", kerawanan="1"),
    dict(code="ASARI", name="Asari", type="Busbar GI", tier=3),
    # Aset milik KTT (customer-owned), drawn inside its own box on Gambar 2.12.
    dict(code="SAMBAS", name="Sambas (aset milik KTT)", type="Busbar GI", tier=3,
         simbol="aset milik KTT"),
    dict(code="CSW", name="CSW (aset milik KTT)", type="Busbar GI", tier=4,
         simbol="aset milik KTT"),
]

# Bay stubs hanging off Tier-1 GNDUL on Gambar 2.12.
BAYS = [
    ("SWGAN", "Sawangan", "GNDUL", None),
    ("CRNDE", "Cirande", "GNDUL", None),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("GNDUL", "PNDAH", "SUTT Gandul - Pondok Indah", 1, 2),
    # kerawanan #1: SKTT 150 kV Gandul-Kemang, I nominal 634 A derating ke 500 A
    L("GNDUL", "KMANG", "SKTT 150 kV Gandul - Kemang", 1, 2, kno="1"),
    L("KMANG", "ASARI", "SUTT Kemang - Asari", 2, 3),
    L("PNDAH", "SAMBAS", "SUTT Pondok Indah - Sambas (aset milik KTT)", 2, 3),
    L("SAMBAS", "CSW", "SUTT Sambas - CSW (aset milik KTT)", 3, 4, sirkit=1),
]

SPEC = dict(
    code="SS_GNDUL24",
    name="Gandul 2,4",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.13 (Tabel 2.11, PDF p.108-110); "
               "topologi dari Gambar 2.12 Peta Kerawanan Subsistem Gandul 2,4 (PDF p.107)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(108, 110, expected=1),
)

if __name__ == "__main__":
    build_workbook(SPEC)
