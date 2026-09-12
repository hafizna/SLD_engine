"""samples/ss_ngimbang_ingest.xlsx -- Subsistem Ngimbang (UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.5, Gambar 5.5 (Peta Kerawanan, PDF p.202)
and Tabel 5.3 (PDF p.202-205).

GITET Ngimbang 500 kV steps down through IBT 1,2 onto NBANG5. A second Tier-1
bus, TJWAR, carries PLTU Tuban Jawa. Seven tiers:

    Tier-2  JDONG, BABAT, MWANG, TUBAN
    Tier-3  CDANG, JBANG, BJGRO, LNGAN, HOLCM (KTT), KEREK
    Tier-4  CERME, PCRAN
    Tier-5  SGMDU5
    Tier-6  SGMDU4 (70 kV, reached through the Sungai Gemadu IBT), PKMIA
    Tier-7  BRATA, SAMSIK (both 70 kV)

CERME is drawn with a grey A-section, i.e. not energised, so that half carries
status Rencana. STBAN, TUBAN III and HOLCM are customer (KTT) assets.

BJGRO feeds CEPU, which the Tanjung Jati 1,2 - Ungaran 3 sheet draws from its
own side as the boundary toward UP2B Jawa Timur -- the two traces meet here.

Run: python scripts/make_ss_ngimbang_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    dict(code="NBANG7", name="GITET Ngimbang", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 NBANG7", name="IBT 1,2 Ngimbang 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1,2",
         bus_hv="NBANG7", bus_lv="NBANG5", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="1"),
    dict(code="NBANG5", name="Ngimbang (bus 150 kV)", type="Busbar GI", tier=1),
    # -- Tier-1 kedua: PLTU Tuban Jawa --
    dict(code="TJWAR", name="Tuban Jawa", type="Busbar GI", tier=1),
    dict(code="KIT_TJWAR", name="PLTU Tuban Jawa", type="Pembangkit", tier=1,
         kv="150 kV"),
    # -- Tier-2 --
    dict(code="JDONG", name="Jatidondong", type="Busbar GI", tier=2),
    dict(code="BABAT", name="Babat", type="Busbar GI", tier=2),
    dict(code="MWANG", name="Merakurak/Mwang", type="Busbar GI", tier=2),
    dict(code="TUBAN", name="Tuban", type="Busbar GI", tier=2, kerawanan="4"),
    # -- Tier-3 --
    dict(code="CDANG", name="Cendang", type="Busbar GI", tier=3),
    dict(code="JBANG", name="Jombang", type="Busbar GI", tier=3,
         simbol="bus A/B"),
    dict(code="BJGRO", name="Bojonegoro", type="Busbar GI", tier=3,
         kerawanan="2"),
    dict(code="LNGAN", name="Lamongan", type="Busbar GI", tier=3),
    dict(code="HOLCM", name="Holcim (KTT)", type="Busbar GI", tier=3,
         simbol="aset milik KTT"),
    dict(code="KEREK", name="Kerek", type="Busbar GI", tier=3),
    # -- Tier-4 --
    # The A section of Cerme is drawn grey: not yet energised.
    dict(code="CERME", name="Cerme", type="Busbar GI", tier=4,
         simbol="seksi A belum energize", kerawanan="3"),
    dict(code="PCRAN", name="Pucuk Ceran", type="Busbar GI", tier=4,
         kerawanan="7"),
    # -- Tier-5 / 6 / 7 --
    dict(code="SGMDU5", name="Sungai Gemadu (bus 150 kV)", type="Busbar GI",
         tier=5, kerawanan="5"),
    dict(code="IBT 1 SGMDU5", name="IBT 150/70 kV Sungai Gemadu",
         type="IBT 3-Winding", tier=6, kv="150/70 kV", ibt="1",
         bus_hv="SGMDU5", bus_lv="SGMDU4", trafo=1, simbol="IBT 150/70 kV"),
    dict(code="SGMDU4", name="Sungai Gemadu (bus 70 kV)", type="Busbar GI",
         tier=6, kv=70),
    dict(code="PKMIA", name="Pakem Mia", type="Busbar GI", tier=6,
         kerawanan="6"),
    dict(code="BRATA", name="Brata", type="Busbar GI", tier=7, kv=70),
    dict(code="SAMSIK", name="Samsik", type="Busbar GI", tier=7, kv=70),
    # -- batas / aset KTT --
    dict(code="CEPU", name="Cepu (SS Tanjung Jati)", type="Busbar GI", tier=4,
         role="SOURCE_BOUNDARY",
         simbol="batas ke UP2B Jateng (SS Tanjung Jati 1,2 - Ungaran 3)"),
    dict(code="STBAN", name="Semen Tuban (KTT)", type="Busbar GI", tier=4,
         role="SOURCE_BOUNDARY", simbol="aset milik KTT"),
    dict(code="TUBAN3", name="Tuban III (KTT)", type="Busbar GI", tier=4,
         role="SOURCE_BOUNDARY", simbol="aset milik KTT"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("KIT_TJWAR", "TJWAR", "Outlet PLTU Tuban Jawa", 1, 1, sirkit=1),
    # -- Tier-1 -> Tier-2 --
    L("NBANG5", "JDONG", "SUTT Ngimbang - Jatidondong", 1, 2),
    L("NBANG5", "BABAT", "SUTT Ngimbang - Babat", 1, 2),
    L("NBANG5", "MWANG", "SUTT Ngimbang - Merakurak", 1, 2),
    L("TJWAR", "TUBAN", "SUTT Tuban Jawa - Tuban", 1, 2, kno="4"),
    L("TJWAR", "MWANG", "SUTT Tuban Jawa - Merakurak", 1, 2),
    # -- Tier-2 -> Tier-3 --
    L("JDONG", "CDANG", "SUTT Jatidondong - Cendang", 2, 3),
    L("NBANG5", "JBANG", "SUTT Ngimbang - Jombang", 1, 3),
    L("NBANG5", "BJGRO", "SUTT Ngimbang - Bojonegoro", 1, 3, kno="2"),
    L("BABAT", "LNGAN", "SUTT Babat - Lamongan", 2, 3),
    L("MWANG", "HOLCM", "SUTT Merakurak - Holcim (aset milik KTT)", 2, 3, sirkit=1),
    L("TUBAN", "KEREK", "SUTT Tuban - Kerek", 2, 3),
    # -- Tier-3 -> Tier-4 --
    L("BJGRO", "CEPU", "SUTT Bojonegoro - Cepu (arah UP2B Jateng)", 3, 4),
    L("LNGAN", "CERME", "SUTT Lamongan - Cerme", 3, 4, kno="3"),
    L("LNGAN", "PCRAN", "SUTT Lamongan - Pucuk Ceran", 3, 4, kno="7"),
    L("KEREK", "STBAN", "SUTT Kerek - Semen Tuban (aset milik KTT)", 3, 4, sirkit=1),
    L("TUBAN", "TUBAN3", "SUTT Tuban - Tuban III (aset milik KTT)", 2, 4, sirkit=1),
    # -- Tier-4 -> Tier-5 / 6 / 7 --
    L("CERME", "SGMDU5", "SUTT Cerme - Sungai Gemadu", 4, 5, kno="5"),
    L("PCRAN", "PKMIA", "SUTT Pucuk Ceran - Pakem Mia", 4, 6, kno="6"),
    L("SGMDU4", "BRATA", "SUTT 70 kV Sungai Gemadu - Brata", 6, 7, kv=70),
    L("SGMDU4", "SAMSIK", "SUTT 70 kV Sungai Gemadu - Samsik", 6, 7, kv=70),
]

SPEC = dict(
    code="SS_NGIMBANG",
    name="Ngimbang",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.5 (Tabel 5.3, PDF p.202-205); "
               "topologi dari Gambar 5.5 Peta Kerawanan (PDF p.202)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(202, 205, expected=7),
)

if __name__ == "__main__":
    build_workbook(SPEC)
