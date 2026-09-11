"""samples/ss_paiton123_ingest.xlsx -- Subsistem Paiton 1,2,3 (UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.9 (PDF p.228-237) for the risk table, and
Lampiran-4 (PDF p.251) for topology. Paiton is the blue-violet block down the
right-hand edge of that drawing.

GITET Paiton 500 kV (PITON7) steps down through IBT 1,3 (2x500 MVA, 500/150 kV)
onto the PITON5 150 kV bus. From there a single long radial chain runs east and
then south around the tip of Java -- this is the shape that drives nearly every
risk in the table, because each ruas in the chain carries the load of everything
downstream of it:

  PITON5 -> STBND (Situbondo) -> BWANG (Banyuwangi) -> GTENG (Genteng)
         -> JMBER (Jember) -> TNGUL (Tanggul) -> LJANG (Lumajang)
  plus BDWSO (Bondowoso) hanging off Situbondo, and PUGER off Jember.

Risks 1-2 are the IBTs themselves (>90% and >80%). Risks 3-6 walk that chain:
Paiton-Situbondo >90%, Situbondo-Bondowoso >60%, Situbondo-Banyuwangi >65%,
Lumajang-Tanggul >60%. Risk 7 is a single-phi pair on Jember-Genteng, and risk 8
is the Kabel Laut SKLT 150 kV Banyuwangi-Gilimanuk 1,2,3,4 that carries the Bali
transfer -- Gilimanuk is on the Bali sheet, so it is a SOURCE_BOUNDARY here.

Run: python scripts/make_ss_paiton123_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # -- 500 kV GITET + pembangkit --
    dict(code="PITON7", name="GITET Paiton", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 1 PITON7", name="IBT 1,3 Paiton 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus150="PITON5", trafo=2,
         simbol="2 IBT x 500 MVA (unit 1,3)", kerawanan="2"),
    dict(code="IBT 2 PITON7", name="IBT 2 Paiton 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus150="PITON5", trafo=1,
         simbol="1 IBT x 500 MVA (unit 2); beban >90%", kerawanan="1"),
    # -- 150 kV injection --
    dict(code="PITON5", name="Paiton (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus A1/B1 - A2/B2"),
    # -- rantai radial ke timur lalu selatan --
    dict(code="STBND", name="Situbondo", type="Busbar GI", tier=2,
         simbol="60/20/60 MVA", kerawanan="3"),
    dict(code="BDWSO", name="Bondowoso", type="Busbar GI", tier=3,
         simbol="20/20/60 MVA", kerawanan="4"),
    dict(code="BWANG", name="Banyuwangi", type="Busbar GI", tier=3,
         simbol="30/60/30 MVA + 25 MVAR + SVC (+50/-25 MVAR)", kerawanan="5"),
    dict(code="GTENG", name="Genteng", type="Busbar GI", tier=4,
         simbol="60/60/60 MVA", kerawanan="7"),
    dict(code="JMBER", name="Jember", type="Busbar GI", tier=5,
         simbol="4x60 MVA + 50 MVAR", kerawanan="7"),
    dict(code="PUGER", name="Puger", type="Busbar GI", tier=6,
         simbol="60 MVA + 2x25 MVAR"),
    dict(code="TNGUL", name="Tanggul", type="Busbar GI", tier=6,
         simbol="60 MVA", kerawanan="6"),
    dict(code="LJANG", name="Lumajang", type="Busbar GI", tier=7,
         simbol="3x60 MVA + 50 MVAR", kerawanan="6"),
    dict(code="KRSAN", name="Kraksaan", type="Busbar GI", tier=2,
         simbol="2x60 MVA"),
    dict(code="GDING", name="Gending", type="Busbar GI", tier=2, simbol="25 MVA"),
    # -- pembangkit --
    dict(code="KIT_IJEN", name="PLTP Ijen", type="Pembangkit", tier=4,
         kv="150 kV", simbol="1x30 MW"),
    # -- batas transfer Jawa-Bali --
    dict(code="GLMUK", name="Gilimanuk (Subsistem Bali)", type="Busbar GI", tier=4,
         role="SOURCE_BOUNDARY", kerawanan="8",
         simbol="ujung Kabel Laut SKLT Jawa-Bali"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, sp=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=sp, koridor=WIL)

LINES = [
    L("PITON5", "GDING", "SUTT Paiton - Gending", 1, 2),
    L("PITON5", "KRSAN", "SUTT Paiton - Kraksaan", 1, 2),
    # kerawanan #3: Paiton-Situbondo 1&2 >90%
    L("PITON5", "STBND", "SUTT Paiton - Situbondo 1,2", 1, 2, kno="3"),
    # kerawanan #4: Situbondo-Bondowoso 1&2 >60%
    L("STBND", "BDWSO", "SUTT Situbondo - Bondowoso 1,2", 2, 3, kno="4"),
    # kerawanan #5: Situbondo-Banyuwangi 1&2 >65%
    L("STBND", "BWANG", "SUTT Situbondo - Banyuwangi 1,2", 2, 3, kno="5"),
    # kerawanan #7: Jember-Genteng dan Genteng-Banyuwangi single phi
    L("BWANG", "GTENG", "SUTT Banyuwangi - Genteng (single phi)",
      3, 4, kno="7", sirkit=1, sp=True),
    L("GTENG", "JMBER", "SUTT Genteng - Jember (single phi)",
      4, 5, kno="7", sirkit=1, sp=True),
    L("JMBER", "PUGER", "SUTT Jember - Puger", 5, 6),
    L("JMBER", "TNGUL", "SUTT Jember - Tanggul", 5, 6),
    # kerawanan #6: Lumajang-Tanggul 1&2 >60%
    L("TNGUL", "LJANG", "SUTT Lumajang - Tanggul 1,2", 6, 7, kno="6"),
    L("BDWSO", "JMBER", "SUTT Bondowoso - Jember", 3, 5),
    L("KIT_IJEN", "GTENG", "Outlet PLTP Ijen - Genteng", 4, 4, sirkit=1),
    # kerawanan #8: Kabel Laut SKLT 150 kV Banyuwangi-Gilimanuk 1,2,3,4
    L("BWANG", "GLMUK", "SKLT 150 kV Banyuwangi - Gilimanuk 1,2,3,4 (Kabel Laut Jawa-Bali)",
      3, 4, kno="8", sirkit=4),
]

SPEC = dict(
    code="SS_PAITON123",
    name="Paiton 1,2,3",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.9 (PDF p.228-237); "
               "topologi dari Lampiran-4 Single Line Diagram Jawa Timur (PDF p.251)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(228, 237, expected=8),
)

if __name__ == "__main__":
    build_workbook(SPEC)
