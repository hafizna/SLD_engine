"""samples/ss_sumbagteng_ingest.xlsx -- Subsistem Sumbagteng (Riau, Sumbar, Jambi).

Source: Kerawanan Sistem Sumatera, UIP3B Sumatera, Sep 2026 (the pptx deck),
slide 18 "Peta Kerawanan Sistem Sumbagteng" (tier SLD, vector) and the risk
table on slides 20-23. Conventions as in make_ss_bengkulu_xlsx.py; the SLD is
read as make_ss_sumsel_xlsx.py describes (crossings carry hop arcs, so a
straight line through a busbar is joined to it).

**MULTIVIEW**, one view per panel of slide 18 (the sheet's own dashed dividers):

    RIAU    -- Perawang 500/275/150, Balai Pungut .. Tembilahan, Pakning, Wina
    SUMBAR  -- Payakumbuh / Kiliranjao / Sungai Rumbai 275, Ombilin .. Muko-Muko
    JAMBI   -- New Aurduri 500/275, Muara Bungo / Bangko 275, Aur Duri .. Pelabuhan Dagang

Two 150 kV ruas cross a divider: Koto Panjang - Payakumbuh and Kiliranjao -
Teluk Kuantan. Both endpoints carry both views, so each panel draws the ruas
whole (the SS_PLBRATU pattern) instead of an arrow to a GI it cannot show.

Slide 18 is vector, so the relations were traced from the PDF's geometry
(busbar = 2.6 pt stroke, conductor = 0.9 pt, hop = curve) and each panel then
checked by eye at 7-8x zoom. The pass-through reading is what the risk text
names: #19 "Aurduri-Muara Bulian & Aurduri-Muara Tebo", #22 "Aurduri-Muara
Sabak dan Aurduri-Payoselincah", #10/#11 "Ombilin-Salak ... Ombilin-Indarung"
all fall out of lines that run straight through a busbar.

Not drawn here, as in the Sumsel sheet (user, 2026-09-23): SUTET 500 kV
Perawang - Peranap - New Aurduri and SUTET 275 kV Perawang - Payakumbuh -
Kiliranjao - Sungai Rumbai - Muara Bungo - Bangko. GITET-to-GITET runs belong
to the backbone fixture; here each GITET is a source over the bus it feeds.
Peranap has no IBT on the sheet, so it lives in the backbone only.

Read off the sheet, noted for review:
  * The bus under the Perawang 500 kV IBT has no label; it is fed by that IBT
    and feeds Perawang 150 kV through IBT 1&2, so it is Perawang 275 kV.
  * The bus fed by PLTMG Sei Gelam has no label either; it is taken as GI Sei
    Gelam, the way PLTP Muara Labuh's bus carries the plant's name.
  * The label that extracts as "SAKTI GARUDA" is GI Garuda Sakti -- the two
    words are stacked on the slide; risks #4/#5 spell it "Garuda Sakti".
  * Merangin - Sungai Penuh: one red conductor and one black one. Risk #21
    says "operasi 1 sirkit", so the ruas is one circuit in service.

Boundary arrows are Bay stubs: Kota Pinang and New Padang Sidempuan 275 kV
(Sumbagut, codes as the Sumbagut sheet spells them), Muara Enim 500 kV and
Lubuk Linggau 275 kV (Sumsel), Argamakmur (Bengkulu), and a Konsumen TT arrow
off Indarung.

Run: python scripts/make_ss_sumbagteng_xlsx.py
"""
from __future__ import annotations

from _kerawanan_sumatera import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Sumbagteng"
RIAU, SUMBAR, JAMBI = ["RIAU"], ["SUMBAR"], ["JAMBI"]
RIAU_SUMBAR = ["RIAU", "SUMBAR"]

