"""samples/ss_slcg_ingest.xlsx  -- Subsistem Suralaya Unit #3 - Suralaya 1,2 - Cilegon 4.

Source: Buku Kerawanan SJB 2026 Sec 2.3 -- Gambar 2.2 (Peta Kerawanan, PDF p79)
+ Tabel 2.1 (3 titik kerawanan, PDF p80).

Traced as-is from Gambar 2.2. Two 500 kV injection groups (Suralaya Baru + Suralaya
via IBT unit 2 / unit 1 onto one 150 kV bus SRLYA; Cilegon Baru via IBT unit 4 onto
CLBRU). GITET/GI codes are the figure's labels.

Run: python scripts/make_ss_slcg_xlsx.py
"""
from __future__ import annotations

from _ss_xlsx_common import build_workbook

WIL = "Banten"

ASSETS = [
    # -- 500 kV GITET busbars. SRLYA / CLBRU share their code with the 150 kV bus
    #    of the same name -> the parser auto-splits them (GITET_SRLYA + SRLYA). --
    dict(code="SRLYABR", name="GITET Suralaya Baru", type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="SRLYA",   name="GITET Suralaya",      type="Busbar GITET", tier=1, kv="500 kV"),
    dict(code="CLBRU",   name="GITET Cilegon Baru",  type="Busbar GITET", tier=1, kv="500 kV"),
    # -- generation: PLTU Suralaya Unit 3, step-up onto GITET Suralaya Baru --
    dict(code="KIT_SRLYA_U3", name="PLTU Suralaya Unit 3", type="Pembangkit", tier=1, kv="500 kV"),
    # -- IBT 500/150 (code's last token = GITET busbar code; Bus 150 kV = the LV bus it feeds) --
    dict(code="IBT 2 SRLYABR", name="IBT 2 Suralaya Baru", type="IBT 3-Winding", tier=2,
         kv="500/150 kV", ibt="2", bus150="SRLYA", kerawanan="1"),
    dict(code="IBT 1 SRLYA", name="IBT 1 Suralaya", type="IBT 3-Winding", tier=2,
         kv="500/150 kV", ibt="1", bus150="SRLYA", kerawanan="1"),
    dict(code="IBT 4 CLBRU", name="IBT 4 Cilegon Baru", type="IBT 3-Winding", tier=2,
         kv="500/150 kV", ibt="4", bus150="CLBRU", kerawanan="2"),
    # -- 150 kV Tier-1 injection buses (same code as the GITET above -> auto-split) --
    dict(code="SRLYA", name="Suralaya (bus 150 kV)", type="Busbar GI", tier=1, kerawanan="1"),
    dict(code="CLBRU", name="Cilegon Baru (bus 150 kV)", type="Busbar GI", tier=1, kerawanan="2"),
    # -- Tier-2 150 kV --
    dict(code="SLRDA", name="Suralaya Dalam", type="Busbar GI", tier=2),
    dict(code="PENDO", name="Pendopo", type="Busbar GI", tier=2),
    dict(code="PENI",  name="Peni",    type="Busbar GI", tier=2, kerawanan="3"),
    dict(code="MCCI5", name="MCCI 5",  type="Busbar GI", tier=2, kerawanan="3"),
    dict(code="CLGON", name="Cilegon Lama", type="Busbar GI", tier=2, kerawanan="3"),
    # -- Tier-3 150 kV --
    dict(code="MTSUI", name="Mitsui", type="Busbar GI", tier=3, kerawanan="3"),
]

# KTT (captive customer) substations drawn as hanging dashed stubs on a parent bus
BAYS = [
    ("KTT_SLFDO1", "KTT SLFDO-1 (78 MVA)", "SLRDA", None),
    ("KTT_SLFDO2", "KTT SLFDO-2 (30 MVA)", "SLRDA", None),
    ("KTT_PENDO",  "KTT Pendopo (35 MVA)", "PENDO", None),
    ("KTT_PENI",   "KTT Peni (40 MVA)",    "PENI",  None),
    ("KTT_LCI",    "KTT LCI (115 MVA)",    "PENI",  None),
    ("KTT_MCCI",   "KTT MCCI (40 MVA)",    "MCCI5", None),
    ("KSTEL_CLBRU", "KTT KSTEL (di CLBRU)", "CLBRU", None),
    ("POSCO_CLBRU", "KTT POSCO (di CLBRU)", "CLBRU", None),
    ("KSTEL_CLGON", "KTT KSTEL (di CLGON)", "CLGON", None),
    ("KTT_MTSUI",  "KTT Mitsui (31 MVA)",  "MTSUI", None),
]

