"""samples/ss_krian3456_ingest.xlsx -- Subsistem Krian 3,4,5,6 (UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.4 (PDF p.197-201) for the risk table, and
Lampiran-4 "Single Line Diagram Subsistem Jawa Timur" (PDF p.251) for topology.
Krian 3,4,5,6 is the cyan block in the middle of that drawing.

GITET Krian 500 kV (KRIAN7) steps down through IBT 3,4,5,6 = 4x500 MVA on a
500/150/66 kV three-winding bank. That bank is why this subsistem carries BOTH
a 150 kV and a 70 kV network, and most of its risks are about the 70 kV side:

  150 kV: KRIAN -> SBRAT5 (Surabaya Barat), BBDAN (Balongbendo), BLBND, DRYJO5
  70 kV : DRYJO4 (Driyorejo 70) -> MIWON, CKMIA, AJMTO, TARIK, BNGUN

Risk #1 notes IBT 6 is a temporary measure pending the SUTET 500 kV project, so
it is modelled as its own asset with status "Beroperasi" but flagged; risks
2, 3 and 7 are single-phi T/L bay configurations, so those ruas carry
Single Phi = Ya, which the renderer draws differently.

Run: python scripts/make_ss_krian3456_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # -- 500 kV GITET --
    dict(code="KRIAN7", name="GITET Krian", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 3 KRIAN7", name="IBT 3,4,5 Krian 500/150/66 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="3", bus_hv="KRIAN7", bus_lv="KRIAN", trafo=3,
         simbol="3 IBT x 500 MVA (unit 3,4,5) 500/150/66 kV"),
    dict(code="IBT 6 KRIAN7", name="IBT 6 Krian 500/150/66 kV (sementara)",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="6", bus_hv="KRIAN7", bus_lv="KRIAN",
         trafo=1, kerawanan="1",
         simbol="1 IBT x 500 MVA; sementara sampai SUTET 500 kV siap"),
    # -- 150 kV --
    dict(code="KRIAN", name="Krian (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="bus A1/A2 - B1/B2"),
    dict(code="SBRAT5", name="Surabaya Barat", type="Busbar GI", tier=2,
         simbol="3x60 MVA", kerawanan="4"),
    dict(code="BBDAN", name="Balongbendo", type="Busbar GI", tier=2,
         simbol="50/50/60 MVA", kerawanan="4"),
    dict(code="BLBND", name="Bulubendo", type="Busbar GI", tier=2,
         simbol="4x60 MVA + 50 MVAR"),
    dict(code="DRYJO5", name="Driyorejo (bus 150 kV)", type="Busbar GI", tier=2,
         simbol="60 MVA (bay 3,4,9,10)", kerawanan="3"),
    dict(code="KSJTM", name="Kasih Jatim", type="Busbar GI", tier=3,
         simbol="T/L bay Surabaya Barat single phi", kerawanan="2"),
    # -- IBT 150/70 kV Driyorejo + jaringan 70 kV --
    dict(code="IBT 1 DRYJO5", name="IBT 150/70 kV Driyorejo", type="IBT 3-Winding",
         tier=3, kv="150/70 kV", ibt="1", bus_hv="DRYJO5", bus_lv="DRYJO4", trafo=2,
         simbol="kapasitas IBT tidak seimbang", kerawanan="5"),
    dict(code="DRYJO4", name="Driyorejo (bus 70 kV)", type="Busbar GI", tier=3,
         kv=70, simbol="single busbar; 30 MVA (bay 8)", kerawanan="6"),
    dict(code="MIWON", name="Miwon", type="Busbar GI", tier=4, kv=70,
         simbol="single busbar; 30 MVA", kerawanan="8"),
    dict(code="CKMIA", name="Cukir / Cikamia", type="Busbar GI", tier=4, kv=70,
         simbol="60/40 MVA"),
    dict(code="AJMTO", name="Ajimoto", type="Busbar GI", tier=4, kv=70,
         simbol="20/12 MVA"),
    dict(code="TARIK", name="Tarik", type="Busbar GI", tier=4, kv=70,
         simbol="30/30/10 MVA"),
    dict(code="BNGUN", name="Bangun", type="Busbar GI", tier=5, kv=70,
         simbol="30 MVA"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, sp=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=sp, koridor=WIL)

LINES = [
    # -- 150 kV --
    L("KRIAN", "SBRAT5", "SUTT Krian - Surabaya Barat", 1, 2),
    L("KRIAN", "BBDAN", "SUTT Krian - Balongbendo", 1, 2),
    # kerawanan #4: Surabaya Barat-Balongbendo >65%, N-1 tidak terpenuhi
    L("SBRAT5", "BBDAN", "SUTT Surabaya Barat - Balongbendo", 2, 2, kno="4"),
    L("KRIAN", "BLBND", "SUTT Krian - Bulubendo", 1, 2),
    L("KRIAN", "DRYJO5", "SUTT Krian - Driyorejo 150 kV", 1, 2),
    # kerawanan #2 / #3: T/L bay single phi ke Surabaya Barat
    L("KSJTM", "SBRAT5", "SUTT Kasih Jatim - Surabaya Barat (single phi)",
      3, 2, kno="2", sirkit=1, sp=True),
    L("DRYJO5", "SBRAT5", "SUTT Driyorejo - Surabaya Barat (single phi)",
      2, 2, kno="3", sirkit=1, sp=True),
    # -- 70 kV --
    L("DRYJO4", "MIWON", "SUTT 70 kV Driyorejo - Miwon (single phi)",
      3, 4, kv=70, kno="7", sirkit=1, sp=True),
    L("DRYJO4", "CKMIA", "SUTT 70 kV Driyorejo - Cikamia", 3, 4, kv=70),
    L("CKMIA", "AJMTO", "SUTT 70 kV Cikamia - Ajimoto", 4, 4, kv=70),
    L("CKMIA", "TARIK", "SUTT 70 kV Cikamia - Tarik", 4, 4, kv=70),
    L("TARIK", "BNGUN", "SUTT 70 kV Tarik - Bangun", 4, 5, kv=70),
]

SPEC = dict(
    code="SS_KRIAN3456",
    name="Krian 3,4,5,6",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.4 (PDF p.197-201); "
               "topologi dari Lampiran-4 Single Line Diagram Jawa Timur (PDF p.251)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(197, 201, expected=8),
)

if __name__ == "__main__":
    build_workbook(SPEC)
