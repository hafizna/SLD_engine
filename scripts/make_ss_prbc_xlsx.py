"""samples/ss_prbc_ingest.xlsx  -- Subsistem Priok - Bekasi 2,4 - Cawang 1.

Source: Buku Kerawanan SJB 2026 Sec 2.10 -- Gambar 2.9 (Peta Kerawanan, TWO SLD
pages, PDF p98) + Tabel 2.8 (7 titik kerawanan, PDF p99-101).

Three panels on PDF p98 -> three analytical views:
    BEKASI  -- sisi Bekasi & Muaratawar (GITET Bekasi IBT 2,4 -> BKASI;
               GITET Muaratawar IBT 1,2 -> MTWAR)  -- book p98 atas
    PRIOK   -- Priok, Muarakarang, Angke and Ancol
    CAWANG  -- GITET Cawang Baru IBT 1 -> CWBRU and descendants

Assets/relations are shared; `Sudut Pandang` says which view(s) draw each row.
Cross-panel connections have explicit reciprocal continuation bays.

Run: python scripts/make_ss_prbc_xlsx.py
"""
from __future__ import annotations

from _ss_xlsx_common import build_workbook

WIL = "DKI Jakarta"
BKS = ["BEKASI"]
PRK = ["PRIOK"]
BOTH = ["BEKASI", "PRIOK"]

VIEWS = [
    ("BEKASI", "Sisi Bekasi & Muaratawar",
     "BKASI;MTWAR", 82),
    ("PRIOK", "Sisi Priok & Cawang Baru",
     "PRTRU;PRTMR;PRBRT;MKLMA;CWBRU", 82),
]

