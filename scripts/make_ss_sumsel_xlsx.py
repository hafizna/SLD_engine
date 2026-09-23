"""samples/ss_sumsel_ingest.xlsx -- Subsistem Sumsel (Sumbagsel).

Source: Kerawanan Sistem Sumatera, UIP3B Sumatera, Sep 2026 (the pptx deck),
slide 11 "Peta Kerawanan Sistem Sumsel" (tier SLD, ppt/media/image49.png) and
the risk table on slide 12. Conventions as in make_ss_bengkulu_xlsx.py:
275 kV light blue, 150 kV red, 70 kV yellow; bare code = 150 kV, `_275` /
`_70` on the other bus of a two-voltage site; `multi_pin` = every kerawanan
number marks where the finding sits, never the GIs it knocks out.

**Reading the tier SLD.** Crossings are drawn with hop arcs throughout, so a
straight line running through a busbar with no hop is joined to it: the
vertical from PLTG Borang runs BRANG -> KNTEN -> TJAPI -> Muntok, the one from
PLTU Bukit Asam BKSAM -> BTRJA -> MPURA -> MRDUA. Every tier this reading
produces matches the tier band the sheet draws the bus in, and the risk text
names the same chains (#1, #4, #5, #7).

Cross-checked against the vector load-flow map on slide 2, which filled three
gaps the tier SLD leaves:
  * PLTU Simpang Belimbing is drawn unconnected on the SLD; the map ties it to
    GI Pendopo with two circuits.
  * SUTT 70 kV Bungaran - Sungai Kedukan (risk #2, "tidak beroperasi") is not
    on the SLD; the map draws it dashed. Modelled out of service.
  * GI Bintuhan (risk #4) is not on the SLD, and the map draws Manna-Bintuhan
    as planned (dashed, hollow dot) while the risk's Dampak has "GI Bintuhan
    hilang tegangan". The user chose (2026-09-23): in service, ONE circuit.
Circuit counts follow the map where it draws a single or half-dashed line
(Gandus-Kota Barat, Kota Barat-Kota Timur, Sungai Juaro-Sungai Kedukan
"beroperasi 1 line"); elsewhere the map draws two and the default 2 stands.
Kota Timur - Kenten is solid on the SLD but dashed on the map; the SLD wins.

Neighbour arrows are Bay stubs: Muntok (Bangka), Blambangan Umpu / Pakuan Ratu
/ Mesuji (Lampung), Pekalongan (Bengkulu), and at 275 kV Sumsel 5 and Bangko
(Jambi). Lubuk Linggau is this subsystem's own GI; the Bengkulu sheet carries
it as its boundary.

Run: python scripts/make_ss_sumsel_xlsx.py
"""
from __future__ import annotations

from _kerawanan_sumatera import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Sumatera Selatan"


def GI(code, name, tier, kv=150, **kw):
    return dict(code=code, name=name, type="Busbar GI", tier=tier, kv=kv, **kw)


def GITET(code, name):
    return dict(code=code, name=name, type="Busbar GITET", tier=1, kv="275 kV")


def IBT(hv, lv, name, kv="275/150 kV", tier=2, **kw):
    return dict(code=f"IBT 1 {hv}", name=name, type="IBT 3-Winding", tier=tier, kv=kv,
                ibt="1", bus_hv=hv, bus_lv=lv, trafo=1, **kw)


def KIT(code, name, kv=150):
    return dict(code=code, name=name, type="Pembangkit", tier=1, kv=f"{kv} kV")


