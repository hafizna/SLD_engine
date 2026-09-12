"""samples/ss_plbratu_ingest.xlsx -- Subsistem Pelabuhan Ratu - Salak -
Cibinong 1,2 - Depok 2 (UP2B Jakarta & Banten).

Source: Buku Kerawanan SJB 2026 Sec 2.11, Gambar 2.10 (Peta Kerawanan, PDF
p.101) and Tabel 2.9 (PDF p.101-104).

**This subsistem is MULTIVIEW.** Gambar 2.10 draws it as two side-by-side
panels because one canvas cannot hold it, exactly like SS_LBK. The workbook
declares two `Sudut Pandang` over ONE canonical GI graph:

    CIBINONG  -- sisi Cibinong 1,2 + Depok 2 (left panel)
    SALAK     -- sisi Salak - Pelabuhan Ratu (right panel)

The two panels are joined by GIs the book draws in BOTH: BGBRU (Bogor Baru),
SNTUL (Sentul) and KTLPA (Katulampa). Those rows carry both view keys, so each
side keeps its own tier and edges while the engine still reconciles them to one
canonical substation -- the point of the multiview path.

Three 500/150 kV injections:
    GITET Cibinong      -> IBT 1,2 -> CIBNG  (Tier-1, sisi Cibinong)
    GITET Depok         -> IBT 2   -> DEPOK  (Tier-1, sisi Cibinong)
    (sisi Salak is fed by generation, not by an IBT)

Generation on the Salak side: PLTP Salak Lama unit 1,2,3 and unit Binary and
PLTP Salak Baru unit 4,5,6 on SALAK/SLBRU, PLTU Pelabuhan Ratu unit 1,2,3 on
PRATU, and PLTA Ubrug unit 1,2,3 on the 70 kV UBRUG bus.

A 70 kV sub-network (drawn orange) hangs under the Cibinong side -- CIBN4,
CLGSI, SMNRU, SMNMA -- plus KTT-owned customer transformers (KTT Aspek, KTT
ITP, KTT Sucofindo, KTT Cemindo) which are shown dashed as customer assets.

Two UP2B Jabar boundary boxes appear on the Salak panel and are modelled as
SOURCE_BOUNDARY, same as in the Bekasi sheet:
    off KTLPA : "UP2B 2 (JABAR)  CNJUR : - / CGRLG : Trf 9,10"
    off LBSTU : "UP2B 2 (JABAR)  CNJUR : - / CGRLG : Trf 9,10 / LGDAR : Trf 1,2,3,4"

Kerawanan #2 and #9 are single-phi configurations (GIS Salak Baru T/L bay arah
Bogor Baru and Cibadak Baru), so those ruas carry Single Phi = Ya.

Run: python scripts/make_ss_plbratu_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"
CBN = ["CIBINONG"]
SLK = ["SALAK"]
BOTH = ["CIBINONG", "SALAK"]

VIEWS = [
    ("CIBINONG", "Sisi Cibinong 1,2 - Depok 2", "CIBNG;DEPOK", 101),
    ("SALAK", "Sisi Salak - Pelabuhan Ratu", "SALAK;PRATU", 101),
]

ASSETS = [
    # ================= sisi Cibinong: 500 kV + IBT =================
    dict(code="CIBNG7", name="GITET Cibinong", type="Busbar GITET", tier=1,
         kv="500 kV", views=CBN),
    dict(code="IBT 1 CIBNG7", name="IBT 1,2 Cibinong 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1,2", bus_hv="CIBNG7", bus_lv="CIBNG", trafo=2,
         simbol="2 IBT (unit 1,2)", views=CBN),
    dict(code="DEPOK7", name="GITET Depok", type="Busbar GITET", tier=1,
         kv="500 kV", views=CBN),
    dict(code="IBT 2 DEPOK7", name="IBT 2 Depok 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="DEPOK7", bus_lv="DEPOK", trafo=1,
         simbol="1 IBT (unit 2)", views=CBN),
    # ================= sisi Cibinong: 150 kV =================
    dict(code="CIBNG", name="Cibinong (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section + kopel", kerawanan="5", views=CBN),
    dict(code="DEPOK", name="Depok (bus 150 kV)", type="Busbar GI", tier=1,
         views=CBN),
    dict(code="SMNRU", name="Semen Baru", type="Busbar GI", tier=2, views=CBN),
    dict(code="CMGIS", name="Cimanggis (GIS)", type="Busbar GIS", tier=2, views=CBN),
    dict(code="ITP", name="ITP", type="Busbar GI", tier=3,
         simbol="KTT ITP 220 MVA", views=CBN),
    dict(code="DPBRU", name="Depok Baru", type="Busbar GI", tier=2, views=CBN),
    # 70 kV sub-network (orange on Gambar 2.10). Each 70 kV island is reached
    # from the 150 kV network through an IBT 150/70 kV, drawn on Gambar 2.10 as
    # an orange transformer pair dropping off the 150 kV bus -- without these
    # rows the 70 kV buses float as a disconnected island in the rendered SLD.
    dict(code="IBT 1 CIBNG", name="IBT 150/70 kV Cibinong", type="IBT 3-Winding",
         tier=2, kv="150/70 kV", ibt="1", bus_hv="CIBNG", bus_lv="CIBN4", trafo=2,
         simbol="2 IBT 150/70 kV", views=CBN),
    dict(code="CIBN4", name="Cibinong (bus 70 kV)", type="Busbar GI", tier=2,
         kv=70, views=CBN),
    dict(code="CLGSI", name="Cileungsi", type="Busbar GI", tier=3, kv=70,
         simbol="KTT Aspek 40 MVA", views=CBN),
    # Gambar 2.10 puts the 70 kV Semen Baru bus on Tier-3, in the same row as
    # Cileungsi, fed by its own IBT from the 150 kV Semen Baru bus on Tier-2.
    dict(code="IBT 1 SMNRU", name="IBT 150/70 kV Semen Baru", type="IBT 3-Winding",
         tier=3, kv="150/70 kV", ibt="1", bus_hv="SMNRU", bus_lv="SMNRU4", trafo=1,
         simbol="IBT 150/70 kV", views=CBN),
    dict(code="SMNRU4", name="Semen Baru (bus 70 kV)", type="Busbar GI", tier=3,
         kv=70, views=CBN),
    dict(code="SMNMA", name="Semen Mas", type="Busbar GI", tier=4, kv=70,
         simbol="KTT Sucofindo 40 MVA", views=CBN),
    dict(code="GDRIA", name="Gandaria", type="Busbar GI", tier=3,
         simbol="aset milik KTT", views=CBN),
    # ================= sisi Salak / Pelabuhan Ratu =================
    dict(code="SALAK", name="Salak", type="Busbar GI", tier=1, views=SLK),
    dict(code="SLBRU", name="Salak Baru (GIS)", type="Busbar GIS", tier=1,
         simbol="T/L bay single phi arah Bogor Baru & Cibadak Baru",
         kerawanan="2", views=SLK),
    dict(code="PRATU", name="Pelabuhan Ratu", type="Busbar GI", tier=1,
         kerawanan="7", views=SLK),
    dict(code="CBDRU", name="Cibadak Baru", type="Busbar GI", tier=2,
         kerawanan="7", views=SLK),
    dict(code="BAYAH", name="Bayah", type="Busbar GI", tier=2,
         simbol="KTT Cemindo 70 MVA", views=SLK),
    dict(code="SJAWA", name="Semen Jawa", type="Busbar GI", tier=2,
         kerawanan="8", views=SLK),
    dict(code="CIAWI", name="Ciawi", type="Busbar GI", tier=2, views=SLK),
    dict(code="LBSTU", name="Lembur Situ", type="Busbar GI", tier=3,
         kerawanan="8", views=SLK),
    dict(code="JMPNG", name="Jampang", type="Busbar GI", tier=2, views=SLK),
    dict(code="MPING", name="Mangunreja/Mping", type="Busbar GI", tier=2, views=SLK),
    # 70 kV sisi Salak -- fed from the 150 kV CBDRU bus through its IBT 150/70.
    dict(code="IBT 1 CBDRU", name="IBT 150/70 kV Cibadak", type="IBT 3-Winding",
         tier=3, kv="150/70 kV", ibt="1", bus_hv="CBDRU", bus_lv="CBDK4", trafo=1,
         simbol="IBT 150/70 kV", views=SLK),
    dict(code="CBDK4", name="Cibadak (bus 70 kV)", type="Busbar GI", tier=3,
         kv=70, views=SLK),
    dict(code="UBRUG", name="Ubrug", type="Busbar GI", tier=3, kv=70, views=SLK),
    dict(code="PRATU4", name="Pelabuhan Ratu (bus 70 kV)", type="Busbar GI",
         tier=4, kv=70, views=SLK),
    # ================= GI yang muncul di KEDUA panel =================
    dict(code="BGBRU", name="Bogor Baru", type="Busbar GI", tier=2,
         simbol="GI simpul; trafo >70%", kerawanan="1;6", views=BOTH),
    dict(code="SNTUL", name="Sentul", type="Busbar GI", tier=2,
         kerawanan="3", views=BOTH),
    dict(code="KTLPA", name="Katulampa", type="Busbar GI", tier=3,
         kerawanan="4", views=BOTH),
    # ================= pembangkit =================
    dict(code="KIT_SALAK", name="PLTP Salak Lama unit 1,2,3", type="Pembangkit",
         tier=1, kv="150 kV", views=SLK),
    dict(code="KIT_SALAKB", name="PLTP Salak Lama unit Binary", type="Pembangkit",
         tier=1, kv="150 kV", views=SLK),
    dict(code="KIT_SLBRU", name="PLTP Salak Baru unit 4,5,6", type="Pembangkit",
         tier=1, kv="150 kV", views=SLK),
    dict(code="KIT_PRATU", name="PLTU Pelabuhan Ratu unit 1,2,3", type="Pembangkit",
         tier=1, kv="150 kV", views=SLK),
    dict(code="KIT_UBRUG", name="PLTA Ubrug unit 1,2,3", type="Pembangkit",
         tier=3, kv="70 kV", views=SLK),
    # ============ batas ke UP2B Jawa Barat ============
    dict(code="CGRLG", name="Cianjur/Cugenang (UP2B Jabar)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="UP2B 2 (JABAR): CNJUR : - / CGRLG : Trf 9,10", views=SLK),
    dict(code="LGDAR", name="Lengkong Dar (UP2B Jabar)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="UP2B 2 (JABAR): LGDAR Trf 1,2,3,4", views=SLK),
]

BAYS = [
    ("JTRBR", "Jatiroto Baru", "CIBNG", None, 1, "Beroperasi", CBN),
]

def L(fr, to, nm, tf, tt, views, kv=150, kno=None, st="Beroperasi", sirkit=2, sp=False):
    return dict(fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt,
                kerawanan=kno, status=st, sirkit=sirkit, single_phi=sp,
                koridor=WIL, views=views)

LINES = [
    # ================= sisi Cibinong =================
    L("CIBNG", "SMNRU", "SUTT Cibinong - Semen Baru", 1, 2, CBN),
    L("CIBNG", "CMGIS", "SUTT Cibinong - Cimanggis", 1, 2, CBN),
    L("CIBNG", "SNTUL", "SUTT Cibinong - Sentul", 1, 2, CBN, kno="3"),
    L("CIBNG", "GDRIA", "SUTT Cibinong - Gandaria", 1, 3, CBN),
    L("CIBNG", "DPBRU", "SUTT Cibinong - Depok Baru", 1, 2, CBN),
    L("DEPOK", "DPBRU", "SUTT Depok - Depok Baru", 1, 2, CBN),
    L("SMNRU", "ITP", "SUTT Semen Baru - ITP", 2, 3, CBN),
    # kerawanan #1: Bogor Baru GI simpul; #6 trafo >70%
    L("CIBNG", "BGBRU", "SUTT Cibinong - Bogor Baru", 1, 2, CBN, kno="1"),
    # kerawanan #3: Bogor Baru - Sentul derating CCC 1350 A -> 1000 A.
    # Both endpoints are drawn on BOTH panels, so the ruas must be too --
    # scoping it to one view leaves the other view with a dangling endpoint.
    L("BGBRU", "SNTUL", "SUTT Bogor Baru - Sentul (derating andongan T.14-T.15)",
      2, 2, BOTH, kno="3"),
    # 70 kV sisi Cibinong. Gambar 2.10 runs the 70 kV chain Cibinong -> Cileungsi
    # (Tier-3), while the 70 kV Semen Baru bus is fed by its OWN IBT off the
    # 150 kV Semen Baru bus and continues down to Semen Mas -- the two 70 kV
    # groups are not tied to each other at this voltage.
    L("CIBN4", "CLGSI", "SUTT 70 kV Cibinong - Cileungsi", 2, 3, CBN, kv=70),
    L("SMNRU4", "SMNMA", "SUTT 70 kV Semen Baru - Semen Mas", 3, 4, CBN, kv=70),
    # ================= sisi Salak =================
    L("KIT_SALAK", "SALAK", "Outlet PLTP Salak Lama 1,2,3", 1, 1, SLK, sirkit=1),
    L("KIT_SALAKB", "SALAK", "Outlet PLTP Salak Lama Binary", 1, 1, SLK, sirkit=1),
    L("KIT_SLBRU", "SLBRU", "Outlet PLTP Salak Baru 4,5,6", 1, 1, SLK, sirkit=1),
    L("KIT_PRATU", "PRATU", "Outlet PLTU Pelabuhan Ratu 1,2,3", 1, 1, SLK, sirkit=1),
    L("SALAK", "SLBRU", "SUTT Salak - Salak Baru", 1, 1, SLK),
    # kerawanan #2: single phi di GIS Salak Baru T/L bay arah Bogor Baru
    L("SLBRU", "BGBRU", "SUTT Salak Baru - Bogor Baru (single phi)",
      1, 2, SLK, kno="2", sirkit=1, sp=True),
    # kerawanan #7: PRATU - Cibadak Baru (N-2 -> kit pratu tidak stabil)
    L("PRATU", "CBDRU", "SUTT Pelabuhan Ratu - Cibadak Baru", 1, 2, SLK, kno="7"),
    L("SLBRU", "CBDRU", "SUTT Salak Baru - Cibadak Baru (single phi)",
      1, 2, SLK, kno="2", sirkit=1, sp=True),
    # kerawanan #8: Pelabuhan Ratu - Lembur Situ - Semen Jawa rating 1600 A
    L("PRATU", "SJAWA", "SUTT Pelabuhan Ratu - Semen Jawa", 1, 2, SLK, kno="8"),
    L("SJAWA", "LBSTU", "SUTT Semen Jawa - Lembur Situ", 2, 3, SLK, kno="8"),
    L("PRATU", "BAYAH", "SUTT Pelabuhan Ratu - Bayah", 1, 2, SLK),
    L("PRATU", "MPING", "SUTT Pelabuhan Ratu - Mping", 1, 2, SLK),
    L("PRATU", "JMPNG", "SUTT Pelabuhan Ratu - Jampang", 1, 2, SLK),
    L("CBDRU", "CIAWI", "SUTT Cibadak Baru - Ciawi", 2, 2, SLK),
    # kerawanan #4: Bogor Baru - Katulampa - Cianjur rating arus kecil 600 A.
    # BGBRU and KTLPA are both drawn on both panels -- see the BGBRU-SNTUL note.
    L("BGBRU", "KTLPA", "SUTT Bogor Baru - Katulampa (rating 600 A, Dove 327,94 mm2)",
      2, 3, BOTH, kno="4"),
    L("KTLPA", "CGRLG", "SUTT Katulampa - Cugenang (arah UP2B Jabar)", 3, 4, SLK),
    L("LBSTU", "LGDAR", "SUTT Lembur Situ - Lengkong Dar (arah UP2B Jabar)", 3, 4, SLK),
    # 70 kV sisi Salak
    L("KIT_UBRUG", "UBRUG", "Outlet PLTA Ubrug 1,2,3", 3, 3, SLK, kv=70, sirkit=1),
    L("CBDK4", "UBRUG", "SUTT 70 kV Cibadak - Ubrug", 3, 3, SLK, kv=70),
    L("UBRUG", "PRATU4", "SUTT 70 kV Ubrug - Pelabuhan Ratu", 3, 4, SLK, kv=70),
]

SPEC = dict(
    code="SS_PLBRATU",
    name="Pelabuhan Ratu - Salak - Cibinong 1,2 - Depok 2",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.11 (Tabel 2.9, PDF p.101-104); "
               "topologi dari Gambar 2.10 Peta Kerawanan, dua panel (PDF p.101)",
    views=VIEWS,
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(101, 104, expected=8),
)

if __name__ == "__main__":
    build_workbook(SPEC)
