"""samples/ss_ungaran12_ingest.xlsx -- Subsistem Ungaran 1,2 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.4, Gambar 4.4 (Peta Kerawanan, PDF p.147)
and Tabel 4.2 (PDF p.147-152).

GITET Ungaran 500 kV steps down through IBT 1,2 onto the UNGAR Tier-1 bus.
Two more Tier-1 buses carry generation drawn straight onto them:
    JELOK  -- PLTA Jelok and PLTA Timo (the same pair the Boyolali sheet sees
              from its side through SUTT Boyolali - Jelok)
    TBROK  -- PLTGU Tambaklorok blok B1 and B3

Tier-2 is WLERI, PYUNG, KRAPK, PDLAM, KLSRI, SYUNG; Tier-3 is KLNGU, BSBRU,
RDRUT, SRDOL, SLIMA. SLIMA and the KLSRI stub are drawn dashed, i.e. not yet
energised, so they carry status Rencana.

Four boundaries are drawn greyed out with their owning subsystem underneath:
    SGRAH / BRNGI   "SS BYOLI"   -- Boyolali 1,2 carries BRNGI
    NBTNG / BNPTH   "SS PMLNG"   -- Pemalang 1,2 carries both
    TJATI / KUDUS   "SS TJATI"   -- Tanjung Jati 1,2 - Ungaran 3

Run: python scripts/make_ss_ungaran12_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    # -- 500 kV GITET --
    dict(code="UNGAR7", name="GITET Ungaran", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 UNGAR7", name="IBT 1,2 Ungaran 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1,2",
         bus_hv="UNGAR7", bus_lv="UNGAR", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="1;2"),
    # -- Tier-1 --
    dict(code="UNGAR", name="Ungaran (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="JELOK", name="Jelok", type="Busbar GI", tier=1),
    dict(code="KIT_JELOK", name="PLTA Jelok", type="Pembangkit", tier=1,
         kv="150 kV"),
    dict(code="KIT_TIMO", name="PLTA Timo", type="Pembangkit", tier=1,
         kv="150 kV"),
    dict(code="TBROK", name="Tambaklorok", type="Busbar GI", tier=1,
         kerawanan="3"),
    dict(code="KIT_TBROKB3", name="PLTGU Tambaklorok Blok B3", type="Pembangkit",
         tier=1, kv="150 kV", kerawanan="8"),
    dict(code="KIT_TBROKB1", name="PLTGU Tambaklorok Blok B1", type="Pembangkit",
         tier=1, kv="150 kV"),
    # -- Tier-2 --
    dict(code="WLERI", name="Weleri", type="Busbar GI", tier=2, kerawanan="4"),
    dict(code="PYUNG", name="Payung", type="Busbar GI", tier=2, kerawanan="5"),
    dict(code="KRAPK", name="Krapyak", type="Busbar GI", tier=2, kerawanan="12"),
    dict(code="PDLAM", name="Pandean Lamper", type="Busbar GI", tier=2),
    dict(code="KLSRI", name="Kalisari", type="Busbar GI", tier=2, kerawanan="13"),
    dict(code="SYUNG", name="Sayung", type="Busbar GI", tier=2, kerawanan="10"),
    # -- Tier-3 --
    dict(code="KLNGU", name="Kaliwungu", type="Busbar GI", tier=3,
         simbol="KTT APF", kerawanan="11"),
    dict(code="BSBRU", name="Bawen Sambiroto Baru", type="Busbar GI", tier=3),
    dict(code="RDRUT", name="Randu Garut", type="Busbar GI", tier=3,
         kerawanan="11"),
    dict(code="SRDOL", name="Srondol", type="Busbar GI", tier=3, kerawanan="9"),
    # Drawn dashed on Gambar 4.4: not yet energised.
    dict(code="SLIMA", name="Selima (rencana)", type="Busbar GI", tier=3,
         status="Rencana", kerawanan="6;7"),
    # -- batas subsistem, digambar abu-abu dengan pemiliknya di bawahnya --
    dict(code="BRNGI", name="Banaran / Sugihrahayu (SS Boyolali)",
         type="Busbar GI", tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Boyolali 1,2"),
    dict(code="NBTNG", name="New Batang (SS Pemalang)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Pemalang 1,2"),
    dict(code="BNPTH", name="Bumi Putih (SS Pemalang)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Pemalang 1,2"),
    dict(code="TJATI", name="Tanjung Jati (SS Tanjung Jati)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Tanjung Jati 1,2 - Ungaran 3"),
    dict(code="KUDUS", name="Kudus (SS Tanjung Jati)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Tanjung Jati 1,2 - Ungaran 3"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    # -- outlet pembangkit --
    L("KIT_JELOK", "JELOK", "Outlet PLTA Jelok", 1, 1, sirkit=1),
    L("KIT_TIMO", "JELOK", "Outlet PLTA Timo", 1, 1, sirkit=1),
    L("KIT_TBROKB3", "TBROK", "Outlet PLTGU Tambaklorok Blok B3", 1, 1, sirkit=1),
    L("KIT_TBROKB1", "TBROK", "Outlet PLTGU Tambaklorok Blok B1", 1, 1, sirkit=1),
    # -- Tier-1 saling terhubung --
    L("JELOK", "UNGAR", "SUTT Jelok - Ungaran", 1, 1),
    L("UNGAR", "TBROK", "SUTT Ungaran - Tambaklorok", 1, 1, kno="3"),
    L("JELOK", "BRNGI", "SUTT Jelok - Banaran (arah SS Boyolali)", 1, 2),
    # -- Tier-1 -> Tier-2 --
    L("UNGAR", "WLERI", "SUTT Ungaran - Weleri", 1, 2, kno="4"),
    L("UNGAR", "PYUNG", "SUTT Ungaran - Payung", 1, 2, kno="5"),
    L("UNGAR", "KRAPK", "SUTT Ungaran - Krapyak", 1, 2, kno="12"),
    L("TBROK", "PDLAM", "SUTT Tambaklorok - Pandean Lamper", 1, 2),
    L("TBROK", "KLSRI", "SUTT Tambaklorok - Kalisari", 1, 2, kno="13"),
    L("TBROK", "SYUNG", "SUTT Tambaklorok - Sayung", 1, 2, kno="10"),
    L("TBROK", "SRDOL", "SUTT Tambaklorok - Srondol", 1, 3, kno="9"),
    # -- Tier-2 -> Tier-3 --
    L("WLERI", "KLNGU", "SUTT Weleri - Kaliwungu", 2, 3, kno="11"),
    L("WLERI", "NBTNG", "SUTT Weleri - New Batang (arah SS Pemalang)", 2, 4),
    L("WLERI", "BNPTH", "SUTT Weleri - Bumi Putih (arah SS Pemalang)", 2, 4),
    L("PYUNG", "BSBRU", "SUTT Payung - Bawen Sambiroto Baru", 2, 3),
    L("KRAPK", "RDRUT", "SUTT Krapyak - Randu Garut", 2, 3, kno="11"),
    L("PDLAM", "SRDOL", "SUTT Pandean Lamper - Srondol", 2, 3),
    # Dashed on the figure: the Selima stubs are not yet energised.
    L("KLSRI", "SLIMA", "SUTT Kalisari - Selima (belum energize)", 2, 3,
      kno="6;7", st="Rencana"),
    L("SYUNG", "TJATI", "SUTT Sayung - Tanjung Jati (arah SS Tanjung Jati)", 2, 4),
    L("SYUNG", "KUDUS", "SUTT Sayung - Kudus (arah SS Tanjung Jati)", 2, 4),
]

SPEC = dict(
    code="SS_UNGARAN12",
    name="Ungaran 1,2",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.4 (Tabel 4.2, PDF p.147-152); "
               "topologi dari Gambar 4.4 Peta Kerawanan (PDF p.147)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(147, 152, expected=13),
)

if __name__ == "__main__":
    build_workbook(SPEC)