ASSETS = [
    # ================= BEKASI view =================
    dict(code="BKASI", name="GITET Bekasi",     type="Busbar GITET", tier=1, kv="500 kV", views=BKS),
    dict(code="MTWAR", name="GITET Muaratawar", type="Busbar GITET", tier=1, kv="500 kV", views=BKS),
    dict(code="IBT 2 BKASI", name="IBT 2,4 Bekasi", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="2,4", bus150="BKASI", trafo=2, simbol="2 IBT (unit 2,4)", views=BKS),
    dict(code="IBT 1 MTWAR", name="IBT 1,2 Muaratawar", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="1,2", bus150="MTWAR", trafo=2, simbol="2 IBT (unit 1,2)", views=BKS),
    dict(code="BKASI", name="Bekasi (bus 150 kV)",     type="Busbar GI", tier=1, views=BKS),
    dict(code="MTWAR", name="Muaratawar (bus 150 kV)", type="Busbar GI", tier=1, views=BKS),
    # Bekasi Tier-2
    dict(code="MRNDA", name="Marunda",     type="Busbar GI", tier=2, views=BOTH),
    dict(code="PGDRU", name="Pegangsaan Dua", type="Busbar GI", tier=2, views=BKS),
    dict(code="RATER", name="Rawa Terate", type="Busbar GI", tier=2, kerawanan="4", views=BKS),
    dict(code="PGLNG", name="Penggilingan", type="Busbar GI", tier=2, kerawanan="4", views=BKS),
    dict(code="HNDAH", name="Harapan Indah", type="Busbar GI", tier=2, views=BOTH),
    dict(code="KDSPI", name="Kandang Sapi",  type="Busbar GI", tier=2, views=BOTH),
    # Bekasi Tier-3
    dict(code="PGDNGK", name="Pegangsaan Konv", type="Busbar GI", tier=3, views=BKS),
    dict(code="RAWAM", name="Rawa Makmur",   type="Busbar GI", tier=3, views=BKS),
    dict(code="RAKUN", name="Rawa Kucing",   type="Busbar GI", tier=3, views=BKS),
    dict(code="JGC",   name="JGC",           type="Busbar GI", tier=3, views=BKS),

    # ================= PRIOK view =================
    dict(code="CWBRU", name="GITET Cawang Baru", type="Busbar GITET", tier=1, kv="500 kV", views=PRK),
    dict(code="IBT 1 CWBRU", name="IBT 1 Cawang Baru", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="1", bus150="CWBRU", views=PRK),
    dict(code="CWBRU", name="Cawang Baru (bus 150 kV)", type="Busbar GI", tier=1, views=PRK),
    # generation
    dict(code="KIT_PRIOK_B3",  name="PLTGU Priok Blok 3",   type="Pembangkit", tier=1, kv="150 kV",
         kerawanan="5", views=PRK),
    dict(code="KIT_PRIOK_B12", name="PLTGU Priok Blok 1 & 2", type="Pembangkit", tier=1, kv="150 kV",
         kerawanan="5", views=PRK),
    dict(code="KIT_MKR_ST30",  name="PLTGU Muarakarang ST 3.0", type="Pembangkit", tier=1, kv="150 kV",
         views=PRK),
    # Priok Tier-1 (150 kV)
    dict(code="PRTRU", name="Priok Timur Lama",  type="Busbar GIS", tier=1, kerawanan="1;6", views=PRK),
    dict(code="PRTMR", name="Priok Timur Baru",  type="Busbar GIS", tier=1, kerawanan="1", views=PRK),
    dict(code="PRBRT", name="Priok Barat",       type="Busbar GIS", tier=1, kerawanan="6", views=PRK),
    dict(code="MKLMA", name="Muarakarang Lama",  type="Busbar GI",  tier=1, views=PRK),
    # Priok Tier-2
    dict(code="PLPNG40", name="Plumpang (40 KA)", type="Busbar GI", tier=2, kerawanan="2;6", views=PRK),
    dict(code="PLPNG20", name="Plumpang (20 KA)", type="Busbar GI", tier=2, kerawanan="6", views=PRK),
    dict(code="ANCOL", name="Ancol",             type="Busbar GI", tier=2, views=PRK),
    dict(code="KMYRN", name="Kemayoran",         type="Busbar GI", tier=2, views=PRK),
    dict(code="PLPRU", name="Pulo Gadung Baru",  type="Busbar GI", tier=2, kerawanan="7", views=PRK),
    dict(code="PGSAN", name="Pegangsaan",        type="Busbar GI", tier=2, kerawanan="6", views=PRK),
    dict(code="PLNDO", name="Pulo Mas Indo (KTT)", type="Busbar GI", tier=2, views=PRK),
    dict(code="ANGKE", name="Angke",             type="Busbar GI", tier=2, views=PRK),
    dict(code="CNANG", name="Cinang / Cawang Baru bawah", type="Busbar GI", tier=2, views=PRK),
    # Priok Tier-3
    dict(code="KLPGD", name="Kelapa Gading",     type="Busbar GI", tier=3, views=PRK),
    dict(code="PKRNG", name="Pekayon Raya",      type="Busbar GI", tier=3, views=PRK),
    dict(code="GMBRU", name="Gambir Baru",       type="Busbar GIS", tier=3, views=PRK),
    dict(code="SNTER", name="Sunter",            type="Busbar GI", tier=3, views=PRK),
    dict(code="GNSHR", name="Gunung Sahari",     type="Busbar GIS", tier=3, views=PRK),
    dict(code="PDMGN", name="Pademangan",        type="Busbar GI", tier=3, views=PRK),
    dict(code="MGBSR", name="Menteng Besar",     type="Busbar GIS", tier=3, views=PRK),
    dict(code="KLBRU", name="Kelapa Baru (KTT)", type="Busbar GI", tier=3, views=PRK),
    dict(code="PLMAS", name="Pulo Mas",          type="Busbar GI", tier=3, views=PRK),
    # Priok Tier-4
    dict(code="GDPLA", name="GIS Gedung Pola",   type="Busbar GIS", tier=4, kerawanan="3;7", views=PRK),
    dict(code="MGRAI", name="GIS Manggarai",     type="Busbar GIS", tier=4, kerawanan="3", views=PRK),
    dict(code="CMPTH", name="Cempaka Putih",     type="Busbar GI", tier=4, views=PRK),
    dict(code="TMTGI", name="Tomang Tinggi",     type="Busbar GI", tier=4, views=PRK),
    # Priok Tier-5
    dict(code="GMLMA", name="Gambir Lama",       type="Busbar GIS", tier=5, views=PRK),
    dict(code="DKTAS", name="GIS Dukuh Atas",    type="Busbar GIS", tier=5, kerawanan="3", views=PRK),
    # Priok Tier-6
    dict(code="KBSRH", name="GIS Kebon Sirih",   type="Busbar GIS", tier=6, views=PRK),
    dict(code="STBDI", name="Setiabudi",         type="Busbar GI", tier=6, views=PRK),
    dict(code="CWANG", name="Cawang Lama",       type="Busbar GI", tier=6, views=PRK),
]