VIEWS = [
    ("RIAU", "Riau", "PRWNG_500;BLPGT;KTPJG;TLMBU;TNYAN;RIAU", 18),
    ("SUMBAR", "Sumatera Barat", "PYBUH_275;KLJAO_275;SRMBI_275;OMBLN;MNJAU;SKRAK;"
                                 "PLIMO;TSRIH;PMLBH", 18),
    ("JAMBI", "Jambi", "NAURD_500;MBUGO_275;BNGKO_275;MRNGN;PYSLC;SGLAM", 18),
]


def GI(code, name, tier, views, kv=150, **kw):
    return dict(code=code, name=name, type="Busbar GI", tier=tier, kv=kv,
                views=views, **kw)


def GITET(code, name, kv, views):
    return dict(code=code, name=name, type="Busbar GITET", tier=1, kv=f"{kv} kV",
                views=views)


def IBT(unit, hv, lv, name, kv, views, **kw):
    return dict(code=f"IBT {unit} {hv}", name=name, type="IBT 3-Winding", tier=2,
                kv=kv, ibt=str(unit), bus_hv=hv, bus_lv=lv, trafo=1, views=views, **kw)


def KIT(code, name, views):
    return dict(code=code, name=name, type="Pembangkit", tier=1, kv="150 kV",
                views=views)


