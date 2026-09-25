"""Verified page map for every subsystem section of Buku Kerawanan SJB 2026.

Each entry is (subsystem label, section, figure page, table page range, risk
count). All four numbers were read back off the PDF rather than the table of
contents: section headings and `Tabel x.y` captions were located by scanning
pages 79-237, and each risk count is what `_kerawanan_tables.risk_rows` actually
returns for that range. A wrong range silently merges two subsystems' risks, so
`make_ss_*.py` passes the count to `as_risk_dicts(..., expected=N)` and the build
fails loudly if the extraction drifts.

`FIGURE` is the page carrying that section's own "Peta Kerawanan" diagram, which
is the topology source -- far more legible than the whole-region Lampiran sheets
and already carrying tier bands, bay stubs and risk pins.
"""
from __future__ import annotations

# label, section, figure page, (table from, table to), risk count
SECTIONS = [
    # ---- UP2B Jakarta & Banten (all built) ----
    # Re-read 24 Sep 2026 from the No column itself (words left of x=82 pt).
    # The old heading-based ranges were off by a page for LBK/BLL/CWD because
    # each table spills onto the next section's heading page (LBK #6 sits on
    # p.88 under the 2.6 heading; CWD #3-4 on p.91 under 2.8). GUCL is 7, not
    # 6: plain-text extraction glues row "7." onto #6's Polyprima text.
    ("Suralaya Unit #3 - Suralaya 1,2 - Cilegon 4", "2.3", 79, (80, 80), 3),
    ("GU Cilegon - Cilegon Baru 1,2,3 - Labuan", "2.4", 81, (82, 84), 7),
    ("Lontar - Balaraja 1,2 - Kembangan 1,2", "2.5", 85, (86, 88), 6),
    ("Balaraja 3,4 - Lengkong 1,2", "2.6", 88, (89, 89), 1),
    ("Cawang 2,3 - Depok 1", "2.7", 89, (90, 91), 4),
    ("Muarakarang 1,2 - Durikosambi 1 - KIT Muarakarang", "2.8", 91, (92, 95), 8),
    ("Durikosambi 2 - Gandul 1,3", "2.9", 96, (97, 97), 1),
    ("Priok - Bekasi 2,4 - Cawang 1", "2.10", 98, (99, 100), 7),
    ("Pelabuhan Ratu - Salak - Cibinong 1,2 - Depok 2", "2.11", 101, (102, 104), 8),
    ("Bekasi 1,3 - Cibinong 3", "2.12", 104, (105, 106), 3),
    ("Gandul 2,4", "2.13", 107, (108, 110), 1),

    # ---- UP2B Jawa Barat (to build) ----
    # Ranges below are the pages whose risk NUMBERS belong to the section, found
    # by reading the per-page sequence and watching where it resets to 1 -- not
    # by taking the section heading page. A table continues past the next
    # section's heading, so heading-based ranges silently pull a neighbour's
    # rows in (New Tambun was picking up Tasikmalaya #5).
    ("Cibatu 3,4 - PLTU Indramayu - Mandirancan 1,2", "3.3", 111, (112, 118), 19),
    ("Cirata 1,2,3", "3.4", 118, (119, 122), 10),
    ("Cibatu 1,2 - Deltamas 1,2", "3.5", 123, (123, 126), 8),
    ("Bandung Selatan 1,2 - New Ujungberung 1,2", "3.6", 127, (128, 132), 12),
    ("Tasikmalaya 1,2", "3.7", 132, (133, 135), 5),
    ("New Tambun", "3.8", 135, (136, 137), 2),
    ("Sukatani 1,2", "3.9", 137, (138, 140), 2),

    # ---- UP2B Jawa Tengah & DIY ----
    ("Tanjung Jati 1,2 - Ungaran 3", "4.3", 141, (141, 146), 14),
    ("Ungaran 1,2", "4.4", 147, (147, 152), 13),
    ("Pedan 1,2", "4.5", 153, (153, 157), 10),
    ("Pedan 3,4", "4.6", 158, (158, 164), 11),
    ("Kesugihan 1,2", "4.7", 165, (166, 172), 18),
    ("Pemalang 1,2", "4.8", 173, (174, 175), 4),
    ("Boyolali 1,2", "4.9", 175, (176, 178), 4),

    # ---- UP2B Jawa Timur (ranges confirmed from the per-page numbering) ----
    ("Krian 1,2 - Gresik 1,2", "5.3", 179, (180, 196), 25),
    ("Krian 3,4,5,6", "5.4", 197, (198, 201), 8),
    ("Ngimbang", "5.5", 202, (202, 205), 7),
    ("Kediri 1,2", "5.6", 206, (206, 208), 6),
    ("Kediri 3,4", "5.7", 209, (210, 217), 15),
    ("Grati 1,2,3", "5.8", 218, (219, 227), 16),
    ("Paiton 1,2,3", "5.9", 228, (229, 234), 8),

    # ---- UP2B Bali ----
    ("Subsistem Bali", "6.3", 238, (239, 246), 11),
]

