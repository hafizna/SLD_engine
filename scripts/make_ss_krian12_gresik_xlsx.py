"""samples/ss_krian12_gresik_ingest.xlsx -- Subsistem Krian 1,2 - Gresik 1,2
(UP2B Jawa Timur).

Source: Buku Kerawanan SJB 2026 Sec 5.3, Gambar 5.3 (Peta Kerawanan, PDF p.179)
and Tabel 5.1 (PDF p.180-196). Completes UP2B Jawa Timur.

The biggest sheet in the book: 25 risks over thirteen tiers, covering Surabaya
and the whole Madura chain down to Sumenep. Re-traced 1 Oct 2026 at zoom 10-12;
the first trace had misread several ruas and most GI names.

Two 500 kV injections, each through IBT 1,2, plus PLTGU Gresik:
    GITET Krian  -> SBRAT5 (Surabaya Barat = the book's "Krian" 150 kV)
    GITET Gresik -> GRSIK5 (the book's "Gresik Baru")
    PLTGU Gresik -> GRLMA (Gresik Lama)

Reading the figure:
* A line drawn straight THROUGH a busbar is an in-out at that GI. The risk
  text confirms it every time it can be checked: Krian-Darmogrande-Waru (#5),
  Tandes-Sawahan-Gunungsari-Waru (#8/#4), Waru-Rungkut-Sukolilo (#12/#16),
  Tandes-Perak-Ujung (#18/#19).
* Dashed ruas are named SKTT so the SLD draws them dashed. They feed GIs that
  have no other supply (UDAAN, KRBAN, GBONG, HJAYA, PTISM), so they cannot be
  normally-open ties. SBRAT5-KLANG is SKTT per the #3 text although the figure
  draws it solid.
* "WARU4" is a bare label in the figure: no bus and no IBT drawn, so it is
  left out rather than given an invented connection.
* Pin 23 is drawn twice: on Bangkalan-Sampang (what #23 names) and on the
  Kenjeran-Kedinding ruas. Both are kept, as drawn.
* GI names come from the risk text where it names them. Codes the book never
  spells out stay "GI <kode>" instead of a guessed name.

Run: python scripts/make_ss_krian12_gresik_xlsx.py
"""
from __future__ import annotations

from _kerawanan_tables import as_risk_dicts
from _ss_xlsx_common import build_workbook

WIL = "Jawa Timur"