ASSETS = [
    # ======================= RIAU =======================
    GITET("PRWNG_500", "GITET Perawang (500 kV)", 500, RIAU),
    IBT(1, "PRWNG_500", "PRWNG_275", "IBT Perawang 500/275 kV", "500/275 kV", RIAU),
    GITET("PRWNG_275", "GITET Perawang (275 kV)", 275, RIAU),
    IBT(1, "PRWNG_275", "PRWNG", "IBT 1 Perawang 275/150 kV", "275/150 kV", RIAU),
    IBT(2, "PRWNG_275", "PRWNG", "IBT 2 Perawang 275/150 kV", "275/150 kV", RIAU),
    GI("PRWNG", "Perawang (bus 150 kV)", 1, RIAU, trafo=1),
    KIT("KIT_BLPGT", "PLTMG/G Balai Pungut 1", RIAU),
    GI("BLPGT", "Balai Pungut", 1, RIAU, trafo=1, kerawanan="1"),
    KIT("KIT_KTPJG", "PLTA Koto Panjang", RIAU),
    GI("KTPJG", "Koto Panjang", 1, RIAU_SUMBAR, trafo=1),
    KIT("KIT_TLMBU", "PLTG/MG Teluk Lembu", RIAU),
    GI("TLMBU", "Teluk Lembu", 1, RIAU, trafo=1),
    KIT("KIT_TNYAN", "PLTU Tenayan", RIAU),
    GI("TNYAN", "Tenayan", 1, RIAU, trafo=1),
    KIT("KIT_RIAU", "PLTGU Riau", RIAU),
    GI("RIAU", "Riau", 1, RIAU),
    GI("DURI", "Duri", 2, RIAU, trafo=1),
    GI("BKNNG", "Bangkinang", 2, RIAU, trafo=1),
    GI("GRSKT", "Garuda Sakti", 2, RIAU, trafo=1),
    GI("NGRSK", "New Garuda Sakti", 2, RIAU, trafo=1),
    GI("PSPTH", "Pasir Putih", 2, RIAU, trafo=1),
    GI("TKTAN", "Teluk Kuantan", 2, RIAU_SUMBAR, trafo=1),
    GI("BGBTU", "Bagan Batu", 3, RIAU, trafo=1),
    GI("DUMAI", "Dumai", 3, RIAU, trafo=1),
    GI("PSPRN", "Pasir Pangaraian", 3, RIAU, trafo=1),
    GI("KPBRU", "Kota Pekanbaru", 3, RIAU, trafo=1),
    GI("SIAK", "Siak", 3, RIAU, trafo=1),
    GI("PKKRC", "Pangkalan Kerinci", 3, RIAU, trafo=1),
    GI("RNGAT", "Rengat", 3, RIAU, trafo=1),
    GI("KID", "KID", 4, RIAU, trafo=1),
    GI("BGSAP", "Bagan Siapi-api", 4, RIAU, trafo=1),
    GI("TBLHN", "Tembilahan", 4, RIAU, trafo=1),
    GI("PKNNG", "Pakning", 5, RIAU, trafo=1),
    GI("WINA", "Wina (GI Konsumen TT)", 5, RIAU, trafo=1, status="Milik Pelanggan"),
    # ======================= SUMATERA BARAT =======================
    GITET("PYBUH_275", "GITET Payakumbuh (275 kV)", 275, SUMBAR),
    IBT(1, "PYBUH_275", "PYBUH", "IBT 1 Payakumbuh 275/150 kV", "275/150 kV", SUMBAR),
    IBT(2, "PYBUH_275", "PYBUH", "IBT 2 Payakumbuh 275/150 kV", "275/150 kV", SUMBAR),
    GI("PYBUH", "Payakumbuh (bus 150 kV)", 1, RIAU_SUMBAR, trafo=1),
    GITET("KLJAO_275", "GITET Kiliranjao (275 kV)", 275, SUMBAR),
    IBT(1, "KLJAO_275", "KLJAO", "IBT 1 Kiliranjao 275/150 kV", "275/150 kV", SUMBAR),
    IBT(2, "KLJAO_275", "KLJAO", "IBT 2 Kiliranjao 275/150 kV", "275/150 kV", SUMBAR),
    GI("KLJAO", "Kiliranjao (bus 150 kV)", 1, RIAU_SUMBAR, trafo=1),
    GITET("SRMBI_275", "GITET Sungai Rumbai (275 kV)", 275, SUMBAR),
    IBT(1, "SRMBI_275", "SRMBI", "IBT Sungai Rumbai 275/150 kV", "275/150 kV", SUMBAR),
    GI("SRMBI", "Sungai Rumbai (bus 150 kV)", 1, SUMBAR, trafo=1),
    KIT("KIT_OMBLN", "PLTU Ombilin", SUMBAR),
    GI("OMBLN", "Ombilin", 1, SUMBAR),
    KIT("KIT_MNJAU", "PLTA Maninjau", SUMBAR),
    GI("MNJAU", "Maninjau", 1, SUMBAR, trafo=1),
    KIT("KIT_SKRAK", "PLTA Singkarak", SUMBAR),
    GI("SKRAK", "Singkarak", 1, SUMBAR),
    KIT("KIT_PLIMO", "PLTG Pauh Limo", SUMBAR),
    GI("PLIMO", "Pauh Limo", 1, SUMBAR, trafo=1),
    KIT("KIT_TSRIH", "PLTU/G Teluk Sirih", SUMBAR),
    GI("TSRIH", "Teluk Sirih", 1, SUMBAR),
    KIT("KIT_PMLBH", "PLTP Muara Labuh", SUMBAR),
    GI("PMLBH", "PLTP Muara Labuh", 1, SUMBAR),
    GI("PDLUR", "Padang Luar", 2, SUMBAR, trafo=1),
    GI("BTSKR", "Batu Sangkar", 2, SUMBAR, trafo=1),
    GI("SPEMP", "Simpang Empat", 2, SUMBAR, trafo=1),
    GI("PRMAN", "Pariaman", 2, SUMBAR, trafo=1),
    GI("LBALG", "Lubuk Alung", 2, SUMBAR, trafo=1),
    GI("PDPJG", "Padang Panjang", 2, SUMBAR, trafo=1),
    GI("PIP", "PIP", 2, SUMBAR, trafo=1),
    GI("SPHRU", "Simpang Haru", 2, SUMBAR, trafo=1),
    GI("INDRG", "Indarung", 2, SUMBAR),
    GI("KMBNG", "Kambang", 2, SUMBAR, trafo=1),
    GI("BNGUS", "Bungus", 2, SUMBAR, trafo=1),
    GI("SALAK", "Salak", 2, SUMBAR, trafo=1),
    GI("MLBUH", "Muara Labuh", 2, SUMBAR, trafo=1),
    GI("PSMAN", "Pasaman", 3, SUMBAR, trafo=1),
    GI("SOLOK", "Solok", 3, SUMBAR, trafo=1),
    GI("TAPAN", "Tapan", 3, SUMBAR, trafo=1),
    GI("MUKO", "Muko-Muko", 4, SUMBAR, trafo=1),
    # ======================= JAMBI =======================
    GITET("NAURD_500", "GITET New Aurduri (500 kV)", 500, JAMBI),
    IBT(1, "NAURD_500", "NAURD_275", "IBT New Aurduri 500/275 kV", "500/275 kV", JAMBI),
    GITET("NAURD_275", "GITET New Aurduri (275 kV)", 275, JAMBI),
    IBT(1, "NAURD_275", "NAURD", "IBT 1 New Aurduri 275/150 kV", "275/150 kV", JAMBI),
    IBT(2, "NAURD_275", "NAURD", "IBT 2 New Aurduri 275/150 kV", "275/150 kV", JAMBI),
    GI("NAURD", "New Aurduri (bus 150 kV)", 1, JAMBI, trafo=1),
    GITET("MBUGO_275", "GITET Muara Bungo (275 kV)", 275, JAMBI),
    IBT(1, "MBUGO_275", "MBUGO", "IBT 1 Muara Bungo 275/150 kV", "275/150 kV", JAMBI),
    IBT(2, "MBUGO_275", "MBUGO", "IBT 2 Muara Bungo 275/150 kV", "275/150 kV", JAMBI),
    GI("MBUGO", "Muara Bungo (bus 150 kV)", 1, JAMBI, trafo=1),
    GITET("BNGKO_275", "GITET Bangko (275 kV)", 275, JAMBI),
    IBT(1, "BNGKO_275", "BNGKO", "IBT 1 Bangko 275/150 kV", "275/150 kV", JAMBI),
    IBT(2, "BNGKO_275", "BNGKO", "IBT 2 Bangko 275/150 kV", "275/150 kV", JAMBI),
    GI("BNGKO", "Bangko (bus 150 kV)", 1, JAMBI, trafo=1),
    KIT("KIT_PYSLC", "PLTG Payo Selincah", JAMBI),
    GI("PYSLC", "Payo Selincah", 1, JAMBI, trafo=1),
    KIT("KIT_SGLAM", "PLTMG Sei Gelam", JAMBI),
    GI("SGLAM", "Sei Gelam", 1, JAMBI, trafo=1,
       simbol="bus tanpa label di bawah PLTMG Sei Gelam"),
    KIT("KIT_MRNGN", "PLTA Merangin", JAMBI),
    GI("MRNGN", "Merangin", 2, JAMBI, trafo=1),
    GI("MTEBO", "Muara Tebo", 2, JAMBI, trafo=1),
    GI("MSBAK", "Muara Sabak", 2, JAMBI, trafo=1),
    GI("AURDR", "Aur Duri", 2, JAMBI, trafo=1),
    GI("SPNUH", "Sungai Penuh", 3, JAMBI, trafo=1),
    GI("MBLAN", "Muara Bulian", 3, JAMBI, trafo=1),
    GI("KLTKL", "Kuala Tungkal", 3, JAMBI, trafo=1),
    GI("SRLGN", "Sarolangun", 4, JAMBI, trafo=1),
    GI("PLDGG", "Pelabuhan Dagang", 4, JAMBI, trafo=1),
]


