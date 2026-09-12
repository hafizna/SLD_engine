"""samples/ss_grati_ingest.xlsx -- Subsistem Grati 1,2,3 (UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.8, Gambar 5.8 (Peta Kerawanan, PDF p.218)
and Tabel 5.5 (PDF p.219-227).

Eleven tiers, the deepest sheet in the book. GITET Grati 500 kV steps down
through IBT 1 and IBT 2,3 onto GRATI5, and three separate 150/70 kV step-downs
feed a large yellow network:

    WLNGI5 -> WLNGI4  -> BLTAR
    KBAGN  -> KBAGN4  -> TUREN, SGRUH (PLTA Sengguruh), GPGAN, KKTES
    SKLNG5 -> SKLNG4  -> PLHAN, BLBNG, MDLAN (PLTA Selorejo), SIMAN, SKTIH4

Four generators, all drawn green with a sine: PLTA Sutami on STAMI, the machine
on WLNGI4, PLTA Sengguruh on SGRUH and PLTA Selorejo on MDLAN.

Run: python scripts/make_ss_grati_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # ================= 500 kV injection =================
    dict(code="GRATI7", name="GITET Grati", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 GRATI7", name="IBT 1 Grati 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="GRATI7", bus_lv="GRATI5",
         trafo=1, simbol="IBT 1", kerawanan="1"),
    dict(code="IBT 2 GRATI7", name="IBT 2 Grati 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="GRATI7", bus_lv="GRATI5",
         trafo=1, kerawanan="1"),
    dict(code="IBT 3 GRATI7", name="IBT 3 Grati 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="3", bus_hv="GRATI7", bus_lv="GRATI5",
         trafo=1, kerawanan="1"),
    dict(code="GRATI5", name="Grati (bus 150 kV)", type="Busbar GI", tier=1),
    # ================= Tier-2 / 3 =================
    dict(code="GDTAN", name="Gedangan", type="Busbar GI", tier=2, kerawanan="2"),
    dict(code="PBLGO", name="Probolinggo", type="Busbar GI", tier=3,
         simbol="seksi A"),
    dict(code="RJOSO", name="Rejoso", type="Busbar GI", tier=3),
    dict(code="PIER", name="PIER", type="Busbar GI", tier=3, kerawanan="2"),
    # ================= Tier-4 / 5 / 6 =================
    dict(code="BNGIL5", name="Bangil (bus 150 kV)", type="Busbar GI", tier=4,
         kerawanan="3"),
    dict(code="PWSRI", name="Purwosari", type="Busbar GI", tier=4),
    dict(code="STAMI", name="Sutami", type="Busbar GI", tier=5, kerawanan="16"),
    dict(code="KIT_STAMI", name="PLTA Sutami", type="Pembangkit", tier=5,
         kv="150 kV"),
    dict(code="NBNGIL", name="New Bangil", type="Busbar GI", tier=5,
         kerawanan="5"),
    dict(code="BCKRO", name="Bacukiro", type="Busbar GI", tier=5),
    dict(code="KIS", name="KIS", type="Busbar GI", tier=5, kerawanan="7"),
    dict(code="PAKIS", name="Pakis", type="Busbar GI", tier=5),
    dict(code="WLNGI5", name="Wlingi (bus 150 kV)", type="Busbar GI", tier=6,
         kerawanan="9;10;15"),
    dict(code="BLKND", name="Blimbing Kandang", type="Busbar GI", tier=6,
         kerawanan="6"),
    dict(code="NPDAN", name="Ngempadan", type="Busbar GI", tier=6, kerawanan="4"),
    dict(code="NPROG", name="Ngeprogo", type="Busbar GI", tier=6),
    # ================= Tier-7 / 8 =================
    dict(code="IBT 1 WLNGI5", name="IBT 1 Wlingi 150/70 kV", type="IBT 3-Winding",
         tier=7, kv="150/70 kV", ibt="1", bus_hv="WLNGI5", bus_lv="WLNGI4",
         trafo=1, kerawanan="11"),
    dict(code="IBT 2 WLNGI5", name="IBT 2 Wlingi 150/70 kV", type="IBT 3-Winding",
         tier=7, kv="150/70 kV", ibt="2", bus_hv="WLNGI5", bus_lv="WLNGI4",
         trafo=1, kerawanan="11"),
    dict(code="WLNGI4", name="Wlingi (bus 70 kV)", type="Busbar GI", tier=7,
         kv=70, kerawanan="15"),
    dict(code="KIT_WLNGI", name="PLTA Wlingi", type="Pembangkit", tier=7,
         kv="70 kV"),
    dict(code="LWANG", name="Lawang", type="Busbar GI", tier=7),
    dict(code="BLTAR", name="Blitar", type="Busbar GI", tier=8, kv=70,
         kerawanan="12"),
    dict(code="KBAGN", name="Kebonagung (bus 150 kV)", type="Busbar GI", tier=8),
    # ================= Tier-9 / 10 / 11 =================
    dict(code="IBT 1 KBAGN", name="IBT 1 Kebonagung 150/70 kV",
         type="IBT 3-Winding", tier=9, kv="150/70 kV", ibt="1",
         bus_hv="KBAGN", bus_lv="KBAGN4", trafo=1),
    dict(code="IBT 2 KBAGN", name="IBT 2 Kebonagung 150/70 kV",
         type="IBT 3-Winding", tier=9, kv="150/70 kV", ibt="2",
         bus_hv="KBAGN", bus_lv="KBAGN4", trafo=1),
    dict(code="IBT 3 KBAGN", name="IBT 3 Kebonagung 150/70 kV",
         type="IBT 3-Winding", tier=9, kv="150/70 kV", ibt="3",
         bus_hv="KBAGN", bus_lv="KBAGN4", trafo=1),
    dict(code="KBAGN4", name="Kebonagung (bus 70 kV)", type="Busbar GI",
         tier=9, kv=70),
    dict(code="SKLNG5", name="Sekarlangit (bus 150 kV)", type="Busbar GI",
         tier=9),
    dict(code="IBT 1 SKLNG5", name="IBT 1 Sekarlangit 150/70 kV",
         type="IBT 3-Winding", tier=10, kv="150/70 kV", ibt="1",
         bus_hv="SKLNG5", bus_lv="SKLNG4", trafo=1,
         kerawanan="14"),
    dict(code="IBT 2 SKLNG5", name="IBT 2 Sekarlangit 150/70 kV",
         type="IBT 3-Winding", tier=10, kv="150/70 kV", ibt="2",
         bus_hv="SKLNG5", bus_lv="SKLNG4", trafo=1,
         kerawanan="14"),
    dict(code="SKLNG4", name="Sekarlangit (bus 70 kV)", type="Busbar GI",
         tier=10, kv=70),
    dict(code="TUREN", name="Turen", type="Busbar GI", tier=10, kv=70,
         kerawanan="13"),
    dict(code="SGRUH", name="Sengguruh", type="Busbar GI", tier=10, kv=70),
    dict(code="KIT_SGRUH", name="PLTA Sengguruh", type="Pembangkit", tier=10,
         kv="70 kV"),
    dict(code="PLHAN", name="Pulahan", type="Busbar GI", tier=10, kv=70),
    dict(code="MDLAN", name="Mendalan", type="Busbar GI", tier=10, kv=70,
         kerawanan="16"),
    dict(code="KIT_SLRJO", name="PLTA Selorejo", type="Pembangkit", tier=10,
         kv="70 kV"),
    dict(code="GPGAN", name="Gondang Pagan", type="Busbar GI", tier=11, kv=70,
         kerawanan="15;16"),
    dict(code="KKTES", name="Karangkates", type="Busbar GI", tier=11, kv=70,
         kerawanan="16"),
    dict(code="BLBNG", name="Balebang", type="Busbar GI", tier=11, kv=70,
         simbol="seksi A/B"),
    dict(code="SIMAN", name="Siman", type="Busbar GI", tier=11, kv=70),
    dict(code="SKTIH4", name="Sukorejo (bus 70 kV)", type="Busbar GI",
         tier=11, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Kediri"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    # -- outlet pembangkit --
    L("KIT_STAMI", "STAMI", "Outlet PLTA Sutami", 5, 5, sirkit=1),
    L("KIT_WLNGI", "WLNGI4", "Outlet PLTA Wlingi", 7, 7, kv=70, sirkit=1),
    L("KIT_SGRUH", "SGRUH", "Outlet PLTA Sengguruh", 10, 10, kv=70, sirkit=1),
    L("KIT_SLRJO", "MDLAN", "Outlet PLTA Selorejo", 10, 10, kv=70, sirkit=1),
    # ================= 150 kV =================
    L("GRATI5", "GDTAN", "SUTT Grati - Gedangan", 1, 2, kno="2"),
    L("GDTAN", "PBLGO", "SUTT Gedangan - Probolinggo", 2, 3),
    L("GDTAN", "RJOSO", "SUTT Gedangan - Rejoso", 2, 3),
    L("GRATI5", "PIER", "SUTT Grati - PIER", 1, 3, kno="2"),
    L("GDTAN", "BNGIL5", "SUTT Gedangan - Bangil", 2, 4, kno="3"),
    L("PIER", "PWSRI", "SUTT PIER - Purwosari", 3, 4),
    L("BNGIL5", "NBNGIL", "SUTT Bangil - New Bangil", 4, 5, kno="5"),
    L("BNGIL5", "BCKRO", "SUTT Bangil - Bacukiro", 4, 5),
    L("BNGIL5", "KIS", "SUTT Bangil - KIS", 4, 5, kno="7"),
    L("BNGIL5", "PAKIS", "SUTT Bangil - Pakis", 4, 5),
    L("BNGIL5", "STAMI", "SUTT Bangil - Sutami", 4, 5, kno="16"),
    L("BCKRO", "NPDAN", "SUTT Bacukiro - Ngempadan", 5, 6, kno="4"),
    L("KIS", "NPROG", "SUTT KIS - Ngeprogo", 5, 6),
    L("STAMI", "WLNGI5", "SUTT Sutami - Wlingi", 5, 6, kno="9"),
    L("NBNGIL", "BLKND", "SUTT New Bangil - Blimbing Kandang", 5, 6, kno="6"),
    L("STAMI", "LWANG", "SUTT Sutami - Lawang", 5, 7, kno="8"),
    L("BLKND", "KBAGN", "SUTT Blimbing Kandang - Kebonagung", 6, 8),
    L("LWANG", "KBAGN", "SUTT Lawang - Kebonagung", 7, 8),
    L("PWSRI", "SKLNG5", "SUTT Purwosari - Sekarlangit", 4, 9),
    # ================= 70 kV =================
    L("WLNGI4", "BLTAR", "SUTT 70 kV Wlingi - Blitar", 7, 8, kv=70, kno="12"),
    L("KBAGN4", "TUREN", "SUTT 70 kV Kebonagung - Turen", 9, 10, kv=70, kno="13"),
    L("KBAGN4", "SGRUH", "SUTT 70 kV Kebonagung - Sengguruh", 9, 10, kv=70),
    L("TUREN", "GPGAN", "SUTT 70 kV Turen - Gondang Pagan", 10, 11, kv=70, kno="15"),
    L("SGRUH", "KKTES", "SUTT 70 kV Sengguruh - Karangkates", 10, 11, kv=70, kno="16"),
    L("SKLNG4", "PLHAN", "SUTT 70 kV Sekarlangit - Pulahan", 10, 10, kv=70),
    L("SKLNG4", "MDLAN", "SUTT 70 kV Sekarlangit - Mendalan", 10, 10, kv=70, kno="16"),
    L("PLHAN", "BLBNG", "SUTT 70 kV Pulahan - Balebang", 10, 11, kv=70),
    L("MDLAN", "SIMAN", "SUTT 70 kV Mendalan - Siman", 10, 11, kv=70),
    L("SIMAN", "SKTIH4", "SUTT 70 kV Siman - Sukorejo (arah SS Kediri)",
      11, 11, kv=70),
]

SPEC = dict(
    code="SS_GRATI",
    name="Grati 1,2,3",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.8 (Tabel 5.5, PDF p.219-227); "
               "topologi dari Gambar 5.8 Peta Kerawanan (PDF p.218)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(219, 227, expected=16),
)

if __name__ == "__main__":
    build_workbook(SPEC)
