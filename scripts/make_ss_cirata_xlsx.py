"""samples/ss_cirata_ingest.xlsx -- Subsistem Cirata 1,2,3 (UP2B Jawa Barat).

Source: Buku Kerawanan SJB 2026 Sec 3.4, Gambar 3.5 (Peta Kerawanan, PDF p.118)
and Tabel 3.3. The rows sit on PDF p.119-122; the Cibatu 3,4 table still runs on
p.118, so the range comes from the risk numbering, not the heading.

One Cirata 500 kV GITET supplies two distinct Tier-1 150 kV bus sections. IBT
1,2 land on CRATA 1,2 and IBT 3 lands on CRATA 3.  The section labels are not
separate GITET sites.  Jatiluhur is represented as one site with distinct 150
kV and 70 kV buses joined by three transformers.

Like Tasikmalaya this subsystem straddles two voltages, and the 70 kV side
(yellow on Gambar 3.5) is much the larger half: PWKTA steps down through an
IBT 150/70 and the 70 kV network then runs IDRMA - SPFIC - KSBRU - SBANG across
Tier-4 and INDCI - CGNEA - IDBRT - CURUG across Tier-5. CRATA itself also has a
70 kV bus. Risks 6-10 all sit on that 70 kV half.

Boundaries, each drawn with its owner in brackets:
    TTJBR, PNDLI, RDSLK   "(SS CBATU 3,4)"
    CGRLG, UBRNG          "(SS BDSLN)"  -- Bandung Selatan 1,2 - New Ujungberung

Run: python scripts/make_ss_cirata_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"

ASSETS = [
    # ================= 500 kV injections =================
    dict(code="CRATA7", name="GITET Cirata", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 CRATA7", name="IBT 1 Cirata 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="CRATA7", bus_lv="CRATA5_12",
         trafo=1, kerawanan="1"),
    dict(code="IBT 2 CRATA7", name="IBT 2 Cirata 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="CRATA7", bus_lv="CRATA5_12",
         trafo=1, kerawanan="1"),
    dict(code="IBT 3 CRATA7", name="IBT 3 Cirata 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="3", bus_hv="CRATA7", bus_lv="CRATA5_3",
         trafo=1, simbol="1 IBT (unit 3)"),
    # ================= Tier-1 150 kV =================
    dict(code="CRATA5_12", name="Cirata 1,2 (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section 1,2"),
    dict(code="CRATA5_3", name="Cirata 3 (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section 3"),
    # -- pembangkit di Tier-1 --
    dict(code="KIT_PTUHA", name="PLTA Cirata (Purwakarta)", type="Pembangkit",
         tier=1, kv="150 kV"),
    dict(code="KIT_JTLHR", name="PLTA Jatiluhur", type="Pembangkit",
         tier=1, kv="150 kV", kerawanan="2"),
    dict(code="KIT_PLTS", name="PLTS Cirata", type="Pembangkit",
         tier=1, kv="150 kV"),
    dict(code="PTUHA", name="Purwakarta (Cirata)", type="Busbar GI", tier=1),
    dict(code="JTLHR", name="Jatiluhur (bus 150 kV)", type="Busbar GI", tier=1,
         kerawanan="2"),
    dict(code="TRF 1 JTLHR", name="Trafo 1 Jatiluhur 150/70 kV",
         type="IBT 3-Winding", tier=2, kv="150/70 kV", ibt="1",
         bus_hv="JTLHR", bus_lv="JTLHR4", trafo=1),
    dict(code="TRF 2 JTLHR", name="Trafo 2 Jatiluhur 150/70 kV",
         type="IBT 3-Winding", tier=2, kv="150/70 kV", ibt="2",
         bus_hv="JTLHR", bus_lv="JTLHR4", trafo=1),
    dict(code="TRF 3 JTLHR", name="Trafo 3 Jatiluhur 150/70 kV",
         type="IBT 3-Winding", tier=2, kv="150/70 kV", ibt="3",
         bus_hv="JTLHR", bus_lv="JTLHR4", trafo=1),
    dict(code="JTLHR4", name="Jatiluhur (bus 70 kV)", type="Busbar GI",
         tier=2, kv=70),
    # ================= Tier-2 150 kV =================
    dict(code="LGDAR", name="Lengkong Dar", type="Busbar GI", tier=2,
         simbol="bus section + kopel"),
    dict(code="PDLRU", name="Padalarang Baru", type="Busbar GI", tier=2,
         kerawanan="3"),
    dict(code="CKMPY", name="Cikampek", type="Busbar GI", tier=2),
    dict(code="PWKTA", name="Purwakarta (bus 150 kV)", type="Busbar GI", tier=2,
         kerawanan="4"),
    # The 70 kV Cirata bus is reached from the 150 kV one through its own
    # transformer, not a penghantar: a cross-voltage tie has to be an IBT_LINK.
    dict(code="IBT 1 CRATA5", name="IBT 150/70 kV Cirata", type="IBT 3-Winding",
         tier=2, kv="150/70 kV", ibt="1", bus_hv="CRATA5_12", bus_lv="CRATA4",
         trafo=1, simbol="IBT 150/70 kV", kerawanan="6"),
    dict(code="CRATA4", name="Cirata (bus 70 kV)", type="Busbar GI", tier=2,
         kv=70, kerawanan="6"),
    # ================= Tier-3 150 kV =================
    dict(code="BDUTR", name="Bandung Utara", type="Busbar GI", tier=3),
    dict(code="CBBRU", name="Cibabat Baru", type="Busbar GI", tier=3, kerawanan="5"),
    dict(code="CBBAT", name="Cibabat", type="Busbar GI", tier=3),
    dict(code="IDRMA5", name="Indramayu (bus 150 kV)", type="Busbar GI", tier=3),
    dict(code="PBRAN", name="Pabuaran", type="Busbar GI", tier=3),
    dict(code="DGPKR", name="Degung Pakar", type="Busbar GI", tier=4),
    # ============ IBT 150/70 kV Purwakarta + jaringan 70 kV ============
    dict(code="IBT 1 PWKTA", name="Trafo 1 Purwakarta 150/70 kV", type="IBT 3-Winding",
         tier=3, kv="150/70 kV", ibt="1", bus_hv="PWKTA", bus_lv="PWKTA4",
         trafo=1, simbol="Trafo 150/70 kV"),
    dict(code="IBT 2 PWKTA", name="Trafo 2 Purwakarta 150/70 kV", type="IBT 3-Winding",
         tier=3, kv="150/70 kV", ibt="2", bus_hv="PWKTA", bus_lv="PWKTA4",
         trafo=1, simbol="Trafo 150/70 kV"),
    dict(code="PWKTA4", name="Purwakarta (bus 70 kV)", type="Busbar GI",
         tier=3, kv=70),
    dict(code="IDRMA", name="Indramayu (bus 70 kV)", type="Busbar GI",
         tier=4, kv=70, kerawanan="7"),
    dict(code="SPFIC", name="Sipfic", type="Busbar GI", tier=4, kv=70,
         kerawanan="8"),
    dict(code="KSBRU", name="Kosambi Baru", type="Busbar GI", tier=4, kv=70,
         kerawanan="10"),
    dict(code="SBANG", name="Subang", type="Busbar GI", tier=4, kv=70,
         kerawanan="9"),
    dict(code="INDCI", name="Indocement", type="Busbar GI", tier=5, kv=70),
    dict(code="CGNEA", name="Cigunea", type="Busbar GI", tier=5, kv=70),
    dict(code="IDBRT", name="Indramayu Barat", type="Busbar GI", tier=5, kv=70),
    dict(code="CURUG", name="Curug", type="Busbar GI", tier=5, kv=70),
    # ============ batas subsistem ============
    dict(code="TTJBR", name="Tegal Tanjung Baru (SS Cibatu 3,4)", type="Busbar GI",
         tier=2, role="SOURCE_BOUNDARY", simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="PNDLI", name="Pondok Ali (SS Cibatu 3,4)", type="Busbar GI",
         tier=5, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="RDSLK", name="Rendeh Salak (SS Cibatu 3,4)", type="Busbar GI",
         tier=5, kv=70, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="CGRLG", name="Cigereleng (SS Bandung Selatan)", type="Busbar GI",
         tier=3, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Bandung Selatan 1,2 - New Ujungberung 1,2"),
    dict(code="UBRNG", name="Ujung Berung (SS Bandung Selatan)", type="Busbar GI",
         tier=5, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Bandung Selatan 1,2 - New Ujungberung 1,2"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, single_phi=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=single_phi, koridor=WIL)

# Aset milik SS/UP2B lain: digambar sebagai stub pada busnya,
# bukan busbar tersendiri -- mengikuti pola UP2B Jakban.
BAYS = [
    ("CGRLG", "Cigereleng", "LGDAR", None, 1, "Beroperasi", "", "SUTT"),
    ("PNDLI", "Pondok Ali", "KSBRU", None, 1, "Beroperasi", "", "SUTT"),
    ("RDSLK", "Rendeh Salak (SS Cibatu 3,4)", "KSBRU", None, 1, "Beroperasi", "", "SUTT"),
    ("TTJBR", "Tegal Tanjung Baru", "JTLHR", None, 1, "Beroperasi", "", "SUTT"),
    ("UBRNG", "Ujung Berung", "DGPKR", None, 1, "Beroperasi", "", "SUTT"),
]

LINES = [
    # -- outlet pembangkit --
    L("KIT_PTUHA", "PTUHA", "Outlet PLTA Cirata", 1, 1, sirkit=1),
    L("KIT_JTLHR", "JTLHR", "Outlet PLTA Jatiluhur", 1, 1, sirkit=1),
    L("KIT_PLTS", "CRATA5_12", "Outlet PLTS Cirata", 1, 1, sirkit=1),
    L("PTUHA", "CRATA5_12", "SUTT Purwakarta - Cirata 1,2", 1, 1),
    # -- 150 kV --
    L("PTUHA", "LGDAR", "SUTT Purwakarta - Lengkong Dar", 1, 2),
    L("JTLHR", "TTJBR", "SUTT Jatiluhur - Tegal Tanjung Baru (arah SS Cibatu 3,4)", 1, 2),
    L("CRATA5_12", "PDLRU", "SUTT Cirata 1,2 - Padalarang Baru", 1, 2, kno="3"),
    L("CRATA5_12", "CKMPY", "SUTT Cirata 1,2 - Cikampek", 1, 2),
    L("CRATA5_3", "PWKTA", "SUTT Cirata 3 - Purwakarta", 1, 2, kno="4"),
    L("CKMPY", "PWKTA", "SUTT Cikampek - Purwakarta single phi", 2, 2,
      sirkit=1, single_phi=True),
    L("LGDAR", "CGRLG", "SUTT Lengkong Dar - Cigereleng (arah SS Bandung Selatan)", 2, 3),
    L("PDLRU", "BDUTR", "SUTT Padalarang Baru - Bandung Utara", 2, 3),
    L("PDLRU", "CBBRU", "SUTT Padalarang Baru - Cibabat Baru", 2, 3, kno="5"),
    L("CKMPY", "CBBAT", "SUTT Cikampek - Cibabat", 2, 3),
    L("CKMPY", "IDRMA5", "SUTT Cikampek - Indramayu", 2, 3),
    L("CKMPY", "PBRAN", "SUTT Cikampek - Pabuaran", 2, 3),
    L("BDUTR", "DGPKR", "SUTT Bandung Utara - Degung Pakar", 3, 4),
    L("DGPKR", "UBRNG", "SUTT Degung Pakar - Ujung Berung (arah SS Bandung Selatan)", 4, 5),
    # -- 70 kV --
    # Gambar 3.5 drops each of these from its own point along the long 70 kV
    # PWKTA bus as a single circuit, not as four 2-sirkit bundles.
    L("PWKTA4", "IDRMA", "SUTT 70 kV Purwakarta - Indramayu", 3, 4, kv=70,
      kno="7", sirkit=1),
    L("PWKTA4", "SPFIC", "SUTT 70 kV Purwakarta - Sipfic", 3, 4, kv=70,
      kno="8", sirkit=1),
    L("PWKTA4", "KSBRU", "SUTT 70 kV Purwakarta - Kosambi Baru", 3, 4, kv=70,
      kno="10", sirkit=1),
    L("PWKTA4", "SBANG", "SUTT 70 kV Purwakarta - Subang", 3, 4, kv=70,
      kno="9", sirkit=1),
    L("IDRMA", "INDCI", "SUTT 70 kV Indramayu - Indocement", 4, 5, kv=70),
    L("SPFIC", "CGNEA", "SUTT 70 kV Sipfic - Cigunea", 4, 5, kv=70),
    L("KSBRU", "IDBRT", "SUTT 70 kV Kosambi Baru - Indramayu Barat", 4, 5, kv=70),
    L("KSBRU", "CURUG", "SUTT 70 kV Kosambi Baru - Curug", 4, 5, kv=70),
    L("KSBRU", "PNDLI", "SUTT 70 kV Kosambi Baru - Pondok Ali (arah SS Cibatu 3,4)",
      4, 5, kv=70),
    L("KSBRU", "RDSLK", "SUTT 70 kV Kosambi Baru - Rendeh Salak (arah SS Cibatu 3,4)",
      4, 5, kv=70),
    # Jatiluhur branches in two directions.  Through CGNEA/SPFIC and
    # CURUG/KSBRU they rejoin the Purwakarta-Cirata 70 kV mesh.
    L("JTLHR4", "CGNEA", "SUTT 70 kV Jatiluhur - Ciganea", 2, 5, kv=70),
    L("JTLHR4", "CURUG", "SUTT 70 kV Jatiluhur - Curug", 2, 5, kv=70),
    L("CRATA4", "PWKTA4", "SUTT 70 kV Cirata - Purwakarta", 2, 3, kv=70,
      sirkit=2),
]

SPEC = dict(
    code="SS_CIRATA",
    name="Cirata 1,2,3",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.4 (Tabel 3.3, PDF p.119-122); "
               "topologi dari Gambar 3.5 Peta Kerawanan (PDF p.118)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(119, 122, expected=10),
)

if __name__ == "__main__":
    build_workbook(SPEC)
