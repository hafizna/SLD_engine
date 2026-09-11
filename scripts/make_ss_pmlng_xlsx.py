"""samples/ss_pmlng_ingest.xlsx -- Subsistem Pemalang 1,2 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.8 (PDF p.173-175) for the risk table, and
Lampiran-3 "Single Line Diagram Subsistem Jawa Tengah Dan DIY" (PDF p.250) for
the topology. The Lampiran shades each subsistem in its own colour; the Pemalang
block is the olive-green area at the top-left, so its membership is read off the
drawing rather than inferred.

Injection is GITET Pemalang 500 kV -> IBT 1,2 -> the 150 kV bus at NBTNG, with
the 500 kV side going out to Tanjungjati and Mandirancan (drawn as bays -- those
GITETs belong to other subsistem sheets, which is why they are not assets here).
The 150 kV network is two chains off that injection:
  NBTNG - BNPTH - WLERI ... (eastward, toward Ungaran)
  NBTNG - BTANG - PKLON - COMAL - PMLNG - TARUB - KBSEN (westward, toward Tegal)
KBSEN (Kebasen) is the boundary toward Subsistem Mandirancan / UP2B Jabar and is
marked SOURCE_BOUNDARY; risks 1, 2 and 4 are all about supplying "sampai GI
Kebasen", so the boundary has to be on the sheet for those pins to make sense.

Run: python scripts/make_ss_pmlng_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    # -- 500 kV GITET (shares its code with the 150 kV bus -> parser auto-splits) --
    dict(code="PMLNG7", name="GITET Pemalang", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 1 PMLNG7", name="IBT 1,2 Pemalang 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus150="NBTNG", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="1"),
    # -- 150 kV injection bus fed by the IBT --
    dict(code="NBTNG", name="New Batang (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="2x60 MVA"),
    # -- eastward chain --
    dict(code="BNPTH", name="Bumi Putih", type="Busbar GI", tier=2, simbol="2x60 MVA"),
    dict(code="WLERI", name="Weleri", type="Busbar GI", tier=3, simbol="2x60 MVA"),
    # -- westward chain toward Tegal --
    dict(code="BTANG", name="Batang", type="Busbar GI", tier=2,
         simbol="30/60/60 MVA + 25 MVAR", kerawanan="2"),
    dict(code="PKLON", name="Pekalongan", type="Busbar GI", tier=3,
         simbol="3x60 MVA + 25 MVAR", kerawanan="2"),
    dict(code="COMAL", name="Comal", type="Busbar GI", tier=4, simbol="60 MVA"),
    dict(code="PMLNG", name="Pemalang", type="Busbar GI", tier=5,
         simbol="3x60 MVA + 25 MVAR (kapasitor 1 PMS busbar)", kerawanan="3"),
    dict(code="TARUB", name="Tarub", type="Busbar GI", tier=6, simbol="60 MVA"),
    dict(code="KBSEN", name="Kebasen", type="Busbar GI", tier=7,
         role="SOURCE_BOUNDARY", kerawanan="4",
         simbol="batas ke Subsistem Mandirancan (UP2B Jabar)"),
]

# 500 kV outgoing bays at GITET Pemalang -- the far ends sit on other sheets.
BAYS = [
    ("TJATI7", "GITET Tanjungjati (500 kV)", "PMLNG7", None, 2),
    ("MDCAN7", "GITET Mandirancan (500 kV)", "PMLNG7", None, 4),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    # eastward
    L("NBTNG", "BNPTH", "SUTT New Batang - Bumi Putih", 1, 2),
    L("BNPTH", "WLERI", "SUTT Bumi Putih - Weleri", 2, 3),
    # westward -- Batang-Pekalongan is kerawanan #2 (>60%, N-1 tidak terpenuhi)
    L("NBTNG", "BTANG", "SUTT New Batang - Batang", 1, 2),
    L("BTANG", "PKLON", "SUTT Batang - Pekalongan", 2, 3, kno="2"),
    L("PKLON", "COMAL", "SUTT Pekalongan - Comal", 3, 4),
    L("COMAL", "PMLNG", "SUTT Comal - Pemalang", 4, 5),
    L("PMLNG", "TARUB", "SUTT Pemalang - Tarub", 5, 6),
    L("TARUB", "KBSEN", "SUTT Tarub - Kebasen", 6, 7, kno="4"),
]

SPEC = dict(
    code="SS_PMLNG",
    name="Pemalang 1,2",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.8 (Tabel 4.6, PDF p.173-175); "
               "topologi dari Lampiran-3 Single Line Diagram Jawa Tengah & DIY (PDF p.250)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(174, 175, expected=4),
)

if __name__ == "__main__":
    build_workbook(SPEC)
