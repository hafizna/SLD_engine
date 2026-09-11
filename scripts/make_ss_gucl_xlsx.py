"""samples/ss_gucl_ingest.xlsx  -- Subsistem GU Cilegon - Cilegon Baru 1,2,3 - Labuan.

Source: Buku Kerawanan SJB 2026 Sec 2.4 -- Gambar 2.3 (Peta Kerawanan, PDF p82)
+ Tabel 2.2 (7 titik kerawanan, PDF p82-84).

Large 150 kV subsystem (~8 Tier bands). One 500 kV injection point:
    GITET Cilegon Baru -> IBT 1,2,3 (500/150) -> bus CLBRU
plus PLTGU Cilegon (steps up onto CLBRU) and PLTU Labuan (steps up onto LBUAN).
Relations traced from Gambar 2.3; node codes are the figure's labels. The deep
customer tails (KTT captive substations) are modelled as hanging bays.

Run: python scripts/make_ss_gucl_xlsx.py
"""
from __future__ import annotations

from _ss_xlsx_common import build_workbook

WIL = "Banten"

ASSETS = [
    # ---- 500 kV source ----
    dict(code="CLBRU", name="GITET Cilegon Baru",  type="Busbar GITET", tier=1, kv="500 kV"),
    # IBT 1,2,3 collapsed to one row (2 IBT+ on one bus -> multi-IBT ingest path mid-fix)
    dict(code="IBT 1 CLBRU", name="IBT 1,2,3 Cilegon Baru", type="IBT 3-Winding", tier=2,
         kv="500/150 kV", ibt="1", bus150="CLBRU", trafo=3, simbol="3 IBT (unit 1,2,3)", kerawanan="1"),
    # ---- generation ----
    dict(code="KIT_PLTGU_CLG", name="PLTGU Cilegon", type="Pembangkit", tier=1, kv="150 kV"),
    dict(code="KIT_PLTU_LBN",  name="PLTU Labuan",   type="Pembangkit", tier=1, kv="150 kV"),
    dict(code="KIT_PLTU_ASAHI", name="PLTU Asahi (aset milik)", type="Pembangkit", tier=2, kv="150 kV"),

    # ---- Tier-1 (150 kV injection / gen buses) ----
    dict(code="CLBRU", name="Cilegon Baru (bus 150 kV)", type="Busbar GI", tier=1, kerawanan="4"),
    dict(code="LBUAN", name="Labuan", type="Busbar GI", tier=1),

    # ---- Tier-2 ----
    dict(code="KRWTU", name="Kramatwatu",      type="Busbar GI", tier=2, kerawanan="3"),
    dict(code="MNA",   name="MNA / Trate",     type="Busbar GI", tier=2, kerawanan="3"),
    dict(code="ALNDO", name="Alindo",          type="Busbar GI", tier=2),
    dict(code="INFRO", name="IFERO",           type="Busbar GI", tier=2),
    dict(code="ASAHI", name="Asahimas",        type="Busbar GI", tier=2, kerawanan="5"),
    dict(code="KDL",   name="Krakatau Daya Listrik (KDL)", type="Busbar GI", tier=2),
    dict(code="CLGON", name="Cilegon Lama",    type="Busbar GI", tier=2),
    dict(code="MENES", name="Menes",           type="Busbar GI", tier=2),
    dict(code="SKETI", name="Saketi",          type="Busbar GI", tier=2),
    dict(code="POLMA", name="Polyprima",       type="Busbar GI", tier=2, kerawanan="6"),

    # ---- Tier-3 ----
    dict(code="SRANG", name="Serang",          type="Busbar GI", tier=3, kerawanan="7"),
    dict(code="CASRI", name="Cikande Serang (CASRI)", type="Busbar GI", tier=3),
    dict(code="ANYER", name="Anyer",           type="Busbar GI", tier=3),
    dict(code="KSTEL", name="KTT KSTEL",       type="Busbar GI", tier=3),
    dict(code="MITSUI", name="Mitsui",         type="Busbar GI", tier=3),
    dict(code="MCOIS", name="MCOIS",           type="Busbar GI", tier=3),
    dict(code="RKBRU", name="Rangkas Baru",    type="Busbar GI", tier=3),
    dict(code="MPING", name="Malimping",       type="Busbar GI", tier=3),

    # ---- Tier-4 ----
    dict(code="GNMLA", name="Gunung Malang (GMS)", type="Busbar GI", tier=4, kerawanan="4"),
    dict(code="BAROS", name="Baros",           type="Busbar GI", tier=4),
    dict(code="KOPOS", name="Kopo Serang",     type="Busbar GI", tier=4, kerawanan="2"),
    dict(code="BUBRU", name="Bubulak Baru",    type="Busbar GI", tier=4),
    dict(code="BAYAH", name="Bayah",           type="Busbar GI", tier=4),

    # ---- Tier-5 ----
    dict(code="IKIAT", name="Indah Kiat",      type="Busbar GI", tier=5, kerawanan="2"),
    dict(code="CKNDE", name="Cikande",         type="Busbar GITET", tier=5, kv="150 kV", kerawanan="2"),
    dict(code="RGKOT", name="Rangkasbitung Kota", type="Busbar GI", tier=5),
    dict(code="MDERN", name="Modern",          type="Busbar GI", tier=5),
    dict(code="LBI",   name="Labuan Industri", type="Busbar GI", tier=5),

    # ---- Tier-6 ----
    dict(code="BLRJA", name="Balaraja (sisi Cilegon)", type="Busbar GI", tier=6, kerawanan="4"),
    dict(code="PUCAM", name="Pucam",           type="Busbar GI", tier=6, kerawanan="2"),
    dict(code="KOPO",  name="Kopo",            type="Busbar GI", tier=6),

    # ---- Tier-7 ----
    dict(code="GORDA", name="Gorda",           type="Busbar GI", tier=7, kerawanan="7"),
    dict(code="NBRJA", name="New Balaraja",    type="Busbar GI", tier=7),
    dict(code="SVRNA", name="Suvarna",         type="Busbar GI", tier=7),
]