BAYS = [
    ("PDKLP", "Pondok Kelapa (di BKASI)", "BKASI", None),
    ("SKTNI", "Sukatani (di BKASI)",      "BKASI", None),
    ("SMRCN", "Semper Cengkareng (di BKASI)", "BKASI", None),
    ("KTT_KESA", "KTT KESA (50 MVA, di PGDNGK)", "PGDNGK", None),
    ("KTT_WRGL", "KTT Wiraguna (35 MVA, di PGSAN)", "PGSAN", None),
    ("KTT_TOSAN", "KTT Tosan (105 MVA, di PGSAN)",  "PGSAN", None),
    ("KTT_VODA",  "KTT Vodafone (50 MVA, di PKRNG)", "PKRNG", None),
    ("MKRNG", "Muarakarang (bay di ANGKE)", "ANGKE", None),
    ("KTPNG", "Ketapang (bay di ANGKE)",    "ANGKE", None),
    ("KARET", "Karet (bay di ANGKE)",       "ANGKE", None),
]

L = lambda fr, to, nm, tf, tt, vw, kv=150, kno=None, st="Beroperasi": dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno, status=st,
    koridor=WIL, views=vw)

LINES = [
    # ===== BEKASI view =====
    L("BKASI", "MRNDA", "SUTT Bekasi - Marunda", 1, 2, BOTH),
    L("BKASI", "PGDRU", "SUTT Bekasi - Pegangsaan Dua", 1, 2, BKS),
    L("BKASI", "RATER", "SUTT Bekasi - Rawa Terate (Penggilingan-Rawa Terate single phi -- kerawanan #4)",
      1, 2, BKS, kno="4"),
    L("BKASI", "PGLNG", "SUTT Bekasi - Penggilingan (kerawanan #4)", 1, 2, BKS, kno="4"),
    L("BKASI", "HNDAH", "SUTT Bekasi - Harapan Indah", 1, 2, BOTH),
    L("BKASI", "KDSPI", "SUTT Bekasi - Kandang Sapi", 1, 2, BOTH),
    L("MTWAR", "HNDAH", "SUTT Muaratawar - Harapan Indah", 1, 2, BKS),
    L("MTWAR", "KDSPI", "SUTT Muaratawar - Kandang Sapi", 1, 2, BKS),
    L("MTWAR", "BKASI", "SUTET/Inc Muaratawar - Bekasi (rencana re-konfigurasi)", 1, 1, BKS, kv=500,
      st="Rencana"),
    L("RATER", "PGLNG", "SUTT Rawa Terate - Penggilingan (double phi -> single phi -- kerawanan #4)",
      2, 2, BKS, kno="4"),
    L("PGDRU", "PGDNGK", "SUTT Pegangsaan Dua - Pegangsaan Konv", 2, 3, BKS),
    L("RATER", "RAWAM", "SUTT Rawa Terate - Rawa Makmur", 2, 3, BKS),
    L("PGLNG", "RAKUN", "SUTT Penggilingan - Rawa Kucing", 2, 3, BKS),
    L("KDSPI", "JGC",   "SUTT Kandang Sapi - JGC", 2, 3, BKS),
    L("HNDAH", "MRNDA", "SUTT Harapan Indah - Marunda (tie)", 2, 2, BKS),

    # ===== PRIOK view =====
    # generation outlets
    L("KIT_PRIOK_B3",  "PRTRU", "Outlet PLTGU Priok Blok 3", 1, 1, PRK),
    L("KIT_PRIOK_B12", "PRBRT", "Outlet PLTGU Priok Blok 1 & 2", 1, 1, PRK),
    L("KIT_MKR_ST30",  "MKLMA", "Outlet PLTGU Muarakarang ST 3.0", 1, 1, PRK),
    # Priok busbar 500 kV -> Priok Timur / Priok Barat via IBT is drawn as a
    # bare 150 kV interconnector between the GIS sections
    L("PRTRU", "PRTMR", "Interconnector-1,2 Priok Timur Lama - Priok Timur Baru (tanpa PMT -- kerawanan #1)",
      1, 1, PRK, kno="1"),
    L("PRTMR", "PRBRT", "Interconnector Priok Timur Baru - Priok Barat", 1, 1, PRK),
    L("PRBRT", "PLPNG40", "SUTT Priok Barat - Plumpang Baru (tower combine -- kerawanan #2)",
      1, 2, PRK, kno="2"),
    L("PRTMR", "PLPNG20", "SUTT Priok Timur Baru - Plumpang (tower combine -- kerawanan #2)",
      1, 2, PRK, kno="2"),
    L("PRTRU", "PLPNG40", "SUTT Priok Timur Lama - Plumpang 40 KA", 1, 2, PRK),
    L("PRBRT", "ANCOL",  "SUTT Priok Barat - Ancol", 1, 2, PRK),
    L("PRBRT", "KMYRN",  "SUTT Priok Barat - Kemayoran", 1, 2, PRK),
    L("PRBRT", "PLPRU",  "SUTT Priok Barat - Pulo Gadung Baru (kerawanan #7)", 1, 2, PRK, kno="7"),
    L("PRBRT", "PGSAN",  "SUTT Priok Barat - Pegangsaan (arus 3I0 -- kerawanan #6)", 1, 2, PRK, kno="6"),
    L("MKLMA", "PLNDO",  "SUTT Muarakarang Lama - Pulo Mas Indo", 1, 2, PRK),
    L("MKLMA", "ANGKE",  "SUTT Muarakarang Lama - Angke", 1, 2, PRK),
    L("CWBRU", "CNANG",  "SUTT Cawang Baru - Cinang", 1, 2, PRK),
    L("PLPNG40", "PLPNG20", "Kopel Plumpang 40 KA - 20 KA (kerawanan #6)", 2, 2, PRK, kno="6"),
    # Priok Tier-2 -> Tier-3
    L("PLPNG40", "KLPGD", "SUTT Plumpang - Kelapa Gading", 2, 3, PRK),
    L("PLPNG20", "PKRNG", "SUTT Plumpang - Pekayon Raya", 2, 3, PRK),
    L("ANCOL", "GMBRU", "SUTT Ancol - Gambir Baru", 2, 3, PRK),
    L("ANCOL", "SNTER", "SUTT Ancol - Sunter", 2, 3, PRK),
    L("KMYRN", "GNSHR", "SUTT Kemayoran - Gunung Sahari", 2, 3, PRK),
    L("KMYRN", "PDMGN", "SUTT Kemayoran - Pademangan", 2, 3, PRK),
    L("PLPRU", "MGBSR", "SUTT Pulo Gadung Baru - Menteng Besar", 2, 3, PRK),
    L("PGSAN", "PLMAS", "SUTT Pegangsaan - Pulo Mas", 2, 3, PRK),
    L("PLNDO", "KLBRU", "SUTT Pulo Mas Indo - Kelapa Baru", 2, 3, PRK),
    L("CNANG", "PLMAS", "SUTT Cinang - Pulo Mas", 2, 3, PRK),
    # Priok Tier-3 -> Tier-4
    L("GNSHR", "GDPLA", "SKTT Gunung Sahari - Gedung Pola (kerawanan #3,7)", 3, 4, PRK, kno="3"),
    L("MGBSR", "MGRAI", "SKTT Menteng Besar - Manggarai (kerawanan #3)", 3, 4, PRK, kno="3"),
    L("PLMAS", "CMPTH", "SUTT Pulo Mas - Cempaka Putih", 3, 4, PRK),
    L("PLMAS", "TMTGI", "SUTT Pulo Mas - Tomang Tinggi", 3, 4, PRK),
    L("PLMAS", "MGRAI", "SKTT Pulo Mas - Manggarai", 3, 4, PRK),
    # Priok Tier-4 -> Tier-5
    L("MGRAI", "GDPLA", "SKTT 150 kV Manggarai - Gedung Pola (1 sirkit -- kerawanan #3)",
      4, 4, PRK, kno="3"),
    L("MGRAI", "DKTAS", "SKTT 150 kV Manggarai - Dukuh Atas (1 sirkit -- kerawanan #3)",
      4, 5, PRK, kno="3"),
    L("GDPLA", "GMLMA", "SKTT Gedung Pola - Gambir Lama", 4, 5, PRK),
    L("CMPTH", "GMLMA", "SUTT Cempaka Putih - Gambir Lama", 4, 5, PRK),
    # Priok Tier-5 -> Tier-6
    L("DKTAS", "KBSRH", "SKTT Dukuh Atas - Kebon Sirih", 5, 6, PRK),
    L("DKTAS", "STBDI", "SKTT Dukuh Atas - Setiabudi", 5, 6, PRK),
    L("GMLMA", "KBSRH", "SKTT Gambir Lama - Kebon Sirih", 5, 6, PRK),
    L("STBDI", "CWANG", "SUTT Setiabudi - Cawang Lama", 6, 6, PRK),
]