LINES = [
    # generation outlet: PLTU Suralaya Unit 3 -> GITET Suralaya Baru 500 kV
    dict(fr="KIT_SRLYA_U3", to="SRLYABR", name="Outlet PLTU Suralaya Unit 3", kv="500 kV",
         sirkit=2, tier_fr=1, tier_to=1, koridor=WIL),
    # SRLYA (Tier-1) -> Tier-2
    dict(fr="SRLYA", to="SLRDA", name="SUTT Suralaya - Suralaya Dalam", tier_fr=1, tier_to=2, koridor=WIL),
    dict(fr="SRLYA", to="PENDO", name="SUTT Suralaya - Pendopo", tier_fr=1, tier_to=2, koridor=WIL),
    dict(fr="SRLYA", to="PENI",  name="SUTT Suralaya - Peni (single phi -- kerawanan #3)",
         tier_fr=1, tier_to=2, kerawanan="3", koridor=WIL),
    dict(fr="SRLYA", to="MCCI5", name="SUTT Suralaya - MCCI (single phi -- kerawanan #3)",
         tier_fr=1, tier_to=2, kerawanan="3", koridor=WIL),
    # SLRDA <-> PENDO tie (Tier-2 bracket)
    dict(fr="SLRDA", to="PENDO", name="SUTT Suralaya Dalam - Pendopo (tie sehadap)",
         tier_fr=2, tier_to=2, koridor=WIL),
    # CLBRU (Tier-1) -> CLGON
    dict(fr="CLBRU", to="CLGON", name="SUTT Cilegon Baru - Cilegon Lama", tier_fr=1, tier_to=2, koridor=WIL),
    # Tier-2 -> Tier-3
    dict(fr="PENI",  to="MTSUI", name="SUTT Peni - Mitsui (single phi -- kerawanan #3)",
         tier_fr=2, tier_to=3, kerawanan="3", koridor=WIL),
    dict(fr="MTSUI", to="CLGON", name="SUTT Mitsui - Cilegon Lama (jalur Suralaya-MCCI-Cilegon)",
         tier_fr=3, tier_to=2, koridor=WIL),
    dict(fr="MCCI5", to="CLGON", name="SUTT MCCI - Cilegon Lama (single phi -- kerawanan #3)",
         tier_fr=2, tier_to=2, kerawanan="3", koridor=WIL),
]

RISKS = [
    dict(no=1, uit="JBB", category="N-1",
         kondisi="Pembebanan IBT-1,2 Suralaya tidak memenuhi kriteria N-1 saat PLTU Suralaya "
                 "unit-3 tidak beroperasi dan IBT-4 Cilegon masuk sub sistem Cilegon.",
         dampak="1. Pemeliharaan IBT sulit dilakukan. 2. Pertumbuhan beban menjadi terhambat. "
                "3. Terjadi pemadaman apabila trip salah satu IBT di Suralaya.",
         mitigasi="1. Sudah terpasang DS OLS IBT 1,2 Suralaya dengan target total 102 MW "
                  "(buku DS 2025). 2. Rencana penambahan target DS OLS SS Suralaya 1,2 total 137 MW. "
                  "3. Pemeliharaan IBT saat beban rendah dan saat PLTU Suralaya Unit-3 beroperasi.",
         usulan="Jangka Pendek: Uprating IBT-1 & 2 Suralaya dari 250 MVA menjadi 500 MVA "
                "(RUPTL 2025-2034, COD 2025)."),
    dict(no=2, uit="JBB", category="N-1-1",
         kondisi="Daya Mampu Pasok IBT Suralaya dan Cilegon tidak sama (IBT #1,2 Suralaya 250 MVA "
                 "sedangkan IBT #4 Cilegon 500 MVA).",
         dampak="1. Ketidakseimbangan beban antara IBT Suralaya dan IBT Cilegon. "
                "2. Kondisi N-1-1 (IBT Suralaya dan IBT Cilegon) berdampak overload pada IBT "
                "Suralaya yang beroperasi.",
         mitigasi="1. Sudah terpasang DS OLS IBT 1,2 Suralaya dengan target total 102 MW (buku DS 2025). "
                  "2. Rencana penambahan target DS OLS SS Suralaya 1,2 total 137 MW. "
                  "3. Pemeliharaan IBT saat beban rendah dan saat PLTU Suralaya Unit-3 beroperasi.",
         usulan="Jangka Pendek: Uprating IBT-1 & 2 Suralaya dari 250 MVA menjadi 500 MVA "
                "(RUPTL 2025-2034, COD 2026)."),
    dict(no=3, uit="JBB", category="N-1-1",
         kondisi="Ruas Penghantar Suralaya-MCCI-Cilegon dan Suralaya-Peni-Mitsui-Cilegon masih single phi.",
         dampak="1. Pemeliharaan Penghantar menjadi sulit dilakukan. "
                "2. Terjadi pemadaman apabila terdapat gangguan N-1-1.",
         mitigasi="1. Pemeliharaan Penghantar menyesuaikan jadwal dari KTT. "
                  "2. Pengaturan konfigurasi jaringan saat pemeliharaan untuk mengurangi dampak padam.",
         usulan="Jangka Menengah: Usulan Double phi pada ruas Suralaya s.d Cilegon Lama "
                "(kajian belum ada). Diusulkan COD Tahun 2030."),
]

SPEC = dict(
    code="SS_SLCG",
    name="Suralaya Unit #3 - Suralaya 1,2 - Cilegon 4",
    apb="UP2B Jakarta & Banten",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 2.3 (Gambar 2.2 + Tabel 2.1)",
    assets=ASSETS,
    lines=LINES,
    bays=BAYS,
    risks=RISKS,
)

if __name__ == "__main__":
    build_workbook(SPEC)