BAYS = [
    ("KTT_POSCO", "KTT Posco (145 MVA, di CLBRU)", "CLBRU", None),
    ("KTT_MNA",   "KTT MNA (30 MVA)",              "MNA",   None),
    ("KTT_ALNDO", "KTT Alindo (55 MVA)",           "ALNDO", None),
    ("KTT_IFERO1", "KTT-1 IFERO (80 MVA)",         "INFRO", None),
    ("KTT_IFERO2", "KTT-2 IFERO",                  "INFRO", None),
    ("KTT_PLPHM", "KTT PLPHM (32 MVA)",            "POLMA", None),
    ("KTT_ASAHI2", "KTT Asahi-2 (123 MVA)",        "ASAHI", None),
    ("KTT_ASAHI3", "KTT Asahi-3 (95 MVA)",         "ASAHI", None),
    ("KTT_NSI",   "KTT NSI (30 MVA)",              "CASRI", None),
    ("KTT_CASRI", "KTT Cikande Serang (54 MVA)",   "CASRI", None),
    ("KTT_CASRI2", "KTT Cikande Serang II (70 MVA)", "CASRI", None),
    ("KTT_GMS",   "KTT GMS (85 MVA)",              "GNMLA", None),
    ("KTT_JAS",   "KTT JAS (50 MVA)",              "CKNDE", None),
    ("KTT_IKIAT", "KTT Indah Kiat (58.8 MVA)",     "IKIAT", None),
    ("KTT_NKMAS", "KTT Nikomas (60 MVA)",          "PUCAM", None),
    ("KTT_GRDMS", "KTT Gerdamas (60 MVA)",         "GORDA", None),
    ("KTT_SMTOR", "KTT Sumitomo (30 MVA)",         "GORDA", None),
    ("KTT_LBI",   "KTT Labuan Industri (60 MVA)",  "LBI",   None),
    ("KRACAK",    "Kracak (spur)",                 "BLRJA", None),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi": dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno, status=st, koridor=WIL)

LINES = [
    # generation outlets
    L("KIT_PLTGU_CLG", "CLBRU", "Outlet PLTGU Cilegon", 1, 1),
    L("KIT_PLTU_LBN",  "LBUAN", "Outlet PLTU Labuan",   1, 1),
    L("KIT_PLTU_ASAHI", "ASAHI", "Outlet PLTU Asahi (aset milik)", 2, 2),

    # ---- CLBRU (Tier-1) fan-out ----
    L("CLBRU", "KRWTU", "SUTT Cilegon Baru - Kramatwatu", 1, 2, kno="3"),
    L("CLBRU", "MNA",   "SUTT Cilegon Baru - MNA (single phi -- kerawanan #3,5)", 1, 2, kno="3"),
    L("CLBRU", "ASAHI", "SUTT Cilegon Baru - Asahimas", 1, 2),
    L("CLBRU", "POLMA", "SUTT Cilegon Baru - Polyprima (single phi -- kerawanan #5)", 1, 2, kno="5"),
    L("CLBRU", "KDL",   "SUTT Cilegon Baru - KDL", 1, 2),
    L("CLBRU", "ALNDO", "SUTT Cilegon Baru - Alindo", 1, 2),
    L("CLBRU", "INFRO", "SUTT Cilegon Baru - IFERO", 1, 2),
    L("CLBRU", "CLGON", "SUTT Cilegon Baru - Cilegon Lama", 1, 2),
    L("CLBRU", "MENES", "SUTT Cilegon Baru - Menes", 1, 2),
    L("CLBRU", "LBUAN", "SUTT Cilegon Baru - Labuan", 1, 1),

    # ---- Tier-2 ties + fan-out ----
    L("MNA", "KRWTU", "SUTT MNA - Kramatwatu (single phi -- kerawanan #3)", 2, 2, kno="3"),
    L("ASAHI", "POLMA", "SUTT Asahimas - Polyprima (single phi -- kerawanan #5)", 2, 2, kno="5"),
    L("ASAHI", "CASRI", "SUTT Asahimas - Cikande Serang", 2, 3),
    L("ASAHI", "ANYER", "SUTT Asahimas - Anyer", 2, 3),
    L("KDL",   "KSTEL", "SUTT KDL - KTT KSTEL", 2, 3),
    L("CLGON", "MITSUI", "SUTT Cilegon Lama - Mitsui", 2, 3),
    L("CLGON", "MCOIS", "SUTT Cilegon Lama - MCOIS", 2, 3),
    L("MENES", "RKBRU", "SUTT Menes - Rangkas Baru", 2, 3),
    L("MENES", "SKETI", "SUTT Menes - Saketi", 2, 2),
    L("LBUAN", "SKETI", "SUTT Labuan - Saketi", 1, 2),
    L("SKETI", "MPING", "SUTT Saketi - Malimping", 2, 3),

    # ---- Tier-3 ----
    L("CASRI", "ANYER", "SUTT Cikande Serang - Anyer (tie sehadap)", 3, 3),
    L("CASRI", "SRANG", "SUTT Cikande Serang - Serang (kerawanan #7)", 3, 3, kno="7"),
    L("ANYER", "KSTEL", "SUTT Anyer - KTT KSTEL", 3, 3),
    L("RKBRU", "KOPOS", "SUTT Rangkas Baru - Kopo Serang", 3, 4),
    L("RKBRU", "BUBRU", "SUTT Rangkas Baru - Bubulak Baru", 3, 4),
    L("MPING", "BAYAH", "SUTT Malimping - Bayah", 3, 4),

    # ---- Serang -> Tier-4 ----
    L("SRANG", "GNMLA", "SUTT Serang - GMS (kerawanan #4,7)", 3, 4, kno="4"),
    L("SRANG", "BAROS", "SUTT Serang - Baros", 3, 4),
    L("SRANG", "GORDA", "SUTT Serang - GMS - Gorda (kerawanan #7)", 3, 7, kno="7"),

    # ---- Tier-4 -> Tier-5 ----
    L("GNMLA", "IKIAT", "SUTT GMS - Indah Kiat (kerawanan #2,3,4)", 4, 5, kno="2"),
    L("GNMLA", "CKNDE", "SUTT GMS - Cikande (kerawanan #2,3,4)", 4, 5, kno="4"),
    L("BAROS", "RGKOT", "SUTT Baros - Rangkasbitung Kota", 4, 5),
    L("KOPOS", "MDERN", "SUTT Kopo Serang - Modern (kerawanan #2)", 4, 5, kno="2"),
    L("BUBRU", "LBI",   "SUTT Bubulak Baru - Labuan Industri", 4, 5),
    L("KOPOS", "LBI",   "SUTT Kopo Serang - Labuan Industri (tie)", 4, 5),

    # ---- Tier-5 -> Tier-6 ----
    L("CKNDE", "BLRJA", "SUTT Cikande - Balaraja (kerawanan #4)", 5, 6, kno="4"),
    L("CKNDE", "PUCAM", "SUTT Cikande - Pucam 1,2 (kerawanan #2)", 5, 6, kno="2"),
    L("IKIAT", "BLRJA", "SUTT Indah Kiat - Balaraja", 5, 6),
    L("MDERN", "KOPO",  "SUTT Modern - Kopo", 5, 6),

    # ---- Tier-6 -> Tier-7 ----
    L("BLRJA", "NBRJA", "SUTT Balaraja - New Balaraja", 6, 7),
    L("BLRJA", "SVRNA", "SUTT Balaraja - Suvarna", 6, 7),
    L("PUCAM", "GORDA", "SUTT Pucam - Gorda (kerawanan #2,7)", 6, 7, kno="2"),
]

RISKS = [
    dict(no=1, uit="JBB", category="N-1",
         kondisi="Pembebanan IBT Cilegon tidak memenuhi kriteria N-1 saat PLTGU Cilegon atau "
                 "PLTU Labuan tidak beroperasi 1 unit.",
         dampak="1. Pemeliharaan IBT sulit dilakukan. 2. Terjadi pemadaman apabila trip salah "
                "satu IBT di Cilegon.",
         mitigasi="1. Pemindahan beban GI Cikande & GI Balaraja ke Subsistem Balaraja 1&2-Lontar-"
                  "Kembangan 1,2. 2. Pemindahan beban Trafo-1 GI Cilegon Baru, KTT Posco dan KTT "
                  "KSTEL ke Sub Sistem Suralaya Unit 3-Suralaya 1,2-Cilegon. 3. Pemindahan beban GI "
                  "Saketi dan Malimping ke Subsistem Pelabuhan Ratu. 4. OLS IBT Cilegon tahap 1-4 "
                  "total 614 MW. 5. Rencana penambahan DS OLS IBT Cilegon total 666 MW. "
                  "6. Usulan pengoperasian 2 GT PLTGU Cilegon.",
         usulan="Jangka Pendek: Pembangunan GITET Cikande + outlet (RUPTL 2025-2034, COD 2027). "
                "Jangka Menengah: Usulan IBT-1 & 2 di GITET Jawa 7 + outlet (diusulkan COD 2029). "
                "Jangka Panjang: BESS tersebar di GI 150 kV Cilegon dan Menes 2x100 MW (COD 2032)."),
    dict(no=2, uit="JBB", category="N-1",
         kondisi="Subsistem memiliki 6 tier dan tidak dapat dilakukan Splitting beban karena sumber "
                 "IBT terpusat di GI Cilegon Baru. Terjadi Drop Tegangan <135 kV di GI PUCAM, Modern, "
                 "Kopo, Gorda, Indah Kiat, Cikande (semua Konsumen Tegangan Tinggi) bila 1 unit PLTU "
                 "Labuan atau GT PLTGU Cilegon tidak beroperasi.",
         dampak="1. Terjadi Drop Tegangan <135 kV di GI PUCAM, Modern, Kopo, Gorda, Indah Kiat, "
                "Cikande. 2. Komplain Drop dan Dip Tegangan Pelanggan Konsumen Tegangan Tinggi.",
         mitigasi="1. Pengaturan MVAR Pembangkit. 2. Pengaturan TAP CHANGER di IBT-1,2&3 Cilegon Baru. "
                  "3. Pemindahan beban GI Cikande & GI Balaraja ke Subsistem Balaraja 1&2-Lontar-"
                  "Kembangan 1,2.",
         usulan="Jangka Pendek: GITET Cikande (Tx SUTET Bojanegara-Balaraja) COD 2026; SUTT 150 kV "
                "Tigaraksa-Tigaraksa II (COD Okt 2025); SUTT 150 kV Baros-Rangkas (COD 2026); SUTT "
                "150 kV Tigaraksa II-Kopo (COD 2028); usulan kapasitor 2x50 Mvar di GI Kopo dan IKPP "
                "(COD 2028)."),
    dict(no=3, uit="JBB", category="N-2",
         kondisi="Potensi Drop tegangan bila terjadi N-2 di ruas SUTT 150 kV Cilegon Baru-Kramatwatu, "
                 "Cilegon Baru-MNA, Serang-GMS 1,2, Cikande-IKPP, Cikande-GMS, Cikande-Pucam 1,2.",
         dampak="1. Permasalahan stabilitas tegangan pada subsistem Cilegon Baru 1,2,3-GU Cilegon "
                "dan Labuan. 2. Komplain Drop dan Dip Tegangan Pelanggan KTT. 3. Kesulitan pemeliharaan.",
         mitigasi="1. Pengaturan MVAR Pembangkit. 2. Pengaturan TAP CHANGER di IBT-1,2&3 Cilegon Baru. "
                  "3. Pemindahan beban GI Cikande & GI Balaraja ke Subsistem Balaraja 1,2-Lontar-"
                  "Kembangan 1,2. 4. Pengaturan pekerjaan di beban rendah/hari libur. 5. Pemindahan "
                  "beban GI Saketi dan Malingping ke Subsistem Pelabuhan Ratu. 6. Usulan rele UVLS.",
         usulan="Jangka Pendek: GITET Cikande + outlet (COD 2026); SUTT 150 kV Baros-Rangkas (COD 2026); "
                "usulan kapasitor 2x50 Mvar di GI Kopo dan IKPP (COD 2028)."),
    dict(no=4, uit="JBB", category="N-1",
         kondisi="Kenaikan arus hubung singkat melebihi BC PMT terkecil di GI 150 kV Cilegon Baru, "
                 "Serang, GMS, Balaraja, dan Cikande saat GITET Cikande dan outletnya beroperasi.",
         dampak="Terjadi kerusakan peralatan pada GI Cilegon Baru, Serang, GMS, Balaraja, dan Cikande "
                "saat terjadi gangguan baik 3 Phase maupun 1 Phase.",
         mitigasi="1. Pengaturan pola pengoperasian Pembangkit di Subsistem Cilegon. 2. Pengaturan "
                  "Pola Splitting pada GI 150 kV Cilegon Baru.",
         usulan="Jangka Pendek: SUTT 150 kV Baros-Rangkas (COD 2026); usulan penggantian 31 PMT "
                "kapasitas lebih tinggi (COD 2027); usulan FCL 10 ohm pada ruas SUTT 150 kV Asahimas-"
                "Polyprima I Cilegon (COD 2027)."),
    dict(no=5, uit="JBB", category="N-1-1",
         kondisi="1. Ruas Penghantar SUTT 150 kV Cilegon Baru-Polyprima-Asahi masih single phi. "
                 "2. Ruas Penghantar SUTT 150 kV Cilegon Baru-MNA, Cilegon Baru-Kramatwatu dan "
                 "MNA-Kramatwatu masih single phi.",
         dampak="1. Saat terjadi N-1-1 GI KTT Polyprima padam. 2. Saat terjadi N-1-1 GI MNA padam.",
         mitigasi="Pengaturan penjadwalan pemeliharaan penghantar.",
         usulan="Jangka Menengah: Usulan Double Phi ruas SUTT Cilegon Baru-Polyprima-Asahi (COD 2029); "
                "Usulan Double Phi ruas SUTT Cilegon Baru-MNA-Kramatwatu (COD 2029)."),
    dict(no=6, uit="JBB", category="N-1",
         kondisi="GI 150 kV Polyprima masih operasi single busbar.",
         dampak="1. Saat terjadi gangguan N-1 Busbar berdampak GI dan KTT Polyprima padam. "
                "2. Kesulitan dalam pemeliharaan busbar.",
         mitigasi="Pengaturan penjadwalan pemeliharaan busbar.",
         usulan="Jangka Menengah: Usulan double busbar GI 150 kV Polyprima (COD 2029)."),
    dict(no=7, uit="JBB", category="N-1",
         kondisi="Ruas Penghantar SUTT 150 kV Serang - GMS tidak memenuhi kriteria N-1 saat KTT di "
                 "wilayah Sub Sistem Cilegon beroperasi penuh.",
         dampak="Ruas Penghantar yang beroperasi overload dan trip sehingga menyebabkan drop tegangan "
                "(<120 kV) pada GI 150 kV Cikande, Pucam, Modern, Gorda, Kopo.",
         mitigasi="1. Pengaturan MVAR Pembangkit. 2. Pengaturan TAP CHANGER di IBT-1,2&3 Cilegon Baru. "
                  "3. Pemindahan beban GI Cikande & GI Balaraja ke Subsistem Balaraja 1,2-Lontar-"
                  "Kembangan 1,2. 4. Pengaturan pekerjaan di beban rendah/hari libur. 5. Usulan rele UVLS.",
         usulan="Jangka Pendek: SUTT 150 kV Baros-Rangkas (COD 2026); usulan kapasitor 2x50 Mvar di "
                "GI Kopo dan IKPP (COD 2026); GITET Cikande + outlet (COD 2026)."),
]

SPEC = dict(
    code="SS_GUCL",
    name="GU Cilegon - Cilegon Baru 1,2,3 - Labuan",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.4 (Gambar 2.3 + Tabel 2.2)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=RISKS,
)

if __name__ == "__main__":
    build_workbook(SPEC)
