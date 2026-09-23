"""samples/ss_bengkulu_ingest.xlsx -- Subsistem Bengkulu (Sumbagsel).

Source: Kerawanan Sistem Sumatera, UIP3B Sumatera, Sep 2026 (the pptx deck),
slide 16 "Peta Kerawanan Sistem Bengkulu" (tier SLD, ppt/media/image51.png)
and the risk table on slide 17.

The first Sumatera sheet, and the conventions every other one follows:

* Colours are the deck's own (legend on slide 19): 275 kV light blue,
  150 kV red, 70 kV yellow. Green is a generator, as in the SJB book; the
  brown circle is PLTM Ketaun, a generator all the same.
* A bare code is the 150 kV bus. A site drawn at two voltages gets a text
  suffix on the other one -- `_275`, `_70` -- never a digit: the deck's own
  codes already end in name digits (SMSL8, SBSL1, SIPAN1).
* `multi_pin`: every "kerawanan" number below marks where the finding SITS,
  i.e. the objects its Kondisi names, never the GIs it knocks out. A finding
  naming a pembangkit is pinned on that generator's own GI, because a pin on a
  generator node cannot be drawn.

    GITET Lubuk Linggau 275 kV -> IBT 275/150 -> LBGAU (Tier-1, boundary: the
    GI is Sumsel's; the Sumsel sheet draws it too, arrowing "PKLNG (BENGKULU)")
    PLTA Musi -> MUSI, PLTU Bengkulu -> BGKLU            (150 kV, Tier-1)
    PLTA Air Putih -> ARPTH, PLTA Tes -> TES, PLTM Ketaun -> KTAUN   (70 kV)

    150 kV: LBGAU - PKLNG - PBAI - ARMUR, MUSI - PKLNG, BGKLU - PBAI
    70 kV : ARPTH - TES; TES - KTAUN - PKLNG_70 and TES - PKLNG_70 direct
            (the "single phi" of risk #4: one circuit of Tes-Pekalongan is
            looped into Ketaun, the other runs straight through); PKLNG_70 -
            SKMDU; PKLNG -> IBT 150/70 -> PKLNG_70

Circuit counts: the deck draws every ruas as one stroke, so the count comes
from the risk text -- "TRIP 2 sirkit" on #1, #2, #3, #5, #6 -- and the single
phi of #4 makes Tes-Ketaun, Ketaun-Pekalongan and the Tes-Pekalongan bypass
one circuit each.

Run: python scripts/make_ss_bengkulu_xlsx.py
"""
from __future__ import annotations

from _kerawanan_sumatera import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Bengkulu"