ASSETS = [
    # ================= 500 kV injections + pembangkit =================
    dict(code="KRIAN7", name="GITET Krian", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 KRIAN7", name="IBT 1 Krian 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="KRIAN7", bus_lv="SBRAT5",
         trafo=1, kerawanan="1"),
    dict(code="IBT 2 KRIAN7", name="IBT 2 Krian 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="KRIAN7", bus_lv="SBRAT5",
         trafo=1, kerawanan="1"),
    dict(code="GRSIK7", name="GITET Gresik", type="Busbar GITET",
         tier=1, kv="500 kV"),
    dict(code="IBT 1 GRSIK7", name="IBT 1 Gresik 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="1", bus_hv="GRSIK7", bus_lv="GRSIK5",
         trafo=1, kerawanan="2"),
    dict(code="IBT 2 GRSIK7", name="IBT 2 Gresik 500/150 kV", type="IBT 3-Winding",
         tier=2, kv="500/150 kV", ibt="2", bus_hv="GRSIK7", bus_lv="GRSIK5",
         trafo=1, kerawanan="2"),
    dict(code="KIT_GRESIK", name="PLTGU Gresik", type="Pembangkit", tier=1,
         kv="150 kV"),
    # ================= Tier-1 =================
    dict(code="SBRAT5", name="Surabaya Barat / Krian (bus 150 kV)",
         type="Busbar GI", tier=1, simbol="seksi A"),
    dict(code="GRSIK5", name="Gresik Baru (bus 150 kV)", type="Busbar GI",
         tier=1),
    dict(code="GRLMA", name="Gresik Lama", type="Busbar GI", tier=1),
    # ================= Tier-2 =================
    dict(code="KLANG", name="Karangpilang", type="Busbar GI", tier=2),
    dict(code="DARMO", name="Darmo Grande", type="Busbar GI", tier=2),
    dict(code="TNDES", name="Tandes", type="Busbar GI", tier=2),
    dict(code="ALTAP", name="GI ALTAP", type="Busbar GI", tier=2),
    dict(code="SGMDU", name="Segoromadu", type="Busbar GI", tier=2,
         simbol="seksi B"),
    dict(code="SKREP", name="Sambikerep", type="Busbar GI", tier=2),
    dict(code="WLMAR", name="Wilmar", type="Busbar GI", tier=2),
    # ================= Tier-3 =================
    dict(code="BAMBE", name="Bambe", type="Busbar GI", tier=3),
    dict(code="SWHAN", name="Sawahan", type="Busbar GI", tier=3, kerawanan="9"),
    dict(code="PKMIA", name="Petrokimia", type="Busbar GI", tier=3),
    dict(code="PERAK", name="Perak", type="Busbar GI", tier=3, kerawanan="19"),
    # ================= Tier-4 =================
    dict(code="KPANG", name="GI KPANG", type="Busbar GI", tier=4),
    dict(code="UDAAN", name="Undaan", type="Busbar GI", tier=4),
    dict(code="KRBAN", name="Krembangan", type="Busbar GI", tier=4),
    dict(code="GNSRI", name="Gunungsari", type="Busbar GI", tier=4),
    dict(code="UJUNG", name="Ujung", type="Busbar GI", tier=4),
    dict(code="PTISM", name="GI PTISM", type="Busbar GI", tier=4),
    # ================= Tier-5 =================
    dict(code="RNKUT", name="Rungkut", type="Busbar GI", tier=5,
         simbol="seksi A/B"),
    dict(code="GBONG", name="GI GBONG", type="Busbar GI", tier=5),
    dict(code="WARU5", name="Waru (bus 150 kV)", type="Busbar GI", tier=5),
    # ================= Tier-6 =================
    dict(code="SBSEL", name="Surabaya Selatan", type="Busbar GI", tier=6),
    dict(code="SLILO", name="Sukolilo", type="Busbar GI", tier=6),
    dict(code="HJAYA", name="GI HJAYA", type="Busbar GI", tier=6),
    dict(code="BDRAN5", name="Buduran (bus 150 kV)", type="Busbar GI", tier=6,
         kerawanan="14"),
    dict(code="JSTEL", name="GI JSTEL", type="Busbar GI", tier=6),
    # ================= Tier-7 =================
    dict(code="KSARI", name="GI KSARI", type="Busbar GI", tier=7),
    dict(code="WKRMO", name="Wonokromo", type="Busbar GI", tier=7),
    dict(code="NGGEL", name="Ngagel", type="Busbar GI", tier=7),
    dict(code="KJRAN", name="Kenjeran", type="Busbar GI", tier=7,
         kerawanan="25"),
    dict(code="IBT 1 BDRAN5", name="IBT 1 Buduran 150/70 kV",
         type="IBT 3-Winding", tier=7, kv="150/70 kV", ibt="1",
         bus_hv="BDRAN5", bus_lv="BDRAN", trafo=1),
    dict(code="IBT 7 BDRAN5", name="IBT 7 Buduran 150/70 kV",
         type="IBT 3-Winding", tier=7, kv="150/70 kV", ibt="7",
         bus_hv="BDRAN5", bus_lv="BDRAN", trafo=1),
    dict(code="BDRAN", name="Buduran (bus 70 kV)", type="Busbar GI",
         tier=7, kv=70),
    dict(code="NBRAN5", name="New Buduran", type="Busbar GI", tier=7),
    # ================= Tier-8 =================
    dict(code="SIMPG", name="Simpang", type="Busbar GI", tier=8),
    dict(code="SDRJO", name="Sidoarjo", type="Busbar GI", tier=8),
    dict(code="SDATI", name="Sedati", type="Busbar GI", tier=8),
    dict(code="MPION", name="Maspion", type="Busbar GI", tier=8, kv=70,
         kerawanan="15"),
    dict(code="KDING", name="Kedinding", type="Busbar GI", tier=8),
    # ================= Tier-9 ke bawah: Madura =================
    dict(code="GLMUR", name="Gilitimur", type="Busbar GI", tier=9),
    dict(code="BKLAN", name="Bangkalan", type="Busbar GI", tier=9,
         simbol="seksi A/B", kerawanan="21"),
    dict(code="SAMPG", name="Sampang", type="Busbar GI", tier=10),
    dict(code="PKSAN", name="Pamekasan", type="Busbar GI", tier=11),
    dict(code="GULUK", name="Guluk-Guluk", type="Busbar GI", tier=12,
         kerawanan="25"),
    dict(code="SMNEP", name="Sumenep", type="Busbar GI", tier=13),
]