RISKS = [
    dict(no=1, uit="JBB", category="N-1",
         kondisi="Tidak ada PMT pada interconnector-1&2 Priok Timur Lama arah Priok Barat.",
         dampak="1. Pemeliharaan Interconnector pada ruas tersebut sulit dilakukan karena harus "
                "memadamkan busbar GIS Priok Barat. 2. Apabila terjadi gangguan pada interconnector "
                "berdampak padam busbar pada GIS 150 kV Priok Barat dan GIS 150 kV Priok Timur.",
         mitigasi="Pengaturan penjadwalan pemeliharaan dilakukan bersamaan pekerjaan pemeliharaan busbar.",
         usulan="Jangka Pendek: Usulan penambahan PMT bay Interconnector-1&2 Priok Barat GIS Priok "
                "Timur Lama. Rencana COD Tahun 2028."),
    dict(no=2, uit="JBB", category="N-2",
         kondisi="Terdapat permasalahan tower combine pada ruas SUTT Priok Barat - Plumpang Baru dan "
                 "Priok Timur Baru - Plumpang.",
         dampak="1. Pemeliharaan pada ruas tersebut sulit dilakukan. 2. Evolusi subsistem sulit dilakukan.",
         mitigasi="1. Pengaturan pembangkitan saat pemeliharaan. 2. Penjadwalan pemeliharaan disamakan "
                  "dengan jadwal pemeliharaan pembangkitan.",
         usulan="Jangka Menengah: Usulan pembangunan SKTT Priok Timur Baru-Sunter-Kandang Sapi dan "
                "SKTT Kemayoran-Cempaka Putih. Rencana COD Tahun 2030."),
    dict(no=3, uit="JBB", category="N-1",
         kondisi="Konfigurasi SKTT 150 kV Manggarai-Gedung Pola dan SKTT 150 kV Manggarai-Dukuh Atas "
                 "hanya ada 1 sirkit (Pelanggan VVIP masuk kategori zero down time). Jika hanya ada "
                 "1 sirkit maka konfigurasi tersebut menjadi kurang andal.",
         dampak="Terjadi pemadaman di GIS Gedung Pola dan GIS Dukuh Atas sebesar 89 MW (Data EOB 2024) "
                "apabila gangguan pada SKTT 150 kV Manggarai-Dukuh Atas.",
         mitigasi="Pengaturan beban (Splitting Busbar di GIS Gedung Pola dan Dukuh Atas).",
         usulan="Jangka Pendek: 1. Pembangunan sirkit ke-2 SKTT 150 kV Manggarai-Dukuh Atas (RUPTL "
                "2025-2034, COD 2026). 2. Pembangunan sirkit ke-2 SKTT 150 kV Manggarai-Gedung Pola "
                "(RUPTL 2025-2034, COD 2027)."),
    dict(no=4, uit="JBB", category="N-1",
         kondisi="Terjadi kerusakan/Breakdown pada Bay Line-1 penghantar SUTT 150 kV Penggilingan-"
                 "Rawa Terate (Ex-Bay Pulogadung Baru) sehingga konfigurasi yang tadinya Double Phi "
                 "menjadi tidak andal karena masih Single Phi (di GIS Penggilingan).",
         dampak="Pada saat pemeliharaan harus mempertimbangkan kemampuan kapasitas penghantar.",
         mitigasi="-",
         usulan="Jangka Pendek: Percepatan perbaikan Line Bay-1 Arah Rater dan Line Bay-1 Bekasi, "
                "Material sudah onsite Oktober 2023 (sudah terkontrak). Perkiraan COD tahun 2026."),
    dict(no=5, uit="JBB", category="N-1-1",
         kondisi="Terjadi fenomena power swing saat gangguan di SS Priok-Cawang 1-Bekasi 2,4 yang "
                 "menyebabkan Pembangkitan Priok ikut trip.",
         dampak="Subsistem mengalami pemadaman meluas dan menyebabkan keandalan berkurang.",
         mitigasi="1. Sudah dilakukan penugasan studi ke Akademisi LAPI ITB untuk menganalisa "
                  "fenomena power swing di SS Priok (2021). 2. Pemasangan Defense Scheme OLS IBT "
                  "untuk Splitting IBT Cawang dan IBT Bekasi jika terjadi gangguan N-2-1.",
         usulan="Jangka Pendek: 1. Pembangunan SUTET 500 kV Muaratawar-Priok untuk Re-konfigurasi "
                "subsistem (RUPTL 2025-2034, COD timeline proyek Des 2026). 2. Pembangunan outlet IBT "
                "GITET Muaratawar SUTT Muaratawar-Inc Bekasi-Plumpang/Kandang Sapi (Nov 2026). "
                "3. Usulan Section pada GIS 150 kV Pegangsaan (COD 2027)."),
    dict(no=6, uit="JBB", category="N-1",
         kondisi="Terjadi fenomena arus 3 I0 pada subsistem Priok-Cawang-Bekasi di sekitar GI Priok "
                 "Barat - Priok Timur - Priok Timur Baru - Plumpang - Pegangsaan dan sekitarnya.",
         dampak="Terjadinya trip penghantar akibat relay GFR bekerja, padahal tidak ada gangguan eksternal.",
         mitigasi="1. Penugasan studi dari UIT JBB ke Puslitbang untuk menganalisa fenomena 3 I0 (2021). "
                  "2. UIT JBB menaikkan setting GFR. 3. Pengaturan pola operasi pembangkit saat ada "
                  "pekerjaan di ruas Priok Barat-Priok Timur-Priok Timur Baru.",
         usulan="Jangka Pendek: Pembangunan SUTET 500 kV Muaratawar-Priok untuk Re-konfigurasi "
                "subsistem (RUPTL 2025-2034, COD timeline proyek Des 2026)."),
    dict(no=7, uit="JBB", category="N-1",
         kondisi="GIS Gedung Pola merupakan pasokan VVIP ke beberapa kantor duta besar negara-negara "
                 "(Zero downtime) sehingga keandalan GIS tersebut menjadi prioritas namun GIS "
                 "Gedungpola masih beroperasi dengan single busbar sehingga ketika terjadi gangguan "
                 "busbar pada GIS Gedungpola akan berdampak padam GIS.",
         dampak="1. Keandalan berkurang untuk pasokan VVIP (zero downtime) di GIS Gedung Pola karena "
                "masih single busbar. 2. Kesulitan dalam pemeliharaan busbar.",
         mitigasi="Manuver beban trafo di GIS Gedung Pola melalui 20 kV.",
         usulan="Jangka Pendek: Pemasangan double busbar GIS Gedung Pola (satu lingkup pekerjaan "
                "sirkit ke-2 SKTT 150 kV Manggarai-Gedung Pola, rencana COD Tahun 2027)."),
]

