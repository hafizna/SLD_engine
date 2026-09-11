"""samples/ss_krian12_gresik_ingest.xlsx -- Subsistem Krian 1,2 - Gresik 1,2
(UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.3, Gambar 5.3 (Peta Kerawanan, PDF p.179)
and Tabel 5.1 (PDF p.180-196). Completes UP2B Jawa Timur.

The biggest sheet in the book: 25 risks over thirteen tiers, covering Surabaya
and the whole Madura chain down to Sumenep.

Two 500 kV injections, each through IBT 1,2:
    GITET Krian  -> SBRAT5 (Surabaya Barat)
    GITET Gresik -> GRSIK5, with PLTU Gresik on GRLMA beside it

    Surabaya barat : SBRAT5 - KLANG / DARMO / SWHAN - KPANG / UDAAN / RNKUT /
                     GBONG - SBSEL / SLILO / HJAYA - KSARI / WKRMO / NGGEL /
                     KJRAN - SIMPG - GLMUR
    Surabaya timur : GRSIK5 / GRLMA - ALTAP / SGMDU / SKREP / WLMAR - PKMIA /
                     PERAK - UJUNG / PTISM - WARU5 - BDRAN5 / WARU4 / JSTEL
    Madura         : KDING - BKLAN - SAMPG - PKSAN - GULUK - SMNEP

BDRAN5 steps down to the 70 kV BDRAN bus feeding SDATI and MPION, the only
70 kV on this sheet.

Run: python scripts/make_ss_krian12_gresik_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # ================= 500 kV injections =================
    dict(code="KRIAN7", name="GITET Krian", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 KRIAN7", name="IBT 1,2 Krian 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="KRIAN7", bus_lv="SBRAT5",
         trafo=2, simbol="2 IBT (unit 1,2)", kerawanan="1"),
    dict(code="GRSIK7", name="GITET Gresik", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 GRSIK7", name="IBT 1,2 Gresik 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="GRSIK7", bus_lv="GRSIK5",
         trafo=2, simbol="2 IBT (unit 1,2)", kerawanan="2"),
    # ================= Tier-1 =================
    dict(code="SBRAT5", name="Surabaya Barat (bus 150 kV)", type="Busbar GI",
         tier=1, simbol="seksi A"),
    dict(code="GRSIK5", name="Gresik (bus 150 kV)", type="Busbar GI", tier=1),
    dict(code="GRLMA", name="Gresik Lama", type="Busbar GI", tier=1),
    dict(code="KIT_GRESIK", name="PLTU Gresik", type="Pembangkit", tier=1,
         kv="150 kV"),
    # ================= Tier-2 =================
    dict(code="KLANG", name="Kalang", type="Busbar GI", tier=2, kerawanan="3"),
    dict(code="DARMO", name="Darmo", type="Busbar GI", tier=2, kerawanan="4"),
    dict(code="TNDES", name="Tandes", type="Busbar GI", tier=2, kerawanan="5;6"),
    dict(code="ALTAP", name="Altap", type="Busbar GI", tier=2),
    dict(code="SGMDU", name="Segoromadu", type="Busbar GI", tier=2,
         simbol="seksi B"),
    dict(code="SKREP", name="Sukorejo Kreb", type="Busbar GI", tier=2,
         kerawanan="7"),
    dict(code="WLMAR", name="Wilmar", type="Busbar GI", tier=2, kerawanan="18"),
    # ================= Tier-3 =================
    dict(code="BAMBE", name="Bambe", type="Busbar GI", tier=3, kerawanan="10"),
    dict(code="SWHAN", name="Suwahan", type="Busbar GI", tier=3,
         kerawanan="8;9"),
    dict(code="PKMIA", name="Pakem Mia", type="Busbar GI", tier=3,
         kerawanan="11"),
    dict(code="PERAK", name="Perak", type="Busbar GI", tier=3, kerawanan="19"),
    # ================= Tier-4 =================
    dict(code="KPANG", name="Kepatihan", type="Busbar GI", tier=4),
    dict(code="UDAAN", name="Undaan", type="Busbar GI", tier=4),
    dict(code="KRBAN", name="Karangbanan", type="Busbar GI", tier=4,
         kerawanan="4"),
    dict(code="GNSRI", name="Gunungsari", type="Busbar GI", tier=4),
    dict(code="UJUNG", name="Ujung", type="Busbar GI", tier=4, kerawanan="18"),
    dict(code="PTISM", name="Petrokimia", type="Busbar GI", tier=4),
    # ================= Tier-5 =================
    dict(code="RNKUT", name="Rungkut", type="Busbar GI", tier=5,
         simbol="seksi A/B"),
    dict(code="GBONG", name="Gubeng", type="Busbar GI", tier=5, kerawanan="12"),
    dict(code="WARU5", name="Waru (bus 150 kV)", type="Busbar GI", tier=5),
    # ================= Tier-6 =================
    dict(code="SBSEL", name="Surabaya Selatan", type="Busbar GI", tier=6),
    dict(code="SLILO", name="Sukolilo", type="Busbar GI", tier=6, kerawanan="16"),
    dict(code="HJAYA", name="Hayam Jaya", type="Busbar GI", tier=6),
    dict(code="BDRAN5", name="Buduran (bus 150 kV)", type="Busbar GI", tier=6,
         kerawanan="13;14"),
    dict(code="IBT 1 WARU5", name="IBT 150/70 kV Waru", type="IBT 3-Winding",
         tier=6, kv="150/70 kV", ibt="1", bus_hv="WARU5", bus_lv="WARU4",
         trafo=1, simbol="IBT 150/70 kV"),
    dict(code="WARU4", name="Waru (bus 70 kV)", type="Busbar GI", tier=6, kv=70),
    dict(code="JSTEL", name="Jawa Steel", type="Busbar GI", tier=6),
    # ================= Tier-7 =================
    dict(code="KSARI", name="Kesari", type="Busbar GI", tier=7),
    dict(code="WKRMO", name="Wonokromo", type="Busbar GI", tier=7),
    dict(code="NGGEL", name="Nganggel", type="Busbar GI", tier=7,
         kerawanan="17"),
    dict(code="KJRAN", name="Kejuron", type="Busbar GI", tier=7),
    dict(code="IBT 1 BDRAN5", name="IBT 1,7 Buduran 150/70 kV",
         type="IBT 3-Winding", tier=7, kv="150/70 kV", ibt="1",
         bus_hv="BDRAN5", bus_lv="BDRAN", trafo=2, simbol="IBT 1 dan 7",
         kerawanan="13"),
    dict(code="BDRAN", name="Buduran (bus 70 kV)", type="Busbar GI",
         tier=7, kv=70),
    dict(code="NBRAN5", name="New Buduran", type="Busbar GI", tier=7),
    # ================= Tier-8 =================
    dict(code="SIMPG", name="Simpang", type="Busbar GI", tier=8),
    dict(code="SDRJO", name="Sidoarjo", type="Busbar GI", tier=8),
    dict(code="SDATI", name="Sedati", type="Busbar GI", tier=8, kv=70),
    dict(code="MPION", name="Mpion", type="Busbar GI", tier=8, kv=70,
         kerawanan="15"),
    dict(code="KDING", name="Kedinding", type="Busbar GI", tier=8,
         kerawanan="22;23"),
    # ================= Tier-9 ke bawah: Madura =================
    dict(code="GLMUR", name="Gelam Ur", type="Busbar GI", tier=9,
         kerawanan="20"),
    dict(code="BKLAN", name="Bangkalan", type="Busbar GI", tier=9,
         simbol="seksi A/B", kerawanan="21;22"),
    dict(code="SAMPG", name="Sampang", type="Busbar GI", tier=10,
         kerawanan="23"),
    dict(code="PKSAN", name="Pamekasan", type="Busbar GI", tier=11,
         kerawanan="24"),
    dict(code="GULUK", name="Guluk-Guluk", type="Busbar GI", tier=12,
         kerawanan="25"),
    dict(code="SMNEP", name="Sumenep", type="Busbar GI", tier=13),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, koridor=WIL)

LINES = [
    L("KIT_GRESIK", "GRLMA", "Outlet PLTU Gresik", 1, 1, sirkit=1),
    L("GRSIK5", "GRLMA", "SUTT Gresik - Gresik Lama", 1, 1),
    # ================= sisi Surabaya Barat =================
    L("SBRAT5", "KLANG", "SUTT Surabaya Barat - Kalang", 1, 2, kno="3"),
    L("SBRAT5", "DARMO", "SUTT Surabaya Barat - Darmo", 1, 2, kno="4"),
    L("SBRAT5", "TNDES", "SUTT Surabaya Barat - Tandes", 1, 2, kno="5"),
    L("KLANG", "BAMBE", "SUTT Kalang - Bambe", 2, 3, kno="10"),
    L("DARMO", "SWHAN", "SUTT Darmo - Suwahan", 2, 3, kno="8"),
    L("TNDES", "SWHAN", "SUTT Tandes - Suwahan", 2, 3, kno="9"),
    L("BAMBE", "KPANG", "SUTT Bambe - Kepatihan", 3, 4),
    L("BAMBE", "UDAAN", "SUTT Bambe - Undaan", 3, 4),
    L("SWHAN", "KRBAN", "SUTT Suwahan - Karangbanan", 3, 4, kno="4"),
    L("TNDES", "GNSRI", "SUTT Tandes - Gunungsari", 2, 4),
    L("KPANG", "RNKUT", "SUTT Kepatihan - Rungkut", 4, 5),
    L("KRBAN", "GBONG", "SUTT Karangbanan - Gubeng", 4, 5, kno="12"),
    L("KLANG", "SBSEL", "SUTT Kalang - Surabaya Selatan", 2, 6),
    L("RNKUT", "SLILO", "SUTT Rungkut - Sukolilo", 5, 6, kno="16"),
    L("GBONG", "HJAYA", "SUTT Gubeng - Hayam Jaya", 5, 6),
    L("SBSEL", "KSARI", "SUTT Surabaya Selatan - Kesari", 6, 7),
    L("SLILO", "WKRMO", "SUTT Sukolilo - Wonokromo", 6, 7),
    L("HJAYA", "NGGEL", "SUTT Hayam Jaya - Nganggel", 6, 7, kno="17"),
    L("HJAYA", "KJRAN", "SUTT Hayam Jaya - Kejuron", 6, 7),
    L("NGGEL", "SIMPG", "SUTT Nganggel - Simpang", 7, 8),
    L("KJRAN", "GLMUR", "SUTT Kejuron - Gelam Ur", 7, 9, kno="20"),
    # ================= sisi Gresik =================
    L("GRLMA", "ALTAP", "SUTT Gresik Lama - Altap", 1, 2),
    L("GRLMA", "SGMDU", "SUTT Gresik Lama - Segoromadu", 1, 2),
    L("GRLMA", "SKREP", "SUTT Gresik Lama - Sukorejo Kreb", 1, 2, kno="7"),
    L("GRLMA", "WLMAR", "SUTT Gresik Lama - Wilmar", 1, 2, kno="18"),
    L("SGMDU", "PKMIA", "SUTT Segoromadu - Pakem Mia", 2, 3, kno="11"),
    L("WLMAR", "PERAK", "SUTT Wilmar - Perak", 2, 3, kno="19"),
    L("WLMAR", "UJUNG", "SUTT Wilmar - Ujung", 2, 4, kno="18"),
    L("PERAK", "PTISM", "SUTT Perak - Petrokimia", 3, 4),
    L("SKREP", "WARU5", "SUTT Sukorejo Kreb - Waru", 2, 5),
    L("GNSRI", "WARU5", "SUTT Gunungsari - Waru", 4, 5),
    L("WARU5", "BDRAN5", "SUTT Waru - Buduran", 5, 6, kno="13"),
    L("WARU5", "JSTEL", "SUTT Waru - Jawa Steel", 5, 6, kno="14"),
    L("BDRAN5", "NBRAN5", "SUTT Buduran - New Buduran", 6, 7),
    L("NBRAN5", "SDRJO", "SUTT New Buduran - Sidoarjo", 7, 8),
    # -- 70 kV Buduran --
    L("BDRAN", "SDATI", "SUTT 70 kV Buduran - Sedati", 7, 8, kv=70),
    L("BDRAN", "MPION", "SUTT 70 kV Buduran - Mpion", 7, 8, kv=70, kno="15"),
    # ================= Madura =================
    L("UJUNG", "KDING", "SUTT Ujung - Kedinding", 4, 8, kno="22"),
    L("KDING", "BKLAN", "SUTT Kedinding - Bangkalan", 8, 9, kno="21;22"),
    L("BKLAN", "SAMPG", "SUTT Bangkalan - Sampang", 9, 10, kno="23"),
    L("SAMPG", "PKSAN", "SUTT Sampang - Pamekasan", 10, 11, kno="24"),
    L("PKSAN", "GULUK", "SUTT Pamekasan - Guluk-Guluk", 11, 12, kno="25"),
    L("GULUK", "SMNEP", "SUTT Guluk-Guluk - Sumenep", 12, 13),
]

SPEC = dict(
    code="SS_KRIAN12_GRESIK",
    name="Krian 1,2 - Gresik 1,2",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.3 (Tabel 5.1, PDF p.180-196); "
               "topologi dari Gambar 5.3 Peta Kerawanan (PDF p.179)",
    assets=ASSETS,
    lines=LINES,
    risks=as_risk_dicts(180, 196, expected=25),
)

if __name__ == "__main__":
    build_workbook(SPEC)