ASSETS = [
    # ================= 275 kV GITET + IBT 275/150 (one symbol each) =========
    GITET("SGLIN_275", "GITET Sungai Lilin (275 kV)"),
    IBT("SGLIN_275", "SGLIN", "IBT Sungai Lilin 275/150 kV"),
    GITET("BTUNG_275", "GITET Betung (275 kV)"),
    IBT("BTUNG_275", "BTUNG", "IBT Betung 275/150 kV"),
    GITET("LMBAI_275", "GITET Lumut Balai (275 kV)"),
    IBT("LMBAI_275", "LMBAI", "IBT Lumut Balai 275/150 kV"),
    GITET("LAHAT_275", "GITET Lahat (275 kV)"),
    IBT("LAHAT_275", "LAHAT", "IBT Lahat 275/150 kV"),
    GITET("LBGAU_275", "GITET Lubuk Linggau (275 kV)"),
    IBT("LBGAU_275", "LBGAU", "IBT Lubuk Linggau 275/150 kV"),
    # ================= Tier-1, 150 kV =================
    GI("SGLIN", "Sungai Lilin (bus 150 kV)", 1, trafo=1),
    GI("BTUNG", "Betung (bus 150 kV)", 1, trafo=1),
    KIT("KIT_TLDKU", "PLTG Talang Duku"),
    GI("KRSAN", "Keramasan (bus 150 kV)", 1, trafo=1),
    KIT("KIT_KSRAN", "PLTGU Keramasan"),
    GI("BRANG", "Borang (bus 150 kV)", 1, trafo=1),
    KIT("KIT_BRANG", "PLTG Borang (150 kV)"),
    GI("AGPBRANG", "AGP Borang", 1, kerawanan="6"),
    KIT("KIT_AGPBRANG", "PLTGU AGP Borang"),
    GI("SPTGA", "Simpang Tiga", 1, trafo=1),
    KIT("KIT_IDLYA", "PLTGU Indralaya"),
    GI("GUMEG", "Gunung Megang", 1, trafo=1),
    KIT("KIT_GUMEG", "PLTGU Gunung Megang"),
    GI("BKSAM", "Bukit Asam", 1, trafo=1),
    KIT("KIT_BKSAM", "PLTU Bukit Asam"),
    GI("SBSL1", "PLTU Sumbagsel-1", 1, kerawanan="6"),
    KIT("KIT_SBSL1", "PLTU Sumbagsel-1"),
    GI("RTDAP", "Rantau Dedap", 1),
    KIT("KIT_RTDAP", "PLTP Rantau Dedap"),
    GI("TPLBI", "PLTP Lumut Balai", 1),
    KIT("KIT_TPLBI", "PLTP Lumut Balai"),
    GI("LMBAI", "Lumut Balai (bus 150 kV)", 1, trafo=1),
    GI("LAHAT", "Lahat (bus 150 kV)", 1, trafo=1),
    GI("SBING", "PLTU Simpang Belimbing", 1, kerawanan="6",
       simbol="SLD tier tidak menggambar penghantarnya; peta slide 2: 2 sirkit ke Pendopo"),
    KIT("KIT_SBING", "PLTU Simpang Belimbing"),
    GI("BSARI", "PLTU Banjarsari", 1, kerawanan="6"),
    KIT("KIT_BSARI", "PLTU Banjarsari"),
    GI("KBANG", "PLTU Keban Agung", 1, kerawanan="6"),
    KIT("KIT_KBANG", "PLTU Keban Agung"),
    GI("LBGAU", "Lubuk Linggau (bus 150 kV)", 1, trafo=1),
    # ================= Tier-2..4, 150 kV =================
    GI("SKAYU", "Sekayu", 2, trafo=1),
    GI("TLKLP", "Talang Kelapa", 2, trafo=1, kapasitor=1),
    GI("GNDUS", "Gandus", 2, trafo=1),
    GI("NJBRG", "New Jakabaring", 2, trafo=1),
    GI("KNTEN", "Kenten", 2, trafo=1),
    GI("MRINA", "Mariana", 2, trafo=1),
    GI("PBLIH", "Prabumulih", 2, trafo=1),
    GI("PNDPO", "Pendopo", 2, trafo=1),
    GI("BTRJA", "Baturaja", 2, trafo=1, kapasitor=1),
    GI("PGLAM", "Pagar Alam", 2, trafo=1),
    GI("EPLWG", "Empat Lawang", 2, trafo=1),
    GI("KOBAR", "Kota Barat", 3, trafo=1),
    GI("KOTIM", "Kota Timur", 3, trafo=1),
    GI("TJAPI", "Tanjung Api-Api", 3, trafo=1),
    GI("KYANG", "Kayu Agung", 3, trafo=1),
    GI("SMBTRJA", "Semen Baturaja", 3),
    GI("MPURA", "Martapura", 3, trafo=1),
    GI("MANNA", "Manna", 3, trafo=1),
    GI("GMWNG", "Gumawang (bus 150 kV)", 4, trafo=1, kapasitor=1),
    GI("MRDUA", "Muara Dua", 4, trafo=1),
    GI("BNTHN", "Bintuhan", 4,
       simbol="tidak di SLD tier; peta slide 2: rencana; teks risiko #4: beroperasi -- "
              "dimodelkan beroperasi 1 sirkit atas keputusan user, perlu konfirmasi P2B"),
    # ================= 70 kV Palembang =================
    IBT("KRSAN", "KRSAN_70", "IBT Keramasan 150/70 kV", kv="150/70 kV", tier=1),
    GI("KRSAN_70", "Keramasan (bus 70 kV)", 1, kv=70, trafo=1),
    KIT("KIT_KSRAN_70", "PLTG Keramasan", kv=70),
    GI("SJARO", "Sungai Juaro", 1, kv=70, trafo=1),
    KIT("KIT_SJARO", "PLTD Sungai Juaro", kv=70),
    IBT("BRANG", "BRANG_70", "IBT Borang 150/70 kV", kv="150/70 kV", tier=1),
    GI("BRANG_70", "Borang (bus 70 kV)", 1, kv=70),
    KIT("KIT_BRANG_70", "PLTG Borang (70 kV)", kv=70),
    GI("BGRAN", "Bungaran", 2, kv=70, trafo=1),
    GI("SKDKN", "Sungai Kedukan", 2, kv=70, trafo=1),
    GI("BKSGT", "Bukit Siguntang", 2, kv=70, trafo=1),
    GI("SDPTH", "Seduduk Putih", 2, kv=70, trafo=1),
    GI("TRATU", "Talang Ratu", 3, kv=70, trafo=1),
    GI("BMBRU", "Boom Baru", 3, kv=70, trafo=1),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, sirkit=2, st="Beroperasi": dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    sirkit=sirkit, status=st, koridor=WIL)