# Each panel is a projection of the same physical network. Cross-panel edges
# remain explicit and acquire reciprocal continuation bays, never duplicate GI.
VIEWS = [
    ('BEKASI', 'Sisi Bekasi & Muaratawar', 'BKASI;MTWAR', 82),
    ('PRIOK', 'Sisi Priok', 'PRTRU;PRTMR;PRBRT;MKLMA', 82),
    ('CAWANG', 'Sisi Cawang Baru', 'CWBRU', 82),
]
CAWANG_CODES = {'CWBRU', 'CNANG', 'PLMAS', 'CMPTH', 'TMTGI', 'MGRAI',
                'GMLMA', 'DKTAS', 'KBSRH', 'STBDI', 'CWANG'}
BEKASI_CODES = {a['code'] for a in ASSETS if 'BEKASI' in a.get('views', [])}
def panel(code):
    base = code.split()[-1] if code.startswith('IBT ') else code
    return 'CAWANG' if base in CAWANG_CODES else ('BEKASI' if base in BEKASI_CODES else 'PRIOK')

# Restore individually identified units; Jumlah Trafo is not an IBT unit list.
for base, unit in [('BKASI', '4'), ('MTWAR', '2')]:
    original = next(a for a in ASSETS if a['code'].startswith('IBT ') and a['code'].endswith(base))
    original['trafo'] = 1
    ASSETS.append({**original, 'code': f'IBT {unit} {base}', 'ibt': unit,
                   'name': f'IBT {unit} {base}', 'simbol': ''})
