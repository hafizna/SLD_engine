"""samples/ss_lbk_ingest.xlsx  -- Subsistem Lontar - Balaraja 1,2 - Kembangan 1,2.

Source: this is a REVERSE of the already-seeded, already-rendered
`app/services/seed_ss_lbk.py` (Buku Kerawanan SJB 2026 Sec 2.5, SLD hal.69
sisi Kembangan + hal.70 sisi Balaraja/Lontar + Tabel 2.3, 6 kerawanan) -- not
a fresh trace from the PDF. seed_ss_lbk.py is the reviewed, live source of
truth; this workbook exists so the SAME subsistem can go through the actual
/ingest probis (upload -> preview -> publish) for a BPO walkthrough, not only
the hard-coded seeder.

One canonical GI graph, two SLD views that share 4 intersection GIs (Cikupa,
Suvarna Sutra, Pasar Kemis, Jatake / Jatake Baru) -- each keeps its own
per-side Tier and edges via `Sudut Pandang`.

PLTD Senayan correction (this session): PLTD Senayan is its OWN GIS busbar
(GIS PLTD Senayan) with a generator behind it, single-phi-chained between the
real GIS Senayan (SNYAN, the Zero-Down-Time load GIS) and Danayasa (DNYSA) --
NOT a generator that "taps a circuit" (the ingest template has no tap-circuit
concept, and a floating tap invites exactly the cross-subsystem inconsistency
this engine exists to catch: the same physical PLTD must not look present in
one SS and absent/misdrawn in another -- see Sec 2.9 Durikosambi-Gandul, which
only shows a dashed unconnected reference to it).

Two ruas replace the old single "Senayan-Danayasa via PLTD, single phi" edge:
    SNYAN - GIS PLTD Senayan   (single phi)
    GIS PLTD Senayan - DNYSA   (single phi)
plus the direct 1-sirkit Senayan-Danayasa circuit (unchanged).

`Single Phi` is stored explicitly on each transmission row; the descriptive
text remains for reviewers reading the workbook.

Run: python scripts/make_ss_lbk_xlsx.py
"""
from __future__ import annotations

from _ss_xlsx_common import build_workbook

WIL = "Banten"
KEM = ["KEMBANGAN"]
BAL = ["BALARAJA"]
BOTH = ["KEMBANGAN", "BALARAJA"]

VIEWS = [
    ("KEMBANGAN", "Sisi Kembangan", "KMBGN", 69),
    ("BALARAJA", "Sisi Lontar-Balaraja", "NBRJA;LTKNG", 70),
]

