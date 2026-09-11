"""samples/ss_kediri12_ingest.xlsx -- Subsistem Kediri 1,2 (UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.6 (PDF p.206-208) for the risk table, and
Lampiran-4 (PDF p.251) for topology. Kediri 1,2 is the magenta block on the
left-centre of that drawing.

Injection is GITET Ngoro / Kediri 500 kV (NGORO7) through IBT 1,2. Like Krian
3,4,5,6 this subsistem straddles two voltages: a 150 kV backbone around Kediri
and a large 70 kV network toward Kertosono, Nganjuk and Caruban -- the 70 kV
side is where risks 4, 5 and 6 sit (Kertosono-Nganjuk >75%, GI Caruban single
busbar, drop tegangan at the far end of the subsistem).

Risk #3 is a single-phi T/L bay at GI 150 kV Jayakertas, so that ruas is marked
Single Phi = Ya.

Run: python scripts/make_ss_kediri12_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # -- 500 kV GITET --
    dict(code="NGORO7", name="GITET Ngoro (Kediri)", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 NGORO7", name="IBT 1,2 Kediri 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus150="NGORO", trafo=2,
         simbol="2 IBT (unit 1,2)", kerawanan="1"),
    # -- 150 kV --
    dict(code="NGORO", name="Ngoro (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="4x60 MVA + 50 MVAR (bay 5 = MBL)"),
    dict(code="KDIRI5", name="Kediri (bus 150 kV)", type="Busbar GI", tier=2,
         simbol="injeksi 150 kV Kediri", kerawanan="2"),
    dict(code="JKTAS", name="Jayakertas", type="Busbar GI", tier=3,
         simbol="T/L bay Kediri single phi", kerawanan="3"),
    dict(code="KTSNO5", name="Kertosono (bus 150 kV)", type="Busbar GI", tier=3,
         simbol="150 kV Kertosono", kerawanan="2"),
    dict(code="SKTIH5", name="Sukorejo (bus 150 kV)", type="Busbar GI", tier=3,
         simbol="60 MVA (bay 6,7,8,9) + 50 MVAR"),
    dict(code="MJGNG", name="Mojoagung", type="Busbar GI", tier=3,
         simbol="60/30/60 MVA"),
    # -- IBT 150/70 kV Kertosono + jaringan 70 kV --
    dict(code="IBT 1 KTSNO5", name="IBT 150/70 kV Kertosono", type="IBT 3-Winding",
         tier=4, kv="150/70 kV", ibt="1", bus150="KTSNO4", trafo=2,
         simbol="2x100 MVA (unit 1,4)"),
    dict(code="KTSNO4", name="Kertosono (bus 70 kV)", type="Busbar GI", tier=4,
         kv=70, simbol="10 MVAR", kerawanan="4"),
    dict(code="NGJUK", name="Nganjuk", type="Busbar GI", tier=5, kv=70,
         simbol="30/30/30 MVA", kerawanan="4"),
    dict(code="CRBAN", name="Caruban", type="Busbar GI", tier=6, kv=70,
         simbol="single busbar; 30/30/30 MVA", kerawanan="5"),
    dict(code="PLOSO", name="Ploso", type="Busbar GI", tier=5, kv=70,
         simbol="30/20/30 MVA"),
    dict(code="BAGOR", name="Bagor", type="Busbar GI", tier=6, kv=70,
         simbol="ujung subsistem; drop tegangan", kerawanan="6"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, sp=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=sp, koridor=WIL)

LINES = [
    # -- 150 kV --
    L("NGORO", "KDIRI5", "SUTT Ngoro - Kediri", 1, 2),
    # kerawanan #2: Kediri-Jayakertas dan Kediri-Kertosono >60%
    L("KDIRI5", "JKTAS", "SUTT Kediri - Jayakertas", 2, 3, kno="2"),
    L("KDIRI5", "KTSNO5", "SUTT Kediri - Kertosono", 2, 3, kno="2"),
    # kerawanan #3: T/L Kediri di GI Jayakertas single phi
    L("JKTAS", "SKTIH5", "SUTT Jayakertas - Sukorejo (single phi)",
      3, 3, kno="3", sirkit=1, sp=True),
    L("NGORO", "SKTIH5", "SUTT Ngoro - Sukorejo", 1, 3),
    L("SKTIH5", "MJGNG", "SUTT Sukorejo - Mojoagung", 3, 3),
    # -- 70 kV --
    # kerawanan #4: Kertosono-Nganjuk 1,2 >75%, N-1 tidak terpenuhi
    L("KTSNO4", "NGJUK", "SUTT 70 kV Kertosono - Nganjuk 1,2", 4, 5, kv=70, kno="4"),
    L("NGJUK", "CRBAN", "SUTT 70 kV Nganjuk - Caruban", 5, 6, kv=70, kno="5"),
    L("KTSNO4", "PLOSO", "SUTT 70 kV Kertosono - Ploso", 4, 5, kv=70),
    L("NGJUK", "BAGOR", "SUTT 70 kV Nganjuk - Bagor", 5, 6, kv=70, kno="6"),
]

SPEC = dict(
    code="SS_KEDIRI12",
    name="Kediri 1,2",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.6 (PDF p.206-208); "
               "topologi dari Lampiran-4 Single Line Diagram Jawa Timur (PDF p.251)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(206, 208, expected=6),
)

if __name__ == "__main__":
    build_workbook(SPEC)