def OUT(kit, bus, name, kv=150):
    return L(kit, bus, f"Outlet {name}", 1, 1, kv=kv, sirkit=1)


LINES = [
    OUT("KIT_TLDKU", "BTUNG", "PLTG Talang Duku"),
    OUT("KIT_KSRAN", "KRSAN", "PLTGU Keramasan"),
    OUT("KIT_BRANG", "BRANG", "PLTG Borang"),
    OUT("KIT_AGPBRANG", "AGPBRANG", "PLTGU AGP Borang"),
    OUT("KIT_IDLYA", "SPTGA", "PLTGU Indralaya"),
    OUT("KIT_GUMEG", "GUMEG", "PLTGU Gunung Megang"),
    OUT("KIT_BKSAM", "BKSAM", "PLTU Bukit Asam"),
    OUT("KIT_SBSL1", "SBSL1", "PLTU Sumbagsel-1"),
    OUT("KIT_RTDAP", "RTDAP", "PLTP Rantau Dedap"),
    OUT("KIT_TPLBI", "TPLBI", "PLTP Lumut Balai"),
    OUT("KIT_SBING", "SBING", "PLTU Simpang Belimbing"),
    OUT("KIT_BSARI", "BSARI", "PLTU Banjarsari"),
    OUT("KIT_KBANG", "KBANG", "PLTU Keban Agung"),
    OUT("KIT_KSRAN_70", "KRSAN_70", "PLTG Keramasan", kv=70),
    OUT("KIT_SJARO", "SJARO", "PLTD Sungai Juaro", kv=70),
    OUT("KIT_BRANG_70", "BRANG_70", "PLTG Borang", kv=70),
    # 275 kV GITET-to-GITET SUTET (Sungai Lilin-Betung, Lumut Balai-Lahat,
    # Lahat-Lubuk Linggau) is drawn on slide 11 but NOT here: as for SUTET
    # 500 kV in the Jamali sheets, those lines belong to the backbone fixture
    # (user, 2026-09-23). A subsystem view floats each GITET over the bus it
    # feeds, in the generator band, where a GITET-to-GITET run has no channel.
    # ================= Palembang 150 kV =================
    L("BTUNG", "SKAYU", "SUTT 150 kV Betung - Sekayu", 1, 2),
    L("BTUNG", "TLKLP", "SUTT 150 kV Betung - Talang Kelapa", 1, 2),
    L("TLKLP", "GNDUS", "SUTT 150 kV Talang Kelapa - Gandus", 2, 2),
    L("TLKLP", "KNTEN", "SUTT 150 kV Talang Kelapa - Kenten", 2, 2),
    L("KRSAN", "GNDUS", "SUTT 150 kV Keramasan - Gandus", 1, 2),
    L("GNDUS", "KOBAR", "SUTT 150 kV Gandus - Kota Barat", 2, 3, sirkit=1),
    L("KOBAR", "KOTIM", "SUTT 150 kV Kota Barat - Kota Timur", 3, 3, sirkit=1),
    L("KOTIM", "KNTEN", "SUTT 150 kV Kota Timur - Kenten", 3, 2, sirkit=1),
    L("KRSAN", "NJBRG", "SUTT 150 kV Keramasan - New Jakabaring", 1, 2),
    L("NJBRG", "MRINA", "SUTT 150 kV New Jakabaring - Mariana", 2, 2),
    L("BRANG", "KNTEN", "SUTT 150 kV Borang - Kenten", 1, 2),
    L("KNTEN", "TJAPI", "SUTT 150 kV Kenten - Tanjung Api-Api", 2, 3, kno="3"),
    L("BRANG", "AGPBRANG", "SUTT 150 kV Borang - AGP Borang", 1, 1),
    L("BRANG", "MRINA", "SUTT 150 kV Borang - Mariana", 1, 2),
    L("MRINA", "KYANG", "SUTT 150 kV Mariana - Kayu Agung", 2, 3, kno="7"),
    L("KYANG", "GMWNG", "SUTT 150 kV Kayu Agung - Gumawang", 3, 4, kno="7"),
    # ================= Keramasan - Pendopo - Lahat corridor =================
    L("KRSAN", "SPTGA", "SUTT 150 kV Keramasan - Simpang Tiga", 1, 1, kno="1"),
    L("SPTGA", "PBLIH", "SUTT 150 kV Simpang Tiga - Prabumulih", 1, 2, kno="1"),
    L("PBLIH", "PNDPO", "SUTT 150 kV Prabumulih - Pendopo", 2, 2, kno="1"),
    L("GUMEG", "PNDPO", "SUTT 150 kV Gunung Megang - Pendopo", 1, 2),
    L("SBING", "PNDPO", "SUTT 150 kV PLTU Simpang Belimbing - Pendopo", 1, 2),
    L("PNDPO", "LAHAT", "SUTT 150 kV Pendopo - Lahat", 2, 1),
    L("GUMEG", "BKSAM", "SUTT 150 kV Gunung Megang - Bukit Asam", 1, 1),
    L("BKSAM", "LAHAT", "SUTT 150 kV Bukit Asam - Lahat", 1, 1),
    # ================= Baturaja - Martapura (arah Lampung) =================
    L("BKSAM", "BTRJA", "SUTT 150 kV Bukit Asam - Baturaja", 1, 2),
    L("SBSL1", "BTRJA", "SUTT 150 kV PLTU Sumbagsel-1 - Baturaja", 1, 2),
    L("BTRJA", "SMBTRJA", "SUTT 150 kV Baturaja - Semen Baturaja", 2, 3),
    L("BTRJA", "MPURA", "SUTT 150 kV Baturaja - Martapura", 2, 3),
    L("MPURA", "MRDUA", "SUTT 150 kV Martapura - Muara Dua", 3, 4, kno="5"),
    # ================= Lahat side =================
    L("LAHAT", "PGLAM", "SUTT 150 kV Lahat - Pagar Alam", 1, 2, kno="4"),
    L("PGLAM", "MANNA", "SUTT 150 kV Pagar Alam - Manna", 2, 3, kno="4"),
    L("MANNA", "BNTHN", "SUTT 150 kV Manna - Bintuhan", 3, 4, kno="4", sirkit=1),
    L("LAHAT", "KBANG", "SUTT 150 kV Lahat - PLTU Keban Agung", 1, 1),
    L("LAHAT", "BSARI", "SUTT 150 kV Lahat - PLTU Banjarsari", 1, 1),
    L("RTDAP", "LMBAI", "SUTT 150 kV Rantau Dedap - Lumut Balai", 1, 1),
    L("LMBAI", "TPLBI", "SUTT 150 kV Lumut Balai - PLTP Lumut Balai", 1, 1),
    L("LBGAU", "EPLWG", "SUTT 150 kV Lubuk Linggau - Empat Lawang", 1, 2),
    # ================= 70 kV Palembang =================
    L("KRSAN_70", "BGRAN", "SUTT 70 kV Keramasan - Bungaran", 1, 2, kv=70),
    L("KRSAN_70", "BKSGT", "SUTT 70 kV Keramasan - Bukit Siguntang", 1, 2, kv=70),
    L("BKSGT", "TRATU", "SUTT 70 kV Bukit Siguntang - Talang Ratu", 2, 3, kv=70),
    L("BRANG_70", "SJARO", "SUTT 70 kV Borang - Sungai Juaro", 1, 1, kv=70, kno="2"),
    L("SJARO", "SKDKN", "SUTT 70 kV Sungai Juaro - Sungai Kedukan (operasi 1 line)", 1, 2,
      kv=70, kno="2", sirkit=1),
    L("BGRAN", "SKDKN", "SUTT 70 kV Bungaran - Sungai Kedukan (tidak beroperasi)", 2, 2,
      kv=70, kno="2", st="Padam"),
    L("BRANG_70", "SDPTH", "SUTT 70 kV Borang - Seduduk Putih", 1, 2, kv=70),
    L("SDPTH", "BMBRU", "SUTT 70 kV Seduduk Putih - Boom Baru", 2, 3, kv=70),
    L("SDPTH", "TRATU", "SUTT 70 kV Seduduk Putih - Talang Ratu", 2, 3, kv=70),
]