ASSETS = [
    # ================= 500 kV sources =================
    dict(code="KMBGN", name="GITET Kembangan",    type="Busbar GITET", tier=1, kv="500 kV", views=KEM),
    dict(code="NBRJA", name="GITET New Balaraja", type="Busbar GITET", tier=1, kv="500 kV", views=BAL),
    dict(code="IBT 1 KMBGN", name="IBT 1 Kembangan", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="1", bus150="KMBGN", trafo=1, views=KEM),
    dict(code="IBT 2 KMBGN", name="IBT 2 Kembangan", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="2", bus150="KMBGN", trafo=1, views=KEM),
    dict(code="IBT 1 NBRJA", name="IBT 1 New Balaraja", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="1", bus150="NBRJA", trafo=1, views=BAL),
    dict(code="IBT 2 NBRJA", name="IBT 2 New Balaraja", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="2", bus150="NBRJA", trafo=1, views=BAL),
    # GITET New Cikupa (NCKUPA) -- NEW_NOT_ENERGIZED, the kerawanan #4/#5
    # solution. Both its busbar and generated IBT link carry status Rencana.
    dict(code="NCKUPA", name="GITET New Cikupa (rencana)", type="Busbar GITET", tier=4, kv="500 kV",
         status="Rencana", views=BAL),
    dict(code="IBT 1 NCKUPA", name="IBT 1 New Cikupa (rencana)", type="IBT 3-Winding", tier=5,
         kv="500/150 kV", ibt="1", bus150="JTAKE", trafo=1,
         status="Rencana", views=BAL),
    dict(code="IBT 2 NCKUPA", name="IBT 2 New Cikupa (rencana)", type="IBT 3-Winding", tier=5,
         kv="500/150 kV", ibt="2", bus150="JTAKE", trafo=1,
         status="Rencana", views=BAL),

    # ================= Tier-1 (150 kV injection points) =================
    dict(code="KMBGN", name="Kembangan (bus 150 kV)", type="Busbar GI", tier=1, kerawanan="1", views=KEM),
    dict(code="NBRJA", name="New Balaraja (bus 150 kV)", type="Busbar GI", tier=1, views=BAL),
    dict(code="LTKNG", name="Lontar", type="Busbar GI", tier=1, views=BAL),
    dict(code="DKSBI", name="Durikosambi", type="Busbar GI", tier=1,
         role="BOUNDARY", views=BOTH),
    dict(code="PKTGN", name="Petukangan", type="Busbar GI", tier=1, views=KEM),

    # ================= Tier-2 =================
    dict(code="MTLAN", name="Metland", type="Busbar GI", tier=2, views=KEM),
    dict(code="NSYAN", name="New Senayan", type="Busbar GI", tier=2, kerawanan="2;6", views=KEM),
    dict(code="BLRJA", name="Balaraja", type="Busbar GI", tier=2, views=BAL),
    dict(code="SDJYA", name="Sindang Jaya", type="Busbar GI", tier=2, views=BAL),
    dict(code="TLKNG2", name="Teluknaga 2 / Dadap", type="Busbar GI", tier=2, views=BAL),
    dict(code="TGBRU", name="Tangerang Baru", type="Busbar GI", tier=2, views=BAL),
    dict(code="TGBRU3", name="Tangerang Baru 3 (belum energize)", type="Busbar GI", tier=2, views=BAL),
    dict(code="CKNDE", name="Cikande", type="Busbar GI", tier=2, views=BAL),

    # ================= Tier-3 =================
    dict(code="CLDUG", name="Ciledug", type="Busbar GI", tier=3, simbol="1 kapasitor", views=KEM),
    dict(code="SNYAN", name="Senayan", type="Busbar GIS", tier=3, kerawanan="6", views=KEM),
    dict(code="ULJMI", name="Ulujami", type="Busbar GI", tier=3, views=KEM),
    dict(code="SVRNA", name="Suvarna Sutra", type="Busbar GI", tier=3, views=BOTH),
    dict(code="TLKGA", name="Teluknaga", type="Busbar GI", tier=3, simbol="1 kapasitor", views=BAL),
    dict(code="CKBRU", name="Cikupa Baru", type="Busbar GI", tier=3, views=BAL),

    # ================= Tier-4 =================
    dict(code="ALTRA", name="Alam Sutera", type="Busbar GI", tier=4, views=KEM),
    dict(code="DNYSA", name="Danayasa", type="Busbar GIS", tier=4, views=KEM),
    dict(code="ABDGP", name="Abadi Guna Papan", type="Busbar GIS", tier=4, views=KEM),
    dict(code="MPANG", name="Mampang", type="Busbar GIS", tier=4, views=KEM),
    dict(code="CKUPA", name="Cikupa", type="Busbar GI", tier=4, kerawanan="4", views=BOTH),
    dict(code="SPTAN", name="Sepatan", type="Busbar GI", tier=4, views=BAL),
    dict(code="CNKNG", name="Cengkareng", type="Busbar GI", tier=4, kerawanan="5", views=BAL),

    # ================= Tier-5 =================
    dict(code="SGS", name="Summarecon Gading Serpong", type="Busbar GI", tier=5, views=KEM),
    dict(code="CURUG", name="Curug", type="Busbar GI", tier=5, views=KEM),
    dict(code="PSKMS", name="Pasar Kemis", type="Busbar GI", tier=5, kerawanan="3", views=BOTH),
    dict(code="PSKBR", name="Pasar Kemis Baru", type="Busbar GI", tier=5, kerawanan="3", views=BAL),
    dict(code="SPTAN2", name="Sepatan 2", type="Busbar GI", tier=5, views=BAL),
    dict(code="TGRNG", name="Tangerang", type="Busbar GI", tier=5, views=BAL),
    dict(code="JTAKE", name="Jatake", type="Busbar GI", tier=5, kerawanan="4",
         simbol="1 trafo + 2 kapasitor", views=KEM),

    # ================= Tier-6 =================
    dict(code="MAXIM", name="Maxim", type="Busbar GI", tier=6, simbol="3 trafo", views=KEM),
    dict(code="JTKBR", name="Jatake Baru", type="Busbar GI", tier=6, views=BOTH),
    dict(code="GJTGL", name="Gajah Tunggal", type="Busbar GI", tier=6, kerawanan="3", views=BAL),

    # ================= Generation =================
    dict(code="KIT_LTKNG", name="PLTU Lontar", type="Pembangkit", tier=1, kv="150 kV", views=BAL),
    # GIS PLTD Senayan + its generator (see module docstring for the correction).
    dict(code="GISPD", name="GIS PLTD Senayan", type="Busbar GIS", tier=3, views=KEM),
    dict(code="KIT_SNYAN", name="PLTD Senayan", type="Pembangkit", tier=3, kv="150 kV", views=KEM),
]

