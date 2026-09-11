"""Build the 500 kV backbone ingest workbook from the Buku Kerawanan SJB 2026
Tabel 1.1.A (Kerawanan SUTET 500 kV, points 1-31, PDF p23-38) and Gambar 1.4
(Peta Kerawanan SUTET 500 kV, PDF p22).

Relations here are read from the kerawanan TABLE, not guessed from the crossing
lines in the figure. GITET codes match the figure's labels; the figure only
fixes the Tier band of each GITET.

Output: samples/backbone_500_ingest.xlsx  (5 sheets, one view).
Run:    python scripts/make_backbone_500_xlsx.py
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Font

OUT = Path(__file__).resolve().parents[1] / "samples" / "backbone_500_ingest.xlsx"

VIEW = "BACKBONE500"

# ---------------------------------------------------------------------------
# GITET busbars + generating units.  (code, name, tier, kind, has_gen, wilayah)
#   tier: the -TIER-n band the GITET sits in on Gambar 1.4
#   kind: "Busbar GITET" | "Pembangkit"
#   has_gen: a KIT complex connects here (the "~" symbol in the figure)
# The figure's Tier bands:  T1 = generation-side GITET,  higher T = further in.
# ---------------------------------------------------------------------------
GITETS = [
    # ---- Tier 1 ----
    ("JAWA7",  "GITET Jawa 7",              1, True,  "Banten"),
    ("LBE",    "GITET Lontar Baru (LBE)",   1, True,  "Banten"),
    ("NSRLA",  "GITET Suralaya Baru",       1, True,  "Banten"),
    ("SRLYA",  "GITET Suralaya",            1, True,  "Banten"),
    ("JAWA910","GITET Jawa 9,10",           1, True,  "Banten"),
    ("PRIDK",  "GITET Priok",               1, True,  "DKI Jakarta"),
    ("MTWAR",  "GITET Muara Tawar",         1, True,  "Jawa Barat"),
    ("CLMYA",  "GITET Cilamaya",            1, True,  "Jawa Barat"),
    ("CRATA",  "GITET Cirata",              1, True,  "Jawa Barat"),
    ("SGLNG",  "GITET Saguling",            1, True,  "Jawa Barat"),
    ("ADPLA",  "GITET Adipala",             1, True,  "Jawa Tengah"),
    ("CLCAP",  "GITET Cilacap",             1, True,  "Jawa Tengah"),
    ("BTANG",  "GITET Batang",              1, True,  "Jawa Tengah"),
    ("NTJTI",  "GITET New Tanjung Jati",    1, True,  "Jawa Tengah"),
    ("TJATI",  "GITET Tanjung Jati B",      1, True,  "Jawa Tengah"),
    ("GRSIK",  "GITET Gresik",              1, True,  "Jawa Timur"),
    ("GRATI",  "GITET Grati",               1, True,  "Jawa Timur"),
    ("PITON",  "GITET Paiton",              1, True,  "Jawa Timur"),
    # ---- Tier 2 ----
    ("BLRJA",  "GITET Balaraja",            2, False, "Banten"),
    ("CLGON",  "GITET Cilegon",             2, False, "Banten"),
    ("TMBUN",  "GITET Tambun",              2, False, "Jawa Barat"),
    ("CWANG",  "GITET Cawang",              2, False, "DKI Jakarta"),
    ("SKTNI",  "GITET Sukatani",            2, False, "Jawa Barat"),
    ("DLTMS",  "GITET Deltamas",            2, False, "Jawa Barat"),
    ("CIBNG",  "GITET Cibinong",            2, False, "Jawa Barat"),
    ("BDSLN",  "GITET Bandung Selatan",     2, False, "Jawa Barat"),
    ("KSGHN",  "GITET Kesugihan",           2, False, "Jawa Tengah"),
    ("PMLNG",  "GITET Pemalang",            2, False, "Jawa Tengah"),
    ("UNGRN",  "GITET Ungaran",             2, False, "Jawa Tengah"),
    ("KRIAN",  "GITET Krian",               2, False, "Jawa Timur"),
    ("KDIRI",  "GITET Kediri",              2, False, "Jawa Timur"),
    # ---- Tier 3 ----
    ("LNGKG",  "GITET Lengkong",            3, False, "Banten"),
    ("KMBNG",  "GITET Kembangan",           3, False, "DKI Jakarta"),
    ("BKASI",  "GITET Bekasi",              3, False, "Jawa Barat"),
    ("CBATU",  "GITET Cibatu",              3, False, "Jawa Barat"),
    ("UBRNG",  "GITET Ujungberung",         3, False, "Jawa Barat"),
    ("IDMYU",  "GITET Indramayu",           3, False, "Jawa Barat"),
    ("MDCAN",  "GITET Mandirancan",         3, False, "Jawa Barat"),
    ("TSMYA",  "GITET Tasikmalaya",         3, False, "Jawa Barat"),
    ("BYOLI",  "GITET Boyolali",            3, False, "Jawa Tengah"),
    ("PEDAN",  "GITET Pedan",               3, False, "Jawa Tengah"),
    ("NBANG",  "GITET Ngimbang",            3, False, "Jawa Timur"),
    # ---- Tier 4 ----
    ("DEPOK",  "GITET Depok",               4, False, "Jawa Barat"),
    ("GNDUL",  "GITET Gandul",              4, False, "Jawa Barat"),
    # ---- Tier 5 ----
    ("DKSBI",  "GITET Durikosambi",         5, False, "DKI Jakarta"),
    # ---- Tier 6 ----
    ("MKRNG",  "GITET Muara Karang",        6, False, "DKI Jakarta"),
]
TIER = {code: t for code, _, t, *_ in GITETS}

# ---------------------------------------------------------------------------
# SUTET ruas.  (from, to, sirkit, status, kerawanan_no, koridor)
#   Read from Tabel 1.1.A "Kondisi" / "Dampak" columns and from mitigation
#   text ("Sudah terpasang OGS SUTET X-Y", "SUTET X-Y trip 1 sirkit ...").
#   status "Beroperasi" unless the text says the ruas is a plan.
# ---------------------------------------------------------------------------
SUTET = [
    # -- Banten generation -> Balaraja / Cilegon / LBE / Lengkong --
    ("JAWA7",  "BLRJA", 2, "Beroperasi", 14, "Banten"),          # #14
    ("JAWA7",  "LBE",   2, "Beroperasi", 15, "Banten"),          # #15 (Jawa7-LBE)
    ("SRLYA",  "NSRLA", 2, "Beroperasi", 13, "Banten"),          # #13 Suralaya-Suralaya Baru
    ("NSRLA",  "LBE",   2, "Beroperasi", 12, "Banten"),          # #12 Suralaya Baru-LBE
    ("SRLYA",  "BLRJA", 2, "Beroperasi", 16, "Banten"),          # #16 Suralaya-Balaraja
    ("SRLYA",  "CLGON", 2, "Beroperasi", 11, "Banten"),          # #11 Suralaya 9,10-Cilegon
    ("JAWA910","CLGON", 2, "Beroperasi", None, "Banten"),
    ("BLRJA",  "LNGKG", 2, "Beroperasi", 17, "Banten"),          # #17 Balaraja-Lengkong >60%
    ("LBE",    "BLRJA", 2, "Beroperasi", None, "Banten"),
    # -- Banten/Jakarta core: Cilegon-Cibinong, Gandul-Depok, Depok-Cibinong --
    ("CLGON",  "CIBNG", 1, "Beroperasi", 1,  "Banten-Jawa Barat"),   # #1 N-2, 1 sirkit
    ("GNDUL",  "DEPOK", 2, "Beroperasi", 2,  "DKI Jakarta"),         # #2 Gandul-Depok (also #9 rotor stability)
    ("DEPOK",  "CIBNG", 2, "Beroperasi", 3,  "Jawa Barat"),          # #3 Depok-Cibinong (also #6 IBT overload)
    ("LNGKG",  "GNDUL", 2, "Beroperasi", None, "Banten-Jakarta"),
    ("KMBNG",  "GNDUL", 2, "Beroperasi", None, "DKI Jakarta"),
    # -- Gandul/Kembangan -> Durikosambi -> Muara Karang (radial ke IBT) --
    ("GNDUL",  "DKSBI", 2, "Beroperasi", 7,  "DKI Jakarta"),         # #7 Gandul-Durkos 55%
    ("KMBNG",  "DKSBI", 2, "Beroperasi", None, "DKI Jakarta"),       # #7 Kembangan-Durkos 43% (pinned to #7 via Gandul ruas)
    ("DKSBI",  "MKRNG", 2, "Beroperasi", 8,  "DKI Jakarta"),         # #8 N-2 Durkos-Muarakarang
    # -- segiempat Jakarta timur: Muaratawar-Cawang / Tambun-Bekasi --
    ("MTWAR",  "CWANG", 2, "Beroperasi", 5,  "Jawa Barat-Jakarta"),  # #5 Muaratawar-Cawang 55% (also #10)
    ("MTWAR",  "TMBUN", 2, "Beroperasi", None, "Jawa Barat"),
    ("TMBUN",  "BKASI", 2, "Beroperasi", 4,  "Jawa Barat"),          # #4 Tambun-Bekasi 70% (also #10)
    ("BKASI",  "MTWAR", 2, "Rencana",    None, "Jawa Barat"),        # usulan 2 sirkit baru Bekasi-Muaratawar (#4)
    ("MTWAR",  "PRIDK", 2, "Rencana",    None, "Jawa Barat-Jakarta"),# usulan SUTET Muaratawar-Priok
    ("PRIDK",  "MKRNG", 2, "Rencana",    None, "DKI Jakarta"),       # usulan SUTET Priok-Muarakarang
    ("CWANG",  "GNDUL", 2, "Rencana",    None, "DKI Jakarta"),       # usulan SUTET Cawang-Gandul
    # -- Jawa Barat selatan / tengah --
    ("SKTNI",  "CLMYA", 2, "Beroperasi", 18, "Jawa Barat"),          # #18 N-2 Sukatani-Cilamaya (PLTGU 2x880)
    ("SKTNI",  "CBATU", 2, "Beroperasi", None, "Jawa Barat"),
    ("DLTMS",  "CBATU", 2, "Beroperasi", None, "Jawa Barat"),
    ("CRATA",  "SKTNI", 2, "Beroperasi", None, "Jawa Barat"),
    ("SGLNG",  "BDSLN", 2, "Beroperasi", None, "Jawa Barat"),
    ("BDSLN",  "UBRNG", 2, "Beroperasi", None, "Jawa Barat"),
    ("MDCAN",  "UBRNG", 2, "Beroperasi", 26, "Jawa Barat"),          # #26 Mandirancan-Ujungberung
    ("MDCAN",  "BDSLN", 2, "Beroperasi", 26, "Jawa Barat"),          # #26 Mandirancan-Bandung Selatan
    ("CIBNG",  "IDMYU", 2, "Beroperasi", None, "Jawa Barat"),
    ("IDMYU",  "MDCAN", 2, "Beroperasi", None, "Jawa Barat"),
    ("TSMYA",  "BDSLN", 2, "Beroperasi", 26, "Jawa Barat"),          # #26 Tasikmalaya-Bandung Selatan
    ("TSMYA",  "DEPOK", 2, "Beroperasi", 26, "Jawa Barat-Jakarta"),  # #26 Tasikmalaya-Depok
    ("KSGHN",  "TSMYA", 2, "Beroperasi", 26, "Jawa Tengah-Barat"),   # #26 Kesugihan-Tasikmalaya
    # -- Jawa Tengah: Cilacap/Adipala, Batang/Pemalang, Tanjung Jati, Ungaran --
    ("KSGHN",  "ADPLA", 2, "Beroperasi", 23, "Jawa Tengah"),         # #23 N-2 Kesugihan-Adipala-Cilacap
    ("ADPLA",  "CLCAP", 2, "Beroperasi", 23, "Jawa Tengah"),         # #23
    ("PMLNG",  "BTANG", 2, "Beroperasi", 24, "Jawa Tengah"),         # #24 N-2 Pemalang-Batang (PLTU 2x1000)
    ("PMLNG",  "NTJTI", 2, "Beroperasi", 22, "Jawa Tengah"),         # #22/#27 New Tanjung Jati-Pemalang
    ("NTJTI",  "UNGRN", 2, "Beroperasi", 27, "Jawa Tengah"),         # #27 Pemalang-Tanjungjati-Ungaran
    ("TJATI",  "UNGRN", 2, "Beroperasi", 20, "Jawa Tengah"),         # #20 N-1 Tanjung Jati-Ungaran (also #21 N-2 rotor)
    ("KSGHN",  "MDCAN", 2, "Beroperasi", None, "Jawa Tengah-Barat"),
    ("KSGHN",  "PMLNG", 2, "Beroperasi", None, "Jawa Tengah"),
    # -- Ungaran-Boyolali-Pedan (Selatan<->Utara), transfer Timur-Barat --
    ("UNGRN",  "BYOLI", 1, "Beroperasi", 19, "Jawa Tengah"),         # #19 N-1 Ungaran-Boyolali >90% (1 sirkit)
    ("BYOLI",  "PEDAN", 1, "Beroperasi", 25, "Jawa Tengah"),         # #25/#26 Boyolali-Pedan (1 sirkit)
    ("UNGRN",  "KRIAN", 2, "Beroperasi", None, "Jawa Tengah-Timur"), # usulan/Purwodadi outlet
    ("UNGRN",  "NBANG", 2, "Beroperasi", None, "Jawa Tengah-Timur"),
    # -- Jawa Timur / Madura: Paiton-Grati-Krian-Kediri-Gresik --
    ("PITON",  "GRATI", 2, "Beroperasi", 28, "Jawa Timur"),          # #28 N-1 Paiton-Grati 79% (also #29 N-2)
    ("GRATI",  "KRIAN", 2, "Beroperasi", 30, "Jawa Timur"),          # #30 N-2 Grati-Krian
    ("PITON",  "KDIRI", 2, "Beroperasi", None, "Jawa Timur"),
    ("KDIRI",  "PEDAN", 2, "Beroperasi", None, "Jawa Timur-Tengah"),
    ("KRIAN",  "GRSIK", 2, "Beroperasi", 31, "Jawa Timur"),          # #31 N-2 Krian-Gresik (Madura)
    ("KRIAN",  "NBANG", 2, "Beroperasi", None, "Jawa Timur"),
]

# ---------------------------------------------------------------------------
# Kerawanan 1-31 : (No, UIT, category, kondisi, dampak, mitigasi, usulan)
#   category -> N-1 / N-2 / N-1-1  (title of Tabel 1.1.A: "N-1, N-2, N-1 N-2";
#   "N-1-2" / "N-1 N-2" in the book maps to N-1-1 in the model's enum)
# ---------------------------------------------------------------------------
K = [
 (1, "JBB", "N-2",
  "Pembebanan SUTET Cilegon-Cibinong akan overload apabila terjadi N-2 SUTET Gandul-Depok "
  "pada saat kit kompleks Banten beroperasi maksimum 8400 MW.",
  "Terjadi overload pada SUTET Cilegon-Cibinong.",
  "1. Sudah terpasang OGS SUTET Cilegon-Cibinong. 2. Usulan pemasangan Island Banten / OFGS Suralaya.",
  "Jangka Pendek: percepatan SUTET Muaratawar-Priok (COD 2026), SUTET Cawang-Gandul (COD 2026), "
  "SUTET Priok-Muarakarang (COD 2027). Jangka Panjang: pembangunan sirkit ke-2 SUTET Cilegon-Cibinong (COD 2031)."),
 (2, "JBB", "N-1",
  "SUTET Gandul-Depok berbeban diatas 50% ketika beroperasinya PLTU Jawa-7 (2 unit) dan PLTU Jawa 9,10 "
  "dengan beban maksimum sehingga kriteria N-1 tidak terpenuhi.",
  "1. Terjadi Overload di SUTET Gandul-Depok jika trip 1 sirkit. 2. Kesulitan pemeliharaan.",
  "1. Pembatasan komplek Suralaya 6400 MW dari total 8400 MW. 2. Defense Scheme OGS SUTET Gandul-Depok "
  "menargetkan komplek pembangkitan Suralaya.",
  "Jangka Pendek: SUTET Muaratawar-Priok (COD 2026), SUTET Cawang-Gandul (COD 2026), SUTET Priok-Muarakarang (COD 2027)."),
 (3, "JBB", "N-1",
  "SUTET Depok-Cibinong sudah berbeban diatas 60%.",
  "1. Terjadi Overload di SUTET Depok-Cibinong jika trip 1 sirkit. 2. Kesulitan pemeliharaan.",
  "1. Pembatasan komplek Suralaya 6400 MW dari total 8400 MW. 2. OGS SUTET Cibinong-Depok melepas unit "
  "pembangkit Suralaya (tahap-1 unit 5/6/7, tahap-2 unit 1/2/3/4).",
  "Jangka Pendek: SUTET Muaratawar-Priok (COD 2026), SUTET Cawang-Gandul (COD 2026), SUTET Priok-Muarakarang (COD 2027)."),
 (4, "JBB", "N-2",
  "1. Terjadi Overload pada ruas SUTET Bekasi-Tambun apabila terjadi gangguan N-1. "
  "2. Terdapat tower combined pada ruas SUTET Muaratawar-Cawang dan SUTET Tambun-Bekasi yang berpotensi "
  "gangguan N-2 bersamaan pada kedua ruas.",
  "Berpotensi pemadaman di Wilayah Jakarta dan sekitarnya pada Subsistem Bekasi 2,4-Cawang 1-Priok, "
  "Bekasi 1,3-Cibinong 3, dan Cawang 2,3-Depok 1 apabila gangguan N-2 di ruas segiempat.",
  "Sudah terpasang OLS Muaratawar-Cawang-Bekasi-Tambun 4 tahapan, total target 1058 MW.",
  "Jangka Pendek: proyek 2 sirkit baru SUTET Bekasi-Muaratawar + Rekonfigurasi GITET Bekasi (COD Nov 2026); "
  "SUTET Muaratawar-Priok menghubungkan PLTGU Muaratawar & Priok di sisi 500 kV (COD 2026); SUTET Cawang-Gandul (COD 2026)."),
 (5, "JBB", "N-2",
  "1. Terjadi Overload pada ruas SUTET Muaratawar-Cawang apabila gangguan N-1. "
  "2. Tower combined pada ruas SUTET Muaratawar-Cawang dan SUTET Tambun-Bekasi berpotensi N-2 bersamaan.",
  "Berpotensi pemadaman di Wilayah Jakarta pada Subsistem Bekasi 2,4-Cawang 1-Priok, Bekasi 1,3-Cibinong 3, "
  "dan Cawang 2,3-Depok 1 apabila gangguan N-2 di ruas segiempat.",
  "Sudah terpasang OLS Muaratawar-Cawang-Bekasi-Tambun 4 tahapan, total target 1.058 MW.",
  "Jangka Pendek: 2 sirkit baru SUTET Bekasi-Muaratawar + Rekonfigurasi GITET Bekasi (COD Nov 2026); "
  "SUTET Muaratawar-Priok (COD 2026); SUTET Cawang-Gandul (COD 2026)."),
 (6, "JBB", "N-2",
  "SUTET Depok-Cibinong memasok wilayah Jakarta dengan pembebanan sudah diatas 60%.",
  "Jika terjadi kondisi N-2 SUTET Depok-Cibinong, maka terjadi pembebanan overload pada IBT #1&2 Depok.",
  "Rencana implementasi Defense Scheme N-2 pada SUTET Depok-Cibinong dan splitting SS Cawang 2,3-Depok 1 "
  "dan Pratu-Salak-Cibinong 1,2-Depok 2.",
  "Jangka Pendek: SUTET Muaratawar-Priok (COD 2026), SUTET Cawang-Gandul (COD 2026), SUTET Priok-Muarakarang (COD 2027)."),
 (7, "JBB", "N-2",
  "SUTET Gandul-Durkos-Kembangan memasok 2 IBT Durikosambi dan 2 IBT Muarakarang secara radial, "
  "pembebanan SUTET Gandul-Durkos 55%, SUTET Kembangan-Durkos 43%.",
  "Jika terjadi N-2 SUTET Gandul-Durkos-Kembangan, terjadi pembebanan konsumen karena padam IBT "
  "Muarakarang dan Durikosambi sebesar 1.700 MW.",
  "Terpasang Defense Scheme N-2 pada SUTET Gandul-Durkos-Kembangan.",
  "Jangka Pendek: SUTET Muaratawar-Priok (COD 2026); SUTET Priok-Muarakarang (COD 2027)."),
 (8, "JBB", "N-2",
  "Kerawanan N-2 Durikosambi-Muarakarang.",
  "Berpotensi padam meluas pada Subsistem Muarakarang 1,2-Durikosambi 1.",
  "Terpasang ADS pada subsistem Muarakarang.",
  "Jangka Pendek: SUTET Muaratawar-Priok (COD 2026); SUTET Priok-Muarakarang (COD 2027)."),
 (9, "JBB", "N-2",
  "Terjadi potensi ketidakstabilan sudut rotor Pembangkit Komplek Banten apabila terjadi N-2 pada ruas "
  "SUTET Gandul-Depok.",
  "Ketidakstabilan pembangkit Banten sehingga berpotensi kehilangan pasokan pembangkit di Komplek Banten "
  "sebesar 8.400 MW.",
  "Terpasang DS 500 kV N-2 SUTET Gandul-Depok melepas unit pembangkit Suralaya bertahap + melepas IBT-1&3 "
  "Bekasi & IBT-3 Cibinong.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang. "
  "Jangka Panjang: sirkit ke-2 SUTET Cilegon-Cibinong (COD 2031)."),
 (10, "JBB", "N-2",
  "SUTET Muaratawar-Cawang dan Tambun-Bekasi memasok wilayah VVIP Jakarta melalui 3 IBT Cawang dan 4 IBT "
  "Bekasi. Pembebanan ruas SUTET Tambun-Bekasi 70%, SUTET Muaratawar-Cawang 55%. Tower combined "
  "berpotensi N-2 bersamaan.",
  "Berpotensi pemadaman di Wilayah Jakarta pada Subsistem Bekasi 2,4-Cawang 1-Priok, Bekasi 1,3-Cibinong 3, "
  "dan Cawang 2,3-Depok 1 apabila gangguan N-2 di ruas segiempat.",
  "1. Tambahan kuota DS OLS 500 kV untuk N-2 SUTET Segiempat, 3 tahapan, total target 1.544 MW. "
  "2. Implementasi tambahan DS OLS Instant SUTET Segiempat + modifikasi logic.",
  "Jangka Pendek: 2 sirkit baru SUTET Bekasi-Muaratawar + Rekonfigurasi GITET Bekasi (COD Nov 2026); "
  "SUTET Muaratawar-Priok (COD 2026); SUTET Cawang-Gandul (COD 2026)."),
 (11, "JBB", "N-2",
  "SUTET Suralaya 9,10-Cilegon memasok GITET Cilegon dengan pembebanan 1.634 MW.",
  "Jika terjadi N-2 SUTET Suralaya 9,10-Cilegon, terjadi pembebanan overload pada IBT subsistem "
  "Suralaya 1,2-Cilegon.",
  "Telah terpasang Defense Scheme N-2 pada SUTET Suralaya 9,10-Cilegon yang akan mensplit IBT Cilegon "
  "dan IBT Suralaya.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang; "
  "Uprating IBT-1&2 Suralaya 250->500 MVA (COD 2026)."),
 (12, "JBB", "N-1-1",
  "SUTET Suralaya Baru-LBE menyalurkan daya dari komplek Suralaya sebesar 3751 MW.",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Suralaya Baru-LBE.",
  "Sudah terpasang Defense Scheme OGS Suralaya Baru-LBE.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang."),
 (13, "JBB", "N-1-1",
  "Kerawanan N-1-2 Suralaya-Suralaya Baru.",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Suralaya-Suralaya Baru.",
  "Sudah terpasang Defense Scheme OGS Suralaya-Suralaya Baru.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang."),
 (14, "JBB", "N-1-1",
  "SUTET Jawa 7-Balaraja menyalurkan daya dari komplek Pembangkitan Jawa 7 (1.982 MW).",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Jawa 7-Balaraja.",
  "Sudah terpasang Defense Scheme OGS Jawa 7-Balaraja.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang."),
 (15, "JBB", "N-1-1",
  "SUTET Jawa 7-LBE menyalurkan daya dari komplek Pembangkitan Jawa 7 (1.982 MW) dan komplek "
  "pembangkitan LBE (625 MW).",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Balaraja-LBE.",
  "Sudah terpasang Defense Scheme OGS Jawa 7-LBE.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang."),
 (16, "JBB", "N-1-1",
  "SUTET Suralaya-Balaraja menyalurkan daya dari komplek Suralaya sebesar 3.751 MW.",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Suralaya-Balaraja.",
  "Sudah terpasang Defense Scheme OGS Suralaya-Balaraja.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang."),
 (17, "JBB", "N-1-1",
  "SUTET Balaraja-Lengkong berbeban diatas 60% ketika beroperasinya PLTU Jawa-7 (2 unit) dan PLTU "
  "Jawa 9,10 dengan beban maksimum sehingga kriteria N-1 tidak terpenuhi.",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Balaraja-Lengkong.",
  "Sudah terpasang Defense Scheme OGS Balaraja-Lengkong.",
  "Jangka Pendek: SUTET Muaratawar-Priok, SUTET Cawang-Gandul, SUTET Priok-Muarakarang."),
 (18, "JBB", "N-2",
  "SUTET Sukatani-Cilamaya menyalurkan daya dari Pembangkit PLTGU Cilamaya sebesar 2 x 880 MW yang "
  "terhubung radial, sehingga jika terjadi N-2 SUTET Sukatani-Cilamaya, hilang pembangkit 2 x 880 MW.",
  "Penurunan frekuensi hingga di bawah 49,0 Hz, pemadaman beban akibat UFLS, berpotensi trip pembangkit "
  "lain karena frekuensi rendah.",
  "Terpasang Adaptive Defense Scheme (ADS) di SUTET Sukatani-Cilamaya.",
  "-"),
 (19, "JBT", "N-1",
  "Pembebanan SUTET Ungaran-Boyolali sudah mencapai >90%.",
  "1. Berpotensi overload di ruas SUTET Ungaran-Boyolali-Pedan yang dapat menyebabkan trip pada SUTET, "
  "penurunan transfer Timur ke Barat, berpotensi menaikkan BPP. 2. Drop tegangan GITET Boyolali dan Pedan "
  "dari 493 kV menjadi 477 kV; sisi 150 kV terendah 137 kV di GI Sanggrahan.",
  "1. Memaksimalkan MVAR PLTGU Gresik, PLTU Pacitan, Tanjung Awar-Awar 2. Rencana pengaktifan target "
  "Defense Scheme SUTET Ungaran-Boyolali-Pedan.",
  "Jangka Pendek: SUTET Ungaran-Boyolali line 2 (COD 2027), SUTET Pedan-Boyolali line 2 (COD 2027)."),
 (20, "JBT", "N-1",
  "Potensi terjadi overload apabila terjadi gangguan N-1 SUTET Tanjung Jati-Ungaran.",
  "Terjadi overload pada SUTET Tanjung Jati-Ungaran.",
  "Sudah terpasang OGS pada SUTET Tanjung Jati-Ungaran.",
  "Jangka Pendek: Pembangunan GITET Purwodadi + outlet (Tx. Tanjung Jati-Pemalang, Ungaran-Krian, "
  "Ungaran-Ngimbang) COD 2028."),
 (21, "JBT", "N-2",
  "Potensi ketidakstabilan sudut rotor pembangkit apabila terjadi N-2 SUTET Tanjung Jati-Ungaran.",
  "1. Ketidakstabilan komplek Tanjung Jati. 2. Potensi kehilangan kompleks pembangkit Tanjung Jati "
  "sebesar 4.640 MW dan beban padam karena UFLS tahap 1-4 sebesar 4.420 MW.",
  "Sudah terpasang Adaptive Defense Scheme (ADS) 500 kV untuk N-2 SUTET Tanjung Jati-Ungaran.",
  "Jangka Pendek: GITET Purwodadi + outlet (COD 2028)."),
 (22, "JBT", "N-2",
  "Potensi ketidakstabilan sudut rotor pembangkit apabila terjadi N-2 SUTET New Tanjung Jati-Pemalang.",
  "1. Ketidakstabilan pada pembangkit Tanjung Jati. 2. Potensi kehilangan kompleks pembangkit Tanjung Jati "
  "sebesar 4.640 MW dan beban padam karena UFLS tahap 1-4 sebesar 4.420 MW.",
  "Sudah terpasang Adaptive Defense Scheme (ADS) 500 kV untuk N-2 SUTET Tanjung Jati-Pemalang.",
  "Jangka Pendek: GITET Purwodadi + outlet (COD 2028)."),
 (23, "JBT", "N-2",
  "Total Komplek Pembangkitan di PLTU Cilacap dan PLTU Adipala total 2.200 MW; apabila terjadi N-2 di "
  "SUTET Kesugihan-Adipala-Cilacap akan terjadi penurunan Frekuensi Sistem.",
  "Sistem Jawa-Madura-Bali kehilangan 2.200 MW serta potensi penurunan Frekuensi Sistem hingga 1.5 Hz.",
  "1-2. Pengaturan pembebanan komplek Cilacap & Adipala dengan setting DS IKS. 3. DS SUTET 500 kV "
  "Kesugihan-Adipala melepas OLS tersebar IBT-1,2,3,4 Pedan dan IBT-1,2 Pemalang total 600 MW. "
  "4. UFLS Tahap 1-7 total 7.740 MW.",
  "Jangka Pendek: percepatan SUTET Kesugihan-Inc. (Adipala-Cilacap) COD 2027."),
 (24, "JBT", "N-2",
  "SUTET Pemalang-Batang menyalurkan daya dari Pembangkit PLTU Batang sebesar 2 x 1000 MW yang terhubung "
  "radial, sehingga jika terjadi N-2 SUTET Pemalang-Batang, hilang pembangkit 2 x 1000 MW.",
  "Penurunan frekuensi hingga di bawah 49,0 Hz, pemadaman beban dari UFLS, berpotensi trip pembangkit lain "
  "karena frekuensi rendah.",
  "1. Pembatasan pengoperasian PLTU Batang dari 2.000 MW menjadi 1.800 MW. 2. Rencana implementasi "
  "Adaptive Defense Scheme (ADS) di SUTET Pemalang-Batang (progres 30%).",
  "-"),
 (25, "JBT", "N-2",
  "Sistem Jawa Bali mentransfer daya dari Timur ke Barat melalui Path 1, 2 dan 3 maksimum 4.200 MW. "
  "Kondisi tertinggi transfer Timur ke Barat mencapai 4.300 MW.",
  "Terjadi ketidakstabilan pembangkit jika transfer Timur-Barat di atas 4.200 MW, kemudian terjadi N-2 "
  "pada ruas SUTET transfer.",
  "1. Pembatasan transfer Timur-Barat 4.200 MW. 2. Rencana implementasi DS N-2 di ruas SUTET transfer "
  "Timur-Barat.",
  "Jangka Pendek: SUTET Ungaran-Boyolali line 2 (COD 2027), SUTET Pedan-Boyolali line 2 (COD 2027), "
  "IBT 3,4 GITET Boyolali (COD 2027)."),
 (26, "JBT", "N-1-1",
  "Keterbatasan transfer dari Timur ke Barat jika SUTET Ungaran-Boyolali-Pedan off karena SUTET ini "
  "penghubung Jalur Selatan ke Utara. Saat pemeliharaan, kontingensi N-2 pada ruas: Kesugihan-Tasikmalaya; "
  "Tasikmalaya-Depok & Tasikmalaya-Bandung Selatan; Paiton-Grati; Grati-Krian; Paiton-Kediri; Kediri-Pedan; "
  "Mandirancan-Ujungberung & Mandirancan-Bandung Selatan; Ungaran-Krian & Ungaran-Ngimbang.",
  "1. Kesulitan pemeliharaan. 2. Jika terjadi N-1-2, berpotensi blackout wilayah Jawa Timur, Bali dan "
  "Yogyakarta.",
  "Rencana implementasi DS N-1-2 Ungaran-Boyolali-Pedan.",
  "Jangka Pendek: SUTET Ungaran-Boyolali line 2 & Pedan-Boyolali line 2 (COD 2027); GITET Bangil-Inc "
  "(Paiton-Kediri) COD 2026; GITET Bangil-Tx Grati/Krian COD 2027; GITET Cikalong + outlet COD 2027."),
 (27, "JBT", "N-1-1",
  "SUTET Pemalang-Tanjungjati-Ungaran menyalurkan daya dari komplek pembangkitan Tanjungjati sebesar "
  "2.643 MW.",
  "Jika terjadi N-1-2, berpotensi overload pada SUTET Pemalang-Tanjungjati-Ungaran.",
  "Sudah terpasang Defense Scheme OGS Tanjung Jati-Ungaran.",
  "Jangka Pendek: GITET Purwodadi + outlet (COD 2028)."),
 (28, "JBM", "N-1",
  "Pembebanan SUTET Paiton-Grati sudah sebesar 79%. Akan terjadi overload apabila ruas SUTET Paiton-Grati "
  "trip 1 sirkit.",
  "Overload SUTET Paiton-Grati pada kondisi N-1.",
  "1. Sistem stabil tanpa DS jika transfer Path Paiton dibatasi maksimum 2.000 MW. 2. DS tahap 3 (Trip KIT "
  "1.800 MW + Trip Load 600 MW), 300 ms, transfer Path Paiton hingga 3.600 MW. 3. OGS SUTET Paiton-Grati "
  "2 tahap.",
  "Jangka Pendek: GITET Bangil + SUTET Bangil-Inc (Paiton-Kediri) COD 2026; GITET Bangil-Tx Grati/Krian "
  "COD 2027; GITET Watudodol/Kalipuro COD 2028; SUTET 500 kV Paiton-Kalipuro COD 2028."),
 (29, "JBM", "N-2",
  "1. Terjadi ketidakstabilan apabila ruas SUTET Paiton-Grati trip 2 Sirkit pada saat pembebanan "
  "Pembangkit Paiton diatas 2.600 MW. 2. Ketidakstabilan pembangkitan Paiton saat SUTET trip 2 sirkit (N-2). "
  "3. Potensi blackout wilayah Jawa Timur dan Bali.",
  "-",
  "1. Sistem stabil tanpa DS jika transfer Path Paiton dibatasi maksimum 2.000 MW. 2. DS tahap 3 (Trip KIT "
  "1.800 MW + Trip Load 600 MW), 300 ms. 3. Defense Scheme di GITET Paiton (tahap-1 unit 1,2/9, tahap-2 "
  "unit 7/8, tahap 3 unit 5/6).",
  "Jangka Pendek: GITET Bangil + SUTET Bangil-Inc (Paiton-Kediri) COD 2026; GITET Bangil-Tx Grati/Krian "
  "COD 2027; GITET Watudodol/Kalipuro COD 2028; SUTET Paiton-Kalipuro COD 2028."),
 (30, "JBM", "N-2",
  "1. Terjadi ketidakstabilan apabila ruas SUTET Grati-Krian trip 2 Sirkit pada saat pembebanan Pembangkit "
  "Paiton diatas 2.600 MW. 2. Ketidakstabilan pembangkitan Paiton saat SUTET trip 2 sirkit (N-2). "
  "3. Potensi blackout wilayah Jawa Timur dan Bali.",
  "-",
  "1. Sistem stabil tanpa DS jika transfer Path Paiton dibatasi maksimum 2.000 MW. 2. DS tahap 3 (Trip KIT "
  "1.800 MW + Trip Load 600 MW), 300 ms. 3. Defense Scheme di GITET Paiton (tahap-1 unit 1,2/9, tahap-2 "
  "unit 7/8).",
  "Jangka Pendek: GITET Bangil + SUTET Bangil-Inc (Paiton-Kediri) COD 2026; GITET Bangil-Tx Grati/Krian "
  "COD 2027; GITET Watudodol/Kalipuro COD 2028; SUTET Paiton-Kalipuro COD 2028."),
 (31, "JBM", "N-2",
  "Kerawanan N-2 Krian-Gresik.",
  "Berpotensi padam meluas pada Subsistem Gresik (Pulau Madura).",
  "1. Pembatasan pembangkit Gresik 500 kV sebesar 500 MW. 2. Operasi looping Subsistem Krian 1,2 dan "
  "Gresik 1,2.",
  "Jangka Pendek: penyelesaian GISTET 500 kV Waru + line bay (COD Januari 2027)."),
]


def _bold(ws):
    for c in ws[1]:
        c.font = Font(bold=True)


def build():
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    # ---- Info ----
    ws = wb.create_sheet("Info")
    ws.append(["Kunci", "Nilai"]); _bold(ws)
    for k, v in [("Kode Subsistem", "BACKBONE_500_JB"),
                 ("Nama Subsistem", "Backbone 500 kV Jawa-Madura-Bali"),
                 ("APB", "UIP2B JAMALI"),
                 ("Rule Profile", "BACKBONE_500")]:
        ws.append([k, v])

    # ---- Views ----
    ws = wb.create_sheet("Views")
    ws.append(["Kode View", "Nama View", "Sumber Tier-1 (kode GI, pisah ;)", "Halaman Buku"]); _bold(ws)
    t1 = ";".join(c for c, _, t, *_ in GITETS if t == 1)
    ws.append([VIEW, "Peta Kerawanan SUTET 500 kV", t1, "6"])

    # a kerawanan whose ruas already carries another No is pinned to a GITET
    # endpoint instead (rotor-stability / IBT-overload points that "also affect"
    # the same ruas).
    GI_PIN = {"DEPOK": 6, "GNDUL": 9, "CWANG": 10, "TJATI": 21, "PITON": 29}

    # ---- Gardu_Induk_dan_Aset ----
    ws = wb.create_sheet("Gardu_Induk_dan_Aset")
    ws.append(["No", "Nama Asset / GI", "Kode Singkatan", "Tipe Asset", "Tier (Mulai 0)",
               "Tegangan", "No IBT", "Status Kerawanan", "No Kerawanan", "Wilayah", "Sudut Pandang"])
    _bold(ws)
    n = 1
    for (code, name, tier, has_gen, wil) in GITETS:
        kno = GI_PIN.get(code, "")
        ws.append([n, name, code, "Busbar GITET", tier - 1, "500 kV", "",
                   "Rawan" if kno else "Normal", kno, wil, VIEW])
        n += 1
        if has_gen:
            ws.append([n, f"Pembangkit {name.replace('GITET ', '')}", f"KIT_{code}",
                       "Pembangkit", tier - 1, "500 kV", "", "Normal", "", wil, VIEW])
            n += 1

    # ---- Jalur_Transmisi ----
    ws = wb.create_sheet("Jalur_Transmisi")
    ws.append(["No", "No Kerawanan", "Nama Penghantar", "Dari GI", "Ke GI", "Tegangan",
               "Panjang Saluran (km)", "Jumlah Sirkit", "Status Operasi", "Tingkat Kerawanan",
               "Pembebanan Sirkit 1 (%)", "Pembebanan Sirkit 2 (%)", "Koridor / Wilayah",
               "Tier Dari", "Tier Ke", "Sudut Pandang"])
    _bold(ws)
    n = 1
    for (fr, to, cc, status, kno, kor) in SUTET:
        rawan = "Sangat Rawan" if kno else ("Rawan" if status == "Rencana" else "Normal")
        ws.append([n, kno or "", f"SUTET {fr} - {to}", fr, to, "500 kV", "", cc, status,
                   rawan, "", "", kor, TIER.get(fr, ""), TIER.get(to, ""), VIEW])
        n += 1

    # ---- KIT connections: a Pembangkit is wired to its GITET busbar via a link.
    #      Model them as rows too so the parser attaches the generator outlet.
    for (code, name, tier, has_gen, wil) in GITETS:
        if has_gen:
            ws.append([n, "", f"Outlet KIT {code}", f"KIT_{code}", code, "500 kV", "", 2,
                       "Beroperasi", "Normal", "", "", wil, tier, tier, VIEW])
            n += 1

    # ---- Data_Kerawanan_Detail ----
    # `Kategori Kontingensi` (N-1 / N-2 / N-1-1) is what the risk map groups by
    # per island. The prefix in the Kondisi text is kept as a fallback in case
    # the parser does not yet read the column.
    ws = wb.create_sheet("Data_Kerawanan_Detail")
    ws.append(["No", "UIT", "Kategori Kontingensi", "Kondisi / Permasalahan",
               "Dampak", "Mitigasi", "Usulan / Solusi"])
    _bold(ws)
    for (no, uit, cat, kondisi, dampak, mit, usul) in K:
        ws.append([no, uit, cat, f"[{cat}] {kondisi}", dampak, mit, usul])

    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT}")
    print(f"  {len(GITETS)} GITET, {sum(1 for g in GITETS if g[3])} KIT, "
          f"{len(SUTET)} SUTET, {len(K)} kerawanan")


if __name__ == "__main__":
    build()