# Arrows to a neighbouring subsystem: (gi, name, feeder, kerawanan, sirkit,
# status, views, jenis, kv)
BAYS = [
    ("MNTOK", "Muntok (Subsistem Bangka)", "TJAPI", "3", 2, "Beroperasi", None, "SUTT", "150 kV"),
    ("BLMPU", "Blambangan Umpu (Subsistem Lampung)", "MPURA", None, 2, "Beroperasi", None, "SUTT", "150 kV"),
    ("PRATU", "Pakuan Ratu (Subsistem Lampung)", "GMWNG", None, 2, "Beroperasi", None, "SUTT", "150 kV"),
    ("MSUJI", "Mesuji (Subsistem Lampung)", "GMWNG", None, 2, "Beroperasi", None, "SUTT", "150 kV"),
    ("PKLNG", "Pekalongan (Subsistem Bengkulu)", "LBGAU", None, 2, "Beroperasi", None, "SUTT", "150 kV"),
    ("SMSL5", "PLTU Sumsel 5 (275 kV)", "SGLIN_275", None, 2, "Beroperasi", None, "SUTT", "275 kV"),
    ("BNGKO_275", "Bangko (Subsistem Jambi, 275 kV)", "LBGAU_275", None, 2, "Beroperasi", None, "SUTT", "275 kV"),
]

SPEC = dict(
    code="SS_SUMSEL",
    name="Sumsel",
    apb="Sumbagsel",
    wilayah=WIL,
    multi_pin=True,
    source_ref="Kerawanan Sistem Sumatera Sep 2026 (UIP3B Sumatera), slide 11 "
               "Peta Kerawanan Sistem Sumsel; tabel risiko slide 12; peta load flow slide 2",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts("SUMSEL"),
)

if __name__ == "__main__":
    build_workbook(SPEC)