def L(fr, to, nm, tf, tt, views, kno=None, sirkit=2, st="Beroperasi"):
    return dict(fr=fr, to=to, name=f"SUTT 150 kV {nm}", kv=150, tier_fr=tf,
                tier_to=tt, kerawanan=kno, sirkit=sirkit, status=st,
                koridor=WIL, views=views)


def OUT(kit, bus, name, views):
    return dict(fr=kit, to=bus, name=f"Outlet {name}", kv=150, tier_fr=1,
                tier_to=1, sirkit=1, koridor=WIL, views=views)


LINES = [
    # ======================= generator outlets =======================
    OUT("KIT_BLPGT", "BLPGT", "PLTMG/G Balai Pungut 1", RIAU),
    OUT("KIT_KTPJG", "KTPJG", "PLTA Koto Panjang", RIAU),
    OUT("KIT_TLMBU", "TLMBU", "PLTG/MG Teluk Lembu", RIAU),
    OUT("KIT_TNYAN", "TNYAN", "PLTU Tenayan", RIAU),
    OUT("KIT_RIAU", "RIAU", "PLTGU Riau", RIAU),
    OUT("KIT_OMBLN", "OMBLN", "PLTU Ombilin", SUMBAR),
    OUT("KIT_MNJAU", "MNJAU", "PLTA Maninjau", SUMBAR),
    OUT("KIT_SKRAK", "SKRAK", "PLTA Singkarak", SUMBAR),
    OUT("KIT_PLIMO", "PLIMO", "PLTG Pauh Limo", SUMBAR),
    OUT("KIT_TSRIH", "TSRIH", "PLTU/G Teluk Sirih", SUMBAR),
    OUT("KIT_PMLBH", "PMLBH", "PLTP Muara Labuh", SUMBAR),
    OUT("KIT_PYSLC", "PYSLC", "PLTG Payo Selincah", JAMBI),
    OUT("KIT_SGLAM", "SGLAM", "PLTMG Sei Gelam", JAMBI),
    OUT("KIT_MRNGN", "MRNGN", "PLTA Merangin", JAMBI),
    # ======================= RIAU =======================
    L("BLPGT", "DURI", "Balai Pungut - Duri", 1, 2, RIAU, kno="3"),
    L("BLPGT", "NGRSK", "Balai Pungut - New Garuda Sakti", 1, 2, RIAU, kno="3"),
    L("KTPJG", "BKNNG", "Koto Panjang - Bangkinang", 1, 2, RIAU, kno="4;5"),
    L("TLMBU", "GRSKT", "Teluk Lembu - Garuda Sakti", 1, 2, RIAU),
    L("TLMBU", "TNYAN", "Teluk Lembu - Tenayan", 1, 1, RIAU),
    L("TNYAN", "RIAU", "Tenayan - Riau", 1, 1, RIAU, kno="7"),
    L("TNYAN", "PRWNG", "Tenayan - Perawang", 1, 1, RIAU),
    L("RIAU", "PSPTH", "Riau - Pasir Putih", 1, 2, RIAU),
    L("PRWNG", "SIAK", "Perawang - Siak", 1, 3, RIAU, kno="6"),
    L("PRWNG", "NGRSK", "Perawang - New Garuda Sakti", 1, 2, RIAU),
    L("DURI", "BGBTU", "Duri - Bagan Batu", 2, 3, RIAU),
    L("DURI", "DUMAI", "Duri - Dumai", 2, 3, RIAU, kno="2"),
    L("BKNNG", "GRSKT", "Bangkinang - Garuda Sakti", 2, 2, RIAU, kno="4;5"),
    L("BKNNG", "PSPRN", "Bangkinang - Pasir Pangaraian", 2, 3, RIAU),
    L("GRSKT", "KPBRU", "Garuda Sakti - Kota Pekanbaru", 2, 3, RIAU),
    L("GRSKT", "PSPTH", "Garuda Sakti - Pasir Putih", 2, 2, RIAU),
    L("PSPTH", "PKKRC", "Pasir Putih - Pangkalan Kerinci", 2, 3, RIAU),
    L("PKKRC", "RNGAT", "Pangkalan Kerinci - Rengat", 3, 3, RIAU),
    L("TKTAN", "RNGAT", "Teluk Kuantan - Rengat", 2, 3, RIAU),
    L("RNGAT", "TBLHN", "Rengat - Tembilahan", 3, 4, RIAU),
    L("DUMAI", "KID", "Dumai - KID", 3, 4, RIAU),
    L("DUMAI", "BGSAP", "Dumai - Bagan Siapi-api", 3, 4, RIAU),
    L("KID", "PKNNG", "KID - Pakning", 4, 5, RIAU, sirkit=1),
    L("KID", "WINA", "KID - Wina", 4, 5, RIAU, sirkit=1),
    # ============ across the Riau | Sumbar divider ============
    L("KTPJG", "PYBUH", "Koto Panjang - Payakumbuh", 1, 1, RIAU_SUMBAR),
    L("KLJAO", "TKTAN", "Kiliranjao - Teluk Kuantan", 1, 2, RIAU_SUMBAR, kno="8;9"),
    # ======================= SUMATERA BARAT =======================
    L("PYBUH", "PDLUR", "Payakumbuh - Padang Luar", 1, 2, SUMBAR),
    L("PYBUH", "BTSKR", "Payakumbuh - Batu Sangkar", 1, 2, SUMBAR),
    L("OMBLN", "BTSKR", "Ombilin - Batu Sangkar", 1, 2, SUMBAR),
    L("OMBLN", "KLJAO", "Ombilin - Kiliranjao", 1, 1, SUMBAR),
    L("OMBLN", "SALAK", "Ombilin - Salak", 1, 2, SUMBAR, kno="10;11", sirkit=1),
    L("OMBLN", "INDRG", "Ombilin - Indarung", 1, 2, SUMBAR, kno="10;11", sirkit=1),
    L("SALAK", "SOLOK", "Salak - Solok", 2, 3, SUMBAR, sirkit=1),
    L("INDRG", "SOLOK", "Indarung - Solok", 2, 3, SUMBAR, sirkit=1),
    L("BTSKR", "PDPJG", "Batu Sangkar - Padang Panjang", 2, 2, SUMBAR, sirkit=1),
    L("SKRAK", "PDPJG", "Singkarak - Padang Panjang", 1, 2, SUMBAR, sirkit=1),
    L("SKRAK", "LBALG", "Singkarak - Lubuk Alung", 1, 2, SUMBAR, kno="12"),
    L("MNJAU", "SPEMP", "Maninjau - Simpang Empat", 1, 2, SUMBAR, kno="16"),
    L("SPEMP", "PSMAN", "Simpang Empat - Pasaman", 2, 3, SUMBAR),
    L("MNJAU", "PRMAN", "Maninjau - Pariaman", 1, 2, SUMBAR, sirkit=1),
    L("PRMAN", "LBALG", "Pariaman - Lubuk Alung", 2, 2, SUMBAR, sirkit=1),
    L("MNJAU", "LBALG", "Maninjau - Lubuk Alung", 1, 2, SUMBAR, sirkit=1),
    L("MNJAU", "PDLUR", "Maninjau - Padang Luar", 1, 2, SUMBAR),
    L("LBALG", "PIP", "Lubuk Alung - PIP", 2, 2, SUMBAR, sirkit=1),
    L("PLIMO", "LBALG", "Pauh Limo - Lubuk Alung", 1, 2, SUMBAR, sirkit=1),
    L("PLIMO", "PIP", "Pauh Limo - PIP", 1, 2, SUMBAR, sirkit=1),
    L("PLIMO", "SPHRU", "Pauh Limo - Simpang Haru", 1, 2, SUMBAR, kno="15"),
    L("PLIMO", "INDRG", "Pauh Limo - Indarung", 1, 2, SUMBAR, kno="13;14"),
    L("INDRG", "BNGUS", "Indarung - Bungus", 2, 2, SUMBAR, kno="17"),
    L("BNGUS", "TSRIH", "Bungus - Teluk Sirih", 2, 1, SUMBAR),
    L("TSRIH", "KMBNG", "Teluk Sirih - Kambang", 1, 2, SUMBAR),
    L("KMBNG", "TAPAN", "Kambang - Tapan", 2, 3, SUMBAR),
    L("TAPAN", "MUKO", "Tapan - Muko-Muko", 3, 4, SUMBAR),
    L("PMLBH", "MLBUH", "PLTP Muara Labuh - Muara Labuh", 1, 2, SUMBAR),
    L("SRMBI", "MLBUH", "Sungai Rumbai - Muara Labuh", 1, 2, SUMBAR),
    # ======================= JAMBI =======================
    L("MBUGO", "MTEBO", "Muara Bungo - Muara Tebo", 1, 2, JAMBI),
    L("MTEBO", "MBLAN", "Muara Tebo - Muara Bulian", 2, 3, JAMBI),
    L("MTEBO", "AURDR", "Muara Tebo - Aur Duri", 2, 2, JAMBI, kno="19", sirkit=1),
    L("MBLAN", "SRLGN", "Muara Bulian - Sarolangun", 3, 4, JAMBI),
    L("MBLAN", "AURDR", "Muara Bulian - Aur Duri", 3, 2, JAMBI, kno="19", sirkit=1),
    L("BNGKO", "MRNGN", "Bangko - Merangin", 1, 2, JAMBI, kno="20"),
    L("MRNGN", "SPNUH", "Merangin - Sungai Penuh (operasi 1 sirkit)", 2, 3, JAMBI,
      kno="21", sirkit=1),
    L("NAURD", "AURDR", "New Aurduri - Aur Duri", 1, 2, JAMBI, kno="18"),
    L("NAURD", "SGLAM", "New Aurduri - Sei Gelam", 1, 1, JAMBI),
    L("PYSLC", "MSBAK", "Payo Selincah - Muara Sabak", 1, 2, JAMBI, sirkit=1),
    L("PYSLC", "AURDR", "Payo Selincah - Aur Duri", 1, 2, JAMBI, kno="22", sirkit=1),
    L("MSBAK", "AURDR", "Muara Sabak - Aur Duri", 2, 2, JAMBI, kno="22", sirkit=1),
    L("MSBAK", "KLTKL", "Muara Sabak - Kuala Tungkal", 2, 3, JAMBI),
    L("KLTKL", "PLDGG", "Kuala Tungkal - Pelabuhan Dagang", 3, 4, JAMBI),
]