BAYS = [
    ("DKSBI", "Durikosambi", "KMBGN", None, 1, "Beroperasi", KEM),
    ("PKTGN", "Petukangan (di bus Kembangan)", "KMBGN", None, 1, "Beroperasi", KEM),
    ("PKTGN", "Petukangan (di bus Senayan, non-aktif)", "SNYAN", None, 1, "Beroperasi", KEM),
    ("ABDGP", "Abadi Guna Papan (di bus Senayan, non-aktif)", "SNYAN", None, 1, "Beroperasi", KEM),
    ("ABDGP", "Abadi Guna Papan (di bus Danayasa)", "DNYSA", None, 1, "Beroperasi", KEM),
    ("MPANG", "Mampang (di bus Danayasa)", "DNYSA", None, 1, "Beroperasi", KEM),
    ("SVRNA", "Suvarna Sutra (bay dari Cikupa, sisi Kembangan)", "CKUPA", None, 1, "Beroperasi", KEM),
    ("PSKMS", "Pasar Kemis (bay dari Cikupa, sisi Kembangan)", "CKUPA", None, 1, "Beroperasi", KEM),
    ("JTKBR", "Jatake Baru (bay dari Jatake, sisi Kembangan)", "JTAKE", None, 1, "Beroperasi", KEM),
]

L = lambda fr, to, nm, tf, tt, vw, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno, status=st,
    koridor=WIL, views=vw, sirkit=sirkit)

