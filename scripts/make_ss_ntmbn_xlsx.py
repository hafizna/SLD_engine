"""samples/ss_ntmbn_ingest.xlsx -- Subsistem New Tambun (UP2B Jawa Barat).

Source: Buku Kerawanan SJB 2026 Sec 3.8, Gambar 3.11 (Peta Kerawanan, PDF p.135)
and Tabel 3.9. The table's rows sit on PDF p.136-137, NOT on the section heading
page: Tasikmalaya's table runs past this section's heading and its risk #5 is
still on p.135, so a heading-based range picks up a neighbour's row.

GITET New Tambun 500 kV (NTMBN) steps down through 2 IBT onto the Tier-1 150 kV
bus. Tier-2 is TMBUN, Tier-3 GDMKR and PCBRU, Tier-4 NPNCL. TYGRI hangs off
Tier-3 in grey on the figure -- a customer/KTT asset rather than a PLN GI.

Two boundaries, both drawn on the figure with their owning subsystem in
brackets and both modelled as SOURCE_BOUNDARY:

  JTWRG  "(UP2B JAKBAN)"    -- Jatiwaringin, on the Bekasi 1,3 - Cibinong 3
                               sheet, which draws this same tie from its side
                               as its own "UP2B 2 (JABAR) NEW TAMBUN" box
  RJPSI  "(SS CBATU 1,2)"   -- Rajapolah/Rejosari toward Cibatu 1,2 - Deltamas

Risk 1 is the IBT pair itself, risk 2 sits on TMBUN.

Run: python scripts/make_ss_ntmbn_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"

ASSETS = [
    dict(code="NTMBN7", name="GITET New Tambun", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 NTMBN7", name="IBT 1 New Tambun 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1",
         bus_hv="NTMBN7", bus_lv="NTMBN", trafo=1, kerawanan="1"),
    dict(code="IBT 2 NTMBN7", name="IBT 2 New Tambun 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="2",
         bus_hv="NTMBN7", bus_lv="NTMBN", trafo=1, kerawanan="1"),
    dict(code="NTMBN", name="New Tambun (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="TMBUN", name="Tambun", type="Busbar GI", tier=2, kerawanan="2"),
    dict(code="GDMKR", name="Gedung Mekar", type="Busbar GI", tier=3),
    dict(code="PCBRU", name="Pancoran Baru", type="Busbar GI", tier=3),
    dict(code="NPNCL", name="Nusa Pancal", type="Busbar GI", tier=4),
    # Grey on Gambar 3.11: a customer-owned bus, not a PLN GI.
    dict(code="TYGRI", name="Tygri (aset milik KTT)", type="Busbar GI", tier=4,
         simbol="aset milik KTT", status="Milik Pelanggan"),
    # -- batas subsistem, digambar dengan pemiliknya dalam kurung --
    dict(code="JTWRG", name="Jatiwaringin (UP2B Jakban)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Bekasi 1,3 - Cibinong 3"),
    dict(code="RJPSI", name="Rejosari (SS Cibatu 1,2)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 1,2 - Deltamas 1,2"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("NTMBN", "TMBUN", "SUTT New Tambun - Tambun", 1, 2, kno="2"),
    L("NTMBN", "JTWRG", "SUTT New Tambun - Jatiwaringin (arah UP2B Jakban)", 1, 2),
    L("TMBUN", "GDMKR", "SUTT Tambun - Gedung Mekar", 2, 3),
    L("TMBUN", "PCBRU", "SUTT Tambun - Pancoran Baru", 2, 3),
    L("PCBRU", "NPNCL", "SUTT Pancoran Baru - Nusa Pancal", 3, 4),
    L("GDMKR", "RJPSI", "SUTT Gedung Mekar - Rejosari (arah SS Cibatu 1,2)", 3, 4),
    L("PCBRU", "TYGRI", "SUTT Pancoran Baru - Tygri (aset milik KTT)", 3, 4, sirkit=1),
]

SPEC = dict(
    code="SS_NTMBN",
    name="New Tambun",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.8 (Tabel 3.9, PDF p.135-136); "
               "topologi dari Gambar 3.11 Peta Kerawanan (PDF p.135)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(136, 137, expected=2),
)

if __name__ == "__main__":
    build_workbook(SPEC)
