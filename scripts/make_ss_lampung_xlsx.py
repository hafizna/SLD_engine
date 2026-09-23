"""samples/ss_lampung_ingest.xlsx -- Subsistem Lampung (Sumbagsel).

Source: Kerawanan Sistem Sumatera, UIP3B Sumatera, Sep 2026 (the pptx deck),
slide 13 "Peta Kerawanan Sistem Lampung" (tier SLD, ppt/media/image50.png) and
the risk table on slides 14-15. Conventions as in make_ss_bengkulu_xlsx.py;
the SLD is read as make_ss_sumsel_xlsx.py describes (crossings carry hop
arcs, so a straight line through a busbar is joined to it).

    GITET Gumawang 275 kV -> IBT -> GMWNG (Tier-1), SUTET arrow to Muara Enim
    Tier-1 generation: PLTA Besai, PLTP Ulubelu 1&2 / 3&4, PLTA Batutegi,
    PLTA Semangka, PLTG Tarahan, PLTU + PLTG New Tarahan, PLTU Sebalang

Two things the drawing cannot say literally:
  * GI Mini Traya hangs off SUTT Pakuan Ratu - Menggala as a T-connection
    (risk #8). The engine has no tee point on a ruas, so Traya is drawn as a
    single-circuit ruas from Pakuan Ratu, named for what it is.
  * Risks #1 and #9 speak of GITET 275 kV Lampung-1 with one IBT, but the SLD
    draws Lampung 1 (LPUG1) as a plain 150 kV bus on Tier-4. The user chose
    (2026-09-23) to follow the SLD: adding the GITET here would re-tier half
    the sheet away from what P2B drew. When P2B confirms it, it goes in as a
    change request, which recomputes the tiers. Risk #9 is pinned on the
    Gumawang IBT and on LPUG1 standing in for the Lampung-1 GITET.

Shared with the Sumsel sheet (same physical GIs): GMWNG, PRATU, MSUJI and
BLMPU, which Sumsel draws as stubs off Gumawang / Martapura.

Run: python scripts/make_ss_lampung_xlsx.py
"""
from __future__ import annotations

from _kerawanan_sumatera import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Lampung"


def GI(code, name, tier, **kw):
    return dict(code=code, name=name, type="Busbar GI", tier=tier, **kw)


def KIT(code, name):
    return dict(code=code, name=name, type="Pembangkit", tier=1, kv="150 kV")


ASSETS = [
    # ================= 275 kV Gumawang =================
    dict(code="GMWNG_275", name="GITET Gumawang (275 kV)", type="Busbar GITET",
         tier=1, kv="275 kV"),
    dict(code="IBT 1 GMWNG_275", name="IBT Gumawang 275/150 kV", type="IBT 3-Winding",
         tier=2, kv="275/150 kV", ibt="1", bus_hv="GMWNG_275", bus_lv="GMWNG", trafo=1,
         simbol="satu IBT digambar (risiko #9: arah Lampung-1 masih 1 IBT)", kerawanan="9"),
    GI("GMWNG", "Gumawang (bus 150 kV)", 1),
    # ================= Tier-1 generation =================
    KIT("KIT_BESAI", "PLTA Besai"), GI("BESAI", "Besai", 1),
    KIT("KIT_ULBLU34", "PLTP Ulubelu 3&4"), GI("ULBLU34", "Ulubelu 3&4", 1, trafo=1),
    KIT("KIT_ULBLU12", "PLTP Ulubelu 1&2"), GI("ULBLU12", "Ulubelu 1&2", 1),
    KIT("KIT_BTEGI", "PLTA Batutegi"), GI("BTEGI", "Batutegi", 1),
    KIT("KIT_SMGKA", "PLTA Semangka"), GI("SMGKA", "Semangka", 1),
    KIT("KIT_TRHAN", "PLTG Tarahan"), GI("TRHAN", "Tarahan", 1, trafo=1),
    KIT("KIT_NTRHN", "PLTU New Tarahan"),
    KIT("KIT_NTRHN_G", "PLTG New Tarahan"),
    GI("NTRHN", "New Tarahan", 1, trafo=1, kerawanan="10",
       simbol="risiko #10 'PLTU Tarahan' = PLTU di bus New Tarahan (satu-satunya PLTU area Tarahan di SLD)"),
    KIT("KIT_SBLNG", "PLTU Sebalang"), GI("SBLNG", "Sebalang", 1, kerawanan="10"),
    # ================= Tier-2..6 =================
    GI("BKMNG", "Bukit Kemuning", 2, trafo=1, kapasitor=1),
    GI("PGLRN", "Pagelaran", 2, trafo=1),
    GI("KGUNG", "Kota Agung", 2, trafo=1),
    GI("STAMI", "Sutami", 2, trafo=1),
    GI("SRBWN", "Sribawono", 2, trafo=1),
    GI("SDMLY", "Sidomulyo", 2, trafo=1),
    GI("PRATU", "Pakuan Ratu", 2),
    GI("MSUJI", "Mesuji", 2, trafo=1),
    GI("BLMPU", "Blambangan Umpu", 3, trafo=1, kapasitor=1),
    GI("LIWA", "Liwa", 3, trafo=1),
    GI("KTBMI", "Kotabumi", 3, trafo=1, kapasitor=1),
    GI("TGNNG", "Tegineneng", 3, trafo=1),
    GI("METRO", "Metro", 3, trafo=1),
    GI("SRAME", "Sukarame", 3, trafo=1),
    GI("SPBYK", "Seputih Banyak", 3, trafo=1),
    GI("KLNDA", "Kalianda", 3, trafo=1),
    GI("MNGLA", "Menggala", 3, trafo=1),
    GI("TRAYA", "Mini Traya", 3, trafo=1, kerawanan="8",
       simbol="T-connection pada SUTT Pakuan Ratu - Menggala"),
    GI("DPSNA", "Dipasena", 3, trafo=1),
    GI("ADJYA", "Adijaya", 4, trafo=1),
    GI("NATAR", "Natar", 4, trafo=1, kapasitor=1),
    GI("LPUG1", "Lampung 1 (bus 150 kV)", 4, trafo=1, kapasitor=1, kerawanan="9",
       simbol="SLD menggambar bus 150 kV saja; GITET 275 kV Lampung-1 (risiko #1/#9) "
              "belum digambar -- menunggu konfirmasi P2B, masuk lewat change request"),
    GI("JTAGG", "Jati Agung", 4, trafo=1),
    # Not KTPNG: the deck's Sumbagut sheet spells Kota Pinang KTPNG, and one
    # code in one system is one GI.
    GI("KTAPG", "Ketapang", 4, trafo=1),
    GI("DTLDS", "Dente Teladas", 4, trafo=1),
    GI("LKPURA", "Langkapura", 5, trafo=1),
    GI("TLBTG", "Teluk Betung", 6, trafo=1),
]

