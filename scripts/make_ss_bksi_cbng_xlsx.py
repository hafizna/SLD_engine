"""samples/ss_bksi_cbng_ingest.xlsx -- Subsistem Bekasi 1,3 - Cibinong 3.

Source: Buku Kerawanan SJB 2026 Sec 2.12, Gambar 2.11 (Peta Kerawanan, PDF
p.104) and Tabel 2.10 (PDF p.105-106).

Two 500/150 kV injections feeding one 150 kV network:
    GITET Bekasi   -> IBT 1,3 -> BKASI  (Tier-1)
    GITET Cibinong -> IBT 3   -> CIBNG  (Tier-1)
Kerawanan #1 is precisely that the two are unbalanced ("Pembebanan IBT 1,3
Bekasi dengan IBT 3 Cibinong tidak seimbang"), so both IBT rows carry it.

Tier-2 is SMRCN, PDKLP, CBBUR and GDRIA; Tier-3 is HALIM, JTWRG, MNTUR, JTRGN
and CRCAS. MRNDA/PGLNG/PGDRU/KDSPI/HNDAH hang off Tier-1 BKASI as bay stubs,
and CMGIS/SNTUL/SMNRU off Tier-1 CIBNG.

**UP2B Jabar interconnections.** Gambar 2.11 draws two rounded grey boxes that
are NOT GIs of this subsistem but the neighbouring UP2B Jawa Barat assets this
subsistem reaches:
    off Tier-1/2  : "UP2B 2 (JABAR)  SUKATANI : Trf 1,2 , STRDA / KSBRU / DAWUAN"
    off Tier-3    : "UP2B 2 (JABAR)  NEW TAMBUN"
They are modelled as SOURCE_BOUNDARY busbars so the ruas that cross the UP2B
boundary still terminate on something and the sheet shows where this subsistem
ends -- the same treatment KBSEN gets in the Pemalang sheet. Their internal
detail (Sukatani's own Trf 1,2) belongs to the Jabar sheets (Sec 3.9 Sukatani
1,2 and Sec 3.8 New Tambun), not here.

Kerawanan #2 is the single-phi configuration at GIS Miniatur, GIS Pondok Kelapa
and GI Jatirangon, so those ruas carry Single Phi = Ya. Kerawanan #3 is the
Bekasi-New Sukatani ruas being not ready for operation, hence status Rencana.

Run: python scripts/make_ss_bksi_cbng_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Barat"

ASSETS = [
    # ================= 500 kV injections =================
    dict(code="BKASI7", name="GITET Bekasi", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="CIBNG7", name="GITET Cibinong", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 1 BKASI7", name="IBT 1,3 Bekasi 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="BKASI7", bus_lv="BKASI", trafo=2,
         simbol="2 IBT (unit 1,3)", kerawanan="1"),
    dict(code="IBT 3 CIBNG7", name="IBT 3 Cibinong 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="3", bus_hv="CIBNG7", bus_lv="CIBNG", trafo=1,
         simbol="1 IBT (unit 3)", kerawanan="1"),
    # ================= Tier-1 150 kV =================
    dict(code="BKASI", name="Bekasi (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section + kopel"),
    dict(code="CIBNG", name="Cibinong (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus section + kopel"),
    # ================= Tier-2 =================
    dict(code="SMRCN", name="Sumur Recon", type="Busbar GI", tier=2),
    dict(code="PDKLP", name="Pondok Kelapa (GIS)", type="Busbar GIS", tier=2,
         simbol="single phi", kerawanan="2"),
    dict(code="CBBUR", name="Cibubur", type="Busbar GI", tier=2),
    dict(code="GDRIA", name="Gandaria", type="Busbar GI", tier=2),
    # ================= Tier-3 =================
    dict(code="HALIM", name="Halim", type="Busbar GI", tier=3),
    dict(code="JTWRG", name="Jatiwaringin", type="Busbar GI", tier=3),
    dict(code="MNTUR", name="Miniatur (GIS)", type="Busbar GIS", tier=3,
         simbol="single phi", kerawanan="2"),
    dict(code="JTRGN", name="Jatirangon", type="Busbar GI", tier=3,
         simbol="single phi", kerawanan="2"),
    dict(code="CRCAS", name="Cireca/Cirencas", type="Busbar GI", tier=3),
    # ============ batas ke UP2B Jawa Barat (bukan GI subsistem ini) ============
    dict(code="SKTNI", name="Sukatani (UP2B Jabar)", type="Busbar GI", tier=2,
         role="SOURCE_BOUNDARY", kerawanan="3",
         simbol="UP2B 2 (JABAR): SUKATANI Trf 1,2 / STRDA, KSBRU, DAWUAN"),
    dict(code="NTMBN", name="New Tambun (UP2B Jabar)", type="Busbar GI", tier=3,
         role="SOURCE_BOUNDARY", simbol="UP2B 2 (JABAR): NEW TAMBUN"),
]

# Bay stubs drawn hanging off the two Tier-1 buses on Gambar 2.11.
BAYS = [
    ("MRNDA", "Marunda", "BKASI", None),
    ("PGLNG", "Pegangsaan", "BKASI", None),
    ("PGDRU", "Pulogadung Baru", "BKASI", None),
    ("KDSPI", "Kandang Sapi", "BKASI", None),
    ("HNDAH", "Hankam Indah", "BKASI", None),
    ("CMGIS", "Cimanggis (GIS)", "CIBNG", None),
    ("SNTUL", "Sentul", "CIBNG", None),
    ("SMNRU", "Semen Baru", "CIBNG", None),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, sp=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=sp, koridor=WIL)

LINES = [
    # -- sisi Bekasi --
    L("BKASI", "SMRCN", "SUTT Bekasi - Sumur Recon", 1, 2),
    L("SMRCN", "HALIM", "SUTT Sumur Recon - Halim", 2, 3),
    # kerawanan #3: Bekasi - New Sukatani belum siap operasi
    L("BKASI", "SKTNI", "SUTT Bekasi - New Sukatani (belum siap operasi)",
      1, 2, kno="3", st="Rencana"),
    # kerawanan #2: single phi di GIS Pondok Kelapa / GIS Miniatur / GI Jatirangon
    L("BKASI", "PDKLP", "SUTT Bekasi - Pondok Kelapa (single phi)",
      1, 2, kno="2", sirkit=1, sp=True),
    L("PDKLP", "MNTUR", "SUTT Pondok Kelapa - Miniatur (single phi)",
      2, 3, kno="2", sirkit=1, sp=True),
    L("MNTUR", "JTRGN", "SUTT Miniatur - Jatirangon (single phi)",
      3, 3, kno="2", sirkit=1, sp=True),
    L("PDKLP", "JTWRG", "SUTT Pondok Kelapa - Jatiwaringin", 2, 3),
    L("JTWRG", "NTMBN", "SUTT Jatiwaringin - New Tambun (arah UP2B Jabar)", 3, 3),
    # -- sisi Cibinong --
    L("CIBNG", "CBBUR", "SUTT Cibinong - Cibubur", 1, 2),
    L("CIBNG", "GDRIA", "SUTT Cibinong - Gandaria", 1, 2),
    L("CBBUR", "JTRGN", "SUTT Cibubur - Jatirangon", 2, 3),
    L("GDRIA", "CRCAS", "SUTT Gandaria - Cirencas", 2, 3),
]

SPEC = dict(
    code="SS_BKSI_CBNG",
    name="Bekasi 1,3 - Cibinong 3",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.12 (Tabel 2.10, PDF p.105-106); "
               "topologi dari Gambar 2.11 Peta Kerawanan (PDF p.104)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(105, 106, expected=3),
)

if __name__ == "__main__":
    build_workbook(SPEC)
