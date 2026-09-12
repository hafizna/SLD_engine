"""samples/ss_bdgsel_nubrg_ingest.xlsx -- Subsistem Bandung Selatan 1,2 -
New Ujungberung 1,2 (UP2B Jawa Barat).

Source: Buku Kerawanan SJB 2026 Sec 3.6, Gambar 3.4 (Peta Kerawanan, PDF p.127)
and Tabel 3.2. The rows sit on PDF p.128-132; the Cibatu 1,2 table still runs on
p.127, so the range comes from the risk numbering, not the heading.

**This subsystem is MULTIVIEW.** Gambar 3.4 draws it as two stacked panels, the
upper one fed by GITET Bandung Selatan (BDSLN) and the lower by GITET New
Ujungberung (NUBRG), exactly the split the name implies. Two `Sudut Pandang`
over one canonical GI graph:

    BDGSEL   -- sisi Bandung Selatan (upper panel)
    NUBRG    -- sisi New Ujungberung (lower panel)

UBRNG (Ujung Berung) and DGPKR are drawn on BOTH panels and carry both view
keys, so they reconcile to one canonical substation per GI. Any ruas whose two
endpoints are both shared has to carry both view keys too, or the other view
renders a dangling endpoint.

Both halves carry a 70 kV network (yellow on the figure) reached through an
IBT 150/70: CGRLG on the Bandung Selatan side feeding CKLNG/LMJAN/SNTSA/MJLYA/
SMDRA/PMPEK, and UBRNG on the New Ujungberung side feeding SMDNG/KDPTN.

Boundaries, each drawn with its owner in brackets:
    LBSTU, BGBRU, TAJUR  "(UP2B JAKBAN)"  -- the Pelabuhan Ratu sheet carries
                                             LBSTU and BGBRU as its own GIs
    LGDAR, DGPKR         "(SS CRATA)"      -- Cirata 1,2,3 carries both
    GARUT                "(SS TASIK)"      -- Tasikmalaya 1,2 carries it
    SRAGI, NKDPT, ARJWN  "(SS MDRCN)"      -- toward Mandirancan
    WYNDU, GDBGE         "(SS BDSLN)"      -- named on the NUBRG panel as the
                                             tie back to the BDSLN half

Run: python scripts/make_ss_bdgsel_nubrg_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"
BDG = ["BDGSEL"]
NUB = ["NUBRG"]
BOTH = ["BDGSEL", "NUBRG"]

VIEWS = [
    ("BDGSEL", "Sisi Bandung Selatan 1,2", "BDSLN", 127),
    ("NUBRG", "Sisi New Ujungberung 1,2", "NUBRG5", 127),
]

ASSETS = [
    # ================= sisi Bandung Selatan =================
    dict(code="BDSLN7", name="GITET Bandung Selatan", type="Busbar GITET",
         tier=1, kv="500 kV", views=BDG),
    dict(code="IBT 1 BDSLN7", name="IBT 1,2 Bandung Selatan 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1,2",
         bus_hv="BDSLN7", bus_lv="BDSLN", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="1", views=BDG),
    dict(code="BDSLN", name="Bandung Selatan (bus 150 kV)", type="Busbar GI",
         tier=1, views=BDG),
    dict(code="KIT_RJMDL", name="PLTA Rajamandala", type="Pembangkit",
         tier=1, kv="150 kV", views=BDG),
    dict(code="RJMDL", name="Rajamandala", type="Busbar GI", tier=1,
         kerawanan="3", views=BDG),
    dict(code="KIT_WYWDU", name="PLTP Wayang Windu", type="Pembangkit",
         tier=1, kv="150 kV", views=BDG),
    dict(code="WYWDU", name="Wayang Windu", type="Busbar GI", tier=1,
         kerawanan="4", views=BDG),
    dict(code="SKLYU", name="Sukaluyu", type="Busbar GI", tier=2,
         simbol="bus section + kopel", views=BDG),
    dict(code="CGRLG", name="Cigereleng", type="Busbar GI", tier=2, views=BDG),
    dict(code="DYKLT", name="Dayeuh Kolot", type="Busbar GI", tier=2, views=BDG),
    dict(code="PNSIA", name="Panasia", type="Busbar GI", tier=2, views=BDG),
    dict(code="KRCDG", name="Kiaracondong", type="Busbar GI", tier=2,
         kerawanan="2", views=BDG),
    dict(code="CNJUR", name="Cianjur", type="Busbar GI", tier=3,
         kerawanan="7", views=BDG),
    dict(code="CBERM", name="Cibereum", type="Busbar GI", tier=3, views=BDG),
    dict(code="BRAGA", name="Braga", type="Busbar GI", tier=3, views=BDG),
    # 70 kV sisi Bandung Selatan
    dict(code="IBT 1 CGRLG", name="IBT 150/70 kV Cigereleng",
         type="IBT 3-Winding", tier=3, kv="150/70 kV", ibt="1",
         bus_hv="CGRLG", bus_lv="CGRLG4", trafo=2,
         simbol="IBT 150/70 kV", views=BDG),
    dict(code="CGRLG4", name="Cigereleng (bus 70 kV)", type="Busbar GI",
         tier=3, kv=70, views=BDG),
    dict(code="CKLNG", name="Cikalong", type="Busbar GI", tier=3, kv=70, views=BDG),
    dict(code="LMJAN", name="Lamajan", type="Busbar GI", tier=3, kv=70, views=BDG),
    dict(code="SNTSA", name="Sentosa", type="Busbar GI", tier=3, kv=70,
         kerawanan="8", views=BDG),
    dict(code="MJLYA", name="Majalaya", type="Busbar GI", tier=4, kv=70, views=BDG),
    # PLNGN carries a generator drawn in green on Gambar 3.4. Green marks a
    # PEMBANGKIT, not a voltage class -- it sits on the 70 kV bus like the
    # yellow-drawn machines at CKLNG and LMJAN. A 20 kV secondary would be drawn
    # orange, the same as any trafo secondary.
    dict(code="PLNGN", name="Plengan", type="Busbar GI", tier=4, kv=70, views=BDG),
    dict(code="KIT_PLNGN", name="PLTA Plengan", type="Pembangkit", tier=4,
         kv="70 kV", views=BDG),
    dict(code="SMDRA", name="Sumedang Raya", type="Busbar GI", tier=4, kv=70,
         views=BDG),
    dict(code="PMPEK", name="Pameungpeuk", type="Busbar GI", tier=5, kv=70,
         views=BDG),
    # ================= sisi New Ujungberung =================
    dict(code="NUBRG7", name="GITET New Ujungberung", type="Busbar GITET",
         tier=1, kv="500 kV", views=NUB),
    dict(code="IBT 1 NUBRG7", name="IBT 1,2 New Ujungberung 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1,2",
         bus_hv="NUBRG7", bus_lv="NUBRG5", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="9", views=NUB),
    dict(code="NUBRG5", name="New Ujungberung (bus 150 kV)", type="Busbar GI",
         tier=1, views=NUB),
    dict(code="NRKBA", name="Nanjung Rancaekek Baru", type="Busbar GI", tier=1,
         views=NUB),
    dict(code="KIT_KMJNG", name="PLTP Kamojang", type="Pembangkit",
         tier=1, kv="150 kV", views=NUB),
    dict(code="KMJNG", name="Kamojang", type="Busbar GI", tier=1,
         kerawanan="10", views=NUB),
    dict(code="KIT_DRJAT", name="PLTP Darajat", type="Pembangkit",
         tier=1, kv="150 kV", views=NUB),
    dict(code="DRJAT", name="Darajat", type="Busbar GI", tier=1, views=NUB),
    dict(code="KIT_JTDGE", name="PLTA Jatigede", type="Pembangkit",
         tier=1, kv="150 kV", views=NUB),
    dict(code="JTDGE", name="Jatigede", type="Busbar GI", tier=1,
         kerawanan="11", views=NUB),
    dict(code="CKSKA", name="Cikasungka", type="Busbar GI", tier=2, views=NUB),
    dict(code="RCKEK", name="Rancaekek", type="Busbar GI", tier=2, views=NUB),
    dict(code="RCKBA", name="Rancaekek Baru", type="Busbar GI", tier=3, views=NUB),
    dict(code="BDTMR", name="Bandung Timur", type="Busbar GI", tier=3, views=NUB),
    dict(code="KIT_PRKAN", name="PLTA Parakan", type="Pembangkit",
         tier=3, kv="70 kV", views=NUB),
    dict(code="PRKAN", name="Parakan", type="Busbar GI", tier=3, kv=70, views=NUB),
    dict(code="SMDNG", name="Sumedang", type="Busbar GI", tier=4, kv=70,
         kerawanan="12", views=NUB),
    dict(code="KDPTN", name="Kadipaten", type="Busbar GI", tier=4, kv=70,
         simbol="bus section + kopel", views=NUB),
    # ================= GI yang muncul di KEDUA panel =================
    dict(code="UBRNG", name="Ujung Berung", type="Busbar GI", tier=2,
         simbol="bus section + kopel", kerawanan="5", views=BOTH),
    dict(code="IBT 1 UBRNG", name="IBT 150/70 kV Ujung Berung",
         type="IBT 3-Winding", tier=3, kv="150/70 kV", ibt="1",
         bus_hv="UBRNG", bus_lv="UBRNG4", trafo=2,
         simbol="IBT 150/70 kV", views=BOTH),
    dict(code="UBRNG4", name="Ujung Berung (bus 70 kV)", type="Busbar GI",
         tier=3, kv=70, views=BOTH),
    # ============ batas subsistem ============
    dict(code="LBSTU", name="Lembur Situ (UP2B Jakban)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Pelabuhan Ratu", views=BDG),
    dict(code="BGBRU", name="Bogor Baru (UP2B Jakban)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Pelabuhan Ratu", views=BDG),
    dict(code="TAJUR", name="Tajur (UP2B Jakban)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke UP2B Jakarta & Banten", views=BDG),
    dict(code="LGDAR", name="Lengkong Dar (SS Cirata)", type="Busbar GI",
         tier=3, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cirata 1,2,3", views=BDG),
    dict(code="DGPKR", name="Degung Pakar (SS Cirata)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY", kerawanan="6",
         simbol="batas ke Subsistem Cirata 1,2,3", views=BOTH),
    dict(code="TRAKSI", name="Traksi Tagolar", type="Busbar GI", tier=5,
         role="SOURCE_BOUNDARY", simbol="penyulang traksi", views=BDG),
    dict(code="GARUT", name="Garut (SS Tasikmalaya)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Tasikmalaya 1,2", views=NUB),
    dict(code="SRAGI", name="Seragi (SS Mandirancan)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Mandirancan 1,2", views=NUB),
    dict(code="NKDPT", name="New Kadipaten (SS Mandirancan)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Mandirancan 1,2", views=NUB),
    dict(code="ARJWN", name="Arjawinangun (SS Mandirancan)", type="Busbar GI",
         tier=5, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Mandirancan 1,2", views=NUB),
    dict(code="WYNDU", name="Wayang Windu (SS Bandung Selatan)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY",
         simbol="batas ke sisi Bandung Selatan", views=NUB),
    dict(code="GDBGE", name="Gedebage (SS Bandung Selatan)", type="Busbar GI",
         tier=3, role="SOURCE_BOUNDARY",
         simbol="batas ke sisi Bandung Selatan", views=NUB),
]


def L(fr, to, nm, tf, tt, views, kv=150, kno=None, st="Beroperasi", sirkit=2):
    return dict(fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt,
                kerawanan=kno, status=st, sirkit=sirkit, koridor=WIL, views=views)


LINES = [
    # ================= sisi Bandung Selatan =================
    L("KIT_RJMDL", "RJMDL", "Outlet PLTA Rajamandala", 1, 1, BDG, sirkit=1),
    L("KIT_WYWDU", "WYWDU", "Outlet PLTP Wayang Windu", 1, 1, BDG, sirkit=1),
    L("RJMDL", "SKLYU", "SUTT Rajamandala - Sukaluyu", 1, 2, BDG, kno="3"),
    L("BDSLN", "CGRLG", "SUTT Bandung Selatan - Cigereleng", 1, 2, BDG),
    L("BDSLN", "DYKLT", "SUTT Bandung Selatan - Dayeuh Kolot", 1, 2, BDG),
    L("BDSLN", "PNSIA", "SUTT Bandung Selatan - Panasia", 1, 2, BDG),
    L("BDSLN", "KRCDG", "SUTT Bandung Selatan - Kiaracondong", 1, 2, BDG, kno="2"),
    L("WYWDU", "KRCDG", "SUTT Wayang Windu - Kiaracondong", 1, 2, BDG, kno="4"),
    L("SKLYU", "CNJUR", "SUTT Sukaluyu - Cianjur", 2, 3, BDG, kno="7"),
    L("SKLYU", "LGDAR", "SUTT Sukaluyu - Lengkong Dar (arah SS Cirata)", 2, 3, BDG),
    L("CGRLG", "CBERM", "SUTT Cigereleng - Cibereum", 2, 3, BDG),
    L("CGRLG", "BRAGA", "SUTT Cigereleng - Braga", 2, 3, BDG),
    L("CNJUR", "LBSTU", "SUTT Cianjur - Lembur Situ (arah UP2B Jakban)", 3, 4, BDG),
    L("CNJUR", "BGBRU", "SUTT Cianjur - Bogor Baru (arah UP2B Jakban)", 3, 4, BDG),
    L("CNJUR", "TAJUR", "SUTT Cianjur - Tajur (arah UP2B Jakban)", 3, 4, BDG),
    # 70 kV sisi Bandung Selatan
    L("CGRLG4", "CKLNG", "SUTT 70 kV Cigereleng - Cikalong", 3, 3, BDG, kv=70, sirkit=1),
    L("CGRLG4", "LMJAN", "SUTT 70 kV Cigereleng - Lamajan", 3, 3, BDG, kv=70, sirkit=1),
    L("CGRLG4", "SNTSA", "SUTT 70 kV Cigereleng - Sentosa", 3, 3, BDG, kv=70,
      kno="8", sirkit=1),
    L("CGRLG4", "MJLYA", "SUTT 70 kV Cigereleng - Majalaya", 3, 4, BDG, kv=70, sirkit=1),
    L("MJLYA", "PLNGN", "SUTT 70 kV Majalaya - Plengan", 4, 4, BDG, kv=70),
    L("KIT_PLNGN", "PLNGN", "Outlet PLTA Plengan", 4, 4, BDG, kv=70, sirkit=1),
    L("SMDRA", "PMPEK", "SUTT 70 kV Sumedang Raya - Pameungpeuk", 4, 5, BDG, kv=70),
    L("SNTSA", "SMDRA", "SUTT 70 kV Sentosa - Sumedang Raya", 3, 4, BDG, kv=70),
    # ================= sisi New Ujungberung =================
    L("KIT_KMJNG", "KMJNG", "Outlet PLTP Kamojang", 1, 1, NUB, sirkit=1),
    L("KIT_DRJAT", "DRJAT", "Outlet PLTP Darajat", 1, 1, NUB, sirkit=1),
    L("KIT_JTDGE", "JTDGE", "Outlet PLTA Jatigede", 1, 1, NUB, sirkit=1),
    L("KMJNG", "WYNDU", "SUTT Kamojang - Wayang Windu (arah sisi Bandung Selatan)",
      1, 2, NUB),
    L("KMJNG", "CKSKA", "SUTT Kamojang - Cikasungka", 1, 2, NUB, kno="10"),
    L("DRJAT", "GARUT", "SUTT Darajat - Garut (arah SS Tasikmalaya)", 1, 2, NUB),
    L("DRJAT", "RCKEK", "SUTT Darajat - Rancaekek", 1, 2, NUB),
    L("JTDGE", "RCKEK", "SUTT Jatigede - Rancaekek", 1, 2, NUB, kno="11"),
    L("JTDGE", "SRAGI", "SUTT Jatigede - Seragi (arah SS Mandirancan)", 1, 2, NUB),
    L("JTDGE", "NKDPT", "SUTT Jatigede - New Kadipaten (arah SS Mandirancan)", 1, 2, NUB),
    L("NUBRG5", "NRKBA", "SUTT New Ujungberung - Nanjung Rancaekek Baru", 1, 1, NUB),
    L("NUBRG5", "UBRNG", "SUTT New Ujungberung - Ujung Berung", 1, 2, NUB),
    L("CKSKA", "RCKBA", "SUTT Cikasungka - Rancaekek Baru", 2, 3, NUB),
    L("RCKEK", "RCKBA", "SUTT Rancaekek - Rancaekek Baru", 2, 3, NUB),
    L("UBRNG", "GDBGE", "SUTT Ujung Berung - Gedebage (arah sisi Bandung Selatan)",
      2, 3, NUB),
    L("UBRNG", "BDTMR", "SUTT Ujung Berung - Bandung Timur", 2, 3, NUB),
    # 70 kV sisi New Ujungberung
    L("KIT_PRKAN", "PRKAN", "Outlet PLTA Parakan", 3, 3, NUB, kv=70, sirkit=1),
    L("UBRNG4", "SMDNG", "SUTT 70 kV Ujung Berung - Sumedang", 3, 4, NUB, kv=70,
      kno="12"),
    L("PRKAN", "KDPTN", "SUTT 70 kV Parakan - Kadipaten", 3, 4, NUB, kv=70),
    L("SMDNG", "KDPTN", "SUTT 70 kV Sumedang - Kadipaten", 4, 4, NUB, kv=70),
    L("KDPTN", "ARJWN", "SUTT 70 kV Kadipaten - Arjawinangun (arah SS Mandirancan)",
      4, 5, NUB, kv=70),
    # ============ ruas yang kedua ujungnya dipakai dua panel ============
    L("UBRNG", "DGPKR", "SUTT Ujung Berung - Degung Pakar (arah SS Cirata)",
      2, 4, BOTH, kno="6"),
    L("UBRNG", "TRAKSI", "SUTT Ujung Berung - Traksi Tagolar", 2, 5, BDG, sirkit=1),
]

SPEC = dict(
    code="SS_BDGSEL_NUBRG",
    name="Bandung Selatan 1,2 - New Ujungberung 1,2",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.6 (Tabel 3.2, PDF p.128-132); "
               "topologi dari Gambar 3.4 Peta Kerawanan, dua panel (PDF p.127)",
    views=VIEWS,
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(128, 132, expected=12),
)

if __name__ == "__main__":
    build_workbook(SPEC)
