"""samples/backbone_sumatera_ingest.xlsx -- Backbone 500/275 kV Sistem Sumatera.

Source: Kerawanan Sistem Sumatera, UIP3B Sumatera, Sep 2026 (the pptx deck).
Risks: the main body's 22-item list, slides 7-10 (the user chose the main body
over the 18-item backup list). Topology: the only backbone tier SLD, slide 33
(backup, ppt/media/image56.png), read as the subsystem sheets are -- a straight
line through a busbar is joined to it, which gives exactly the chains the risks
name (Lahat - Lubuk Linggau - Bangko - Muara Bungo - Sungai Rumbai - Kiliranjao,
Perawang - Payakumbuh - NP Sidempuan - Sarulla - Simangkok - Galang - Binjai -
Pangkalan Susu). Its pin numbers follow the backup list, so each pin here is
remapped to the 22 numbering by its text.

System scope, like SS Jamali's backbone_500_ingest.xlsx: GITETs, their plants
and the SUTET between them -- the GITET-to-GITET runs the SS sheets leave out.
The 150 kV side stays on the SS sheets, so a risk about an IBT 275/150 is pinned
on its GITET. Codes are the SS sheets' own (MENIM_500, BNGKO_275, PSUSU_275,
SMUT4_275 ...), so each physical GITET is one node across all sheets.

Read off the sheets, noted for review:
  * SUTET 500 kV Muara Enim - New Aurduri is on slide 18 (Sumbagteng: "KE SBS
    MUARA ENIM", two arrows) but not on the backup backbone SLD; the main-body
    slide wins, so it is here.
  * Lampung 1 is a 275 kV GITET on this sheet (Gumawang - Lampung 1), while
    the Lampung SS sheet draws only its 150 kV bus -- the user chose to follow
    that SLD there. Here it is LPUG1_275.
  * Peranap has a 500/275 kV IBT onto a short 275 kV bar with nothing else on
    it; drawn as the sheet has it.
  * GITET Arun is not on the backbone SLD; it is added unconnected (with its
    plant) because risk #15 is about it.
  * Risk #21 lists coal plants in SBUT; only PLTU Pangkalan Susu sits on the
    backbone, Ombilin and Teluk Sirih are on the Sumbagteng sheet.

Run: python scripts/make_backbone_sumatera_xlsx.py
"""
from __future__ import annotations

from _kerawanan_sumatera import as_risk_dicts
from _ss_xlsx_common import build_workbook

V = ["BACKBONE"]


def GITET(code, name, kv, tier=1, **kw):
    return dict(code=code, name=name, type="Busbar GITET", tier=tier, kv=f"{kv} kV",
                views=V, **kw)


def IBT(hv, lv, name, **kw):
    return dict(code=f"IBT 1 {hv}", name=name, type="IBT 3-Winding", tier=2,
                kv="500/275 kV", ibt="1", bus_hv=hv, bus_lv=lv, trafo=1, views=V, **kw)


def KIT(code, name, kv):
    return dict(code=code, name=name, type="Pembangkit", tier=1, kv=f"{kv} kV", views=V)


