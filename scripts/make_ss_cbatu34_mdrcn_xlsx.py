"""samples/ss_cbatu34_mdrcn_ingest.xlsx -- Subsistem Cibatu 3,4 - PLTU Indramayu
- Mandirancan 1,2 (UP2B Jawa Barat).

Source: Buku Kerawanan SJB 2026 Sec 3.3, Gambar 3.3 (Peta Kerawanan, PDF p.111)
and Tabel 3.1. The rows sit on PDF p.112-118; the range comes from the risk
numbering, not the heading.

**This subsystem is MULTIVIEW.** Gambar 3.3 draws two stacked panels: the upper
one is the Cibatu 3,4 half, the lower one the PLTU Indramayu - Mandirancan half
fed by GITET Mandirancan (MDRCN). Two `Sudut Pandang` over one canonical graph:

    CBATU34   -- sisi Cibatu 3,4 (upper panel)
    MDRCN     -- sisi PLTU Indramayu - Mandirancan 1,2 (lower panel)

The largest risk table in the book at 19 rows.

Boundaries, each drawn with its owner in brackets. Nearly all of them are GIs a
neighbouring sheet already carries, which is the cross-check that the traces
agree:
    HNKOK          "(SS CBATU 1,2)"   -- Cibatu 1,2 - Deltamas carries it
    TGHRG, MGKYA   "(SS DLTMS)"       -- same sheet
    SKMDI          "(SS MDRCN 1,2)"   -- the lower panel of this sheet
    PDLRU, PWKTA   "(SS CRATA ...)"   -- Cirata 1,2,3 carries both
    SKTNI          "(SS SKTNI 1,2)"   -- Sukatani 1,2 carries it
    PRKAN          "(SS NUBRG)"       -- Bandung Selatan - New Ujungberung

Run: python scripts/make_ss_cbatu34_mdrcn_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"
CBT = ["CBATU34"]
MDR = ["MDRCN"]
BOTH = ["CBATU34", "MDRCN"]

VIEWS = [
    ("CBATU34", "Sisi Cibatu 3,4", "CBATU34", 111),
    ("MDRCN", "Sisi PLTU Indramayu - Mandirancan 1,2", "MDRCN5", 111),
]

ASSETS = [
    # ================= sisi Cibatu 3,4 =================
    dict(code="CBATU347", name="GITET Cibatu 3,4", type="Busbar GITET",
         tier=1, kv="500 kV", views=CBT),
    dict(code="IBT 3 CBATU347", name="IBT 3 Cibatu 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="3",
         bus_hv="CBATU347", bus_lv="CBATU34", trafo=1, kerawanan="1", views=CBT),
    dict(code="IBT 4 CBATU347", name="IBT 4 Cibatu 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="4",
         bus_hv="CBATU347", bus_lv="CBATU34", trafo=1, kerawanan="1", views=CBT),
    dict(code="CBATU34", name="Cibatu 3,4 (bus 150 kV)", type="Busbar GI",
         tier=1, simbol="bus section + kopel", views=CBT),
    dict(code="JUSIN", name="Jababeka Usin", type="Busbar GI", tier=2, views=CBT),
    dict(code="CLGSI", name="Cilegsi", type="Busbar GI", tier=2, views=CBT),
    dict(code="MKSRI", name="Maka Sri", type="Busbar GI", tier=2,
         kerawanan="2", views=CBT),
    dict(code="KSBRU", name="Kesambi Baru", type="Busbar GI", tier=2, views=CBT),
    dict(code="PNYNG", name="Pinayungan", type="Busbar GI", tier=3,
         simbol="GI Simpul 4 subsistem; split busbar + kopel",
         kerawanan="3", views=CBT),
    dict(code="KTMKR", name="Katomukti", type="Busbar GI", tier=3, views=CBT),
    dict(code="MLIGI", name="Maligi", type="Busbar GI", tier=3, views=CBT),
    dict(code="PRURI", name="Peruri", type="Busbar GI", tier=4,
         kerawanan="4", views=CBT),
    dict(code="PRMYA", name="Purwamaya", type="Busbar GI", tier=4, views=CBT),
    dict(code="TLJBE", name="Tanjung Jabe", type="Busbar GI", tier=5, views=CBT),
    dict(code="HONDA", name="Honda", type="Busbar GI", tier=5, views=CBT),
    dict(code="ILBTY", name="Indolakto Beauty", type="Busbar GI", tier=4, views=CBT),
    dict(code="KRPYG", name="Karang Pawitan", type="Busbar GI", tier=4, views=CBT),
    # Lampiran-2 places Tegal Tanjung Baru out toward Dawuan rather than beside
    # Kesambi Baru, so it belongs a tier further down. At Tier-2 its ruas shared
    # a band with Maka Sri - Pinayungan and the two read as one conductor.
    dict(code="TTJBR", name="Tegal Tanjung Baru", type="Busbar GI", tier=3,
         views=CBT),
    dict(code="DWUAN", name="Dawuan", type="Busbar GI", tier=3, views=CBT),
    # 70 kV sisi Cibatu 3,4
    dict(code="IBT 1 DWUAN", name="IBT 150/70 kV Dawuan", type="IBT 3-Winding",
         tier=3, kv="150/70 kV", ibt="1", bus_hv="DWUAN", bus_lv="DWUAN4",
         trafo=2, simbol="IBT 150/70 kV", kerawanan="5", views=CBT),
    dict(code="DWUAN4", name="Dawuan (bus 70 kV)", type="Busbar GI",
         tier=3, kv=70, simbol="bus section + kopel", views=CBT),
    # The 70 kV tail sits a tier below the 70 kV Dawuan bus. Keeping it at the
    # same tier put it level with DWUAN4 once the renderer nudged that bus under
    # its 150 kV parent, leaving the chain no downward channel.
    dict(code="RDLOK", name="Rengasdengklok", type="Busbar GI", tier=5, kv=70,
         kerawanan="6", views=CBT),
    dict(code="PNDLI", name="Pondok Ali", type="Busbar GI", tier=5, kv=70,
         views=CBT),
    # ================= sisi PLTU Indramayu - Mandirancan =================
    dict(code="MDRCN7", name="GITET Mandirancan", type="Busbar GITET",
         tier=1, kv="500 kV", views=MDR),
    dict(code="IBT 1 MDRCN7", name="IBT 1 Mandirancan 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1",
         bus_hv="MDRCN7", bus_lv="MDRCN5", trafo=1, kerawanan="7", views=MDR),
    dict(code="IBT 2 MDRCN7", name="IBT 2 Mandirancan 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="2",
         bus_hv="MDRCN7", bus_lv="MDRCN5", trafo=1, kerawanan="7", views=MDR),
    dict(code="MDRCN5", name="Mandirancan (bus 150 kV)", type="Busbar GI",
         tier=1, views=MDR),
    dict(code="KIT_IDMYU", name="PLTU Indramayu", type="Pembangkit",
         tier=1, kv="150 kV", views=MDR),
    dict(code="IDMYU5", name="Indramayu (bus PLTU)", type="Busbar GI", tier=1,
         kerawanan="9", views=MDR),
    dict(code="SKMDI", name="Sukamedi", type="Busbar GI", tier=2, views=MDR),
    dict(code="NARJW", name="Narajiwa", type="Busbar GI", tier=2, views=MDR),
    dict(code="SRAGI", name="Seragi", type="Busbar GI", tier=2,
         kerawanan="8", views=MDR),
    dict(code="HRGLS", name="Haurgeulis", type="Busbar GI", tier=3, views=MDR),
    dict(code="JTBRG", name="Jatibarang", type="Busbar GI", tier=3, views=MDR),
    dict(code="CKRBR", name="Cikarang Barat", type="Busbar GI", tier=3,
         kerawanan="15", views=MDR),
    dict(code="CKDNG", name="Cikedung", type="Busbar GI", tier=4, views=MDR),
    # 70 kV sisi Mandirancan
    dict(code="IBT 1 JTBRG", name="IBT 150/70 kV Jatibarang",
         type="IBT 3-Winding", tier=4, kv="150/70 kV", ibt="1",
         bus_hv="JTBRG", bus_lv="ARJWN", trafo=2,
         simbol="IBT 150/70 kV", kerawanan="12", views=MDR),
    dict(code="ARJWN", name="Arjawinangun (bus 70 kV)", type="Busbar GI",
         tier=4, kv=70, simbol="bus section + kopel", views=MDR),
    dict(code="IDMYU", name="Indramayu (bus 70 kV)", type="Busbar GI",
         tier=5, kv=70, kerawanan="16", views=MDR),
    dict(code="SEMEN", name="Semen", type="Busbar GI", tier=4, kv=70,
         kerawanan="17", views=MDR),
    dict(code="KDPTN", name="Kadipaten (bus 70 kV)", type="Busbar GI",
         tier=4, kv=70, kerawanan="18", views=MDR),
    # GI Sunyaragi: the anchor for risks 10, 11, 13 and 14. It steps 150 kV down
    # twice at DIFFERENT ratios -- IBT 1 & 5 at 150/70 and IBT 2 at 150/66 --
    # and risk 11 is precisely that the two cannot run in parallel because of
    # that ratio difference. Modelling only one of them would erase the risk.
    dict(code="SYRGI", name="Sunyaragi", type="Busbar GI", tier=3, views=MDR),
    dict(code="IBT 1 SYRGI", name="IBT 1 Sunyaragi 150/70 kV",
         type="IBT 3-Winding", tier=4, kv="150/70 kV", ibt="1",
         bus_hv="SYRGI", bus_lv="SYRGI4", trafo=1, kerawanan="10", views=MDR),
    dict(code="IBT 5 SYRGI", name="IBT 5 Sunyaragi 150/70 kV",
         type="IBT 3-Winding", tier=4, kv="150/70 kV", ibt="5",
         bus_hv="SYRGI", bus_lv="SYRGI4", trafo=1, kerawanan="10", views=MDR),
    dict(code="SYRGI4", name="Sunyaragi (bus 70 kV)", type="Busbar GI",
         tier=4, kv=70, views=MDR),
    dict(code="IBT 2 SYRGI", name="IBT 2 Sunyaragi 150/66 kV",
         type="IBT 3-Winding", tier=4, kv="150/66 kV", ibt="2",
         bus_hv="SYRGI", bus_lv="SYRGI6", trafo=1,
         simbol="IBT 2 150/66 kV; beda rasio, tidak paralel dengan IBT 1&5",
         kerawanan="11", views=MDR),
    dict(code="SYRGI6", name="Sunyaragi (bus 66 kV)", type="Busbar GI",
         tier=4, kv=66, views=MDR),
    dict(code="KNNGN6", name="Kuningan (bus 66 kV)", type="Busbar GI",
         tier=5, kv=66, simbol="tegangan primer rendah (risiko 11)",
         kerawanan="11", views=MDR),
    dict(code="BBKAN", name="Babakan", type="Busbar GI", tier=5, kv=70,
         kerawanan="14", views=MDR),
    dict(code="KNNGN", name="Kuningan", type="Busbar GI", tier=5, kv=70,
         kerawanan="13;19", views=MDR),
    # ============ batas subsistem ============
    dict(code="HNKOK", name="Hankook (SS Cibatu 1,2)", type="Busbar GI", tier=2,
         role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 1,2 - Deltamas 1,2", views=CBT),
    dict(code="TGHRG", name="Tegal Herang (SS Deltamas)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 1,2 - Deltamas 1,2", views=CBT),
    dict(code="MGKYA", name="Mega Kaya (SS Deltamas)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 1,2 - Deltamas 1,2", views=CBT),
    dict(code="SKTNI", name="Sukatani (SS Sukatani 1,2)", type="Busbar GI",
         tier=3, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Sukatani 1,2", views=CBT),
    dict(code="PDLRU", name="Padalarang Baru (SS Cirata)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cirata 1,2,3", views=CBT),
    dict(code="PWKTA", name="Purwakarta (SS Cirata)", type="Busbar GI",
         tier=6, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cirata 1,2,3", views=CBT),
    dict(code="IDBRT", name="Indramayu Barat (SS Cirata)", type="Busbar GI",
         tier=6, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cirata 1,2,3", views=CBT),
    dict(code="CURUG", name="Curug (SS Cirata)", type="Busbar GI",
         tier=6, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cirata 1,2,3", views=CBT),
    dict(code="PRKAN", name="Parakan (SS New Ujungberung)", type="Busbar GI",
         tier=5, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Bandung Selatan - New Ujungberung",
         views=MDR),
    dict(code="KSBRU_M", name="Kesambi Baru (sisi Mandirancan)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke sisi Cibatu 3,4", views=MDR),
]


def L(fr, to, nm, tf, tt, views, kv=150, kno=None, st="Beroperasi", sirkit=2):
    return dict(fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt,
                kerawanan=kno, status=st, sirkit=sirkit, koridor=WIL, views=views)


LINES = [
    # ================= sisi Cibatu 3,4 =================
    L("CBATU34", "JUSIN", "SUTT Cibatu 3,4 - Jababeka Usin", 1, 2, CBT),
    L("CBATU34", "CLGSI", "SUTT Cibatu 3,4 - Cilegsi", 1, 2, CBT),
    L("CBATU34", "HNKOK", "SUTT Cibatu 3,4 - Hankook (arah SS Cibatu 1,2)", 1, 2, CBT),
    L("CBATU34", "MKSRI", "SUTT Cibatu 3,4 - Maka Sri", 1, 2, CBT, kno="2"),
    L("CBATU34", "KSBRU", "SUTT Cibatu 3,4 - Kesambi Baru", 1, 2, CBT),
    L("MKSRI", "PNYNG", "SUTT Maka Sri - Pinayungan", 2, 3, CBT, kno="3"),
    L("PNYNG", "TGHRG", "SUTT Pinayungan - Tegal Herang (arah SS Deltamas)", 3, 4, CBT),
    L("PNYNG", "MGKYA", "SUTT Pinayungan - Mega Kaya (arah SS Deltamas)", 3, 4, CBT),
    L("PNYNG", "PRURI", "SUTT Pinayungan - Peruri", 3, 4, CBT, kno="4"),
    L("PRURI", "PRMYA", "SUTT Peruri - Purwamaya", 4, 4, CBT),
    L("PRMYA", "TLJBE", "SUTT Purwamaya - Tanjung Jabe", 4, 5, CBT),
    L("PRMYA", "HONDA", "SUTT Purwamaya - Honda", 4, 5, CBT),
    L("KSBRU", "KTMKR", "SUTT Kesambi Baru - Katomukti", 2, 3, CBT),
    L("KSBRU", "MLIGI", "SUTT Kesambi Baru - Maligi", 2, 3, CBT),
    L("MLIGI", "ILBTY", "SUTT Maligi - Indolakto Beauty", 3, 4, CBT),
    L("MLIGI", "KRPYG", "SUTT Maligi - Karang Pawitan", 3, 4, CBT),
    L("KSBRU", "SKMDI", "SUTT Kesambi Baru - Sukamedi (arah sisi Mandirancan)",
      2, 2, CBT),
    L("KSBRU", "TTJBR", "SUTT Kesambi Baru - Tegal Tanjung Baru", 2, 3, CBT),
    L("TTJBR", "PDLRU", "SUTT Tegal Tanjung Baru - Padalarang Baru (arah SS Cirata)",
      3, 2, CBT),
    L("TTJBR", "DWUAN", "SUTT Tegal Tanjung Baru - Dawuan", 3, 3, CBT),
    L("DWUAN", "SKTNI", "SUTT Dawuan - Sukatani (arah SS Sukatani 1,2)", 3, 3, CBT),
    # 70 kV sisi Cibatu 3,4. Lampiran-2 draws this as ONE long 70 kV bar with
    # PNDLI, RSDLK, CURUG and IDBRT tapped off it at 440 A each, not as a fan of
    # separate ruas out of Dawuan -- the fan version had no routable channel.
    # The symbols under RSDLK and CURUG are orange load transformers (70/20 kV),
    # not generators; the green machines on this sheet are PLTS Cirata at SGLNG
    # and CRATA.
    L("DWUAN4", "PNDLI", "SUTT 70 kV Dawuan - Pondok Ali", 3, 5, CBT, kv=70, sirkit=1),
    L("PNDLI", "RDLOK", "SUTT 70 kV Pondok Ali - Rengasdengklok", 5, 5, CBT,
      kv=70, kno="6", sirkit=1),
    L("RDLOK", "CURUG", "SUTT 70 kV Rengasdengklok - Curug (arah SS Cirata)",
      5, 6, CBT, kv=70, sirkit=1),
    L("PNDLI", "IDBRT", "SUTT 70 kV Pondok Ali - Indramayu Barat (arah SS Cirata)",
      5, 6, CBT, kv=70, sirkit=1),
    L("PNDLI", "PWKTA", "SUTT 70 kV Pondok Ali - Purwakarta (arah SS Cirata)",
      5, 6, CBT, kv=70),
    # ================= sisi Mandirancan =================
    L("KIT_IDMYU", "IDMYU5", "Outlet PLTU Indramayu", 1, 1, MDR, sirkit=1),
    L("IDMYU5", "KSBRU_M", "SUTT Indramayu - Kesambi Baru (arah sisi Cibatu 3,4)",
      1, 2, MDR),
    L("IDMYU5", "SKMDI", "SUTT Indramayu - Sukamedi", 1, 2, MDR, kno="9"),
    L("MDRCN5", "NARJW", "SUTT Mandirancan - Narajiwa", 1, 2, MDR),
    L("MDRCN5", "SRAGI", "SUTT Mandirancan - Seragi", 1, 2, MDR, kno="8"),
    L("SKMDI", "HRGLS", "SUTT Sukamedi - Haurgeulis", 2, 3, MDR),
    L("NARJW", "JTBRG", "SUTT Narajiwa - Jatibarang", 2, 3, MDR),
    L("SRAGI", "CKRBR", "SUTT Seragi - Cikarang Barat", 2, 3, MDR, kno="15"),
    L("HRGLS", "CKDNG", "SUTT Haurgeulis - Cikedung", 3, 4, MDR),
    L("JTBRG", "CKDNG", "SUTT Jatibarang - Cikedung", 3, 4, MDR),
    # 70 kV sisi Mandirancan
    L("ARJWN", "IDMYU", "SUTT 70 kV Arjawinangun - Indramayu", 4, 5, MDR, kv=70,
      kno="16"),
    L("ARJWN", "SEMEN", "SUTT 70 kV Arjawinangun - Semen", 4, 4, MDR, kv=70,
      kno="17", sirkit=1),
    L("ARJWN", "KDPTN", "SUTT 70 kV Arjawinangun - Kadipaten", 4, 4, MDR, kv=70,
      kno="18", sirkit=1),
    L("KDPTN", "KNNGN", "SUTT 70 kV Kadipaten - Kuningan", 4, 5, MDR, kv=70,
      kno="19"),
    # Sunyaragi feeds the 70 kV tail; risks 13 and 14 name these two ruas.
    L("SRAGI", "SYRGI", "SUTT Seragi - Sunyaragi", 2, 3, MDR),
    L("SYRGI4", "KNNGN", "SUTT 70 kV Sunyaragi - Kuningan 1,2", 4, 5, MDR,
      kv=70, kno="13"),
    L("SYRGI4", "BBKAN", "SUTT 70 kV Sunyaragi - Babakan 1,2", 4, 5, MDR,
      kv=70, kno="14"),
    L("SYRGI4", "ARJWN", "SUTT 70 kV Sunyaragi - Arjawinangun", 4, 4, MDR, kv=70),
    L("SYRGI6", "KNNGN6", "SUTT 66 kV Sunyaragi - Kuningan", 4, 5, MDR, kv=66),
    L("KDPTN", "PRKAN", "SUTT 70 kV Kadipaten - Parakan (arah SS New Ujungberung)",
      4, 5, MDR, kv=70),
]

SPEC = dict(
    code="SS_CBATU34_MDRCN",
    name="Cibatu 3,4 - PLTU Indramayu - Mandirancan 1,2",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.3 (Tabel 3.1, PDF p.112-118); "
               "topologi dari Gambar 3.3 Peta Kerawanan, dua panel (PDF p.111)",
    views=VIEWS,
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(112, 118, expected=19),
)

if __name__ == "__main__":
    build_workbook(SPEC)
