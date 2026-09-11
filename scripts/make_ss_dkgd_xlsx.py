"""samples/ss_dkgd_ingest.xlsx  -- Subsistem Durikosambi 2 - Gandul 1,3.

Source: Buku Kerawanan SJB 2026 Sec 2.9 -- Gambar 2.8 (Peta Kerawanan, PDF p96)
+ Tabel 2.7 (1 titik kerawanan, PDF p97).

Traced as-is from Gambar 2.8. Two 500 kV injection groups:
  GITET Gandul       -> IBT 1 + IBT 3 (500/150) -> bus GNDUL
  GITET Durikosambi  -> IBT 2 (500/150)         -> bus DKSBI
5 Tier bands, all 150 kV. GI codes are the figure's labels.

Run: python scripts/make_ss_dkgd_xlsx.py
"""
from __future__ import annotations

from _ss_xlsx_common import build_workbook

WIL = "DKI Jakarta"

ASSETS = [
    # -- 500 kV GITET busbars (share code with the 150 kV bus -> parser auto-splits) --
    dict(code="GNDUL", name="GITET Gandul",      type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="DKSBI", name="GITET Durikosambi", type="Busbar GITET", tier=1, kv="500 kV"),
    # -- IBT 500/150. Gandul has 2 IBT (unit 1 & 3) onto one bus; modelled as one
    #    IBT row (2 trafo) -- the multi-IBT-per-GITET ingest path is mid-fix. --
    dict(code="IBT 1 GNDUL", name="IBT 1,3 Gandul", type="IBT 3-Winding", tier=2,
         kv="500/150 kV", ibt="1", bus150="GNDUL", trafo=2, simbol="2 trafo (IBT 1 & 3)"),
    dict(code="IBT 2 DKSBI", name="IBT 2 Durikosambi", type="IBT 3-Winding", tier=2,
         kv="500/150 kV", ibt="2", bus150="DKSBI"),
    # -- 150 kV Tier-1 injection buses --
    dict(code="GNDUL", name="Gandul (bus 150 kV)",      type="Busbar GI", tier=1),
    dict(code="DKSBI", name="Durikosambi (bus 150 kV)", type="Busbar GI", tier=1),
    # -- Tier-2 --
    dict(code="SWGAN", name="Sawangan",       type="Busbar GI", tier=2),
    dict(code="CRNDU", name="Cirendeu",       type="Busbar GI", tier=2),
    dict(code="KMBGN", name="Kembangan",      type="Busbar GI", tier=2, kerawanan="1"),
    dict(code="GRGBR", name="Grogol Baru",    type="Busbar GIS", tier=2),
    # -- Tier-3 --
    dict(code="SRPNG", name="Serpong",        type="Busbar GI", tier=3),
    dict(code="PTKGN", name="Petukangan",     type="Busbar GI", tier=3),
    dict(code="GROGOL", name="Grogol",        type="Busbar GIS", tier=3),
    # -- Tier-4 --
    dict(code="BNTRO", name="Bintaro",        type="Busbar GI", tier=4),
    dict(code="TMANG", name="Tomang",         type="Busbar GIS", tier=4),
    # -- Tier-5 --
    dict(code="BTRBR", name="Bintaro Baru",   type="Busbar GI", tier=5),
]

BAYS = [
    ("LKONG2", "Lengkong 2 (bay di Serpong)", "SRPNG", None),
    ("SNYAN",  "GIS Senayan (bay di Petukangan; lihat catatan Sec 2.5 -- feeder "
               "Petukangan-Senayan bermasalah, Senayan sebenarnya disuplai dari "
               "Kembangan; GIS PLTD Senayan yang sesungguhnya = node terpisah "
               "hanya di SS_LBK, single phi dengan SNYAN & DNYSA)", "PTKGN", None),
]

