"""samples/ss_byoli_ingest.xlsx -- Subsistem Boyolali 1,2 (UP2B Jateng & DIY).

Source: Buku Kerawanan SJB 2026 Sec 4.9 (Tabel 4.7, PDF p.175-178) for the risk
table, and Lampiran-3 (PDF p.250) for the topology -- Boyolali is the dark-green
block in the middle-right of that drawing.

GITET Boyolali 500 kV (BYOLI) takes SUTET bays toward Ungaran 1 and Pedan 2 and
steps down through IBT 1,2 (2x500 MVA) onto a sectionalised 150 kV bus drawn
with four sections A/B/C/D and two bus couplers (Kopel A, Kopel B). The 150 kV
side fans out to BRNGI, BDONO, MJNGO, MKRAN and JAJAR.

Risks 1-4 all hinge on that single IBT pair: N-1 is not met when the subsistem
supplies Kalasan/Bantul/Semanu (#1), and looping toward Tanjungjati or Ungaran
pushes IBT-3 Ungaran and SUTT Ungaran-Jelok into overload (#2, #4). Those two
remote assets are outside this subsistem, so the risks pin to the SUTET bays
that carry the loop rather than to assets this sheet does not own.

Run: python scripts/make_ss_byoli_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Tengah"

ASSETS = [
    # -- 500 kV GITET --
    dict(code="BYOLI7", name="GITET Boyolali", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="IBT 1 BYOLI7", name="IBT 1,2 Boyolali 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="BYOLI7", bus_lv="BYOLI", trafo=2,
         simbol="2 IBT x 500 MVA (unit 1,2)", kerawanan="1"),
    # -- 150 kV injection bus: 4 seksi (A/B/C/D) + Kopel A / Kopel B --
    dict(code="BYOLI", name="Boyolali (bus 150 kV)", type="Busbar GI", tier=1,
         simbol="4 seksi bus (A/B/C/D) + Kopel A, Kopel B; 60 MVA"),
    # -- 150 kV fan-out --
    dict(code="BRNGI", name="Boyolali Ring / Banaran", type="Busbar GI", tier=2,
         simbol="2x60 MVA"),
    dict(code="BDONO", name="Bendono", type="Busbar GI", tier=2,
         simbol="3x60 MVA + 50 MVAR"),
    dict(code="MJNGO", name="Mojosongo", type="Busbar GI", tier=2,
         simbol="2x60 MVA", kerawanan="3"),
    dict(code="MKRAN", name="Mangkunegaran", type="Busbar GI", tier=3,
         simbol="2x60 MVA", kerawanan="3"),
    dict(code="JAJAR", name="Jajar", type="Busbar GI", tier=3,
         simbol="3x60 MVA; batas ke Subsistem Pedan 1,2", role="SOURCE_BOUNDARY"),
    dict(code="GDRJO", name="Gondangrejo", type="Busbar GI", tier=3,
         simbol="2x60 MVA", kerawanan="3"),
]

# 500 kV SUTET bays -- the remote GITETs live on other subsistem sheets.
# Risks 2 and 4 are about looping through these, so they carry the kerawanan no.
BAYS = [
    ("UNGA7", "GITET Ungaran (500 kV)", "BYOLI7", "2", 1),
    ("PDAN7", "GITET Pedan (500 kV)", "BYOLI7", "4", 2),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("BYOLI", "BRNGI", "SUTT Boyolali - Banaran", 1, 2),
    L("BYOLI", "BDONO", "SUTT Boyolali - Bendono", 1, 2),
    # kerawanan #3: Boyolali-Mojosongo N-1 tidak terpenuhi saat memasok
    # GI Mangkunegaran dan Gondangrejo.
    L("BYOLI", "MJNGO", "SUTT Boyolali - Mojosongo", 1, 2, kno="3"),
    L("MJNGO", "MKRAN", "SUTT Mojosongo - Mangkunegaran", 2, 3, kno="3"),
    L("MJNGO", "GDRJO", "SUTT Mojosongo - Gondangrejo", 2, 3, kno="3"),
    L("BDONO", "JAJAR", "SUTT Bendono - Jajar", 2, 3),
    L("BYOLI", "JAJAR", "SUTT Boyolali - Jajar", 1, 3),
]

SPEC = dict(
    code="SS_BYOLI",
    name="Boyolali 1,2",
    apb="UP2B Jawa Tengah & DIY",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 4.9 (Tabel 4.7, PDF p.175-178); "
               "topologi dari Lampiran-3 Single Line Diagram Jawa Tengah & DIY (PDF p.250)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=as_risk_dicts(176, 178, expected=4),
)

if __name__ == "__main__":
    build_workbook(SPEC)