L = lambda fr, to, nm, tf, tt, kv=150, kno=None, st="Beroperasi", sirkit=2, single_phi=False: dict(
    fr=fr, to=to, name=nm, kv=kv, tier_fr=tf, tier_to=tt, kerawanan=kno,
    status=st, sirkit=sirkit, single_phi=single_phi, koridor=WIL)

LINES = [
    L("KIT_GRESIK", "GRLMA", "Outlet PLTGU Gresik", 1, 1, sirkit=1),
    # ================= dari Surabaya Barat (Krian) =================
    L("SBRAT5", "KLANG", "SKTT Surabaya Barat - Karangpilang", 1, 2, kno="3"),
    L("KLANG", "BAMBE", "SUTT Karangpilang - Bambe", 2, 3),
    L("SBRAT5", "SWHAN", "SUTT Surabaya Barat - Sawahan", 1, 3, kno="4"),
    L("SBRAT5", "DARMO", "SUTT Surabaya Barat - Darmo Grande", 1, 2, kno="5"),
    L("DARMO", "WARU5", "SUTT Darmo Grande - Waru", 2, 5, kno="5"),
    L("SBRAT5", "ALTAP", "SUTT Surabaya Barat - ALTAP", 1, 2),
    # ================= dari Gresik Baru / Gresik Lama =================
    L("GRSIK5", "TNDES", "SUTT Gresik Baru - Tandes", 1, 2, kno="6"),
    L("GRLMA", "ALTAP", "SUTT Gresik Lama - ALTAP", 1, 2),
    L("ALTAP", "SGMDU", "SUTT ALTAP - Segoromadu", 2, 2),
    L("GRLMA", "SGMDU", "SUTT Gresik Lama - Segoromadu", 1, 2),
    L("SGMDU", "PKMIA", "SUTT Segoromadu - Petrokimia", 2, 3),
    L("GRLMA", "SKREP", "SUTT Gresik Lama - Sambikerep", 1, 2, kno="7"),
    L("SKREP", "WARU5", "SUTT Sambikerep - Waru", 2, 5, kno="11"),
    L("GRLMA", "WLMAR", "SUTT Gresik Lama - Wilmar", 1, 2, sirkit=1),
    # ================= Tandes: ke Sawahan dan ke utara =================
    L("TNDES", "SWHAN", "SUTT Tandes - Sawahan", 2, 3, kno="8"),
    L("SWHAN", "GNSRI", "SUTT Sawahan - Gunungsari", 3, 4, kno="4"),
    L("GNSRI", "WARU5", "SUTT Gunungsari - Waru", 4, 5, kno="4"),
    # Tabel 5.1 #19 explicitly says single phi towards Tandes and Ujung.
    L("TNDES", "PERAK", "SUTT Tandes - Perak", 2, 3, kno="18", sirkit=1, single_phi=True),
    L("PERAK", "UJUNG", "SUTT Perak - Ujung", 3, 4, kno="18", sirkit=1, single_phi=True),
    L("TNDES", "UJUNG", "SUTT Tandes - Ujung", 2, 4, kno="18", sirkit=1),
    L("PERAK", "PTISM", "SKTT Perak - PTISM", 3, 4, sirkit=1),
    # ================= Karangpilang / Bambe / Sawahan ke bawah =================
    L("KLANG", "RNKUT", "SUTT Karangpilang - Rungkut", 2, 5, kno="10"),
    L("BAMBE", "KPANG", "SUTT Bambe - KPANG", 3, 4),
    L("SWHAN", "UDAAN", "SKTT Sawahan - Undaan", 3, 4),
    L("UDAAN", "GBONG", "SKTT Undaan - GBONG", 4, 5),
    L("SWHAN", "KRBAN", "SKTT Sawahan - Krembangan", 3, 4),
    # ================= Rungkut / Sukolilo =================
    L("WARU5", "RNKUT", "SUTT Waru - Rungkut", 5, 5, kno="12"),
    L("RNKUT", "SLILO", "SUTT Rungkut - Sukolilo", 5, 6, kno="16"),
    L("RNKUT", "SBSEL", "SUTT Rungkut - Surabaya Selatan", 5, 6),
    L("SBSEL", "KSARI", "SUTT Surabaya Selatan - KSARI", 6, 7),
    L("RNKUT", "HJAYA", "SKTT Rungkut - HJAYA", 5, 6, sirkit=1),
    L("SLILO", "KSARI", "SKTT Sukolilo - KSARI", 6, 7),
    L("SLILO", "WKRMO", "SUTT Sukolilo - Wonokromo", 6, 7),
    L("SLILO", "NGGEL", "SKTT Sukolilo - Ngagel", 6, 7),
    L("NGGEL", "SIMPG", "SUTT Ngagel - Simpang", 7, 8),
    L("SLILO", "KJRAN", "SUTT Sukolilo - Kenjeran", 6, 7, kno="17"),
    # ================= Waru ke Sidoarjo =================
    L("WARU5", "SDRJO", "SUTT Waru - Sidoarjo", 5, 8, kno="13", sirkit=1),
    L("WARU5", "BDRAN5", "SUTT Waru - Buduran", 5, 6, kno="13", sirkit=1),
    L("BDRAN5", "NBRAN5", "SUTT Buduran - New Buduran", 6, 7, kno="13",
      sirkit=1),
    L("NBRAN5", "SDRJO", "SUTT New Buduran - Sidoarjo", 7, 8, sirkit=1),
    L("NBRAN5", "SDATI", "SUTT New Buduran - Sedati", 7, 8),
    L("WARU5", "JSTEL", "SUTT Waru - JSTEL", 5, 6, sirkit=1),
    L("BDRAN", "MPION", "SUTT 70 kV Buduran - Maspion", 7, 8, kv=70),
    # ================= ke Madura =================
    L("UJUNG", "KDING", "SUTT Ujung - Kedinding", 4, 8, kno="22", sirkit=1),
    L("UJUNG", "BKLAN", "SUTT Ujung - Bangkalan", 4, 9, kno="22", sirkit=1),
    L("KDING", "BKLAN", "SUTT Kedinding - Bangkalan", 8, 9, kno="22"),
    L("KJRAN", "KDING", "SUTT Kenjeran - Kedinding", 7, 8, kno="23", sirkit=1),
    # Tabel 5.1 #20 explicitly says Kenjeran-Gilitimur-Bangkalan single phi.
    L("KJRAN", "GLMUR", "SUTT Kenjeran - Gilitimur", 7, 9, kno="20", sirkit=1, single_phi=True),
    L("GLMUR", "BKLAN", "SUTT Gilitimur - Bangkalan", 9, 9, kno="20", sirkit=1, single_phi=True),
    L("BKLAN", "SAMPG", "SUTT Bangkalan - Sampang", 9, 10, kno="23"),
    L("SAMPG", "PKSAN", "SUTT Sampang - Pamekasan", 10, 11, kno="24"),
    L("PKSAN", "GULUK", "SUTT Pamekasan - Guluk-Guluk", 11, 12),
    L("GULUK", "SMNEP", "SUTT Guluk-Guluk - Sumenep", 12, 13),
]