ASSETS = [
    # ======================= 500 kV =======================
    KIT("KIT_SMSL8", "PLTU Sumsel 8", 500),
    GITET("SMSL8", "PLTU Sumsel 8 (500 kV)", 500, kerawanan="5"),
    GITET("MENIM_500", "GITET Muara Enim (500 kV)", 500),
    IBT("MENIM_500", "MENIM_275", "IBT Muara Enim 500/275 kV", kerawanan="6"),
    GITET("NAURD_500", "GITET New Aurduri (500 kV)", 500),
    IBT("NAURD_500", "NAURD_275", "IBT New Aurduri 500/275 kV", kerawanan="1"),
    GITET("PRNAP_500", "GITET Peranap (500 kV)", 500),
    IBT("PRNAP_500", "PRNAP_275", "IBT Peranap 500/275 kV"),
    GITET("PRWNG_500", "GITET Perawang (500 kV)", 500),
    IBT("PRWNG_500", "PRWNG_275", "IBT Perawang 500/275 kV", kerawanan="1"),
    # ======================= 275 kV, Sumbagsel =======================
    GITET("MENIM_275", "GITET Muara Enim (275 kV)", 275),
    GITET("GMWNG_275", "GITET Gumawang (275 kV)", 275, tier=2),
    GITET("LPUG1_275", "GITET Lampung 1 (275 kV)", 275, tier=3,
          simbol="SS Lampung menggambar bus 150 kV saja; lembar backbone menggambar GITET 275 kV"),
    GITET("LMBAI_275", "GITET Lumut Balai (275 kV)", 275),
    GITET("LAHAT_275", "GITET Lahat (275 kV)", 275),
    GITET("LBGAU_275", "GITET Lubuk Linggau (275 kV)", 275, kerawanan="19"),
    KIT("KIT_SMSL5", "PLTU Sumsel 5", 275),
    GITET("SMSL5", "PLTU Sumsel 5 (275 kV)", 275),
    GITET("SGLIN_275", "GITET Sungai Lilin (275 kV)", 275, tier=2),
    GITET("BTUNG_275", "GITET Betung (275 kV)", 275, tier=2),
    KIT("KIT_SMSL1", "PLTU Sumsel 1", 275),
    GITET("SMSL1", "PLTU Sumsel 1 (275 kV)", 275),
    # ======================= 275 kV, Sumbagteng =======================
    GITET("BNGKO_275", "GITET Bangko (275 kV)", 275, kerawanan="10"),
    GITET("MBUGO_275", "GITET Muara Bungo (275 kV)", 275, tier=2),
    GITET("SRMBI_275", "GITET Sungai Rumbai (275 kV)", 275, kerawanan="11"),
    GITET("KLJAO_275", "GITET Kiliranjao (275 kV)", 275, tier=2),
    GITET("PYBUH_275", "GITET Payakumbuh (275 kV)", 275, tier=3),
    GITET("PRWNG_275", "GITET Perawang (275 kV)", 275, kerawanan="12"),
    GITET("PRNAP_275", "GITET Peranap (275 kV)", 275),
    GITET("NAURD_275", "GITET New Aurduri (275 kV)", 275, kerawanan="3"),
    # ======================= 275 kV, Sumbagut =======================
    GITET("NPSDM_275", "GITET New Padang Sidempuan (275 kV)", 275, tier=2),
    GITET("SMUT4_275", "GITET Sarulla (275 kV, label SMUT4)", 275),
    GITET("SMKOK_275", "GITET Simangkuk (275 kV)", 275, tier=2),
    KIT("KIT_ASAHN", "PLTA Asahan", 275),
    GITET("ASAHN_275", "PLTA Asahan (275 kV)", 275),
    GITET("GLANG_275", "GITET Galang (275 kV)", 275, tier=3),
    GITET("BNJAI_275", "GITET Binjai (275 kV)", 275, tier=2),
    KIT("KIT_PSUSU", "PLTU Pangkalan Susu", 275),
    GITET("PSUSU_275", "PLTU Pangkalan Susu (275 kV)", 275, kerawanan="14;21"),
    KIT("KIT_NAGAN_275", "PLTU Nagan Raya (275 kV)", 275),
    GITET("NAGAN_275", "GITET Nagan Raya (275 kV)", 275, kerawanan="16;18"),
    GITET("SIGLI_275", "GITET Sigli (275 kV)", 275, tier=2, kerawanan="16"),
    GITET("ULKRG_275", "GITET Ulee Kareng (275 kV)", 275, tier=2, kerawanan="16"),
    KIT("KIT_ARUN_275", "PLTMG Arun", 275),
    GITET("ARUN_275", "GITET Arun (275 kV)", 275, kerawanan="15",
          simbol="tidak digambar di SLD backbone; ditambahkan untuk risiko #15"),
]


def S(fr, to, nm, tf, tt, kv=275, kno=None, sirkit=2):
    return dict(fr=fr, to=to, name=f"SUTET {kv} kV {nm}", kv=kv, tier_fr=tf, tier_to=tt,
                kerawanan=kno, sirkit=sirkit, koridor="Sumatera", views=V)


def OUT(kit, bus, name, kv):
    return dict(fr=kit, to=bus, name=f"Outlet {name}", kv=kv, tier_fr=1, tier_to=1,
                sirkit=1, koridor="Sumatera", views=V)


