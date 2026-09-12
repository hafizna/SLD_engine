"""samples/ss_bll_ingest.xlsx  -- Subsistem Balaraja 3,4 - Lengkong 1,2.

Source: this is a REVERSE of the already-seeded, already-rendered
`app/services/seed_ss_bll.py` (Buku Kerawanan SJB 2026 Sec 2.6, Gambar 2.5 +
Tabel 2.4) -- not a fresh trace from the PDF. seed_ss_bll.py is the reviewed,
live source of truth; this workbook exists so the SAME subsistem can be
demonstrated going through the actual /ingest probis (upload -> preview ->
publish) instead of only the hard-coded seeder, for a BPO walkthrough.

Two independent Tier-1 sources (GITET New Balaraja unit 3,4 -> bus New
Balaraja; GITET Lengkong unit 1,2 -> bus Lengkong Baru) meeting only at
Tier-5 via a normal 2-sirkit penghantar (Citra Habitat - Sinar Sahabat), not a
bus-tie.

Run: python scripts/make_ss_bll_xlsx.py
"""
from __future__ import annotations

from _ss_xlsx_common import build_workbook

WIL = "Banten"

ASSETS = [
    # -- 500 kV GITET busbars (share code with their 150 kV bus -> parser auto-splits) --
    dict(code="NBRJA", name="GITET New Balaraja", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="LKBRU", name="GITET Lengkong",     type="Busbar GITET", tier=1, kv="500 kV"),
    # -- IBT 500/150 (2 IBT per GITET -> collapsed to one row until the
    #    multi-IBT-per-bus ingest path is confirmed stable; see Sec 2.9/2.4 note) --
    dict(code="IBT 3 NBRJA", name="IBT 3 New Balaraja", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="3", bus150="NBRJA", trafo=1),
    dict(code="IBT 4 NBRJA", name="IBT 4 New Balaraja", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="4", bus150="NBRJA", trafo=1),
    dict(code="IBT 1 LKBRU", name="IBT 1 Lengkong", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="1", bus150="LKBRU", trafo=1),
    dict(code="IBT 2 LKBRU", name="IBT 2 Lengkong", type="IBT 3-Winding", tier=2, kv="500/150 kV",
         ibt="2", bus150="LKBRU", trafo=1),
    # -- 150 kV Tier-1 injection buses --
    dict(code="NBRJA", name="New Balaraja (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="LKBRU", name="Lengkong Baru (bus 150 kV)", type="Busbar GI", tier=1),
    # -- Tier-2 --
    dict(code="LSTEL", name="Lautan Steel", type="Busbar GI", tier=2, simbol="KTT LSI 129,6 MVA"),
    dict(code="LKONG", name="Lengkong",     type="Busbar GI", tier=2, simbol="1 kapasitor non-aktif"),
    dict(code="SRPNG", name="Serpong",      type="Busbar GI", tier=2, kerawanan="1",
         simbol="1 kapasitor aktif"),
    # -- Tier-3 --
    dict(code="SPMIL", name="Spinmill", type="Busbar GI", tier=3, simbol="KTT SPNML 50 MVA"),
    dict(code="BSD",   name="BSD",      type="Busbar GI", tier=3),
    # -- Tier-4 --
    dict(code="MLNUM", name="Millenium", type="Busbar GI", tier=4),
    dict(code="LEGOK",  name="Legok",     type="Busbar GI", tier=4, simbol="2 kapasitor aktif"),
    # -- Tier-5 (the two halves meet here) --
    dict(code="CITRA", name="Citra Habitat", type="Busbar GI", tier=5),
    dict(code="SSBAT", name="Sinar Sahabat", type="Busbar GI", tier=5),
    # -- Tier-6 --
    dict(code="TGRSA",  name="Tigaraksa",   type="Busbar GI", tier=6, simbol="1 kapasitor + 1 trafo"),
    dict(code="TGRSA2", name="Tigaraksa 2", type="Busbar GI", tier=6),
]

BAYS = [
    ("BLRJA", "Balaraja",  "NBRJA", None),
    ("SWGAN", "Sawangan",  "SRPNG", None),
    ("BNTRO", "Bintaro",   "SRPNG", None),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi": dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno, status=st, koridor=WIL)

LINES = [
    # sisi Balaraja (New Balaraja)
    L("NBRJA", "LSTEL", "SUTT New Balaraja - Lautan Steel", 1, 2),
    L("LSTEL", "SPMIL", "SUTT Lautan Steel - Spinmill", 2, 3),
    L("SPMIL", "MLNUM", "SUTT Spinmill - Millenium", 3, 4),
    L("MLNUM", "CITRA", "SUTT Millenium - Citra Habitat", 4, 5),
    L("CITRA", "TGRSA", "SUTT Citra Habitat - Tigaraksa", 5, 6),
    L("TGRSA", "TGRSA2", "SUTT Tigaraksa - Tigaraksa 2 (belum energize)", 6, 6, st="Rencana"),
    # sisi Lengkong (Lengkong Baru)
    L("LKBRU", "LKONG", "SUTT Lengkong Baru - Lengkong (ruas Lengkong I)", 1, 2),
    L("LKBRU", "SRPNG", "SUTT Lengkong Baru - Serpong (ruas Lengkong II, bottleneck MTU -- kerawanan #1)",
      1, 2, kno="1"),
    L("LKONG", "BSD",   "SUTT Lengkong - BSD", 2, 3),
    L("BSD",   "LEGOK", "SUTT BSD - Legok", 3, 4),
    L("LEGOK", "SSBAT", "SUTT Legok - Sinar Sahabat", 4, 5),
    # titik temu dua sisi (Tier-5, penghantar normal, bukan bus-tie)
    L("CITRA", "SSBAT", "SUTT Citra Habitat - Sinar Sahabat (penghantar normal, bukan bus-tie)", 5, 5),
]

RISKS = [
    dict(no=1, uit="JBB", category="N-1",
         kondisi="Terdapat bottle neck ruas transmisi karena keterbatasan kapasitas MTU (I nominal "
                 "1858 A derating menjadi 1000 A dikarenakan CT masih 1000 A) di GI 150 kV Serpong bay "
                 "Lengkong II sirkit 2. Fleksibilitas pasokan beban melalui GI Serpong (SS Gandul "
                 "1,3-Durikosambi 2) dan GI New Balaraja (SS Lontar).",
         dampak="Fleksibilitas operasi antara Sub Sistem Balaraja 3,4-Lengkong 1,2 dengan Sub Sistem "
                "Gandul 1,3-Durikosambi 2 menjadi berkurang.",
         mitigasi="1. Pengoperasian radial SUTT Lengkong II-Serpong sesuai dengan kemampuan penghantar "
                  "eksisting. 2. Pemeliharaan SUTT dilaksanakan saat periode beban rendah.",
         usulan="Jangka Pendek: Usulan penggantian MTU di GI Serpong bay Lengkong II sesuai kapasitas "
                "penghantar SUTT 150 kV Lengkong II-Serpong (diusulkan COD 2027)."),
]

SPEC = dict(
    code="SS_BLL",
    name="Balaraja 3,4 - Lengkong 1,2",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.6 (Gambar 2.5 + Tabel 2.4); "
               "reversed from app/services/seed_ss_bll.py for the /ingest probis demo",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=RISKS,
)

if __name__ == "__main__":
    build_workbook(SPEC)