for a in ASSETS:
    a['views'] = [panel(a['code'])]

LINES += [
    L('ANGKE', 'ANCOL', 'SUTT Angke - Ancol', 2, 2, PRK),
    L('MRNDA', 'KLBRU', 'SKTT Marunda - Kelapa Baru (lanjutan antar panel)', 2, 3, BOTH),
    {**L('HNDAH', 'PLPNG40', 'SUTT Harapan Indah - Plumpang 40 KA (lanjutan)', 2, 2, BOTH), 'sirkit': 1},
    {**L('KDSPI', 'PLPNG40', 'SUTT Kandang Sapi - Plumpang 40 KA (lanjutan)', 2, 2, BOTH), 'sirkit': 1},
]
BAYS = [(*b[:4], 1, 'Beroperasi', [panel(b[2])]) for b in BAYS]
for line in LINES:
    left, right = panel(line['fr']), panel(line['to'])
    line['views'] = list(dict.fromkeys([left, right]))
    if left != right:
        for endpoint, feeder, view in [(line['fr'], line['to'], right), (line['to'], line['fr'], left)]:
            BAYS.append((endpoint, endpoint + ' (lanjutan panel ' + panel(endpoint) + ')', feeder,
                         None, line.get('sirkit', 2), line.get('status', 'Beroperasi'), [view]))
BAYS.append(('CWANG', 'Cawang (lanjutan)', 'STBDI', None, 2, 'Beroperasi', ['CAWANG']))

SPEC = dict(
    code="SS_PRBC",
    name="Priok - Bekasi 2,4 - Cawang 1",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.10 (Gambar 2.9 PDF98, tiga panel; Tabel 2.8); koreksi Angke-Ancol pengguna 2026-09-12",
    views=VIEWS,
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=RISKS,
)

if __name__ == "__main__":
    build_workbook(SPEC)
