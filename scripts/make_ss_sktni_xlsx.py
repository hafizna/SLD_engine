"""samples/ss_sktni_ingest.xlsx -- Subsistem Sukatani 1,2 (UP2B Jawa Barat).

Source: Buku Kerawanan SJB 2026 Sec 3.9, Gambar 3.12 (Peta Kerawanan, PDF p.137)
and Tabel 3.10. The table's rows sit on PDF p.138-140; New Tambun's table still
runs on p.137, so the range is taken from the risk numbering, not the heading.

GITET Sukatani 500 kV (SKTNI) steps down through 2 IBT onto the NSKTN Tier-1
bus. Tier-2 is the 150 kV SKTNI bus, Tier-3 MTSDA and KSBRU, Tier-4 DWUAN.

This sheet is the Jawa Barat side of the tie the Bekasi 1,3 - Cibinong 3 sheet
draws as its grey "UP2B 2 (JABAR) SUKATANI : Trf 1,2 , STRDA / KSBRU / DAWUAN"
box: BKASI appears here marked "(UP2B JAKBAN)" and is a SOURCE_BOUNDARY, while
KSBRU (Kesambi Baru) and DWUAN (Dawuan) are real GIs of THIS subsystem. Same
physical tie, drawn from both ends.

TTJBR, IDBRU and MLIGI/KTMKR hang off Tier-3 marked "(SS CBATU 3,4)" -- the
boundary toward Cibatu 3,4 - PLTU Indramayu - Mandirancan 1,2.

Run: python scripts/make_ss_sktni_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"

ASSETS = [
    dict(code="SKTNI7", name="GITET Sukatani", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 SKTNI7", name="IBT 1 Sukatani 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="1",
         bus_hv="SKTNI7", bus_lv="NSKTN", trafo=1),
    dict(code="IBT 2 SKTNI7", name="IBT 2 Sukatani 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="2",
         bus_hv="SKTNI7", bus_lv="NSKTN", trafo=1),
    dict(code="NSKTN", name="New Sukatani (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="SKTNI", name="Sukatani (bus 150 kV)", type="Busbar GI", tier=2,
         simbol="Trf 1,2", kerawanan="1"),
    dict(code="MTSDA", name="Mitsuda", type="Busbar GI", tier=3),
    dict(code="KSBRU", name="Kesambi Baru", type="Busbar GI", tier=3,
         kerawanan="2"),
    dict(code="DWUAN", name="Dawuan", type="Busbar GI", tier=4),
    # -- batas subsistem, digambar dengan pemiliknya dalam kurung --
    dict(code="BKASI", name="Bekasi (UP2B Jakban)", type="Busbar GI", tier=2,
         role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Bekasi 1,3 - Cibinong 3"),
    dict(code="TTJBR", name="Tegal Tanjung Baru (SS Cibatu 3,4)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="IDBRU", name="Indramayu Baru (SS Cibatu 3,4)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 3,4"),
    dict(code="MLIGI", name="Maligi / Katomukti (SS Cibatu 3,4)", type="Busbar GI",
         tier=4, role="SOURCE_BOUNDARY",
         simbol="batas ke Subsistem Cibatu 3,4"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

# Aset milik SS/UP2B lain: digambar sebagai stub pada busnya,
# bukan busbar tersendiri -- mengikuti pola UP2B Jakban.
BAYS = [
    ("BKASI", "Bekasi (bus 150 kV)", "NSKTN", None, 1, "Beroperasi", "", "SUTT"),
    ("IDBRU", "Indramayu Baru (SS Cibatu 3,4)", "MTSDA", None, 1, "Beroperasi", "", "SUTT"),
    ("MLIGI", "Maligi", "MTSDA", None, 1, "Beroperasi", "", "SUTT"),
    ("TTJBR", "Tegal Tanjung Baru", "MTSDA", None, 1, "Beroperasi", "", "SUTT"),
]

LINES = [
    # kerawanan #1: bottleneck MTU GI Tambun / T-L bay incomer New Sukatani
    L("NSKTN", "SKTNI", "SUTT New Sukatani - Sukatani", 1, 2, kno="1"),
    L("NSKTN", "BKASI", "SUTT New Sukatani - Bekasi (arah UP2B Jakban)", 1, 2),
    L("SKTNI", "MTSDA", "SUTT Sukatani - Mitsuda", 2, 3),
    L("SKTNI", "KSBRU", "SUTT Sukatani - Kesambi Baru", 2, 3, kno="2"),
    L("KSBRU", "DWUAN", "SUTT Kesambi Baru - Dawuan", 3, 4),
    L("MTSDA", "TTJBR", "SUTT Mitsuda - Tegal Tanjung Baru (arah SS Cibatu 3,4)", 3, 4),
    L("MTSDA", "IDBRU", "SUTT Mitsuda - Indramayu Baru (arah SS Cibatu 3,4)", 3, 4),
    L("MTSDA", "MLIGI", "SUTT Mitsuda - Maligi/Katomukti (arah SS Cibatu 3,4)", 3, 4),
]

SPEC = dict(
    code="SS_SKTNI",
    name="Sukatani 1,2",
    apb="UP2B Jawa Barat",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 3.9 (Tabel 3.10, PDF p.138-140); "
               "topologi dari Gambar 3.12 Peta Kerawanan (PDF p.137)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(138, 140, expected=2),
)

if __name__ == "__main__":
    build_workbook(SPEC)