LINES = [
    # ---- generation outlets ----
    L("KIT_LTKNG", "LTKNG", "Outlet PLTU Lontar", 1, 1, BAL),
    L("KIT_SNYAN", "GISPD", "Outlet PLTD Senayan", 3, 3, KEM),

    # ================= Kembangan side (SLD hal.69) =================
    L("KMBGN", "MTLAN", "SKTT Kembangan - Metland (ruas turun; Metland tap, lanjut ke Ciledug)", 1, 2, KEM),
    L("MTLAN", "CLDUG", "SKTT Metland - Ciledug", 2, 3, KEM),
    L("KMBGN", "NSYAN", "SKTT Kembangan - New Senayan (pembebanan 72% -- kerawanan #2)", 1, 2, KEM, kno="2"),
    L("NSYAN", "SNYAN", "SKTT New Senayan - Senayan (radial, kawasan ZDT -- kerawanan #6)", 2, 3, KEM, kno="6"),
    L("NSYAN", "ULJMI", "SKTT New Senayan - Ulujami (dead-end)", 2, 3, KEM),
    L("SNYAN", "DNYSA", "SKTT Senayan - Danayasa (direct, 1 sirkit)", 3, 4, KEM, kv="150 kV", sirkit=1),
    L("SNYAN", "GISPD", "SKTT Senayan - GIS PLTD Senayan (single phi)", 3, 3, KEM, kv="150 kV", sirkit=1),
    L("GISPD", "DNYSA", "SKTT GIS PLTD Senayan - Danayasa (single phi; usulan double phi)",
      3, 4, KEM, kv="150 kV", sirkit=1),
    L("SNYAN", "ABDGP", "SKTT Senayan - Abadi Guna Papan (rencana)", 3, 4, KEM, st="Rencana"),
    L("CLDUG", "ALTRA", "SKTT Ciledug - Alam Sutera", 3, 4, KEM),
    L("ALTRA", "SGS", "SKTT Alam Sutera - Summarecon Gading Serpong", 4, 5, KEM),
    L("SGS", "CURUG", "SKTT Summarecon Gading Serpong - Curug", 5, 5, KEM),
    L("CURUG", "CKUPA", "SKTT Curug - Cikupa (bay panjang T5->T4, sisi Kembangan)", 5, 4, KEM),
    L("DNYSA", "ABDGP", "SKTT Danayasa - Abadi Guna Papan (bay menggantung)", 4, 4, KEM),
    L("DNYSA", "MPANG", "SKTT Danayasa - Mampang (bay menggantung)", 4, 4, KEM),
    L("CKUPA", "SVRNA", "SKTT Cikupa - Suvarna Sutra (bay stub sisi Kembangan)", 4, 3, KEM),
    L("CKUPA", "PSKMS", "SKTT Cikupa - Pasar Kemis (bay stub sisi Kembangan)", 4, 5, KEM),
    L("CKUPA", "JTAKE", "SUTT Cikupa - Jatake (overload N-1-1/N-2 -- kerawanan #4)", 4, 5, BOTH, kno="4"),
    L("JTAKE", "JTKBR", "SKTT Jatake - Jatake Baru", 5, 6, KEM),
    L("JTAKE", "MAXIM", "SKTT Jatake - Maxim", 5, 6, KEM),

    # ================= Balaraja / Lontar side (SLD hal.70) =================
    L("NBRJA", "BLRJA", "SUTT New Balaraja - Balaraja", 1, 2, BAL),
    L("LTKNG", "SDJYA", "SUTT Lontar - Sindang Jaya", 1, 2, BAL),
    L("LTKNG", "TLKNG2", "SUTT Lontar - Teluknaga 2 / Dadap", 1, 2, BAL),
    L("LTKNG", "TGBRU", "SUTT Lontar - Tangerang Baru (kerawanan #4)", 1, 2, BAL, kno="4"),
    L("LTKNG", "TGBRU3", "SUTT Lontar - Tangerang Baru 3 (belum energize)", 1, 2, BAL, st="Rencana"),
    L("BLRJA", "CKNDE", "SUTT Balaraja - Cikande", 2, 2, BAL),
    L("BLRJA", "SDJYA", "SUTT Balaraja - Sindang Jaya", 2, 2, BAL),
    L("SDJYA", "SVRNA", "SUTT Sindang Jaya - Suvarna Sutra", 2, 3, BAL),
    L("TLKNG2", "TLKGA", "SUTT Teluknaga 2 / Dadap - Teluknaga", 2, 3, BAL),
    L("TGBRU", "CKBRU", "SUTT Tangerang Baru - Cikupa Baru", 2, 3, BAL),
    L("TLKGA", "SPTAN", "SUTT Teluknaga - Sepatan", 3, 4, BAL),
    L("CKBRU", "CNKNG", "SUTT Cikupa Baru - Cengkareng (kerawanan #5)", 3, 4, BAL, kno="5"),
    L("DKSBI", "CNKNG", "SUTT Durikosambi - Cengkareng (kerawanan #5)", 1, 4, BAL, kno="5"),
    L("SPTAN", "PSKBR", "SUTT Sepatan - Pasar Kemis Baru", 4, 5, BAL),
    L("SPTAN", "SPTAN2", "SUTT Sepatan - Sepatan 2 (dead-end)", 4, 5, BAL),
    L("PSKMS", "PSKBR", "SUTT Pasar Kemis - Pasar Kemis Baru (single phi -- kerawanan #3)",
      5, 5, BAL, kno="3", sirkit=1),
    L("PSKBR", "GJTGL", "SUTT Pasar Kemis Baru - Gajah Tunggal (single phi -- kerawanan #3)",
      5, 6, BAL, kno="3", sirkit=1),
    L("GJTGL", "PSKMS", "SUTT Gajah Tunggal - Pasar Kemis (single phi, menutup loop -- kerawanan #3)",
      6, 5, BAL, kno="3", sirkit=1),
    L("CNKNG", "TGRNG", "SUTT Cengkareng - Tangerang (hotspot #5)", 4, 5, BAL),
    L("TGRNG", "JTAKE", "SUTT Tangerang - Jatake", 5, 6, BAL),
]