L = lambda fr, to, nm, tf, tt, kno=None, sirkit=2, kv=150: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    sirkit=sirkit, koridor=WIL)


def OUT(kit, bus, name):
    return L(kit, bus, f"Outlet {name}", 1, 1, sirkit=1)


LINES = [
    OUT("KIT_BESAI", "BESAI", "PLTA Besai"),
    OUT("KIT_ULBLU34", "ULBLU34", "PLTP Ulubelu 3&4"),
    OUT("KIT_ULBLU12", "ULBLU12", "PLTP Ulubelu 1&2"),
    OUT("KIT_BTEGI", "BTEGI", "PLTA Batutegi"),
    OUT("KIT_SMGKA", "SMGKA", "PLTA Semangka"),
    OUT("KIT_TRHAN", "TRHAN", "PLTG Tarahan"),
    OUT("KIT_NTRHN", "NTRHN", "PLTU New Tarahan"),
    OUT("KIT_NTRHN_G", "NTRHN", "PLTG New Tarahan"),
    OUT("KIT_SBLNG", "SBLNG", "PLTU Sebalang"),
    # ================= north: Besai - Bukit Kemuning =================
    L("BESAI", "BKMNG", "SUTT 150 kV Besai - Bukit Kemuning", 1, 2),
    L("BKMNG", "BLMPU", "SUTT 150 kV Bukit Kemuning - Blambangan Umpu", 2, 3, kno="1"),
    L("BKMNG", "LIWA", "SUTT 150 kV Bukit Kemuning - Liwa", 2, 3, kno="6"),
    L("BKMNG", "KTBMI", "SUTT 150 kV Bukit Kemuning - Kotabumi", 2, 3, kno="1"),
    L("KTBMI", "ADJYA", "SUTT 150 kV Kotabumi - Adijaya", 3, 4),
    L("KTBMI", "TGNNG", "SUTT 150 kV Kotabumi - Tegineneng", 3, 3),
    L("ADJYA", "TGNNG", "SUTT 150 kV Adijaya - Tegineneng", 4, 3),
    # ================= west: Ulubelu - Batutegi - Pagelaran - Semangka =========
    L("ULBLU34", "ULBLU12", "SUTT 150 kV Ulubelu 3&4 - Ulubelu 1&2", 1, 1),
    L("ULBLU12", "BTEGI", "SUTT 150 kV Ulubelu 1&2 - Batutegi", 1, 1, kno="3"),
    L("ULBLU12", "PGLRN", "SUTT 150 kV Ulubelu 1&2 - Pagelaran", 1, 2),
    L("BTEGI", "PGLRN", "SUTT 150 kV Batutegi - Pagelaran", 1, 2, kno="3"),
    L("PGLRN", "TGNNG", "SUTT 150 kV Pagelaran - Tegineneng", 2, 3, kno="3"),
    L("PGLRN", "KGUNG", "SUTT 150 kV Pagelaran - Kota Agung", 2, 2, kno="3"),
    L("SMGKA", "KGUNG", "SUTT 150 kV Semangka - Kota Agung", 1, 2, kno="3"),
    # ================= Tegineneng - Natar - Teluk Betung =================
    L("TGNNG", "NATAR", "SUTT 150 kV Tegineneng - Natar", 3, 4, kno="2"),
    L("NATAR", "LKPURA", "SUTT 150 kV Natar - Langkapura", 4, 5, kno="4"),
    L("LKPURA", "TLBTG", "SUTT 150 kV Langkapura - Teluk Betung", 5, 6, kno="4"),
    L("TGNNG", "LPUG1", "SUTT 150 kV Tegineneng - Lampung 1", 3, 4),
    L("TGNNG", "SRBWN", "SUTT 150 kV Tegineneng - Sribawono", 3, 2),
    L("METRO", "SRBWN", "SUTT 150 kV Metro - Sribawono", 3, 2),
    L("METRO", "LPUG1", "SUTT 150 kV Metro - Lampung 1", 3, 4),
    L("NATAR", "SRAME", "SUTT 150 kV Natar - Sukarame", 4, 3),
    # ================= Tarahan =================
    L("TRHAN", "STAMI", "SUTT 150 kV Tarahan - Sutami", 1, 2),
    L("STAMI", "SRAME", "SUTT 150 kV Sutami - Sukarame", 2, 3),
    L("SRAME", "JTAGG", "SUTT 150 kV Sukarame - Jati Agung", 3, 4),
    L("NTRHN", "STAMI", "SUTT 150 kV New Tarahan - Sutami", 1, 2),
    L("NTRHN", "SRBWN", "SUTT 150 kV New Tarahan - Sribawono", 1, 2),
    L("SRBWN", "SPBYK", "SUTT 150 kV Sribawono - Seputih Banyak", 2, 3),
    L("SPBYK", "MNGLA", "SUTT 150 kV Seputih Banyak - Menggala", 3, 3),
    L("NTRHN", "SBLNG", "SUTT 150 kV New Tarahan - Sebalang", 1, 1, kno="7"),
    L("SBLNG", "SDMLY", "SUTT 150 kV Sebalang - Sidomulyo", 1, 2, kno="7"),
    L("SDMLY", "KLNDA", "SUTT 150 kV Sidomulyo - Kalianda", 2, 3, kno="7"),
    L("KLNDA", "KTAPG", "SUTT 150 kV Kalianda - Ketapang", 3, 4, kno="7"),
    # ================= Gumawang (east) =================
    L("GMWNG", "PRATU", "SUTT 150 kV Gumawang - Pakuan Ratu", 1, 2, kno="1"),
    L("PRATU", "MNGLA", "SUTT 150 kV Pakuan Ratu - Menggala", 2, 3, kno="1"),
    L("PRATU", "TRAYA", "SUTT 150 kV T-connection Mini Traya (dari Pakuan Ratu - Menggala)",
      2, 3, kno="8", sirkit=1),
    L("GMWNG", "MSUJI", "SUTT 150 kV Gumawang - Mesuji", 1, 2, kno="5"),
    L("MSUJI", "DPSNA", "SUTT 150 kV Mesuji - Dipasena", 2, 3, kno="5"),
    L("DPSNA", "DTLDS", "SUTT 150 kV Dipasena - Dente Teladas", 3, 4, kno="5"),
]

# Arrows to a neighbouring subsystem: (gi, name, feeder, kerawanan, sirkit,
# status, views, jenis, kv)
BAYS = [
    ("MPURA", "Martapura (Subsistem Sumsel)", "BLMPU", "1", 2, "Beroperasi", None, "SUTT", "150 kV"),
    ("MENIM_275", "Muara Enim (Subsistem Sumsel, 275 kV)", "GMWNG_275", None, 2, "Beroperasi", None, "SUTT", "275 kV"),
]

SPEC = dict(
    code="SS_LAMPUNG",
    name="Lampung",
    apb="Sumbagsel",
    wilayah=WIL,
    multi_pin=True,
    source_ref="Kerawanan Sistem Sumatera Sep 2026 (UIP3B Sumatera), slide 13 "
               "Peta Kerawanan Sistem Lampung; tabel risiko slide 14-15",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts("LAMPUNG"),
)

if __name__ == "__main__":
    build_workbook(SPEC)
