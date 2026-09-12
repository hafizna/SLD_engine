"""samples/ss_tasik_ingest.xlsx -- Subsistem Tasikmalaya 1,2 (UP2B Jawa Barat).

Source: Buku Kerawanan SJB 2026 Sec 3.7, Gambar 3.9 (Peta Kerawanan, PDF p.132)
and Tabel 3.7. The rows sit on PDF p.133-135; Bandung Selatan's table still runs
on p.132, so the range comes from the risk numbering, not the heading.

GITET Tasikmalaya Baru 500 kV (TSBRU) steps down onto the Tier-1 150 kV bus,
which also carries two generators drawn straight onto it, DRJAT and KRAHA.

Like Kediri 1,2 and Krian 3,4,5,6 this subsystem straddles two voltages. The
70 kV network (drawn yellow on Gambar 3.9) hangs under TSMYA through an
IBT 150/70 and runs TSMYA(70) - MLBNG - PDRAN; risk 4 sits at its far end.

Two boundaries, each drawn with its owner in brackets:
  KMJNG "(SS NUBRG)"      -- toward Bandung Selatan 1,2 - New Ujungberung 1,2
  MNANG "(UP2B JATENG)"   -- Majenang, which the Kesugihan 1,2 sheet already
                             carries as one of its own GIs

Run: python scripts/make_ss_tasik_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"

ASSETS = [
    # -- 500 kV GITET --
    dict(code="TSBRU7", name="GITET Tasikmalaya Baru", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 TSBRU7", name="IBT 1 Tasikmalaya Baru 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1",
         bus_hv="TSBRU7", bus_lv="TSBRU", trafo=1, kerawanan="1"),
    dict(code="IBT 2 TSBRU7", name="IBT 2 Tasikmalaya Baru 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="2",
         bus_hv="TSBRU7", bus_lv="TSBRU", trafo=1, kerawanan="1"),
    dict(code="TSBRU", name="Tasikmalaya Baru (bus 150 kV)", type="Busbar GI",
         tier=1),
    # -- pembangkit di Tier-1 --
    dict(code="KIT_DRJAT", name="PLTP Darajat", type="Pembangkit", tier=1,
         kv="150 kV"),
    dict(code="KIT_KRAHA", name="PLTP Kamojang / Karaha", type="Pembangkit",
         tier=1, kv="150 kV"),
    # -- 150 kV --
    dict(code="GARUT", name="Garut", type="Busbar GI", tier=2),
    dict(code="TSMYA", name="Tasikmalaya", type="Busbar GI", tier=2,
         kerawanan="2"),
    dict(code="KRNGL", name="Karangnunggal", type="Busbar GI", tier=2),
    dict(code="CAMIS", name="Ciamis", type="Busbar GI", tier=3),
    dict(code="BNJAR", name="Banjar", type="Busbar GI", tier=4, kerawanan="5"),
    # -- IBT 150/70 kV Tasikmalaya + jaringan 70 kV --
    dict(code="IBT 1 TSMYA", name="IBT 150/70 kV Tasikmalaya",
         type="IBT 3-Winding", tier=3, kv="150/70 kV", ibt="1",
         bus_hv="TSMYA", bus_lv="TSMYA4", trafo=2, simbol="IBT 150/70 kV"),
    dict(code="TSMYA4", name="Tasikmalaya (bus 70 kV)", type="Busbar GI",
         tier=3, kv=70),
    dict(code="MLBNG", name="Malangbong", type="Busbar GI", tier=4, kv=70,
         kerawanan="3"),
    dict(code="PDRAN", name="Pangandaran", type="Busbar GI", tier=6, kv=70,
         simbol="ujung subsistem", kerawanan="4"),
    # -- batas subsistem --
    dict(code="KMJNG", name="Kamojang (SS New Ujungberung)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Bandung Selatan 1,2 - New Ujungberung 1,2"),
    dict(code="MNANG", name="Majenang (UP2B Jateng)", type="Busbar GI",
         tier=5, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Kesugihan 1,2 (UP2B Jateng & DIY)"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

# Aset milik SS/UP2B lain: digambar sebagai stub pada busnya,
# bukan busbar tersendiri -- mengikuti pola UP2B Jakban.
BAYS = [
    ("KMJNG", "Kamojang", "TSBRU", None, 1, "Beroperasi", "", "SUTT"),
    ("MNANG", "Majenang", "BNJAR", None, 1, "Beroperasi", "", "SUTT"),
]

LINES = [
    # -- outlet pembangkit --
    L("KIT_DRJAT", "TSBRU", "Outlet PLTP Darajat", 1, 1, sirkit=1),
    L("KIT_KRAHA", "TSBRU", "Outlet PLTP Karaha", 1, 1, sirkit=1),
    # -- 150 kV --
    L("TSBRU", "KMJNG", "SUTT Tasikmalaya Baru - Kamojang (arah SS New Ujungberung)", 1, 2),
    L("TSBRU", "GARUT", "SUTT Tasikmalaya Baru - Garut", 1, 2),
    L("TSBRU", "TSMYA", "SUTT Tasikmalaya Baru - Tasikmalaya", 1, 2, kno="2"),
    L("TSBRU", "KRNGL", "SUTT Tasikmalaya Baru - Karangnunggal", 1, 2),
    L("TSMYA", "CAMIS", "SUTT Tasikmalaya - Ciamis", 2, 3),
    # kerawanan #5: ruas Ciamis - Banjar >50%, N-1 tidak terpenuhi saat
    # memasok sampai GI Majenang (UP2B JTD)
    L("CAMIS", "BNJAR", "SUTT Ciamis - Banjar 1,2", 3, 4, kno="5"),
    L("BNJAR", "MNANG", "SUTT Banjar - Majenang (arah UP2B Jateng)", 4, 5),
    # -- 70 kV --
    L("TSMYA4", "MLBNG", "SUTT 70 kV Tasikmalaya - Malangbong", 3, 4, kv=70, kno="3"),
    L("TSMYA4", "PDRAN", "SUTT 70 kV Tasikmalaya - Pangandaran", 3, 6, kv=70, kno="4"),
]

SPEC = dict(
    code="SS_TASIK",
    name="Tasikmalaya 1,2",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.7 (Tabel 3.7, PDF p.133-135); "
               "topologi dari Gambar 3.9 Peta Kerawanan (PDF p.132)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(133, 135, expected=5),
)

if __name__ == "__main__":
    build_workbook(SPEC)
