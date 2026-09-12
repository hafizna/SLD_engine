"""samples/ss_cbatu12_dltms_ingest.xlsx -- Subsistem Cibatu 1,2 - Deltamas 1,2.

Source: Buku Kerawanan SJB 2026 Sec 3.5, Gambar 3.7 (Peta Kerawanan, PDF p.123)
and Tabel 3.5 (PDF p.123-126). UP2B Jawa Barat.

Two 500 kV injections on one 150 kV network:
    GITET Cibatu   (CBATU 1,2) -> IBT 1,2 -> Tier-1 bus, risk 1
    GITET Deltamas (DLTMS)     -> IBT 1,2,3,4 -> its own Tier-1 bus, risk 4
Risk 1 is explicitly about the Cibatu pair being >70% when PLTGU Cikarang
Listrindo is out, so the two generators drawn straight onto Tier-1 (BKPWR and
CLNDO) matter to it and are modelled as Pembangkit.

Tier-2 runs JUSIN, CLGSI, HNKOK, JBBKA, CIKRG, CKLPO, SKMHI; Tier-3 RJPSI,
FJSWA, GDMKR, THK, MGKYA; Tier-4 PNYGN; Tier-5 TGHRG.

Five boundaries, each drawn with its owner in brackets and modelled as
SOURCE_BOUNDARY:
    MKSRI, SZUKI, PRURI, PRMYA   "(SS CBATU 3,4)"
    TMBUN                        "(SS TMBUN)"  -- the New Tambun sheet carries
                                                  TMBUN as one of its own GIs

Run: python scripts/make_ss_cbatu12_dltms_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"

ASSETS = [
    # ================= 500 kV injections =================
    dict(code="CBATU7", name="GITET Cibatu", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 1 CBATU7", name="IBT 1 Cibatu 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="CBATU7", bus_lv="CBATU",
         trafo=1, kerawanan="1"),
    dict(code="IBT 2 CBATU7", name="IBT 2 Cibatu 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="CBATU7", bus_lv="CBATU",
         trafo=1, kerawanan="1"),
    dict(code="DLTMS7", name="GITET Deltamas", type="Busbar GITET", tier=1, kv="500 kV"),
    # Risk 4 is the bank as drawn; risk 7 is specifically IBT 1 & 2 of it
    # ("berpotensi naik diatas 50%"), so the row carries both numbers.
    dict(code="IBT 1 DLTMS7", name="IBT 1 Deltamas 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1",
         bus_hv="DLTMS7", bus_lv="DLTMS", trafo=1, kerawanan="4;7"),
    dict(code="IBT 2 DLTMS7", name="IBT 2 Deltamas 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="2",
         bus_hv="DLTMS7", bus_lv="DLTMS", trafo=1, kerawanan="4;7"),
    dict(code="IBT 3 DLTMS7", name="IBT 3 Deltamas 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="3",
         bus_hv="DLTMS7", bus_lv="DLTMS", trafo=1, kerawanan="4;7"),
    dict(code="IBT 4 DLTMS7", name="IBT 4 Deltamas 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="4",
         bus_hv="DLTMS7", bus_lv="DLTMS", trafo=1, kerawanan="4;7"),
    # ================= Tier-1 150 kV =================
    dict(code="CBATU", name="Cibatu (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="DLTMS", name="Deltamas (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section + kopel"),
    # -- pembangkit di Tier-1 --
    dict(code="KIT_BKPWR", name="PLTGU Bekasi Power", type="Pembangkit",
         tier=1, kv="150 kV"),
    dict(code="KIT_CLNDO", name="PLTGU Cikarang Listrindo", type="Pembangkit",
         tier=1, kv="150 kV", kerawanan="1"),
    dict(code="BKPWR", name="Bekasi Power", type="Busbar GI", tier=1),
    dict(code="CLNDO", name="Cikarang Listrindo", type="Busbar GI", tier=1),
    # ================= Tier-2 =================
    dict(code="JUSIN", name="Jababeka Usin", type="Busbar GI", tier=2),
    dict(code="CLGSI", name="Cilegsi", type="Busbar GI", tier=2),
    dict(code="HNKOK", name="Hankook", type="Busbar GI", tier=2, kerawanan="2"),
    dict(code="JBBKA", name="Jababeka", type="Busbar GI", tier=2),
    dict(code="CIKRG", name="Cikarang", type="Busbar GI", tier=2),
    dict(code="CKLPO", name="Cikarang Lippo", type="Busbar GI", tier=2,
         kerawanan="5"),
    dict(code="SKMHI", name="Sukamahi", type="Busbar GI", tier=2,
         simbol="bus section + kopel"),
    # ================= Tier-3 =================
    dict(code="RJPSI", name="Rejosari", type="Busbar GI", tier=3),
    dict(code="MYKMK", name="Meyko Makmur", type="Busbar GI", tier=3),
    dict(code="FJSWA", name="Fajar Surya Wisesa", type="Busbar GI", tier=3,
         kerawanan="3"),
    dict(code="GDMKR", name="Gandamekar", type="Busbar GI", tier=3,
         simbol="bus section + kopel", kerawanan="6"),
    dict(code="THK", name="THK", type="Busbar GI", tier=3),
    dict(code="MGKYA", name="Mega Kaya", type="Busbar GI", tier=3),
    # ================= Tier-4 / 5 =================
    # Risk 8: GI Simpul where four subsystems meet (Cibatu 1,2 / Cibatu 3,4 /
    # Mandirancan 1,2 / Deltamas 3,4), operated split-busbar -- which is why the
    # figure draws a coupler on it.
    dict(code="PNYGN", name="Pinayungan", type="Busbar GI", tier=4,
         simbol="GI Simpul 4 subsistem; split busbar + kopel", kerawanan="8"),
    dict(code="TGHRG", name="Tegal Herang", type="Busbar GI", tier=5),
    # ============ batas subsistem ============
    dict(code="MKSRI", name="Maka Sri (SS Cibatu 3,4)", type="Busbar GI", tier=2,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="SZUKI", name="Suzuki (SS Cibatu 3,4)", type="Busbar GI", tier=2,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="PRURI", name="Peruri (SS Cibatu 3,4)", type="Busbar GI", tier=5,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="PRMYA", name="Purwamaya (SS Cibatu 3,4)", type="Busbar GI", tier=5,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="TMBUN", name="Tambun (SS New Tambun)", type="Busbar GI", tier=4,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem New Tambun"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

# Aset milik SS/UP2B lain: digambar sebagai stub pada busnya,
# bukan busbar tersendiri -- mengikuti pola UP2B Jakban.
BAYS = [
    ("PRMYA", "Purwamaya (SS Cibatu 3,4)", "PNYGN", None, 1, "Beroperasi", "", "SUTT"),
    ("PRURI", "Peruri (SS Cibatu 3,4)", "PNYGN", None, 1, "Beroperasi", "", "SUTT"),
    ("SZUKI", "Suzuki (SS Cibatu 3,4)", "CBATU", None, 1, "Beroperasi", "", "SUTT"),
    ("TMBUN", "Tambun (SS New Tambun)", "GDMKR", None, 1, "Beroperasi", "", "SUTT"),
]

LINES = [
    # -- outlet pembangkit --
    L("KIT_BKPWR", "BKPWR", "Outlet PLTGU Bekasi Power", 1, 1, sirkit=1),
    L("KIT_CLNDO", "CLNDO", "Outlet PLTGU Cikarang Listrindo", 1, 1, sirkit=1),
    # -- sisi Cibatu --
    L("CBATU", "MKSRI", "SUTT Cibatu - Maka Sri (arah SS Cibatu 3,4)", 1, 2),
    L("CBATU", "SZUKI", "SUTT Cibatu - Suzuki (arah SS Cibatu 3,4)", 1, 2),
    L("CBATU", "JUSIN", "SUTT Cibatu - Jababeka Usin", 1, 2),
    L("CBATU", "CLGSI", "SUTT Cibatu - Cilegsi", 1, 2),
    # kerawanan #2: konfigurasi di GI Hankook
    L("CBATU", "HNKOK", "SUTT Cibatu - Hankook", 1, 2, kno="2"),
    L("BKPWR", "JBBKA", "SUTT Bekasi Power - Jababeka", 1, 2),
    L("CLNDO", "CIKRG", "SUTT Cikarang Listrindo - Cikarang", 1, 2),
    L("HNKOK", "RJPSI", "SUTT Hankook - Rejosari", 2, 3),
    L("JBBKA", "MYKMK", "SUTT Jababeka - Meyko Makmur", 2, 3),
    # kerawanan #3: ruas ke Fajar Surya Wisesa
    L("CIKRG", "FJSWA", "SUTT Cikarang - Fajar Surya Wisesa", 2, 3, kno="3"),
    # -- sisi Deltamas --
    L("DLTMS", "CKLPO", "SUTT Deltamas - Cikarang Lippo", 1, 2, kno="5"),
    L("DLTMS", "SKMHI", "SUTT Deltamas - Sukamahi", 1, 2),
    # kerawanan #6: ruas ke Gandamekar
    L("CKLPO", "GDMKR", "SUTT Cikarang Lippo - Gandamekar", 2, 3, kno="6"),
    L("SKMHI", "THK", "SUTT Sukamahi - THK", 2, 3),
    L("SKMHI", "MGKYA", "SUTT Sukamahi - Mega Kaya", 2, 3),
    L("GDMKR", "TMBUN", "SUTT Gandamekar - Tambun (arah SS New Tambun)", 3, 4),
    L("MGKYA", "PNYGN", "SUTT Mega Kaya - Pinayungan", 3, 4),
    L("PNYGN", "TGHRG", "SUTT Pinayungan - Tegal Herang", 4, 5),
    L("PNYGN", "MKSRI", "SUTT Pinayungan - Maka Sri (arah SS Cibatu 3,4)", 4, 2),
    L("PNYGN", "PRURI", "SUTT Pinayungan - Peruri (arah SS Cibatu 3,4)", 4, 5),
    L("PNYGN", "PRMYA", "SUTT Pinayungan - Purwamaya (arah SS Cibatu 3,4)", 4, 5),
]

SPEC = dict(
    code="SS_CBATU12_DLTMS",
    name="Cibatu 1,2 - Deltamas 1,2",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.5 (Tabel 3.5, PDF p.123-126); "
               "topologi dari Gambar 3.7 Peta Kerawanan (PDF p.123)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(123, 126, expected=8),
)

if __name__ == "__main__":
    build_workbook(SPEC)