LINES = [
    # GNDUL (Tier-1) -> Tier-2
    dict(fr="GNDUL", to="SWGAN", name="SUTT Gandul - Sawangan", tier_fr=1, tier_to=2, koridor=WIL),
    dict(fr="GNDUL", to="CRNDU", name="SUTT Gandul - Cirendeu", tier_fr=1, tier_to=2, koridor=WIL),
    dict(fr="GNDUL", to="KMBGN", name="SKTT Gandul - Kembangan", tier_fr=1, tier_to=2, koridor=WIL),
    # DKSBI (Tier-1) -> Tier-2  (SKTT Durikosambi-Kembangan = kerawanan #1)
    dict(fr="DKSBI", to="KMBGN", name="SKTT Durikosambi - Kembangan (bottleneck derating -- kerawanan #1)",
         kv="150 kV", tier_fr=1, tier_to=2, kerawanan="1", koridor=WIL),
    dict(fr="DKSBI", to="GRGBR", name="SKTT Durikosambi - Grogol Baru", kv="150 kV",
         tier_fr=1, tier_to=2, koridor=WIL),
    # Tier-2 -> Tier-3
    dict(fr="SWGAN", to="SRPNG", name="SUTT Sawangan - Serpong", tier_fr=2, tier_to=3, koridor=WIL),
    dict(fr="CRNDU", to="PTKGN", name="SUTT Cirendeu - Petukangan", tier_fr=2, tier_to=3, koridor=WIL),
    dict(fr="KMBGN", to="PTKGN", name="SKTT Kembangan - Petukangan", kv="150 kV",
         tier_fr=2, tier_to=3, koridor=WIL),
    dict(fr="GRGBR", to="GROGOL", name="SKTT Grogol Baru - Grogol", kv="150 kV",
         tier_fr=2, tier_to=3, koridor=WIL),
    # Tier-3 -> Tier-4
    dict(fr="SRPNG", to="BNTRO", name="SUTT Serpong - Bintaro", tier_fr=3, tier_to=4, koridor=WIL),
    dict(fr="PTKGN", to="BNTRO", name="SUTT Petukangan - Bintaro", tier_fr=3, tier_to=4, koridor=WIL),
    dict(fr="GROGOL", to="TMANG", name="SKTT Grogol - Tomang", kv="150 kV",
         tier_fr=3, tier_to=4, koridor=WIL),
    # Tier-4 -> Tier-5
    dict(fr="BNTRO", to="BTRBR", name="SUTT Bintaro - Bintaro Baru", tier_fr=4, tier_to=5, koridor=WIL),
]

RISKS = [
    dict(no=1, uit="JBB", category="N-1",
         kondisi="SKTT 150 kV Durikosambi-Kembangan merupakan jalur pasokan VVIP tetapi mengalami "
                 "Bottleneck karena kemampuan hantar arus dari Inom 920 A/sirkit Derating menjadi "
                 "800 A/sirkit (faktor usia kabel, operasi sejak 2000; 3 titik kebocoran minyak antara "
                 "join 2 dan 5-6). Pembebanan di ruas SKTT tersebut sudah diatas 60% dan tidak "
                 "memenuhi kriteria N-1 saat Sub sistem looping dengan IBT-1 Durikosambi.",
         dampak="1. Keandalan berkurang untuk pasokan VVIP (zero downtime) di jalur SKTT 150 kV "
                "Durikosambi-Kembangan. 2. Terjadi Overload apabila trip 1 sirkit pada salah satu "
                "ruas SKTT tersebut.",
         mitigasi="1. Pengaturan pembebanan di ruas SKTT Durikosambi-Kembangan tidak melebihi "
                  "kemampuan deklarasi SKTT. 2. Terpasang OLS directional SKTT 150 kV "
                  "Durikosambi-Kembangan Tahap 1-3, total target 225 MW (buku DS 2025). "
                  "3. Rencana penambahan target OLS directional total 239 MW. "
                  "4. Pemasangan ADS Island pembangkit Muarakarang. "
                  "5. Terpasang OLS IBT Durikosambi 1,2 / IBT Gandul 1,3, total target 447 MW. "
                  "6. Terpasang ADS subsistem Muarakarang-Gandul 1,3-Durikosambi 1,2.",
         usulan="Jangka Pendek: Uprating ruas SKTT 150 kV Durikosambi-Kembangan menjadi 2000 A "
                "per sirkit (RUPTL 2025-2034, COD 2027)."),
]

SPEC = dict(
    code="SS_DKGD",
    name="Durikosambi 2 - Gandul 1,3",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.9 (Gambar 2.8 + Tabel 2.7)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=RISKS,
)

if __name__ == "__main__":
    build_workbook(SPEC)