# Internal bus sections traced from Gambar 5.3 and the supplied close-ups.
# This preserves ONE physical GI. Terminal assignments below distinguish the
# two sections electrically; a label A/B alone does not create connectivity.
for asset in ASSETS:
    if asset['code'] in {'RNKUT', 'BKLAN'}:
        asset['bus_sections'] = ['A', 'B']
    elif asset['code'] == 'SWHAN':
        # #9 establishes an OPEN coupler but not all terminal assignments.
        # 1/2 are model identifiers, not claims about the source's bus labels.
        asset['bus_sections'] = ['1', '2']
        asset['simbol'] = 'Seksi 1/2: ID model; bay belum dipetakan; kopel OPEN per risiko #9'

SECTION_TERMINALS = {
    ('KLANG', 'RNKUT'): (None, 'A'),
    ('WARU5', 'RNKUT'): (None, 'B'),
    ('RNKUT', 'SBSEL'): ('A', None),
    ('RNKUT', 'SLILO'): ('B', None),
    ('RNKUT', 'HJAYA'): ('B', None),
    ('GLMUR', 'BKLAN'): (None, 'A'),
    ('UJUNG', 'BKLAN'): (None, 'B'),
    ('KDING', 'BKLAN'): (None, 'B'),
}
section_lines = []
for line in LINES:
    fr, to = line['fr'], line['to']
    if (fr, to) == ('BKLAN', 'SAMPG'):
        # One drawn conductor leaves each section. The book does not identify
        # circuit numbers, so A/B are endpoint identifiers, not guessed 1/2.
        for section in ('A', 'B'):
            section_lines.append({**line, 'sirkit': 1, 'unit_no': section,
                                  'section_fr': section})
    else:
        sf, st = SECTION_TERMINALS.get((fr, to), (None, None))
        section_lines.append({**line, 'section_fr': sf, 'section_to': st})