LINES = [
    OUT("KIT_SMSL8", "SMSL8", "PLTU Sumsel 8", 500),
    OUT("KIT_SMSL5", "SMSL5", "PLTU Sumsel 5", 275),
    OUT("KIT_SMSL1", "SMSL1", "PLTU Sumsel 1", 275),
    OUT("KIT_ASAHN", "ASAHN_275", "PLTA Asahan", 275),
    OUT("KIT_PSUSU", "PSUSU_275", "PLTU Pangkalan Susu", 275),
    OUT("KIT_NAGAN_275", "NAGAN_275", "PLTU Nagan Raya", 275),
    OUT("KIT_ARUN_275", "ARUN_275", "PLTMG Arun", 275),
    # ======================= 500 kV =======================
    S("SMSL8", "MENIM_500", "Sumsel 8 - Muara Enim", 1, 1, kv=500, kno="5"),
    S("MENIM_500", "NAURD_500", "Muara Enim - New Aurduri", 1, 1, kv=500),
    S("NAURD_500", "PRNAP_500", "New Aurduri - Peranap", 1, 1, kv=500, kno="2"),
    S("PRNAP_500", "PRWNG_500", "Peranap - Perawang", 1, 1, kv=500, kno="2"),
    # ======================= 275 kV Sumbagsel =======================
    S("MENIM_275", "GMWNG_275", "Muara Enim - Gumawang", 1, 2),
    S("GMWNG_275", "LPUG1_275", "Gumawang - Lampung 1", 2, 3),
    S("MENIM_275", "LMBAI_275", "Muara Enim - Lumut Balai", 1, 1, kno="9"),
    S("LMBAI_275", "LAHAT_275", "Lumut Balai - Lahat", 1, 1, kno="9"),
    S("LAHAT_275", "LBGAU_275", "Lahat - Lubuk Linggau", 1, 1, kno="7;8"),
    S("NAURD_275", "SMSL5", "New Aurduri - Sumsel 5", 1, 1, kno="4"),
    S("SMSL5", "SGLIN_275", "Sumsel 5 - Sungai Lilin", 1, 2, kno="4"),
    S("SGLIN_275", "BTUNG_275", "Sungai Lilin - Betung", 2, 2, kno="4"),
    S("SMSL1", "BTUNG_275", "Sumsel 1 - Betung", 1, 2),
    # ======================= 275 kV Sumbagteng =======================
    S("LBGAU_275", "BNGKO_275", "Lubuk Linggau - Bangko", 1, 1, kno="7;8"),
    S("BNGKO_275", "MBUGO_275", "Bangko - Muara Bungo", 1, 2, kno="7;8"),
    S("MBUGO_275", "SRMBI_275", "Muara Bungo - Sungai Rumbai", 2, 1, kno="7;8"),
    S("SRMBI_275", "KLJAO_275", "Sungai Rumbai - Kiliranjao", 1, 2, kno="7;8"),
    S("KLJAO_275", "PYBUH_275", "Kiliranjao - Payakumbuh", 2, 3, kno="22"),
    S("PRWNG_275", "PYBUH_275", "Perawang - Payakumbuh", 1, 3),
    # ======================= 275 kV Sumbagut =======================
    S("PYBUH_275", "NPSDM_275", "Payakumbuh - New Padang Sidempuan", 3, 2, kno="13"),
    S("NPSDM_275", "SMUT4_275", "New Padang Sidempuan - Sarulla", 2, 1),
    S("SMUT4_275", "SMKOK_275", "Sarulla - Simangkuk", 1, 2),
    S("ASAHN_275", "SMKOK_275", "Asahan - Simangkuk", 1, 2),
    S("SMKOK_275", "GLANG_275", "Simangkuk - Galang", 2, 3, kno="20"),
    S("GLANG_275", "BNJAI_275", "Galang - Binjai", 3, 2),
    S("BNJAI_275", "PSUSU_275", "Binjai - Pangkalan Susu", 2, 1, kno="14"),
    S("NAGAN_275", "SIGLI_275", "Nagan Raya - Sigli", 1, 2, kno="17"),
    S("SIGLI_275", "ULKRG_275", "Sigli - Ulee Kareng", 2, 2),
]

SPEC = dict(
    code="BACKBONE_SUMATERA",
    name="Backbone 500/275 kV Sumatera",
    apb="UIP3B Sumatera",
    wilayah="Sumatera",
    rule_profile="BACKBONE_SUMATERA",
    multi_pin=True,
    source_ref="Kerawanan Sistem Sumatera Sep 2026 (UIP3B Sumatera), tabel risiko slide 7-10 "
               "(22 butir); topologi dari SLD backbone slide 33 (backup) + slide 18",
    views=[("BACKBONE", "Backbone 500/275 kV Sumatera",
            "SMSL8;MENIM_500;NAURD_500;PRWNG_500;SMSL5;SMSL1;ASAHN_275;PSUSU_275;NAGAN_275;ARUN_275",
            33)],
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts("BACKBONE"),
)

if __name__ == "__main__":
    build_workbook(SPEC)