# Arrows to a neighbouring subsystem: (gi, name, feeder, kerawanan, sirkit,
# status, views, jenis, kv)
BAYS = [
    ("KTPNG", "Kota Pinang (Subsistem Sumbagut)", "BGBTU", None, 2, "Beroperasi", RIAU, "SUTT", "150 kV"),
    ("NPSDM_275", "New Padang Sidempuan (Subsistem Sumbagut, 275 kV)", "PYBUH_275", None, 2,
     "Beroperasi", SUMBAR, "SUTT", "275 kV"),
    ("ARMUR", "Argamakmur (Subsistem Bengkulu)", "MUKO", None, 2, "Beroperasi", SUMBAR, "SUTT", "150 kV"),
    ("KTT_INDRG", "Konsumen TT (dari Indarung)", "INDRG", None, 1, "Beroperasi", SUMBAR, "SUTT", "150 kV"),
    ("MENIM_500", "Muara Enim (Subsistem Sumsel, 500 kV)", "NAURD_500", None, 2,
     "Beroperasi", JAMBI, "SUTT", "500 kV"),
    ("LBGAU_275", "Lubuk Linggau (Subsistem Sumsel, 275 kV)", "BNGKO_275", None, 2,
     "Beroperasi", JAMBI, "SUTT", "275 kV"),
]

SPEC = dict(
    code="SS_SUMBAGTENG",
    name="Sumbagteng",
    apb="Sumbagteng",
    wilayah=WIL,
    multi_pin=True,
    source_ref="Kerawanan Sistem Sumatera Sep 2026 (UIP3B Sumatera), slide 18 "
               "Peta Kerawanan Sistem Sumbagteng (tiga panel); tabel risiko slide 20-23",
    views=VIEWS,
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts("SUMBAGTENG"),
)

if __name__ == "__main__":
    build_workbook(SPEC)