# book section -> the fixture build_static_site.py publishes for it
FIXTURES = {
    "2.3": "ss_slcg_ingest.xlsx", "2.4": "ss_gucl_ingest.xlsx",
    "2.5": "ss_lbk_ingest.xlsx", "2.6": "seed_ss_bll", "2.7": "seed_ss_cwd",
    "2.8": "ss_muarakarang_durikosambi_ingest.xlsx", "2.9": "ss_dkgd_ingest.xlsx",
    "2.10": "ss_prbc_ingest.xlsx", "2.11": "ss_plbratu_ingest.xlsx",
    "2.12": "ss_bksi_cbng_ingest.xlsx", "2.13": "ss_gndul24_ingest.xlsx",
    "3.3": "ss_cbatu34_mdrcn_ingest.xlsx", "3.4": "ss_cirata_ingest.xlsx",
    "3.5": "ss_cbatu12_dltms_ingest.xlsx", "3.6": "ss_bdgsel_nubrg_ingest.xlsx",
    "3.7": "ss_tasik_ingest.xlsx", "3.8": "ss_ntmbn_ingest.xlsx",
    "3.9": "ss_sktni_ingest.xlsx",
    "4.3": "ss_tjati_ungaran3_ingest.xlsx", "4.4": "ss_ungaran12_ingest.xlsx",
    "4.5": "ss_pedan12_ingest.xlsx", "4.6": "ss_pedan34_ingest.xlsx",
    "4.7": "ss_ksghn_ingest.xlsx", "4.8": "ss_pmlng_ingest.xlsx",
    "4.9": "ss_byoli_ingest.xlsx",
    "5.3": "ss_krian12_gresik_ingest.xlsx", "5.4": "ss_krian3456_ingest.xlsx",
    "5.5": "ss_ngimbang_ingest.xlsx", "5.6": "ss_kediri12_ingest.xlsx",
    "5.7": "ss_kediri34_ingest.xlsx", "5.8": "ss_grati_ingest.xlsx",
    "5.9": "ss_paiton123_ingest.xlsx",
    "6.3": "ss_bali_ingest.json",
}

# Chapter 1 (sistem 500 kV), same No-column read. SUTET and IBT are drawn as
# SLDs (backbone_500 / system_ibt_500 workbooks, 31 + 38). Peralatan and
# Pembangkit are equipment/plant findings with no topology object of their
# own, so they are published as the book's tables
# (make_system_tables_json.py -> samples/system_tables_jamali.json).
SYSTEM_TABLES = [
    ("Tabel 1.1.A Kerawanan SUTET 500 kV", (23, 38), 31, "backbone_500_ingest.xlsx"),
    ("Tabel 1.2 Kerawanan IBT 500/150 kV", (41, 64), 38, "system_ibt_500_ingest.xlsx"),
    ("Tabel 1.3 Kerawanan Peralatan", (66, 72), 20, "system_tables_jamali.json"),
    ("Tabel 1.4 Kerawanan Pembangkit", (72, 76), 14, "system_tables_jamali.json"),
]

# Lampiran single-line diagrams, 1-based PDF pages. Cross-check only: use each
# section's own figure for tracing.
LAMPIRAN = {
    "JAKARTA_BANTEN": 248, "JAWA_BARAT": 249, "JAWA_TENGAH_DIY": 250,
    "JAWA_TIMUR": 251, "BALI": 252,
}


if __name__ == "__main__":
    for label, sec, fig, (a, b), n in SECTIONS:
        print(f"{sec:5} {label:48} fig p.{fig:3}  tabel p.{a}-{b}  risks={n}")
