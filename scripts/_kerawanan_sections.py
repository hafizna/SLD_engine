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
    ("Suralaya Unit #3 - Suralaya 1,2 - Cilegon 4", "2.3", 79, (79, 80), None),
    ("GU Cilegon - Cilegon Baru 1,2,3 - Labuan", "2.4", 81, (82, 84), None),
    ("Lontar - Balaraja 1,2 - Kembangan 1,2", "2.5", 85, (86, 87), None),
    ("Balaraja 3,4 - Lengkong 1,2", "2.6", 88, (88, 88), None),
    ("Cawang 2,3 - Depok 1", "2.7", 89, (89, 90), None),
    ("Muarakarang 1,2 - Durikosambi 1 - KIT Muarakarang", "2.8", 91, (92, 95), None),
    ("Durikosambi 2 - Gandul 1,3", "2.9", 96, (96, 97), None),
    ("Priok - Bekasi 2,4 - Cawang 1", "2.10", 98, (98, 100), None),
    ("Pelabuhan Ratu - Salak - Cibinong 1,2 - Depok 2", "2.11", 101, (101, 104), 8),
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
    ("Sukatani 1,2", "3.9", 137, (138, 140), None),

    # ---- UP2B Jawa Tengah & DIY ----
    ("Tanjung Jati 1,2 - Ungaran 3", "4.3", 141, (141, 146), 14),
    ("Ungaran 1,2", "4.4", 147, (147, 152), 13),
    ("Pedan 1,2", "4.5", 153, (153, 157), 10),
    ("Pedan 3,4", "4.6", 158, (158, 164), 11),
    ("Kesugihan 1,2", "4.7", 165, (166, 172), 18),
    ("Pemalang 1,2", "4.8", 173, (174, 175), 4),
    ("Boyolali 1,2", "4.9", 175, (176, 178), 4),

    # ---- UP2B Jawa Timur ----
    ("Krian 1,2 - Gresik 1,2", "5.3", 179, (179, 196), 25),
    ("Krian 3,4,5,6", "5.4", 197, (197, 201), 8),
    ("Ngimbang", "5.5", 202, (202, 205), 7),
    ("Kediri 1,2", "5.6", 206, (206, 208), 6),
    ("Kediri 3,4", "5.7", 209, (209, 217), 15),
    ("Grati 1,2,3", "5.8", 218, (218, 227), 16),
    ("Paiton 1,2,3", "5.9", 228, (228, 237), 8),

    # ---- UP2B Bali ----
    ("Subsistem Bali", "6.3", 238, (239, 246), 11),
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
