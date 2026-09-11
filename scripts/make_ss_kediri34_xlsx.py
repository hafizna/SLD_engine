"""samples/ss_kediri34_ingest.xlsx -- Subsistem Kediri 3,4 (UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.7, Gambar 5.7 (Peta Kerawanan, PDF p.209)
and Tabel 5.5 (PDF p.210-217).

Eight tiers, the deepest sheet in the book, and the most 70 kV of any: THREE
separate 150/70 kV step-downs feed a large yellow network.

    GITET Kediri 500 kV -> IBT 3,4 -> KDIRI5 (Tier-1)
    PLTU Pacitan on its own Tier-1 bus, PCTAN

    150 kV: KDIRI5 - BNRAN5 - MJGNG / SKTIH5 / KTSNO5, and
            PCTAN - PNRGO - SYZAG - NGJUK5 - MNRJO5 - NGAWI
    70 kV : PNRGO4 - TGLEK - TLGPA - TLGNG (with PLTA Tlagong)
            BNRAN4 - TLGNG B / GGRAM / PARE
            MNRJO4 - MRGEN - MGTAN

NGAWI is the same GI the Pedan 3,4 sheet draws as its boundary toward UP2B Jawa
Timur, and PCTAN the same PLTU Pacitan bus Pedan 3,4 carries -- both traces meet
here.

Run: python scripts/make_ss_kediri34_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # ================= 500 kV injection =================
    dict(code="KDIRI7", name="GITET Kediri", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 3 KDIRI7", name="IBT 3,4 Kediri 500/150 kV",
         type="IBT 3-Winding", tier=2, kv="500/150 kV", ibt="3",
         bus_hv="KDIRI7", bus_lv="KDIRI5", trafo=2,
         simbol="2 IBT (unit 3,4)", kerawanan="1"),
    dict(code="KDIRI5", name="Kediri (bus 150 kV)", type="Busbar GI", tier=1),
    # -- Tier-1 kedua: PLTU Pacitan --
    dict(code="PCTAN5", name="PLTU Pacitan (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="KIT_PCTAN", name="PLTU Pacitan", type="Pembangkit", tier=1,
         kv="150 kV"),
    # ================= sisi Pacitan =================
    dict(code="NGTDI", name="Ngadi", type="Busbar GI", tier=2),
    dict(code="PCTAN", name="Pacitan", type="Busbar GI", tier=2, kerawanan="2"),
    dict(code="PNRGO", name="Ponorogo (bus 150 kV)", type="Busbar GI", tier=3),
    dict(code="SYZAG", name="Suryazag", type="Busbar GI", tier=3, kerawanan="4"),
    dict(code="NGJUK5", name="Nganjuk (bus 150 kV)", type="Busbar GI", tier=4,
         kerawanan="5;14"),
    dict(code="MNRJO5", name="Manisrejo (bus 150 kV)", type="Busbar GI", tier=5,
         kerawanan="6"),
    dict(code="NGAWI", name="Ngawi", type="Busbar GI", tier=6, kerawanan="15"),
    dict(code="SRGEN", name="Sragen", type="Busbar GI", tier=7,
         role="SOURCE_BOUNDARY", simbol="batas ke UP2B Jateng (SS Pedan 3,4)"),
    # ================= sisi Kediri 150 kV =================
    dict(code="BNRAN5", name="Banaran (bus 150 kV)", type="Busbar GI", tier=2,
         kerawanan="3"),
    dict(code="MJGNG", name="Mojoagung", type="Busbar GI", tier=3),
    dict(code="SKTIH5", name="Sukorejo (bus 150 kV)", type="Busbar GI", tier=4),
    dict(code="KTSNO5", name="Kertosono (bus 150 kV)", type="Busbar GI", tier=5),
    # ================= 70 kV: tiga IBT 150/70 =================
    dict(code="IBT 1 PNRGO", name="IBT 150/70 kV Ponorogo", type="IBT 3-Winding",
         tier=4, kv="150/70 kV", ibt="1", bus_hv="PNRGO", bus_lv="PNRGO4",
         trafo=1, simbol="IBT 150/70 kV; beban 73%", kerawanan="6"),
    dict(code="PNRGO4", name="Ponorogo (bus 70 kV)", type="Busbar GI",
         tier=4, kv=70),
    dict(code="TGLEK", name="Trenggalek", type="Busbar GI", tier=5, kv=70,
         kerawanan="9"),
    dict(code="TLGPA", name="Tulungagung Pagerwojo", type="Busbar GI",
         tier=6, kv=70, kerawanan="11"),
    dict(code="TLGNGA", name="Tlagong (seksi A)", type="Busbar GI",
         tier=7, kv=70, simbol="seksi A"),
    dict(code="KIT_TLGNG", name="PLTA Tlagong", type="Pembangkit", tier=6,
         kv="70 kV"),
    dict(code="IBT 1 BNRAN5", name="IBT 1,3 dan 2,6 Banaran 150/70 kV",
         type="IBT 3-Winding", tier=3, kv="150/70 kV", ibt="1",
         bus_hv="BNRAN5", bus_lv="BNRAN4", trafo=2,
         simbol="IBT 1,3 (44%) dan 2,6 (47%)", kerawanan="7;8"),
    dict(code="BNRAN4", name="Banaran (bus 70 kV)", type="Busbar GI",
         tier=3, kv=70),
    dict(code="TLGNGB", name="Tlagong (seksi B)", type="Busbar GI",
         tier=4, kv=70, simbol="seksi B"),
    dict(code="GGRAM", name="Gudang Garam", type="Busbar GI", tier=4, kv=70),
    # Risk 10 is "GI 70 kV Pare hanya single Busbar", risk 11 its loading.
    dict(code="PARE", name="Pare", type="Busbar GI", tier=4, kv=70,
         simbol="single busbar", kerawanan="10;11"),
    dict(code="IBT 1 MNRJO5", name="IBT 1,3 dan 2 Manisrejo 150/70 kV",
         type="IBT 3-Winding", tier=6, kv="150/70 kV", ibt="1",
         bus_hv="MNRJO5", bus_lv="MNRJO4", trafo=2,
         simbol="IBT 1,3 dan 2", kerawanan="12"),
    dict(code="MNRJO4", name="Manisrejo (bus 70 kV)", type="Busbar GI",
         tier=6, kv=70),
    dict(code="MRGEN", name="Mergen", type="Busbar GI", tier=7, kv=70,
         kerawanan="13"),
    dict(code="MGTAN", name="Magetan", type="Busbar GI", tier=8, kv=70,
         kerawanan="14"),
    dict(code="DLOPO", name="Dolopo", type="Busbar GI", tier=5, kv=70,
         kerawanan="11"),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("KIT_PCTAN", "PCTAN5", "Outlet PLTU Pacitan", 1, 1, sirkit=1),
    L("KIT_TLGNG", "TLGPA", "Outlet PLTA Tlagong", 6, 6, kv=70, sirkit=1),
    # ================= sisi Pacitan 150 kV =================
    L("PCTAN5", "NGTDI", "SUTT PLTU Pacitan - Ngadi", 1, 2, sirkit=1),
    L("PCTAN5", "PCTAN", "SUTT PLTU Pacitan - Pacitan", 1, 2, kno="2"),
    L("PCTAN", "PNRGO", "SUTT Pacitan - Ponorogo", 2, 3),
    L("PNRGO", "SYZAG", "SUTT Ponorogo - Suryazag", 3, 3, kno="4"),
    L("SYZAG", "NGJUK5", "SUTT Suryazag - Nganjuk", 3, 4, kno="5"),
    L("NGJUK5", "MNRJO5", "SUTT Nganjuk - Manisrejo", 4, 5, kno="6"),
    L("MNRJO5", "NGAWI", "SUTT Manisrejo - Ngawi", 5, 6, kno="15"),
    L("NGAWI", "SRGEN", "SUTT Ngawi - Sragen (arah UP2B Jateng)", 6, 7, sirkit=1),
    # ================= sisi Kediri 150 kV =================
    L("KDIRI5", "BNRAN5", "SUTT Kediri - Banaran", 1, 2, kno="3"),
    L("BNRAN5", "MJGNG", "SUTT Banaran - Mojoagung", 2, 3),
    L("BNRAN5", "SKTIH5", "SUTT Banaran - Sukorejo", 2, 4),
    L("MJGNG", "KTSNO5", "SUTT Mojoagung - Kertosono", 3, 5),
    L("SKTIH5", "KTSNO5", "SUTT Sukorejo - Kertosono", 4, 5),
    # ================= 70 kV Ponorogo =================
    L("PNRGO4", "TGLEK", "SUTT 70 kV Ponorogo - Trenggalek", 4, 5, kv=70, kno="9"),
    L("PNRGO4", "DLOPO", "SUTT 70 kV Ponorogo - Dolopo", 4, 5, kv=70, kno="11"),
    L("TGLEK", "TLGPA", "SUTT 70 kV Trenggalek - Tulungagung Pagerwojo",
      5, 6, kv=70, kno="11"),
    L("TLGPA", "TLGNGA", "SUTT 70 kV Tulungagung Pagerwojo - Tlagong A",
      6, 7, kv=70),
    # ================= 70 kV Banaran =================
    L("BNRAN4", "TLGNGB", "SUTT 70 kV Banaran - Tlagong B", 3, 4, kv=70),
    L("BNRAN4", "GGRAM", "SUTT 70 kV Banaran - Gudang Garam", 3, 4, kv=70),
    L("BNRAN4", "PARE", "SUTT 70 kV Banaran - Pare", 3, 4, kv=70, kno="11"),
    # ================= 70 kV Manisrejo =================
    L("MNRJO4", "MRGEN", "SUTT 70 kV Manisrejo - Mergen", 6, 7, kv=70, kno="13"),
    L("MRGEN", "MGTAN", "SUTT 70 kV Mergen - Magetan", 7, 8, kv=70, kno="14"),
]

SPEC = dict(
    code="SS_KEDIRI34",
    name="Kediri 3,4",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.7 (Tabel 5.5, PDF p.210-217); "
               "topologi dari Gambar 5.7 Peta Kerawanan (PDF p.209)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(210, 217, expected=15),
)

if __name__ == "__main__":
    build_workbook(SPEC)