ASSETS = [
    # ================= 275 kV injection (Lubuk Linggau, Sumsel's GITET) ======
    dict(code="LBGAU_275", name="GITET Lubuk Linggau (275 kV)", type="Busbar GITET",
         tier=1, kv="275 kV", role="SOURCE_BOUNDARY",
         simbol="GITET subsistem Sumsel / backbone 275 kV"),
    dict(code="IBT 1 LBGAU_275", name="IBT Lubuk Linggau 275/150 kV",
         type="IBT 3-Winding", tier=2, kv="275/150 kV", ibt="1",
         bus_hv="LBGAU_275", bus_lv="LBGAU", trafo=1,
         simbol="satu simbol IBT digambar; nomor unit tidak disebut deck"),
    dict(code="LBGAU", name="Lubuk Linggau (bus 150 kV)", type="Busbar GI",
         tier=1, role="SOURCE_BOUNDARY", simbol="GI subsistem Sumsel"),
    # ================= 150 kV generation =================
    dict(code="KIT_MUSI", name="PLTA Musi", type="Pembangkit", tier=1, kv="150 kV"),
    dict(code="MUSI", name="Musi", type="Busbar GI", tier=1, trafo=1, kerawanan="6"),
    dict(code="KIT_BGKLU", name="PLTU Bengkulu", type="Pembangkit", tier=1, kv="150 kV"),
    dict(code="BGKLU", name="PLTU Bengkulu (bus 150 kV)", type="Busbar GI", tier=1,
         trafo=1, kerawanan="6"),
    # ================= 150 kV network =================
    dict(code="PKLNG", name="Pekalongan (bus 150 kV)", type="Busbar GI", tier=2, trafo=1),
    dict(code="PBAI", name="Pulau Baai", type="Busbar GI", tier=2, trafo=1),
    dict(code="ARMUR", name="Argamakmur", type="Busbar GI", tier=3, trafo=1),
    # ================= 70 kV =================
    dict(code="IBT 1 PKLNG", name="IBT Pekalongan 150/70 kV", type="IBT 3-Winding",
         tier=2, kv="150/70 kV", ibt="1", bus_hv="PKLNG", bus_lv="PKLNG_70", trafo=1,
         simbol="IBT 150/70 kV; satu simbol digambar"),
    dict(code="PKLNG_70", name="Pekalongan (bus 70 kV)", type="Busbar GI", tier=2,
         kv=70, trafo=1),
    dict(code="KIT_ARPTH", name="PLTA Air Putih", type="Pembangkit", tier=1, kv="70 kV"),
    dict(code="ARPTH", name="Air Putih", type="Busbar GI", tier=1, kv=70),
    dict(code="KIT_TES", name="PLTA Tes", type="Pembangkit", tier=1, kv="70 kV"),
    # Risk #4 names GI Ketaun and GI Tes as still single busbar.
    dict(code="TES", name="Tes", type="Busbar GI", tier=1, kv=70,
         simbol="single busbar", kerawanan="4"),
    dict(code="KIT_KTAUN", name="PLTM Ketaun", type="Pembangkit", tier=1, kv="70 kV"),
    dict(code="KTAUN", name="Ketaun", type="Busbar GI", tier=1, kv=70, trafo=1,
         simbol="single busbar", kerawanan="4"),
    dict(code="SKMDU", name="Sukamerindu", type="Busbar GI", tier=3, kv=70,
         trafo=1, kapasitor=1, simbol="kapasitor 1x50 MVAr", kerawanan="7"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    sirkit=sirkit, koridor=WIL)

LINES = [
    L("KIT_MUSI", "MUSI", "Outlet PLTA Musi", 1, 1, sirkit=1),
    L("KIT_BGKLU", "BGKLU", "Outlet PLTU Bengkulu", 1, 1, sirkit=1),
    L("KIT_ARPTH", "ARPTH", "Outlet PLTA Air Putih", 1, 1, kv=70, sirkit=1),
    L("KIT_TES", "TES", "Outlet PLTA Tes", 1, 1, kv=70, sirkit=1),
    L("KIT_KTAUN", "KTAUN", "Outlet PLTM Ketaun", 1, 1, kv=70, sirkit=1),
    # ================= 150 kV =================
    L("LBGAU", "PKLNG", "SUTT 150 kV Lubuk Linggau - Pekalongan", 1, 2, kno="1"),
    L("PKLNG", "PBAI", "SUTT 150 kV Pekalongan - Pulau Baai", 2, 2, kno="1"),
    L("PBAI", "ARMUR", "SUTT 150 kV Pulau Baai - Argamakmur", 2, 3, kno="2"),
    L("MUSI", "PKLNG", "SUTT 150 kV Musi - Pekalongan", 1, 2),
    L("BGKLU", "PBAI", "SUTT 150 kV PLTU Bengkulu - Pulau Baai", 1, 2),
    # ================= 70 kV =================
    L("ARPTH", "TES", "SUTT 70 kV Air Putih - Tes", 1, 1, kv=70, kno="3"),
    L("TES", "KTAUN", "SUTT 70 kV Tes - Ketaun (single phi)", 1, 1, kv=70,
      kno="3;4", sirkit=1),
    L("KTAUN", "PKLNG_70", "SUTT 70 kV Ketaun - Pekalongan (single phi)", 1, 2,
      kv=70, kno="3;4", sirkit=1),
    L("TES", "PKLNG_70", "SUTT 70 kV Tes - Pekalongan", 1, 2, kv=70, sirkit=1),
    L("PKLNG_70", "SKMDU", "SUTT 70 kV Pekalongan - Sukamerindu", 2, 3, kv=70, kno="5"),
]

SPEC = dict(
    code="SS_BENGKULU",
    name="Bengkulu",
    apb="Sumbagsel",
    wilayah=WIL,
    multi_pin=True,
    source_ref="Kerawanan Sistem Sumatera Sep 2026 (UIP3B Sumatera), slide 16 "
               "Peta Kerawanan Sistem Bengkulu; tabel risiko slide 17",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts("BENGKULU"),
)

if __name__ == "__main__":
    build_workbook(SPEC)
