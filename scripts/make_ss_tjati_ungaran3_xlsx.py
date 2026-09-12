"""samples/ss_tjati_ungaran3_ingest.xlsx -- Subsistem Tanjung Jati 1,2 -
Ungaran 3 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.3, Gambar 4.3 (Peta Kerawanan, PDF p.141)
and Tabel 4.1 (PDF p.141-146).

Two 500 kV injections onto one 150 kV network, GITET Ungaran (unit 3 here) and
GITET Tanjungjati, plus generation drawn straight onto Tier-1:
    JELOK  -- PLTA Jelok and PLTA Timo, the pair the Ungaran 1,2 and Boyolali
              sheets also see
    TBROK  -- PLTGU Tambaklorok blok B1 and B2
    RBKIT  -- PLTU Rembang

The network runs seven tiers deep, the longest in the book:
    Tier-2  BAWEN, MRGEN, SYUNG, JPARA, PATI, RBANG
    Tier-3  SGRAH, SCANG, SBGAN, KUDUS, JKULO, SINDO
    Tier-4  MDARI, PRWDI, BLORA
    Tier-5  KNTUG, KDNBO (with its PLTA), CEPU
    Tier-6  GJYAN

Boundaries are drawn greyed out with their owner underneath: BYOLI toward
Boyolali 1,2, TMGNG toward Kesugihan 1,2, and BJGRO toward UP2B Jawa Timur --
the Jatim sheets draw BJGRO from their side as SS Ngimbang.

Run: python scripts/make_ss_tjati_ungaran3_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    # ================= 500 kV injections =================
    dict(code="UNGAR7", name="GITET Ungaran", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 3 UNGAR7", name="IBT 3 Ungaran 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="3",
         bus_hv="UNGAR7", bus_lv="UNGAR", trafo=1,
         simbol="1 IBT (unit 3)", kerawanan="3;4"),
    dict(code="TJATI7", name="GITET Tanjungjati", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 TJATI7", name="IBT 1,2 Tanjungjati 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1,2",
         bus_hv="TJATI7", bus_lv="TJATI", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="1;2"),
    # ================= Tier-1 =================
    dict(code="JELOK", name="Jelok", type="Busbar GI", tier=1, kerawanan="13"),
    dict(code="KIT_JELOK", name="PLTA Jelok", type="Pembangkit", tier=1, kv="150 kV"),
    dict(code="KIT_TIMO", name="PLTA Timo", type="Pembangkit", tier=1, kv="150 kV"),
    dict(code="UNGAR", name="Ungaran (bus 150 kV)", type="Busbar GI", tier=1,
         kerawanan="14"),
    dict(code="TBROK", name="Tambaklorok", type="Busbar GI", tier=1),
    dict(code="KIT_TBROKB2", name="PLTGU Tambaklorok Blok B2", type="Pembangkit",
         tier=1, kv="150 kV"),
    dict(code="KIT_TBROKB1", name="PLTGU Tambaklorok Blok B1", type="Pembangkit",
         tier=1, kv="150 kV"),
    dict(code="TJATI", name="Tanjungjati (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="RBKIT", name="Rembang KIT", type="Busbar GI", tier=1, kerawanan="5"),
    dict(code="KIT_RBANG", name="PLTU Rembang", type="Pembangkit", tier=1,
         kv="150 kV"),
    # ================= Tier-2 =================
    dict(code="BAWEN", name="Bawen", type="Busbar GI", tier=2),
    dict(code="MRGEN", name="Mranggen", type="Busbar GI", tier=2),
    dict(code="SYUNG", name="Sayung", type="Busbar GI", tier=2),
    dict(code="JPARA", name="Jepara", type="Busbar GI", tier=2),
    dict(code="PATI", name="Pati", type="Busbar GI", tier=2, kerawanan="6"),
    dict(code="RBANG", name="Rembang", type="Busbar GI", tier=2),
    # ================= Tier-3 =================
    dict(code="SGRAH", name="Sugihrahayu", type="Busbar GI", tier=3,
         kerawanan="10"),
    dict(code="SCANG", name="Secang (Bus 1)", type="Busbar GI", tier=3,
         simbol="Bus 1"),
    dict(code="SBGAN", name="Sambungan", type="Busbar GI", tier=3,
         simbol="KTT SBGAN"),
    dict(code="KUDUS", name="Kudus", type="Busbar GI", tier=3, kerawanan="7"),
    dict(code="JKULO", name="Jekulo", type="Busbar GI", tier=3),
    dict(code="SINDO", name="Sindo", type="Busbar GI", tier=3,
         simbol="KTT SINDO"),
    # ================= Tier-4 / 5 / 6 =================
    dict(code="MDARI", name="Mandari", type="Busbar GI", tier=4, kerawanan="9"),
    dict(code="PRWDI", name="Purwodadi", type="Busbar GI", tier=4),
    dict(code="BLORA", name="Blora", type="Busbar GI", tier=4, kerawanan="8"),
    dict(code="KNTUG", name="Kanetug", type="Busbar GI", tier=5, kerawanan="11"),
    dict(code="KDNBO", name="Kedungombo", type="Busbar GI", tier=5),
    dict(code="KIT_KDNBO", name="PLTA Kedungombo", type="Pembangkit", tier=5,
         kv="150 kV"),
    dict(code="CEPU", name="Cepu", type="Busbar GI", tier=5, kerawanan="8"),
    dict(code="GJYAN", name="Gajahan", type="Busbar GI", tier=6, kerawanan="12"),
    # ================= batas subsistem =================
    dict(code="BYOLI", name="Boyolali (SS Boyolali)", type="Busbar GI", tier=3,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Boyolali 1,2"),
    dict(code="TMGNG", name="Temanggung (SS Kesugihan)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Kesugihan 1,2"),
    dict(code="BJGRO", name="Bojonegoro (UP2B Jatim)", type="Busbar GI",
         tier=6, role="SOURCE_BOUNDARY",
         simbol="batas ke UP2B Jawa Timur (SS Ngimbang)"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    # -- outlet pembangkit --
    L("KIT_JELOK", "JELOK", "Outlet PLTA Jelok", 1, 1, sirkit=1),
    L("KIT_TIMO", "JELOK", "Outlet PLTA Timo", 1, 1, sirkit=1),
    L("KIT_TBROKB2", "TBROK", "Outlet PLTGU Tambaklorok Blok B2", 1, 1, sirkit=1),
    L("KIT_TBROKB1", "TBROK", "Outlet PLTGU Tambaklorok Blok B1", 1, 1, sirkit=1),
    L("KIT_RBANG", "RBKIT", "Outlet PLTU Rembang", 1, 1, sirkit=1),
    L("KIT_KDNBO", "KDNBO", "Outlet PLTA Kedungombo", 5, 5, sirkit=1),
    # -- Tier-1 --
    L("JELOK", "UNGAR", "SUTT Jelok - Ungaran", 1, 1, kno="13"),
    L("UNGAR", "TBROK", "SUTT Ungaran - Tambaklorok", 1, 1),
    L("TBROK", "TJATI", "SUTT Tambaklorok - Tanjungjati", 1, 1),
    L("TJATI", "RBKIT", "SUTT Tanjungjati - Rembang KIT", 1, 1, kno="5"),
    # -- Tier-1 -> Tier-2 --
    L("UNGAR", "BAWEN", "SUTT Ungaran - Bawen", 1, 2, kno="14"),
    L("UNGAR", "MRGEN", "SUTT Ungaran - Mranggen", 1, 2),
    L("TBROK", "SYUNG", "SUTT Tambaklorok - Sayung", 1, 2),
    L("TJATI", "JPARA", "SUTT Tanjungjati - Jepara", 1, 2),
    L("TJATI", "PATI", "SUTT Tanjungjati - Pati", 1, 2, kno="6"),
    L("RBKIT", "RBANG", "SUTT Rembang KIT - Rembang", 1, 2),
    # -- Tier-2 -> Tier-3 --
    L("BAWEN", "SGRAH", "SUTT Bawen - Sugihrahayu", 2, 3, kno="10"),
    L("BAWEN", "BYOLI", "SUTT Bawen - Boyolali (arah SS Boyolali)", 2, 3),
    L("UNGAR", "SCANG", "SUTT Ungaran - Secang", 1, 3),
    L("MRGEN", "SBGAN", "SUTT Mranggen - Sambungan", 2, 3),
    L("JPARA", "KUDUS", "SUTT Jepara - Kudus", 2, 3, kno="7"),
    L("PATI", "JKULO", "SUTT Pati - Jekulo", 2, 3),
    L("RBANG", "SINDO", "SUTT Rembang - Sindo", 2, 3),
    # -- Tier-3 -> Tier-4 --
    L("SGRAH", "MDARI", "SUTT Sugihrahayu - Mandari", 3, 4, kno="9"),
    L("SCANG", "TMGNG", "SUTT Secang - Temanggung (arah SS Kesugihan)", 3, 4),
    L("SBGAN", "PRWDI", "SUTT Sambungan - Purwodadi", 3, 4),
    L("SINDO", "BLORA", "SUTT Sindo - Blora", 3, 4, kno="8"),
    # -- Tier-4 -> Tier-5 / 6 --
    L("MDARI", "KNTUG", "SUTT Mandari - Kanetug", 4, 5, kno="11"),
    L("PRWDI", "KDNBO", "SUTT Purwodadi - Kedungombo", 4, 5),
    L("BLORA", "CEPU", "SUTT Blora - Cepu", 4, 5, kno="8"),
    L("KNTUG", "GJYAN", "SUTT Kanetug - Gajahan", 5, 6, kno="12"),
    L("CEPU", "BJGRO", "SUTT Cepu - Bojonegoro (arah UP2B Jatim)", 5, 6),
]

SPEC = dict(
    code="SS_TJATI_UNGARAN3",
    name="Tanjung Jati 1,2 - Ungaran 3",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.3 (Tabel 4.1, PDF p.141-146); "
               "topologi dari Gambar 4.3 Peta Kerawanan (PDF p.141)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(141, 146, expected=14),
)

if __name__ == "__main__":
    build_workbook(SPEC)
