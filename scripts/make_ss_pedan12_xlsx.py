"""samples/ss_pedan12_ingest.xlsx -- Subsistem Pedan 1,2 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.5, Gambar 4.5 (Peta Kerawanan, PDF p.153)
and Tabel 4.3 (PDF p.154-157).

GITET Pedan 500 kV steps down through IBT 1,2 onto the PEDAN Tier-1 bus, which
splits into two branches:
    west  PEDAN - KLATN - KLASN - BANTL - SMANU
    east  PEDAN - JAJAR - MKRAN / GDRJO - PALUR

Jajar - Mangkunegaran is drawn RED dashed with red CBs, which in this book
means a CABLE (SKTT), not a planned circuit. Only GREY dashed with grey CBs
means rencana. MKRAN itself is a normal red busbar.

Six boundaries drawn greyed out with their owner underneath, every one of them
a GI a neighbouring sheet already holds:
    AMPEL, BDONO        "SS BOYOLALI"   -- Boyolali 1,2 carries BDONO
    WATES               "SS KSGHN"      -- Kesugihan 1,2 carries it
    WBJAN/GDEAN, SLBRU,
    MSRAN               "SS PEDAN 3,4"  -- the neighbouring Pedan sheet

Run: python scripts/make_ss_pedan12_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    dict(code="PEDAN7", name="GITET Pedan", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 PEDAN7", name="IBT 1 Pedan 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1",
         bus_hv="PEDAN7", bus_lv="PEDAN", trafo=1, kerawanan="1"),
    dict(code="IBT 2 PEDAN7", name="IBT 2 Pedan 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="2",
         bus_hv="PEDAN7", bus_lv="PEDAN", trafo=1, kerawanan="1"),
    dict(code="PEDAN", name="Pedan (bus 150 kV)", type="Busbar GI", tier=1,
         kerawanan="2"),
    # -- cabang barat --
    dict(code="KLATN", name="Klaten", type="Busbar GI", tier=2, kerawanan="9"),
    dict(code="KLASN", name="Kalasan", type="Busbar GI", tier=3, kerawanan="5"),
    dict(code="BANTL", name="Bantul", type="Busbar GI", tier=4, kerawanan="6;8"),
    dict(code="SMANU", name="Semanu", type="Busbar GI", tier=5),
    # -- cabang timur --
    dict(code="JAJAR", name="Jajar", type="Busbar GI", tier=2, kerawanan="10"),
    dict(code="MKRAN", name="Mangkunegaran", type="Busbar GI", tier=3),
    dict(code="GDRJO", name="Gondangrejo", type="Busbar GI", tier=3,
         kerawanan="3"),
    dict(code="PALUR", name="Palur", type="Busbar GI", tier=4, kerawanan="4;7"),
    # -- batas subsistem --
    dict(code="AMPEL", name="Ampel (SS Boyolali)", type="Busbar GI", tier=3,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Boyolali 1,2"),
    dict(code="BDONO", name="Bendono (SS Boyolali)", type="Busbar GI", tier=3,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Boyolali 1,2"),
    dict(code="WATES", name="Wates (SS Kesugihan)", type="Busbar GI", tier=5,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Kesugihan 1,2"),
    dict(code="WBJAN", name="Wonosari/Gedean (SS Pedan 3,4)", type="Busbar GI",
         tier=5, role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Pedan 3,4"),
    dict(code="SLBRU", name="Solo Baru (SS Pedan 3,4)", type="Busbar GI",
         tier=5, role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Pedan 3,4"),
    dict(code="MSRAN", name="Masaran (SS Pedan 3,4)", type="Busbar GI",
         tier=5, role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Pedan 3,4"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    # -- cabang barat --
    L("PEDAN", "KLATN", "SUTT Pedan - Klaten", 1, 2, kno="9"),
    L("KLATN", "AMPEL", "SUTT Klaten - Ampel (arah SS Boyolali)", 2, 3),
    L("KLATN", "KLASN", "SUTT Klaten - Kalasan", 2, 3, kno="5"),
    L("KLASN", "BANTL", "SUTT Kalasan - Bantul", 3, 4, kno="6"),
    L("BANTL", "SMANU", "SUTT Bantul - Semanu", 4, 5),
    L("BANTL", "WATES", "SUTT Bantul - Wates (arah SS Kesugihan)", 4, 5, kno="8"),
    L("BANTL", "WBJAN", "SUTT Bantul - Wonosari/Gedean (arah SS Pedan 3,4)", 4, 5),
    # -- cabang timur --
    L("PEDAN", "JAJAR", "SUTT Pedan - Jajar", 1, 2, kno="10"),
    L("JAJAR", "BDONO", "SUTT Jajar - Bendono (arah SS Boyolali)", 2, 3),
    L("JAJAR", "MKRAN", "SKTT Jajar - Mangkunegaran", 2, 3),
    L("JAJAR", "GDRJO", "SUTT Jajar - Gondangrejo", 2, 3, kno="3"),
    L("GDRJO", "PALUR", "SUTT Gondangrejo - Palur", 3, 4, kno="4"),
    L("PALUR", "SLBRU", "SUTT Palur - Solo Baru (arah SS Pedan 3,4)", 4, 5, kno="7"),
    L("PALUR", "MSRAN", "SUTT Palur - Masaran (arah SS Pedan 3,4)", 4, 5),
]

SPEC = dict(
    code="SS_PEDAN12",
    name="Pedan 1,2",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.5 (Tabel 4.3, PDF p.154-157); "
               "topologi dari Gambar 4.5 Peta Kerawanan (PDF p.153)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(154, 157, expected=10),
)

if __name__ == "__main__":
    build_workbook(SPEC)