RISKS = [
    dict(no=1, uit="JBB", category="N-1",
         kondisi="Pembebanan IBT-1,2 Kembangan tidak memenuhi kriteria N-1 saat PLTU Lontar tidak "
                 "beroperasi 1 unit.",
         dampak="1. Terjadi pemadaman jika terjadi gangguan N-1 pada salah satu IBT Kembangan. "
                "2. Pemeliharaan IBT Kembangan hanya dilakukan saat hari Minggu.",
         mitigasi="1. Sudah terpasang OLS IBT Kembangan tahap 1 sd 4 sebesar 908 MW (Buku DS 2025). "
                  "2. Rencana penambahan target OLS IBT Kembangan tahap 1 sd 4 total 1207 MW. "
                  "3. Pekerjaan dilaksanakan saat beban pembangkitan Lontar 4 unit maksimum atau saat "
                  "beban rendah. 4. Pengalihan beban ke Sub Sistem Muarakarang atau Gandul "
                  "1,3-Durikosambi 2.",
         usulan="Jangka Pendek: (1) GITET Cikupa + 2 unit IBT 500/150 kV + outlet (RUPTL 2025-2034, "
                "COD 2025); (2) 2 unit IBT 500/150 kV Ext IBT 3,4 Durikosambi (COD 2026); (3) PLTSA "
                "Tangerang 45 MW (COD 2028). Jangka Panjang: BESS di GI Cikupa & GI Teluknaga "
                "masing-masing 100 MW (COD 2032)."),
    dict(no=2, uit="JBB", category="N-1",
         kondisi="Pembebanan SKTT Kembangan-New Senayan mencapai 72% / tidak memenuhi kriteria N-1.",
         dampak="1. Terjadi Overload apabila trip 1 sirkit di ruas SKTT 150 kV Kembangan-New Senayan. "
                "2. Fleksibilitas operasi dan keandalan berkurang.",
         mitigasi="1. Sudah terpasang OLS SKTT Kembangan-New Senayan dengan target 120 MW "
                  "(Buku DS 2025). 2. Pemeliharaan dilaksanakan saat beban rendah. 3. Pengalihan beban "
                  "GI Danayasa ke Sub Sistem Cawang 2,3-Depok 1.",
         usulan="Jangka Pendek: (1) Pembangunan SKTT 150 kV Petukangan-PLTD Senayan menjadi 2cct, "
                "1000 A/sirkit (kabel eksisting rusak, RUPTL 2025-2034, COD 2027); (2) 2 Line bay di "
                "GIS PLTD Senayan agar SKTT Petukangan-PLTD Senayan bisa operasi 2 sirkit (COD 2027)."),
    dict(no=3, uit="JBB", category="N-1-1",
         kondisi="Ruas Penghantar Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis masih beroperasi single phi.",
         dampak="Berpotensi Padam pada KTT GI Gajah Tunggal saat terjadi N-1-1.",
         mitigasi="Pengaturan penjadwalan pemeliharaan penghantar.",
         usulan="Jangka Menengah: Usulan Double Phi pada ruas Pasar Kemis Baru-Gajah Tunggal-Pasar "
                "Kemis (diusulkan COD 2029)."),
    dict(no=4, uit="JBB", category="N-1-1",
         kondisi="Ruas Penghantar Cikupa-Jatake berpotensi overload saat terjadi kondisi N-1-1 atau "
                 "N-2 pada ruas penghantar Lontar-Tangerang Baru.",
         dampak="Pemeliharaan ruas penghantar Lontar-Tangerang Baru hanya bisa dilakukan saat beban "
                "rendah.",
         mitigasi="1. Pengaturan penjadwalan pemeliharaan penghantar. 2. Sudah terpasang OLS SUTT "
                  "Jatake-Cikupa sebesar 240 MW (Buku DS 2025). 3. Rencana penambahan target OLS SUTT "
                  "Jatake-Cikupa total 375 MW (Buku DS 2025).",
         usulan="Jangka Pendek: GITET Cikupa + 2 unit IBT 500/150 kV + outlet untuk mengambil beban GI "
                "Cikupa, GI Jatake Baru, GI Maxim dan GI Tangerang Lama (RUPTL 2025-2034, COD 2025). "
                "Jangka Panjang: BESS di GI Cikupa & GI Teluknaga masing-masing 100 MW (COD 2032)."),
    dict(no=5, uit="JBB", category="N-1",
         kondisi="Ruas Penghantar Durikosambi-Cengkareng tidak memenuhi kriteria N-1 saat GI Jatake, "
                 "Jatake Baru, Tangerang dan Cengkareng dipasok dari Sub Sistem Muarakarang.",
         dampak="1. Berpotensi adanya pemadaman saat terjadi kondisi N-1 pada ruas penghantar tersebut. "
                "2. Fleksibilitas operasi Sub Sistem Lontar dan Sub Sistem Muarakarang berkurang.",
         mitigasi="Pengaturan penjadwalan pemeliharaan penghantar hanya bisa dilakukan saat PLTU "
                  "Lontar beroperasi 4 unit dan saat GI Jatake, Jatake Baru, Tangerang dan Cengkareng "
                  "dipasok Sub Sistem Lontar.",
         usulan="Jangka Pendek: GITET Cikupa + 2 unit IBT 500/150 kV + outlet untuk mengambil beban GI "
                "Cikupa, GI Jatake Baru, GI Maxim dan GI Tangerang Lama (RUPTL 2025-2034, COD 2025). "
                "Jangka Panjang: BESS di GI Cikupa & GI Teluknaga masing-masing 100 MW (COD 2032)."),
    dict(no=6, uit="JBB", category="N-1-1",
         kondisi="GIS 150 kV Senayan masuk dalam kawasan Zero Down Time (ZDT) namun saat ini dipasok "
                 "radial dari SKTT New Senayan-Senayan.",
         dampak="Apabila terjadi N-1-1 pada ruas SKTT Kembangan-New Senayan menyebabkan GIS 150 kV "
                "Senayan padam.",
         mitigasi="Pengalihan beban ke Sub Sistem Cawang 2,3-Depok 1 atau Sub Sistem Muarakarang "
                  "1,2-Durikosambi 1-KIT Muarakarang saat pemeliharaan SKTT Kembangan-New Senayan.",
         usulan="Jangka Pendek: (1) 2 Line bay di GIS PLTD Senayan agar SKTT Petukangan-PLTD Senayan "
                "bisa operasi 2 sirkit (COD 2027); (2) SKTT 150 kV Petukangan-PLTD Senayan menjadi "
                "2cct, 1000 A/sirkit (kabel eksisting rusak, RUPTL 2025-2034, COD 2027)."),
]

SPEC = dict(
    code="SS_LBK",
    name="Lontar - Balaraja 1,2 - Kembangan 1,2",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.5 (SLD hal.69 + hal.70 + Tabel 2.3); "
               "reversed from app/services/seed_ss_lbk.py for the /ingest probis demo",
    views=VIEWS,
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=RISKS,
)

if __name__ == "__main__":
    build_workbook(SPEC)