LINES = section_lines

COUPLERS = [
    dict(gi='RNKUT', id='KOP_AB', fr='A', to='B', state='OPEN',
         note='Kopel Rungkut A-B; Gambar 5.3; splitting sesuai mitigasi #3. Posisi sumber buku, bukan telemetri.'),
    dict(gi='BKLAN', id='KOP_AB', fr='A', to='B', state='OPEN', kerawanan='21',
         note='Kopel Bangkalan A-B dibuka; Tabel 5.1 #21 dan Gambar 5.3.'),
    dict(gi='SWHAN', id='KOP_12', fr='1', to='2', state='OPEN', kerawanan='9',
         note='Kopel Sawahan dibuka per #9; terminal belum dipetakan; 1/2 adalah ID model.'),
]

SPEC = dict(
    code="SS_KRIAN12_GRESIK",
    name="Krian 1,2 - Gresik 1,2",
    apb="UP2B Jawa Timur",
    wilayah=WIL,
    # Every number above marks where its finding sits (a pin drawn in
    # Gambar 5.3, or a GI the Kondisi names), never a GI it knocks out.
    multi_pin=True,
    source_ref="Buku Kerawanan SJB 2026 Sec 5.3 (Tabel 5.1, PDF p.180-196); "
               "topologi dari Gambar 5.3 Peta Kerawanan (PDF p.179)",
    assets=ASSETS,
    lines=LINES,
    couplers=COUPLERS,
    risks=as_risk_dicts(180, 196, expected=25),
)

if __name__ == "__main__":
    build_workbook(SPEC)
