"""Seed: Subsistem Lontar - Balaraja 1,2 - Kembangan 1,2  (SS_LBK).

Source: Buku Kerawanan SJB 2026, section 2.5
    - hal. 69  SLD sisi Kembangan
    - hal. 70  SLD sisi Balaraja / Lontar
    - Tabel 2.3 (hal. 70-72)  6 titik kerawanan

One canonical GI graph, two layout views (Kembangan side / Balaraja side)
that share the intersection GIs (Cikupa, Suvarna, Pasar Kemis, Jatake Baru).

Edge confidence:
    1.0  = stated in the vulnerability table or unambiguous in the SLD
    0.6  = traced from the SLD, plausible
    0.4  = traced from the SLD, uncertain -> NEEDS_REVIEW
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    AnalyticalView,
    ChangeSet,
    Circuit,
    DefenseScheme,
    DSRelation,
    GeneratingUnit,
    RiskRecord,
    SourceDocument,
    Substation,
    Subsystem,
    SubsystemMembership,
    TopologyVersion,
    Transformer,
    TransformerWinding,
    ViewMembership,
)

SS_CODE = "SS_LBK"

# ---------------------------------------------------------------------------
# Substations. `tier_k` / `tier_b` = the Tier band the GI's busbar sits in on
# the Kembangan (hal.69) / Balaraja (hal.70) SLD. The book's drawing is the
# authority for the risk map; a GI can be a different Tier on each drawing
# (Suvarna: 5 on Kembangan as a Cikupa spur, 3 on Balaraja fed from Sindang
# Jaya). `None` = not drawn on that side.
# fields: code, name, type, voltage, status, busbar_config, busbar_note, role,
#         external_subsystem, tier_k, tier_b, has_transformer, has_capacitor,
#         symbol_note, note
# ---------------------------------------------------------------------------
SUBSTATIONS = [
    dict(code="GITET_KMBGN", name="GITET Kembangan", type="GITET", voltage=500, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None,
         tier_k=1, tier_b=None, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET 500 kV, 2x IBT 500/150 ke bus Kembangan 150. Kopel ada di bus 150 kV (KMBGN), bukan di bus 500 kV ini."),
    dict(code="GITET_NBRJA", name="GITET New Balaraja", type="GITET", voltage=500, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None,
         tier_k=None, tier_b=1, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET 500 kV, 2x IBT 500/150 ke bus New Balaraja 150"),

    # --- Tier 1 (150 kV injection points) ---
    dict(code="KMBGN", name="Kembangan", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="DOUBLE_1CB", busbar_note="2 bus, 1 CB kopel, tanpa section",
         role="SOURCE", external_subsystem=None, tier_k=1, tier_b=None,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Bus 150 kV disuplai IBT-1,2 Kembangan. Kerawanan #1."),
    dict(code="NBRJA", name="New Balaraja", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None,
         tier_k=None, tier_b=1, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Bus 150 kV disuplai IBT-1,2 New Balaraja"),
    dict(code="LTKNG", name="Lontar", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None,
         tier_k=None, tier_b=1, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GI outlet PLTU Lontar (BUKAN GI Teluknaga)."),
    dict(code="DKSBI", name="Durikosambi", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="DOUBLE_SECTIONALIZED", busbar_note="Bus 1A / 2A / 1B / 2B",
         role="BOUNDARY", external_subsystem="SS Muarakarang 1,2 - Durikosambi 1 - KIT Muarakarang",
         tier_k=1, tier_b=1, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="GI batas; irisan 2 SLD. Kerawanan #5 (Durikosambi-Cengkareng)."),
    dict(code="PKTGN", name="Petukangan", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=1, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Feeder Petukangan-Senayan bermasalah (SKTT rusak); Senayan tetap disuplai dari Kembangan."),

    # --- Tier 2 ---
    dict(code="MTLAN", name="Metland", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=2, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="NSYAN", name="New Senayan", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=2, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Simpul kerawanan #2 dan #6."),
    dict(code="BLRJA", name="Balaraja", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=2, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="SDJYA", name="Sindang Jaya", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=2, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="TLKNG2_DADAP", name="Teluknaga 2 / Dadap", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=2, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="TGBRU", name="Tangerang Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=2, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="TGBRU_3", name="Tangerang Baru 3", type="GI", voltage=150, status="NEW_NOT_ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=2, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Busbar hitam di SLD = belum energize"),
    dict(code="CKNDE", name="Cikande", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="BOUNDARY",
         external_subsystem="SS GU Cilegon - Cilegon Baru 1,2,3 - Labuan",
         tier_k=None, tier_b=2, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="GI batas ke SS Cilegon"),

    # --- Tier 3 ---
    dict(code="CLDUG", name="Ciledug", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=3, tier_b=None, has_transformer=True, has_capacitor=True, symbol_note="1 shunt capacitor", note=None),
    dict(code="SNYAN", name="Senayan", type="GIS", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=3, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="GIS kawasan Zero Down Time (ZDT), disuplai radial dari SKTT New Senayan-Senayan. Kerawanan #6."),
    dict(code="ULJMI", name="Ulujami", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=3, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Disuplai dari New Senayan. Dead-end load (trafo 150/20 saja)."),
    dict(code="SVRNA", name="Suvarna Sutra", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=5, tier_b=3, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Irisan 2 SLD. Kembangan: T5 spur dari Cikupa. Balaraja: T3 dari Sindang Jaya/Balaraja."),
    dict(code="TLKGA", name="Teluknaga", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=3, has_transformer=True, has_capacitor=True, symbol_note="1 shunt capacitor",
         note="GI Teluknaga (berbeda dari GI Lontar)"),
    dict(code="CKBRU", name="Cikupa Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=3, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="ITS", name="KTT ITS", type="KTT", voltage=150, status="OWNED_BY_CUSTOMER",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None,
         tier_k=None, tier_b=3, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Konsumen tegangan tinggi"),

    # --- Tier 4 ---
    dict(code="ALTRA", name="Alam Sutera", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=4, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="DNYSA", name="Danayasa", type="GIS", voltage=150, status="ENERGIZED",
         busbar_config="DOUBLE_1CB", busbar_note="gap bus section di SLD",
         role="BOUNDARY", external_subsystem="SS Gandul 2,4",
         tier_k=4, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="GI batas -> SS Gandul 2,4. Ruas Mampang-AGP-Danayasa. Dialihkan ke SS Cawang 2,3-Depok 1 saat pemeliharaan Kembangan-New Senayan."),
    dict(code="ABDGP", name="Abadi Guna Papan", type="GIS", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="BOUNDARY", external_subsystem="SS Gandul 2,4",
         tier_k=4, tier_b=None, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GIS AGP. Ruas AGP-Mampang SKTT baru 1000A. Feeder Senayan-AGP masih PLANNED."),
    dict(code="MPANG", name="Mampang", type="GIS", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="BOUNDARY", external_subsystem="SS Gandul 2,4",
         tier_k=4, tier_b=None, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GIS Mampang Baru. Ujung ruas Mampang-AGP-Danayasa."),
    dict(code="CKUPA", name="Cikupa", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=4, tier_b=4, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Irisan 2 SLD. Kerawanan #4 (Cikupa-Jatake). Kembangan: fed dari Curug (bay panjang)."),
    dict(code="NCKUPA", name="GITET New Cikupa", type="GITET", voltage=500, status="NEW_NOT_ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=4, has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET (IBT 500/150) BELUM energize -- busbar hitam. Solusi kerawanan #4. Saat COD = perubahan struktural via change request, bukan toggle. Tidak dihitung dalam Tier kondisi sekarang."),
    dict(code="SPTAN", name="Sepatan", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=4, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="CNKNG", name="Cengkareng", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=4, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Kerawanan #5 (Durikosambi-Cengkareng)"),
    dict(code="BSH", name="BSH", type="KTT", voltage=150, status="OWNED_BY_CUSTOMER",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None,
         tier_k=None, tier_b=4, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Dalam kotak dashed 'Aset milik KTT'"),

    # --- Tier 5 ---
    dict(code="SGS", name="Summarecon Gading Serpong", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=5, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None, note=None),
    dict(code="CURUG", name="Curug", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=5, tier_b=None, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Kembangan: T5, punya bay panjang ke Cikupa (T4)."),
    dict(code="PSKMS", name="Pasar Kemis", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=5, tier_b=5, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Irisan 2 SLD. Kembangan: spur T5 dari Cikupa. Kerawanan #3 (single phi)."),
    dict(code="PSKBR", name="Pasar Kemis Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=5, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Kerawanan #3 (Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis single phi)"),
    dict(code="SPTAN2", name="Sepatan 2", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=5, has_transformer=True, has_capacitor=False, symbol_note=None, note="Dead-end load"),
    dict(code="TGRNG", name="Tangerang", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=5, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="GI Tangerang (Lama). Bebannya akan diambil GITET Cikupa (RUPTL). Hotspot #5."),
    dict(code="JTAKE", name="Jatake", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=5, tier_b=6, has_transformer=True, has_capacitor=True,
         symbol_note="output bay: 1 trafo + 2 kapasitor + bay Jatake Baru",
         note="Irisan 2 SLD. Kerawanan #4. Kembangan: T5 output ke Jatake Baru & Maxim. Balaraja: output bay off T6."),

    # --- Tier 6 ---
    dict(code="MAXIM", name="Maxim", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=6, tier_b=None, has_transformer=True, has_capacitor=False,
         symbol_note="3 trafo di SLD (perlu konfirmasi OSL)", note=None),
    dict(code="JTKBR", name="Jatake Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=6, tier_b=6, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Disuplai dari Jatake (Kembangan) / Tangerang (Balaraja). Irisan 2 SLD."),
    dict(code="GJTGL", name="Gajah Tunggal", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None,
         tier_k=None, tier_b=6, has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Single phi (kerawanan #3)"),
]

# Generating units  (code, name, unit_type, voltage, rated_mw, unit_count, outlet_code, operator, status)
# outlet_code may be a substation code (feeds that bus) or a circuit code
# prefixed "@" (taps that circuit -- e.g. PLTD Senayan on the Senayan-Danayasa run).
GENERATORS = [
    ("PLTU_LONTAR", "PLTU Lontar", "PLTU", 150, 945.0, 4, "LTKNG", "PIP", "ENERGIZED"),
    ("PLTD_SNYAN_GEN", "PLTD Senayan", "PLTD", 150, None, None, "@SKTT_SNYAN_DNYSA_SP", "PLN", "STANDBY"),
]

# Transformers  (code, name, type, substation_code, unit_no, rating_mva, windings[(no,kv,role)])
TRANSFORMERS = [
    ("IBT_KMBGN_1", "IBT 1 Kembangan", "IBT", "KMBGN", "1", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_KMBGN_2", "IBT 2 Kembangan", "IBT", "KMBGN", "2", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_NBRJA_1", "IBT 1 New Balaraja", "IBT", "NBRJA", "1", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_NBRJA_2", "IBT 2 New Balaraja", "IBT", "NBRJA", "2", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
]

# Circuits  (code, name, type, from_code, to_code, kv, transformer_code, circuit_count,
#            single_phi, status, confidence, side, note)
#   side "K" = drawn on the Kembangan SLD (hal.69)
#   side "B" = drawn on the Balaraja/Lontar SLD (hal.70)
# A view renders only its own side's circuits, so the two SLDs are not
# force-merged. Intersection GIs (Cikupa, Suvarna, Pasar Kemis, Jatake, Jatake
# Baru, Maxim, Durikosambi) appear in both views with their own side's edges.
# Only busbar-to-busbar connections. 150/20 transformers & capacitors are GI attributes.
CIRCUITS = [
    # -- IBT links (500/150 step-down at GITET) --
    ("IBT_KMBGN_1_LINK", "IBT 1 Kembangan 500/150", "IBT_LINK", "GITET_KMBGN", "KMBGN", 500, "IBT_KMBGN_1", None, False, "ENERGIZED", 1.0, "K", None),
    ("IBT_KMBGN_2_LINK", "IBT 2 Kembangan 500/150", "IBT_LINK", "GITET_KMBGN", "KMBGN", 500, "IBT_KMBGN_2", None, False, "ENERGIZED", 1.0, "K", None),
    ("IBT_NBRJA_1_LINK", "IBT 1 New Balaraja 500/150", "IBT_LINK", "GITET_NBRJA", "NBRJA", 500, "IBT_NBRJA_1", None, False, "ENERGIZED", 1.0, "B", None),
    ("IBT_NBRJA_2_LINK", "IBT 2 New Balaraja 500/150", "IBT_LINK", "GITET_NBRJA", "NBRJA", 500, "IBT_NBRJA_2", None, False, "ENERGIZED", 1.0, "B", None),

    # ================= Kembangan side (SLD hal.69) =================
    ("PHT_KMBGN_MTLAN", "Kembangan - Metland", "SKTT", "KMBGN", "MTLAN", 150, None, 2, False, "ENERGIZED", 0.7, "K", "Ruas 2 sirkit KMBGN turun; Metland tap di tengah, lanjut ke Ciledug"),
    ("PHT_MTLAN_CLDUG", "Metland - Ciledug", "SKTT", "MTLAN", "CLDUG", 150, None, 2, False, "ENERGIZED", 0.7, "K", "Ciledug 'mampir' Metland dulu; ruas lanjut dari KMBGN"),
    ("SKTT_KMBGN_NSYAN", "Kembangan - New Senayan", "SKTT", "KMBGN", "NSYAN", 150, None, 2, False, "ENERGIZED", 1.0, "K", "Kerawanan #2: pembebanan 72%, N-1 tak terpenuhi (2 sirkit, trip 1 -> overload)"),
    ("PHT_KMBGN_DKSBI", "Kembangan - Durikosambi", "SKTT", "KMBGN", "DKSBI", 150, None, 2, False, "ENERGIZED", 0.5, "K", "DKSBI boundary stub"),
    ("PHT_KMBGN_PKTGN", "Kembangan - Petukangan", "SKTT", "KMBGN", "PKTGN", 150, None, 2, False, "ENERGIZED", 0.5, "K", "traced"),
    ("SKTT_NSYAN_SNYAN", "New Senayan - Senayan", "SKTT", "NSYAN", "SNYAN", 150, None, 2, False, "ENERGIZED", 1.0, "K", "2 sirkit. Kerawanan #6: Senayan (GIS ZDT) hanya bersumber dari New Senayan (tidak ada backup GI lain); N-1-1 di hulu Kembangan-New Senayan -> Senayan padam."),
    ("PHT_NSYAN_ULJMI", "New Senayan - Ulujami", "SKTT", "NSYAN", "ULJMI", 150, None, 2, False, "ENERGIZED", 0.6, "K", "Ulujami dead-end load"),
    ("SKTT_SNYAN_DNYSA_DIRECT", "Senayan - Danayasa (direct)", "SKTT", "SNYAN", "DNYSA", 150, None, 1, False, "ENERGIZED", 0.5, "K", "1 sirkit direct. DNYSA boundary -> Gandul 2,4"),
    ("SKTT_SNYAN_DNYSA_SP", "Senayan - Danayasa (via PLTD Senayan, single phi)", "SKTT", "SNYAN", "DNYSA", 150, None, 1, True, "ENERGIZED", 0.5, "K", "Sirkit ke-2 'mampir' PLTD Senayan (standby). Sistem single-phi Senayan-PLTD-Danayasa; usulan double phi."),
    ("SKTT_SNYAN_ABDGP", "Senayan - Abadi Guna Papan", "SKTT", "SNYAN", "ABDGP", 150, None, 1, False, "PLANNED", 0.4, "K", "Bay abu -> PLANNED (belum jadi)"),
    ("PHT_CLDUG_ALTRA", "Ciledug - Alam Sutera", "SKTT", "CLDUG", "ALTRA", 150, None, 2, False, "ENERGIZED", 0.6, "K", "traced"),
    ("PHT_ALTRA_SGS", "Alam Sutera - Summarecon Gading Serpong", "SKTT", "ALTRA", "SGS", 150, None, 2, False, "ENERGIZED", 0.6, "K", "traced"),
    ("PHT_SGS_CURUG", "Summarecon Gading Serpong - Curug", "SKTT", "SGS", "CURUG", 150, None, 2, False, "ENERGIZED", 0.5, "K", "traced"),
    ("PHT_CURUG_CKUPA", "Curug - Cikupa", "SKTT", "CURUG", "CKUPA", 150, None, 2, False, "ENERGIZED", 0.6, "K", "Bay panjang T5 Curug -> T4 Cikupa (sisi Kembangan)"),
    ("PHT_DNYSA_ABDGP", "Danayasa - Abadi Guna Papan", "SKTT", "DNYSA", "ABDGP", 150, None, 2, False, "ENERGIZED", 0.5, "K", "Ruas Mampang-AGP-Danayasa (teks p91)"),
    ("PHT_ABDGP_MPANG", "Abadi Guna Papan - Mampang", "SKTT", "ABDGP", "MPANG", 150, None, 2, False, "ENERGIZED", 0.5, "K", "SKTT baru 1000A (teks p91)"),
    ("PHT_CKUPA_SVRNA_K", "Cikupa - Suvarna Sutra", "SKTT", "CKUPA", "SVRNA", 150, None, 2, False, "ENERGIZED", 0.6, "K", "output bay Cikupa"),
    ("PHT_CKUPA_PSKMS_K", "Cikupa - Pasar Kemis", "SKTT", "CKUPA", "PSKMS", 150, None, 2, False, "ENERGIZED", 0.6, "K", "output bay Cikupa"),
    ("SUTT_CKUPA_JTAKE", "Cikupa - Jatake", "SKTT", "CKUPA", "JTAKE", 150, None, 2, False, "ENERGIZED", 1.0, "K", "Kerawanan #4: overload saat N-1-1/N-2 ruas Lontar-Tangerang Baru. Jatake jadi selevel T5."),
    ("PHT_JTAKE_JTKBR_K", "Jatake - Jatake Baru", "SKTT", "JTAKE", "JTKBR", 150, None, 2, False, "ENERGIZED", 0.7, "K", "output bay Jatake"),
    ("PHT_JTAKE_MAXIM", "Jatake - Maxim", "SKTT", "JTAKE", "MAXIM", 150, None, 2, False, "ENERGIZED", 0.7, "K", "Jatake -> Maxim (T6, sisi Kembangan). Jatake juga punya output 1 trafo + 2 kapasitor."),

    # ================= Balaraja / Lontar side (SLD hal.70) =================
    ("PHT_NBRJA_BLRJA", "New Balaraja - Balaraja", "SUTT", "NBRJA", "BLRJA", 150, None, 2, False, "ENERGIZED", 0.6, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_LTKNG_SDJYA", "Lontar - Sindang Jaya", "SUTT", "LTKNG", "SDJYA", 150, None, 2, False, "ENERGIZED", 0.6, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_LTKNG_TLKNG2", "Lontar - Teluknaga 2 / Dadap", "SUTT", "LTKNG", "TLKNG2_DADAP", 150, None, 2, False, "ENERGIZED", 0.6, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_LTKNG_TGBRU", "Lontar - Tangerang Baru", "SUTT", "LTKNG", "TGBRU", 150, None, 2, False, "ENERGIZED", 0.7, "B", "Ruas Lontar-Tangerang Baru (disebut di kerawanan #4) [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_LTKNG_TGBRU3", "Lontar - Tangerang Baru 3", "SUTT", "LTKNG", "TGBRU_3", 150, None, 2, False, "NEW_NOT_ENERGIZED", 0.4, "B", "TGBRU 3 belum energize [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_BLRJA_CKNDE", "Balaraja - Cikande", "SUTT", "BLRJA", "CKNDE", 150, None, 2, False, "ENERGIZED", 0.5, "B", "CKNDE boundary -> Cilegon [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_BLRJA_SVRNA", "Balaraja - Suvarna Sutra", "SUTT", "BLRJA", "SVRNA", 150, None, 2, False, "ENERGIZED", 0.5, "B", "traced (cross-routing di SLD) [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_SDJYA_SVRNA", "Sindang Jaya - Suvarna Sutra", "SUTT", "SDJYA", "SVRNA", 150, None, 2, False, "ENERGIZED", 0.4, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_TLKNG2_TLKGA", "Teluknaga 2 / Dadap - Teluknaga", "SUTT", "TLKNG2_DADAP", "TLKGA", 150, None, 2, False, "ENERGIZED", 0.5, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_TGBRU_CKBRU", "Tangerang Baru - Cikupa Baru", "SUTT", "TGBRU", "CKBRU", 150, None, 2, False, "ENERGIZED", 0.6, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_TGBRU_ITS", "Tangerang Baru - KTT ITS", "SUTT", "TGBRU", "ITS", 150, None, 1, False, "ENERGIZED", 0.4, "B", "KTT ITS external [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_SVRNA_CKUPA", "Suvarna Sutra - Cikupa", "SUTT", "SVRNA", "CKUPA", 150, None, 2, False, "ENERGIZED", 0.6, "B", "traced (irisan) - Cikupa T4 dari sisi Balaraja [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_TLKGA_SPTAN", "Teluknaga - Sepatan", "SUTT", "TLKGA", "SPTAN", 150, None, 2, False, "ENERGIZED", 0.5, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("SUTT_CKBRU_CNKNG", "Cikupa Baru - Cengkareng", "SUTT", "CKBRU", "CNKNG", 150, None, 2, False, "ENERGIZED", 0.6, "B", "terkait kerawanan #5 [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_CKBRU_BSH", "Cikupa Baru - BSH", "SUTT", "CKBRU", "BSH", 150, None, 1, False, "ENERGIZED", 0.5, "B", "BSH milik KTT [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("SUTT_DKSBI_CNKNG", "Durikosambi - Cengkareng", "SUTT", "DKSBI", "CNKNG", 150, None, 2, False, "ENERGIZED", 1.0, "B", "Kerawanan #5: N-1 tak terpenuhi saat GI Jatake/Jatake Baru/Tangerang/Cengkareng dipasok SS Muarakarang [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_NCKUPA_JTAKE", "GITET New Cikupa - Jatake (rencana)", "IBT_LINK", "NCKUPA", "JTAKE", 500, None, 2, False, "NEW_NOT_ENERGIZED", 0.4, "B",
     "Future: saat GITET New Cikupa COD, menyuntik di area Cikupa-Jatake. Belum energize."),
    ("PHT_SPTAN_PSKBR", "Sepatan - Pasar Kemis Baru", "SUTT", "SPTAN", "PSKBR", 150, None, 2, False, "ENERGIZED", 0.5, "B", "traced [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_SPTAN_SPTAN2", "Sepatan - Sepatan 2", "SUTT", "SPTAN", "SPTAN2", 150, None, 2, False, "ENERGIZED", 0.5, "B", "Sepatan 2 dead-end [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("SUTT_PSKMS_PSKBR", "Pasar Kemis - Pasar Kemis Baru", "SUTT", "PSKMS", "PSKBR", 150, None, 1, True, "ENERGIZED", 1.0, "B", "Kerawanan #3: single phi Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("SUTT_PSKBR_GJTGL", "Pasar Kemis Baru - Gajah Tunggal", "SUTT", "PSKBR", "GJTGL", 150, None, 1, True, "ENERGIZED", 1.0, "B", "Kerawanan #3: single phi; KTT Gajah Tunggal padam saat N-1-1 [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("SUTT_GJTGL_PSKMS", "Gajah Tunggal - Pasar Kemis", "SUTT", "GJTGL", "PSKMS", 150, None, 1, True, "ENERGIZED", 0.7, "B", "Kerawanan #3: garis tipis semi-hilang di SLD, menutup loop single-phi [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_CNKNG_TGRNG", "Cengkareng - Tangerang", "SUTT", "CNKNG", "TGRNG", 150, None, 2, False, "ENERGIZED", 0.5, "B", "Hotspot #5 [jenis SUTT/SKTT NEEDS_REVIEW dgn SLD referensi]"),
    ("PHT_TGRNG_JTAKE", "Tangerang - Jatake", "SUTT", "TGRNG", "JTAKE", 150, None, 2, False, "ENERGIZED", 0.5, "B", "Jatake output bay dari sisi Balaraja (label PDF blur 'ITAKE' = JTAKE) [NEEDS_REVIEW]"),
    ("PHT_JTAKE_JTKBR_B", "Jatake - Jatake Baru", "SUTT", "JTAKE", "JTKBR", 150, None, 2, False, "ENERGIZED", 0.6, "B", "Jatake Baru dari Jatake (sama spt sisi Kembangan) [NEEDS_REVIEW]"),
]

# Risk records  (seq, title, condition, impact, mitigation, follow_up, priority,
#                attach_kind, attach_code)
RISKS = [
    (1, "Pembebanan IBT-1,2 Kembangan tidak memenuhi N-1 saat PLTU Lontar -1 unit",
     "Pembebanan IBT-1,2 Kembangan tidak memenuhi kriteria N-1 saat PLTU Lontar tidak beroperasi 1 unit.",
     "1. Terjadi pemadaman jika terjadi gangguan N-1 pada salah satu IBT Kembangan. "
     "2. Pemeliharaan IBT Kembangan hanya dilakukan saat hari Minggu.",
     "1. Sudah terpasang OLS IBT Kembangan tahap 1 sd 4 sebesar 908 MW (Buku DS 2025). "
     "2. Rencana penambahan target OLS IBT Kembangan tahap 1 sd 4 total 1207 MW. "
     "3. Pekerjaan dilaksanakan saat beban pembangkitan Lontar 4 unit maksimum atau saat beban rendah. "
     "4. Pengalihan beban ke Sub Sistem Muarakarang atau Gandul 1,3-Durikosambi 2.",
     "Jangka Pendek: (1) GITET Cikupa + 2 unit IBT 500/150 kV + outlet (RUPTL 2025-2034, COD 2025); "
     "(2) 2 unit IBT 500/150 kV Ext IBT 3,4 Durikosambi (COD 2026); (3) PLTSA Tangerang 45 MW (COD 2028). "
     "Jangka Panjang: BESS di GI Cikupa & GI Teluknaga masing-masing 100 MW (COD 2032).",
     "High", "TRANSFORMER", "IBT_KMBGN_1"),
    (2, "Pembebanan SKTT Kembangan-New Senayan 72% / tidak memenuhi N-1",
     "Pembebanan SKTT Kembangan-New Senayan mencapai 72% / tidak memenuhi kriteria N-1.",
     "1. Terjadi Overload apabila trip 1 sirkit di ruas SKTT 150 kV Kembangan-New Senayan. "
     "2. Fleksibilitas operasi dan keandalan berkurang.",
     "1. Sudah terpasang OLS SKTT Kembangan-New Senayan dengan target 120 MW (Buku DS 2025). "
     "2. Pemeliharaan dilaksanakan saat beban rendah. "
     "3. Pengalihan beban GI Danayasa ke Sub Sistem Cawang 2,3-Depok 1.",
     "Jangka Pendek: (1) Pembangunan SKTT 150 kV Petukangan-PLTD Senayan menjadi 2cct, 1000 A/sirkit "
     "(kabel eksisting rusak, RUPTL 2025-2034, COD 2027); (2) 2 Line bay di GIS PLTD Senayan agar "
     "SKTT Petukangan-PLTD Senayan bisa operasi 2 sirkit (COD 2027).",
     "High", "CIRCUIT", "SKTT_KMBGN_NSYAN"),
    (3, "Ruas Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis masih single phi",
     "Ruas Penghantar Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis masih beroperasi single phi.",
     "Berpotensi Padam pada KTT GI Gajah Tunggal saat terjadi N-1-1.",
     "Pengaturan penjadwalan pemeliharaan penghantar.",
     "Jangka Menengah: Usulan Double Phi pada ruas Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis "
     "(diusulkan COD 2029).",
     "Medium", "CIRCUIT", "SUTT_PSKBR_GJTGL"),
    (4, "Ruas Cikupa-Jatake berpotensi overload saat N-1-1 / N-2 ruas Lontar-Tangerang Baru",
     "Ruas Penghantar Cikupa-Jatake berpotensi overload saat terjadi kondisi N-1-1 atau N-2 pada "
     "ruas penghantar Lontar-Tangerang Baru.",
     "Pemeliharaan ruas penghantar Lontar-Tangerang Baru hanya bisa dilakukan saat beban rendah.",
     "1. Pengaturan penjadwalan pemeliharaan penghantar. "
     "2. Sudah terpasang OLS SUTT Jatake-Cikupa sebesar 240 MW (Buku DS 2025). "
     "3. Rencana penambahan target OLS SUTT Jatake-Cikupa total 375 MW (Buku DS 2025).",
     "Jangka Pendek: GITET Cikupa + 2 unit IBT 500/150 kV + outlet untuk mengambil beban GI Cikupa, "
     "GI Jatake Baru, GI Maxim dan GI Tangerang Lama (RUPTL 2025-2034, COD 2025). "
     "Jangka Panjang: BESS di GI Cikupa & GI Teluknaga masing-masing 100 MW (COD 2032).",
     "High", "CIRCUIT", "SUTT_CKUPA_JTAKE"),
    (5, "Ruas Durikosambi-Cengkareng tidak memenuhi N-1 saat pasok dari SS Muarakarang",
     "Ruas Penghantar Durikosambi-Cengkareng tidak memenuhi kriteria N-1 saat GI Jatake, Jatake Baru, "
     "Tangerang dan Cengkareng dipasok dari Sub Sistem Muarakarang.",
     "1. Berpotensi adanya pemadaman saat terjadi kondisi N-1 pada ruas penghantar tersebut. "
     "2. Fleksibilitas operasi Sub Sistem Lontar dan Sub Sistem Muarakarang berkurang.",
     "Pengaturan penjadwalan pemeliharaan penghantar hanya bisa dilakukan saat PLTU Lontar beroperasi "
     "4 unit dan saat GI Jatake, Jatake Baru, Tangerang dan Cengkareng dipasok Sub Sistem Lontar.",
     "Jangka Pendek: GITET Cikupa + 2 unit IBT 500/150 kV + outlet untuk mengambil beban GI Cikupa, "
     "GI Jatake Baru, GI Maxim dan GI Tangerang Lama (RUPTL 2025-2034, COD 2025). "
     "Jangka Panjang: BESS di GI Cikupa & GI Teluknaga masing-masing 100 MW (COD 2032).",
     "High", "CIRCUIT", "SUTT_DKSBI_CNKNG"),
    (6, "GIS 150 kV Senayan (ZDT) dipasok radial dari SKTT New Senayan-Senayan",
     "GIS 150 kV Senayan masuk dalam kawasan Zero Down Time (ZDT) namun saat ini dipasok radial dari "
     "SKTT New Senayan-Senayan.",
     "Apabila terjadi N-1-1 pada ruas SKTT Kembangan-New Senayan menyebabkan GIS 150 kV Senayan padam.",
     "Pengalihan beban ke Sub Sistem Cawang 2,3-Depok 1 atau Sub Sistem Muarakarang 1,2-Durikosambi 1-"
     "KIT Muarakarang saat pemeliharaan SKTT Kembangan-New Senayan.",
     "Jangka Pendek: (1) 2 Line bay di GIS PLTD Senayan agar SKTT Petukangan-PLTD Senayan bisa operasi "
     "2 sirkit (COD 2027); (2) SKTT 150 kV Petukangan-PLTD Senayan menjadi 2cct, 1000 A/sirkit "
     "(kabel eksisting rusak, RUPTL 2025-2034, COD 2027).",
     "High", "SUBSTATION", "SNYAN"),
]

# Bays: a small GI drawn only as a stub on a feeder busbar (no busbar of its
# own). A GI can be a bay on more than one busbar (Petukangan: off Kembangan,
# and separately off Senayan with a broken feeder).
#   (gi_code, feeder_code, side, status, note)
BAYS = [
    # sisi Kembangan
    ("DKSBI", "KMBGN", "K", "ENERGIZED", "Bay Durikosambi di bus Kembangan (GI batas -> SS Muarakarang)"),
    ("PKTGN", "KMBGN", "K", "ENERGIZED", "Bay Petukangan di bus Kembangan"),
    ("PKTGN", "SNYAN", "K", "DE_ENERGIZED", "Bay Petukangan di bus Senayan - feeder SKTT rusak"),
    ("ABDGP", "SNYAN", "K", "PLANNED", "Bay AGP di bus Senayan - SKTT belum jadi (abu di SLD)"),
    ("ABDGP", "DNYSA", "K", "ENERGIZED", "Bay AGP di bus Danayasa - ruas Mampang-AGP-Danayasa"),
    ("MPANG", "ABDGP", "K", "ENERGIZED", "Bay Mampang - ujung ruas Mampang-AGP-Danayasa"),
    ("SVRNA", "CKUPA", "K", "ENERGIZED", "Bay Suvarna Sutra dari Cikupa (SKTT)"),
    ("PSKMS", "CKUPA", "K", "ENERGIZED", "Bay Pasar Kemis dari Cikupa (SKTT)"),
    ("JTKBR", "JTAKE", "K", "ENERGIZED", "Bay Jatake Baru dari Jatake (SKTT)"),
]

# Defense schemes  (key, name, type, status, scope, target_mw, target_mw_planned, stages, ref,
#                   [ (attach_kind, attach_code, role, coverage_note) ])
DEFENSE_SCHEMES = [
    ("DS_OLS_IBT_KMBGN", "OLS IBT Kembangan", "OLS", "ACTIVE", "LOCAL", 908.0, 1207.0,
     "tahap 1 sd 4", "Buku DS 2025",
     [("TRANSFORMER", "IBT_KMBGN_1", "TRIGGER_ACTION", "1 SS"),
      ("TRANSFORMER", "IBT_KMBGN_2", "TRIGGER_ACTION", "1 SS")]),
    ("DS_OLS_KMBGN_NSYAN", "OLS SKTT Kembangan-New Senayan", "OLS", "ACTIVE", "LOCAL", 120.0, None,
     None, "Buku DS 2025",
     [("CIRCUIT", "SKTT_KMBGN_NSYAN", "TRIGGER_ACTION", "1 SS")]),
    ("DS_OLS_JTAKE_CKUPA", "OLS SUTT Jatake-Cikupa", "OLS", "ACTIVE", "LOCAL", 240.0, 375.0,
     None, "Buku DS 2025",
     [("CIRCUIT", "SUTT_CKUPA_JTAKE", "TRIGGER_ACTION", "1 SS")]),
]


def seed_ss_lbk(db: Session) -> None:
    if db.query(Subsystem).filter(Subsystem.code == SS_CODE).first():
        return

    doc = SourceDocument(
        filename="Buku Kerawanan SJB Tahun 2026.pdf",
        document_type="SLD_PDF_PAGE",
        analytical_hint="SUBSYSTEM_150",
        source_ref="Buku Kerawanan SJB 2026 hal.69-72 (Sec 2.5)",
        effective_date="2026-06-30",
    )
    db.add(doc)
    db.flush()

    ss = Subsystem(
        code=SS_CODE,
        name="Lontar - Balaraja 1,2 - Kembangan 1,2",
        apb="UP2B Jakarta & Banten",
        source_ref="Buku Kerawanan SJB 2026 Sec 2.5",
    )
    db.add(ss)
    db.flush()

    tv = TopologyVersion(
        version_key="TV-SS_LBK-2026-06",
        status="ACTIVE",
        effective_date="2026-06-30",
        description="Baseline SS Lontar-Balaraja-Kembangan dari Buku Kerawanan SJB 2026 Sec 2.5 "
        "(traced from SLD hal.69-70; edge confidence-tagged, pending field review).",
    )
    db.add(tv)
    tv_future = TopologyVersion(
        version_key="TV-SS_LBK-NCKUPA-COD",
        status="PROPOSED",
        description="Saat GITET New Cikupa (IBT 500/150) COD: menjadi sumber Tier-1 baru yang "
        "menyuntik di area Cikupa-Jatake, menghilangkan overload ruas Cikupa-Jatake (kerawanan #4).",
    )
    db.add(tv_future)
    db.flush()
    db.add(ChangeSet(
        change_key="CR-SS_LBK-001", version_id=tv_future.id, action="ADD_GITET",
        target_kind="SUBSTATION", target_ref="NCKUPA",
        description="Energize GITET New Cikupa; ubah status PHT_NCKUPA_JTAKE -> ENERGIZED; "
        "evaluasi ulang beban ruas Cikupa-Jatake.",
        status="PROPOSED",
    ))

    subs: dict[str, Substation] = {}
    role_in_ss: dict[str, str] = {}
    tier_k: dict[str, int | None] = {}
    tier_b: dict[str, int | None] = {}
    for d in SUBSTATIONS:
        s = Substation(
            code=d["code"], name=d["name"], substation_type=d["type"], voltage_kv=d["voltage"],
            status=d["status"], busbar_config=d["busbar_config"], busbar_note=d["busbar_note"],
            has_transformer=d["has_transformer"], has_shunt_capacitor=d["has_capacitor"],
            symbol_note=d["symbol_note"], apb="UP2B Jakarta & Banten", uit="JBB",
            note=d["note"], confidence=1.0,
        )
        db.add(s)
        subs[d["code"]] = s
        role_in_ss[d["code"]] = d["role"]
        tier_k[d["code"]] = d["tier_k"]
        tier_b[d["code"]] = d["tier_b"]
        db.flush()
        db.add(SubsystemMembership(
            subsystem_id=ss.id, node_kind="SUBSTATION", node_id=s.id,
            role=d["role"], external_subsystem=d["external_subsystem"],
            display_order=d["tier_k"] or d["tier_b"],
        ))

    # circuits are created below; a generator that taps a circuit is wired
    # after the circuits pass, so defer those.
    _gen_defs = list(GENERATORS)

    txs: dict[str, Transformer] = {}
    for (code, name, ttype, scode, unit, mva, windings) in TRANSFORMERS:
        t = Transformer(
            code=code, name=name, transformer_type=ttype, substation_id=subs[scode].id,
            unit_no=unit, rating_mva=mva, winding_count=len(windings),
        )
        db.add(t)
        txs[code] = t
        db.flush()
        for (wno, wkv, wrole) in windings:
            db.add(TransformerWinding(transformer_id=t.id, winding_no=wno, voltage_kv=wkv, role=wrole))
    db.flush()
    for code in txs:
        db.add(SubsystemMembership(
            subsystem_id=ss.id, node_kind="TRANSFORMER", node_id=txs[code].id,
            role="SOURCE_BOUNDARY", display_order=1,
        ))

    circuits: dict[str, Circuit] = {}
    for (code, name, ctype, fr, to, kv, txcode, ccnt, sphi, status, conf, side, note) in CIRCUITS:
        c = Circuit(
            code=code, name=name, circuit_type=ctype, voltage_kv=kv,
            from_substation_id=subs[fr].id, to_substation_id=subs[to].id,
            transformer_id=txs[txcode].id if txcode else None,
            circuit_count=ccnt, single_phi=sphi, status=status, scenario_id="NORMAL",
            drawing_side=side, source_document_id=doc.id,
            note=("NEEDS_REVIEW; " + (note or "")) if conf < 0.9 else note,
            confidence=conf,
        )
        db.add(c)
        circuits[code] = c
    db.flush()

    gens: dict[str, GeneratingUnit] = {}
    for (code, name, utype, kv, mw, ucnt, outlet, op, status) in _gen_defs:
        kw = dict(code=code, name=name, unit_type=utype, voltage_kv=kv, rated_mw=mw,
                  unit_count=ucnt, operator=op, status=status)
        if outlet.startswith("@"):
            kw["tap_circuit_id"] = circuits[outlet[1:]].id
        else:
            kw["outlet_substation_id"] = subs[outlet].id
        g = GeneratingUnit(**kw)
        db.add(g)
        gens[code] = g
    db.flush()
    for code in gens:
        db.add(SubsystemMembership(
            subsystem_id=ss.id, node_kind="GENERATING_UNIT", node_id=gens[code].id,
            role="SOURCE", display_order=1,
        ))

    from app.models import Bay
    for (gi, feeder, side, status, note) in BAYS:
        db.add(Bay(
            substation_id=subs[gi].id, feeder_substation_id=subs[feeder].id,
            name=f"Bay {subs[gi].name} @ {subs[feeder].name}", bay_type="LINE",
            drawing_side=side, status=status, note=note,
        ))
    db.flush()

    def resolve(kind: str, code: str):
        if kind == "SUBSTATION":
            return subs.get(code)
        if kind == "TRANSFORMER":
            return txs.get(code)
        if kind == "CIRCUIT":
            return circuits.get(code)
        if kind == "GENERATING_UNIT":
            return gens.get(code)
        return None

    for (seq, title, cond, impact, mit, fu, prio, akind, acode) in RISKS:
        obj = resolve(akind, acode)
        db.add(RiskRecord(
            risk_key=f"RISK-{SS_CODE}-{seq:02d}",
            subsystem_id=ss.id, seq_no=seq, uit="JBB",
            attach_kind=akind, attach_id=(obj.id if obj else None), attach_label=acode,
            title=title, condition=cond, impact=impact, mitigation=mit, follow_up=fu,
            priority=prio, status="OPEN", source_document_id=doc.id,
        ))

    for (key, name, stype, status, scope, mw, mwp, stages, ref, rels) in DEFENSE_SCHEMES:
        d = DefenseScheme(
            scheme_key=key, name=name, scheme_type=stype, status=status, scope_level=scope,
            target_mw=mw, target_mw_planned=mwp, stages=stages, reference=ref,
        )
        db.add(d)
        db.flush()
        for (akind, acode, arole, cov) in rels:
            obj = resolve(akind, acode)
            db.add(DSRelation(
                scheme_id=d.id, subsystem_id=ss.id, attach_kind=akind,
                attach_id=(obj.id if obj else None), attach_label=acode,
                role=arole, coverage_note=cov,
            ))

    # ---- analytical views: TWO layout projections of the same canonical SS
    #      graph, one per SLD in the book. A merged single-diagram view is NOT
    #      produced -- the two sides meet at intersection GIs (Cikupa, Suvarna,
    #      Pasar Kemis, Jatake, Jatake Baru, Durikosambi) and stitching them into
    #      one readable diagram needs a seam-aware layout that is not built yet.
    #      The intersection GIs are still ONE physical object, present in both
    #      views -- that part of the model already works.
    v_kem = AnalyticalView(
        view_key=f"{SS_CODE}_KEMBANGAN", view_type="SUBSYSTEM",
        name="SS Lontar-Balaraja-Kembangan - sisi Kembangan (SLD hal.69)",
        rule_profile="SUBSYSTEM_150", subsystem_id=ss.id,
        layout_hint="KEMBANGAN_SIDE", drawing_side="K",
    )
    v_bal = AnalyticalView(
        view_key=f"{SS_CODE}_BALARAJA", view_type="SUBSYSTEM",
        name="SS Lontar-Balaraja-Kembangan - sisi Balaraja/Lontar (SLD hal.70)",
        rule_profile="SUBSYSTEM_150", subsystem_id=ss.id,
        layout_hint="BALARAJA_SIDE", drawing_side="B",
    )
    db.add_all([v_kem, v_bal])
    db.flush()

    id_to_code = {s.id: code for code, s in subs.items()}
    circuits_by_id = {c.id: c for c in circuits.values()}
    tier_for = {"K": tier_k, "B": tier_b}

    # a GI is in a side's view if it has a book Tier on that side OR is an
    # endpoint of a circuit drawn on that side
    side_subs: dict[str, set[int]] = {"K": set(), "B": set()}
    for code, s in subs.items():
        if tier_k[code] is not None:
            side_subs["K"].add(s.id)
        if tier_b[code] is not None:
            side_subs["B"].add(s.id)
    for (code, name, ctype, fr, to, kv, txcode, ccnt, sphi, status, conf, side, note) in CIRCUITS:
        side_subs[side].add(subs[fr].id)
        side_subs[side].add(subs[to].id)

    def add_view_members(view: AnalyticalView, side: str):
        tiers = tier_for[side]
        for sid in side_subs[side]:
            code = id_to_code[sid]
            role = role_in_ss[code]
            bt = tiers.get(code)
            # ViewMembership.tier_seed carries the book Tier for this side
            db.add(ViewMembership(
                view_id=view.id, node_kind="SUBSTATION", node_id=sid,
                role=role, tier_seed=bt, display_order=bt,
            ))
        for g in gens.values():
            in_side = (g.outlet_substation_id in side_subs[side]) or (
                g.tap_circuit_id is not None
                and {circuits_by_id[g.tap_circuit_id].from_substation_id,
                     circuits_by_id[g.tap_circuit_id].to_substation_id} & side_subs[side]
            )
            if in_side:
                # a standby plant is not a Tier-1 seed
                seed = 1 if g.status == "ENERGIZED" else None
                db.add(ViewMembership(
                    view_id=view.id, node_kind="GENERATING_UNIT", node_id=g.id,
                    role="SOURCE" if seed else "DOWNSTREAM_CONTEXT",
                    tier_seed=seed, display_order=seed,
                ))

    add_view_members(v_kem, "K")
    add_view_members(v_bal, "B")

    db.commit()
