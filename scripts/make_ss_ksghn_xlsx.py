"""samples/ss_ksghn_ingest.xlsx -- Subsistem Kesugihan 1,2 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.7 (PDF p.165-172) for the risk table, and
Lampiran-3 (PDF p.250) for topology -- Kesugihan is the large yellow block
covering the whole south-west of that drawing.

This is the biggest of the Jateng subsistem sheets. Injection is GITET Kesugihan
500 kV -> IBT 1,2 -> the KSGHN 150 kV bus, reinforced by PLTU Cilacap (U1,U2 =
2x300 MW on the CLCAP bus, plus U3 660 MW and U4 945 MW) and PLTA Mrica / PLTP
Dieng out at the eastern end.

The 150 kV network is a wide ring rather than a chain, and the risk table names
almost every ruas outright, so the topology below is largely read straight out
of Tabel 4.5 and then confirmed against the Lampiran:

  west  : KSGHN - LMNIS / SMNUS (both single phi at Lomanis, risk #5)
  north : KSGHN - RWALO - KLBKL - BMAYU - BLPLG - KBSEN (risks #4, #7, #11)
  north : RWALO - PBLGA - MRICA - WSOBO - GARNG - DIENG (risks #2, #8, #9, #10)
  east  : KSGHN - GBONG - KBMEN - PWRJO - WATES (risks #3, #14, #17, #18)

Single-phi ruas called out in risks 4, 5 and 9 are marked Single Phi = Ya.
KBSEN (Kebasen) and WATES/BANTUL are the boundaries toward Pemalang and Pedan,
so they carry SOURCE_BOUNDARY.

Run: python scripts/make_ss_ksghn_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    # -- 500 kV GITET --
    dict(code="KSGHN7", name="GITET Kesugihan", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 1 KSGHN7", name="IBT 1,2 Kesugihan 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1,2", bus_hv="KSGHN7", bus_lv="KSGHN", trafo=2,
         simbol="2 IBT x 500 MVA (unit 1,2)", kerawanan="1"),
    # -- 150 kV injection --
    dict(code="KSGHN", name="Kesugihan (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="2x60 MVA"),
    # -- PLTU Cilacap --
    dict(code="CLCAP", name="Cilacap (bus PLTU)", type="Busbar GI", tier=2,
         simbol="SST 40 MVA; outlet tower combined", kerawanan="12"),
    dict(code="KIT_CLCAP", name="PLTU Cilacap U1,U2", type="Pembangkit", tier=2,
         kv="150 kV", simbol="2x300 MW"),
    dict(code="KIT_CLCAP34", name="PLTU Cilacap U3,U4", type="Pembangkit", tier=2,
         kv="150 kV", simbol="U3 660 MW + U4 945 MW"),
    # -- sisi barat / Lomanis --
    dict(code="LMNIS", name="Lomanis", type="Busbar GI", tier=3,
         simbol="single phi; 20/60/30 MVA + KTT Pertamina", kerawanan="5"),
    dict(code="SMNUS", name="Semen Nusantara", type="Busbar GI", tier=3,
         simbol="single phi di GI Lomanis", kerawanan="6"),
    dict(code="STARA", name="Sitanala / Stara", type="Busbar GI", tier=3,
         simbol="2x60 MVA + KTT SBI"),
    # -- sisi utara --
    dict(code="RWALO", name="Rawalo", type="Busbar GI", tier=2,
         simbol="60/30 MVA", kerawanan="2"),
    dict(code="KLBKL", name="Kalibakal", type="Busbar GI", tier=3,
         simbol="30/20/60/60/60 MVA", kerawanan="4"),
    dict(code="KTNGR", name="Katenger", type="Busbar GI", tier=4,
         simbol="PLTA 8,3 MW"),
    dict(code="BMAYU", name="Bumiayu", type="Busbar GI", tier=4,
         simbol="60 MVA", kerawanan="7"),
    dict(code="BLPLG", name="Balapulang", type="Busbar GI", tier=5,
         simbol="2x60 MVA", kerawanan="11"),
    dict(code="KBSEN", name="Kebasen", type="Busbar GI", tier=6,
         role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Pemalang 1,2"),
    # -- cabang Purbalingga / Mrica / Dieng --
    dict(code="PBLGA", name="Purbalingga", type="Busbar GI", tier=3,
         simbol="3x60 MVA", kerawanan="2"),
    dict(code="MRICA", name="PLTA Mrica", type="Busbar GI", tier=4,
         simbol="PLTA Mrica; bay A1-A5 / B1-B4", kerawanan="13"),
    dict(code="WSOBO", name="Wonosobo", type="Busbar GI", tier=5,
         simbol="30 MVA", kerawanan="8"),
    dict(code="GARNG", name="Garung", type="Busbar GI", tier=6,
         simbol="single phi + single busbar; aset PT Geo Dipa Energi",
         kerawanan="9"),
    dict(code="DIENG", name="PLTP Dieng", type="Busbar GI", tier=6,
         simbol="74,5 MVA + 30 MVA", kerawanan="10"),
    # -- sisi timur --
    dict(code="GBONG", name="Gombong", type="Busbar GI", tier=3,
         simbol="60/20/30 MVA + SMPOR 1 MW", kerawanan="14"),
    dict(code="KBMEN", name="Kebumen", type="Busbar GI", tier=4,
         simbol="30/60/60 MVA", kerawanan="18"),
    dict(code="PWRJO", name="Purworejo", type="Busbar GI", tier=5,
         simbol="30/60 MVA", kerawanan="17"),
    dict(code="WATES", name="Wates", type="Busbar GI", tier=6,
         role="SOURCE_BOUNDARY", simbol="batas ke GI Bantul / Subsistem Pedan",
         kerawanan="17"),
    dict(code="WDLTG", name="Wadaslintang", type="Busbar GI", tier=5,
         simbol="16 MVA + PJKLN 1,4 MW + U1,U2 8 MW"),
    dict(code="MNANG", name="Majenang", type="Busbar GI", tier=3,
         simbol="20/30/60 MVA; arah BNJAR SS Tasik"),
    dict(code="START", name="Sidareja / Start", type="Busbar GI", tier=3,
         simbol="60 MVA"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, sp=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=sp, koridor=WIL)

LINES = [
    # -- outlet PLTU Cilacap (tower combined -- kerawanan #12) --
    L("KIT_CLCAP", "CLCAP", "Outlet PLTU Cilacap U1,U2", 2, 2, sirkit=1),
    L("KIT_CLCAP34", "CLCAP", "Outlet PLTU Cilacap U3,U4", 2, 2, sirkit=1),
    L("CLCAP", "RWALO", "SUTT Cilacap - Rawalo 1,2", 2, 2, kno="12"),
    L("CLCAP", "KLBKL", "SUTT Cilacap - Kalibakal (single phi)",
      2, 3, kno="4", sirkit=1, sp=True),
    L("CLCAP", "SMNUS", "SUTT Cilacap - Semen Nusantara", 2, 3, kno="12"),
    # -- sisi barat / Lomanis (single phi di GI Lomanis -- kerawanan #5) --
    # Risks 5/15 (Lomanis) and 6/16 (Semen Nusantara) are the same two ruas seen
    # under different contingencies, so each ruas carries both numbers.
    L("KSGHN", "LMNIS", "SUTT Kesugihan - Lomanis (single phi)",
      1, 3, kno="5;15", sirkit=1, sp=True),
    L("KSGHN", "SMNUS", "SUTT Kesugihan - Semen Nusantara (single phi)",
      1, 3, kno="6;16", sirkit=1, sp=True),
    L("LMNIS", "STARA", "SUTT Lomanis - Stara", 3, 3),
    # -- sisi utara --
    L("KSGHN", "RWALO", "SUTT Kesugihan - Rawalo", 1, 2),
    L("RWALO", "KLBKL", "SUTT Rawalo - Kalibakal (single phi)",
      2, 3, kno="4", sirkit=1, sp=True),
    L("KLBKL", "KTNGR", "SUTT Kalibakal - Katenger", 3, 4),
    L("KLBKL", "BMAYU", "SUTT Kalibakal - Bumiayu", 3, 4, kno="7"),
    L("BMAYU", "BLPLG", "SUTT Bumiayu - Balapulang", 4, 5, kno="11"),
    L("BLPLG", "KBSEN", "SUTT Balapulang - Kebasen", 5, 6),
    L("MNANG", "START", "SUTT Majenang - Sidareja", 3, 3),
    L("START", "RWALO", "SUTT Sidareja - Rawalo", 3, 2),
    # -- cabang Purbalingga / Mrica / Dieng --
    L("RWALO", "PBLGA", "SUTT Rawalo - Purbalingga 1,2", 2, 3, kno="2"),
    L("PBLGA", "MRICA", "SUTT Purbalingga - Mrica 1,2", 3, 4, kno="13"),
    L("MRICA", "WSOBO", "SUTT Mrica - Wonosobo 1,2", 4, 5, kno="2"),
    L("WSOBO", "GARNG", "SUTT Wonosobo - Garung (single phi)",
      5, 6, kno="9", sirkit=1, sp=True),
    L("GARNG", "DIENG", "SUTT Garung - Dieng", 6, 6, kno="8"),
    L("WSOBO", "DIENG", "SUTT Wonosobo - Dieng", 5, 6, kno="10"),
    L("WSOBO", "WDLTG", "SUTT Wonosobo - Wadaslintang", 5, 5),
    # -- sisi timur --
    # Risk 3 is the voltage-excursion case on either of these two ruas, so it
    # rides along with the loading risks already on them (#14, #18).
    L("KSGHN", "GBONG", "SUTT Kesugihan - Gombong 1,2", 1, 3, kno="14;3"),
    L("GBONG", "KBMEN", "SUTT Gombong - Kebumen", 3, 4, kno="18;3"),
    L("KBMEN", "PWRJO", "SUTT Kebumen - Purworejo", 4, 5),
    L("PWRJO", "WATES", "SUTT Purworejo - Wates", 5, 6, kno="17"),
    L("WDLTG", "PWRJO", "SUTT Wadaslintang - Purworejo", 5, 5),
]

SPEC = dict(
    code="SS_KSGHN",
    name="Kesugihan 1,2",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.7 (Tabel 4.5, PDF p.165-172); "
               "topologi dari Lampiran-3 Single Line Diagram Jawa Tengah & DIY (PDF p.250)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(166, 172, expected=18),
)

if __name__ == "__main__":
    build_workbook(SPEC)
