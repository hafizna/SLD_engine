"""samples/ss_pedan34_ingest.xlsx -- Subsistem Pedan 3,4 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.6, Gambar 4.6 (Peta Kerawanan, PDF p.158)
and Tabel 4.4 (PDF p.159-164). Completes UP2B Jawa Tengah & DIY.

GITET Pedan 500 kV steps down through IBT 3,4 onto the PEDAN Tier-1 bus. A
second Tier-1 bus, PCTAN, carries PLTU Pacitan. Three branches:
    west   PEDAN - KNTUG - GDEAN - BANTL - WBJAN
    east   PEDAN - WSARI - SLBRU / RAYUM - PALUR - MSRAN - SRAGN
    PCTAN  - NGTDI - WNGRI, which ties back into RAYUM

The KNTUG-GDEAN and BANTL-WBJAN stubs are drawn dashed, so they carry status
Rencana.

Boundaries, all mirrored on a neighbouring sheet:
    SGRAH/MDARI, GJYAN   "SS TJATI"      -- Tanjung Jati 1,2 - Ungaran 3 holds
                                            all three
    WATES                "SS KSGHN"      -- Kesugihan 1,2
    SMANU, GDRJO         "SS PEDAN 1,2"  -- the neighbouring Pedan sheet
    NGAWI                "SS KEDIRI"     -- UP2B Jawa Timur

Run: python scripts/make_ss_pedan34_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    dict(code="PEDAN7", name="GITET Pedan", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 3 PEDAN7", name="IBT 3,4 Pedan 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="3",
         bus_hv="PEDAN7", bus_lv="PEDAN", trafo=2,
         simbol="2 IBT (unit 3,4)", kerawanan="1;2"),
    dict(code="PEDAN", name="Pedan (bus 150 kV)", type="Busbar GI", tier=1),
    # -- Tier-1 kedua: PLTU Pacitan --
    dict(code="PCTAN", name="Pacitan", type="Busbar GI", tier=1),
    dict(code="KIT_PCTAN", name="PLTU Pacitan", type="Pembangkit", tier=1,
         kv="150 kV"),
    # -- cabang barat --
    dict(code="KNTUG", name="Kanetug", type="Busbar GI", tier=2, kerawanan="11"),
    dict(code="GDEAN", name="Godean", type="Busbar GI", tier=3,
         status="Rencana", kerawanan="3;4"),
    dict(code="BANTL", name="Bantul", type="Busbar GI", tier=4, kerawanan="8"),
    dict(code="WBJAN", name="Wonosari Bejan", type="Busbar GI", tier=5,
         status="Rencana"),
    # -- cabang timur --
    dict(code="WSARI", name="Wonosari", type="Busbar GI", tier=2, kerawanan="10"),
    dict(code="SLBRU", name="Solo Baru", type="Busbar GI", tier=3, kerawanan="5"),
    dict(code="RAYUM", name="Rayung", type="Busbar GI", tier=3,
         simbol="KTT RUM", kerawanan="6"),
    dict(code="PALUR", name="Palur", type="Busbar GI", tier=4),
    dict(code="MSRAN", name="Masaran", type="Busbar GI", tier=5, kerawanan="9"),
    dict(code="SRAGN", name="Sragen", type="Busbar GI", tier=6, kerawanan="7"),
    # -- cabang Pacitan --
    dict(code="NGTDI", name="Ngunut/Ngadi", type="Busbar GI", tier=2),
    dict(code="WNGRI", name="Wonogiri", type="Busbar GI", tier=3),
    # -- batas subsistem --
    dict(code="SGRAH", name="Sugihrahayu/Mandari (SS Tanjung Jati)",
         type="Busbar GI", tier=3, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Tanjung Jati 1,2 - Ungaran 3"),
    dict(code="GJYAN", name="Gajahan (SS Tanjung Jati)", type="Busbar GI",
         tier=3, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Tanjung Jati 1,2 - Ungaran 3"),
    dict(code="WATES", name="Wates (SS Kesugihan)", type="Busbar GI", tier=5,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Kesugihan 1,2"),
    dict(code="SMANU", name="Semanu (SS Pedan 1,2)", type="Busbar GI", tier=5,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Pedan 1,2"),
    dict(code="GDRJO", name="Gondangrejo (SS Pedan 1,2)", type="Busbar GI",
         tier=5, role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Pedan 1,2"),
    dict(code="NGAWI", name="Ngawi (SS Kediri)", type="Busbar GI", tier=7,
         role="SOURCE_BOUNDARY", simbol="batas ke UP2B Jawa Timur (SS Kediri)"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("KIT_PCTAN", "PCTAN", "Outlet PLTU Pacitan", 1, 1, sirkit=1),
    # -- cabang barat --
    L("PEDAN", "KNTUG", "SUTT Pedan - Kanetug", 1, 2, kno="11"),
    L("KNTUG", "SGRAH", "SUTT Kanetug - Sugihrahayu (arah SS Tanjung Jati)", 2, 3),
    # Dashed on Gambar 4.6: not yet energised.
    L("KNTUG", "GDEAN", "SUTT Kanetug - Godean (belum energize)", 2, 3,
      kno="3", st="Rencana"),
    L("KNTUG", "GJYAN", "SUTT Kanetug - Gajahan (arah SS Tanjung Jati)", 2, 3),
    L("PEDAN", "BANTL", "SUTT Pedan - Bantul", 1, 4, kno="4"),
    L("BANTL", "WATES", "SUTT Bantul - Wates (arah SS Kesugihan)", 4, 5, kno="8"),
    L("BANTL", "SMANU", "SUTT Bantul - Semanu (arah SS Pedan 1,2)", 4, 5),
    L("BANTL", "WBJAN", "SUTT Bantul - Wonosari Bejan (belum energize)", 4, 5,
      st="Rencana"),
    # -- cabang timur --
    L("PEDAN", "WSARI", "SUTT Pedan - Wonosari", 1, 2, kno="10"),
    L("WSARI", "SLBRU", "SUTT Wonosari - Solo Baru", 2, 3, kno="5"),
    L("WSARI", "RAYUM", "SUTT Wonosari - Rayung", 2, 3, kno="6"),
    L("SLBRU", "PALUR", "SUTT Solo Baru - Palur", 3, 4),
    L("PALUR", "GDRJO", "SUTT Palur - Gondangrejo (arah SS Pedan 1,2)", 4, 5),
    L("PALUR", "MSRAN", "SUTT Palur - Masaran", 4, 5, kno="9"),
    L("MSRAN", "SRAGN", "SUTT Masaran - Sragen", 5, 6, kno="7"),
    L("SRAGN", "NGAWI", "SUTT Sragen - Ngawi (arah UP2B Jatim)", 6, 7),
    # -- cabang Pacitan --
    L("PCTAN", "NGTDI", "SUTT Pacitan - Ngadi", 1, 2),
    L("NGTDI", "WNGRI", "SUTT Ngadi - Wonogiri", 2, 3),
    L("WNGRI", "RAYUM", "SUTT Wonogiri - Rayung", 3, 3),
]

SPEC = dict(
    code="SS_PEDAN34",
    name="Pedan 3,4",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.6 (Tabel 4.4, PDF p.159-164); "
               "topologi dari Gambar 4.6 Peta Kerawanan (PDF p.158)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(159, 164, expected=11),
)

if __name__ == "__main__":
    build_workbook(SPEC)
