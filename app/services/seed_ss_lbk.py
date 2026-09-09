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
# Substations
#   (code, name, type, voltage, status, busbar_config, busbar_note,
#    role, external_subsystem, tier_hint, side, has_transformer, has_capacitor,
#    symbol_note, note)
# side: layout view(s) the GI is drawn in -- "K" Kembangan, "B" Balaraja, "KB" both
# ---------------------------------------------------------------------------
SUBSTATIONS = [
    # --- 500 kV source substations ---
    ("GITET_KMBGN", "GITET Kembangan", "GITET", 500, "ENERGIZED", "DOUBLE_1CB", None,
     "SOURCE", None, 1, "K", False, False, None, "GITET 500 kV, 2x IBT 500/150 ke bus Kembangan 150"),
    ("GITET_NBRJA", "GITET New Balaraja", "GITET", 500, "ENERGIZED", "UNKNOWN", None,
     "SOURCE", None, 1, "B", False, False, None, "GITET 500 kV, 2x IBT 500/150 ke bus New Balaraja 150"),

    # --- Tier 1 (150 kV injection points) ---
    ("KMBGN", "Kembangan", "GI", 150, "ENERGIZED", "DOUBLE_1CB", "2 bus, 1 CB kopel, tanpa section",
     "SOURCE", None, 1, "K", False, False, None,
     "Bus 150 kV disuplai IBT-1,2 Kembangan. Kerawanan #1. Ada 1 GI trafo-only tak berlabel di ujung kiri bus (di-skip)."),
    ("NBRJA", "New Balaraja", "GI", 150, "ENERGIZED", "UNKNOWN", None,
     "SOURCE", None, 1, "B", False, False, None, "Bus 150 kV disuplai IBT-1,2 New Balaraja"),
    ("LTKNG", "Lontar", "GI", 150, "ENERGIZED", "UNKNOWN", None,
     "SOURCE", None, 1, "B", False, False, None,
     "GI outlet PLTU Lontar (BUKAN GI Teluknaga). Busbar Tier-1 panjang."),
    ("DKSBI", "Durikosambi", "GI", 150, "ENERGIZED", "DOUBLE_SECTIONALIZED", "Bus 1A / 2A / 1B / 2B",
     "BOUNDARY", "SS Muarakarang 1,2 - Durikosambi 1 - KIT Muarakarang", 1, "KB", True, False, None,
     "GI batas; irisan 2 SLD. Kerawanan #5 (Durikosambi-Cengkareng)."),
    ("PKTGN", "Petukangan", "GI", 150, "ENERGIZED", "UNKNOWN", None,
     "CORE", None, 1, "K", True, False, None,
     "1 GI. Feeder Petukangan-Senayan bermasalah (SKTT rusak); Senayan tetap disuplai dari Kembangan."),

    # --- Tier 2 ---
    ("MTLAN", "Metland", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "K", True, False, None, None),
    ("NSYAN", "New Senayan", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "K", True, False, None,
     "Simpul kerawanan #2 dan #6."),
    ("BLRJA", "Balaraja", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "B", True, False, None, None),
    ("SDJYA", "Sindang Jaya", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "B", True, False, None, None),
    ("TLKNG2_DADAP", "Teluknaga 2 / Dadap", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "B", True, False, None, None),
    ("TGBRU", "Tangerang Baru", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "B", True, False, None, None),
    ("TGBRU_3", "Tangerang Baru 3", "GI", 150, "NEW_NOT_ENERGIZED", "UNKNOWN", None, "CORE", None, 2, "B", False, False, None,
     "Busbar hitam di SLD = belum energize"),
    ("CKNDE", "Cikande", "GI", 150, "ENERGIZED", "UNKNOWN", None, "BOUNDARY",
     "SS GU Cilegon - Cilegon Baru 1,2,3 - Labuan", 2, "B", True, False, None, "GI batas ke SS Cilegon"),

    # --- Tier 3 ---
    ("CLDUG", "Ciledug", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 3, "K", True, True, "1 shunt capacitor", None),
    ("SNYAN", "Senayan", "GIS", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 3, "K", True, False, None,
     "GIS kawasan Zero Down Time (ZDT), disuplai radial dari SKTT New Senayan-Senayan. Kerawanan #6."),
    ("ULJMI", "Ulujami", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 3, "K", True, False, None,
     "GI terpisah dari Senayan; disuplai dari New Senayan. Dead-end load (trafo 150/20 saja)."),
    ("SVRNA", "Suvarna Sutra", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 3, "KB", True, False, None, "Irisan 2 SLD"),
    ("TLKGA", "Teluknaga", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 3, "B", True, True, "1 shunt capacitor",
     "GI Teluknaga (berbeda dari GI Lontar)"),
    ("CKBRU", "Cikupa Baru", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 3, "B", True, False, None, None),
    ("ITS", "KTT ITS", "KTT", 150, "OWNED_BY_CUSTOMER", "UNKNOWN", None, "EXTERNAL_CONTEXT", None, 3, "B", False, False, None,
     "Konsumen tegangan tinggi"),

    # --- Tier 4 ---
    ("ALTRA", "Alam Sutera", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 4, "K", True, False, None, None),
    ("DNYSA", "Danayasa", "GIS", 150, "ENERGIZED", "DOUBLE_1CB", "gap bus section di SLD",
     "BOUNDARY", "SS Gandul 2,4", 4, "K", True, False, None,
     "GI batas -> SS Gandul 2,4. Ruas Mampang-AGP-Danayasa. Dialihkan ke SS Cawang 2,3-Depok 1 saat pemeliharaan Kembangan-New Senayan."),
    ("ABDGP", "Abadi Guna Papan", "GIS", 150, "ENERGIZED", "UNKNOWN", None, "BOUNDARY", "SS Gandul 2,4", 4, "K", False, False, None,
     "GIS AGP. Ruas AGP-Mampang SKTT baru 1000A. Feeder Senayan-AGP masih PLANNED."),
    ("MPANG", "Mampang", "GIS", 150, "ENERGIZED", "UNKNOWN", None, "BOUNDARY", "SS Gandul 2,4", 4, "K", False, False, None,
     "GIS Mampang Baru. Ujung ruas Mampang-AGP-Danayasa."),
    ("CKUPA", "Cikupa", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 4, "KB", True, False, None,
     "Irisan 2 SLD. Kerawanan #4 (Cikupa-Jatake)."),
    ("NCKUPA", "GITET New Cikupa", "GITET", 500, "NEW_NOT_ENERGIZED", "UNKNOWN", None, "CORE", None, 4, "B", False, False, None,
     "GITET (IBT 500/150) BELUM energize -- busbar hitam di SLD. Solusi kerawanan #4: dibangun untuk "
     "menyuntik daya di titik Cikupa-Jatake agar ruas tidak overload. Saat COD nanti = perubahan "
     "struktural (TopologyVersion baru, kemungkinan SS baru) via change request -- BUKAN toggle. "
     "Node disimpan sbg informasi; tidak dihitung dalam Tier kondisi sekarang."),
    ("SPTAN", "Sepatan", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 4, "B", True, False, None, None),
    ("CNKNG", "Cengkareng", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 4, "B", True, False, None,
     "Kerawanan #5 (Durikosambi-Cengkareng)"),
    ("BSH", "BSH", "KTT", 150, "OWNED_BY_CUSTOMER", "UNKNOWN", None, "EXTERNAL_CONTEXT", None, 4, "B", True, False, None,
     "Dalam kotak dashed 'Aset milik KTT'"),

    # --- Tier 5 ---
    ("SGS", "Summarecon Gading Serpong", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "K", True, False, None, None),
    ("CURUG", "Curug", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "K", True, False, None, None),
    ("PSKMS", "Pasar Kemis", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "KB", True, False, None,
     "Irisan 2 SLD. Kerawanan #3 (single phi)."),
    ("PSKBR", "Pasar Kemis Baru", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "B", True, False, None,
     "Kerawanan #3 (Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis single phi)"),
    ("SPTAN2", "Sepatan 2", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "B", True, False, None, "Dead-end load"),
    ("TGRNG", "Tangerang", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "B", True, False, None,
     "GI Tangerang (Lama). Bebannya akan diambil GITET Cikupa (RUPTL). Hotspot #5."),
    ("JTAKE", "Jatake", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 5, "KB", True, True, "2 shunt capacitor",
     "Irisan 2 SLD. Kerawanan #4."),

    # --- Tier 6 ---
    ("MAXIM", "Maxim", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 6, "K", True, False, "3 trafo di SLD (perlu konfirmasi OSL)", None),
    ("JTKBR", "Jatake Baru", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 6, "KB", True, False, None,
     "Tier 6. Disuplai dari Jatake (sisi Kembangan) / Tangerang (sisi Balaraja). Irisan 2 SLD."),
    ("GJTGL", "Gajah Tunggal", "GI", 150, "ENERGIZED", "UNKNOWN", None, "CORE", None, 6, "B", True, False, None,
     "Single phi (kerawanan #3)"),
]
# NOTE: the blurred "ITAKE/ITAKF" label on the Balaraja SLD is GI JATAKE (PDF quality).
# Jatake appears in BOTH SLDs at DIFFERENT tiers:
#   - Kembangan side: Jatake = Tier 5  (Jatake Baru = Tier 6)
#   - Balaraja side:  Jatake drawn as an OUTPUT BAY off Tier 6 (fed from Tangerang)
# This is exactly why Tier is computed per-projection and NOT stored on Substation.
JTAKE_SIDE_OVERRIDE = "KB"  # applied below

# Generating units  (code, name, unit_type, voltage, rated_mw, unit_count, outlet_code, operator)
GENERATORS = [
    ("PLTU_LONTAR", "PLTU Lontar", "PLTU", 150, 945.0, 4, "LTKNG", "PIP"),
]

# Transformers  (code, name, type, substation_code, unit_no, rating_mva, windings[(no,kv,role)])
TRANSFORMERS = [
    ("IBT_KMBGN_1", "IBT 1 Kembangan", "IBT", "KMBGN", "1", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_KMBGN_2", "IBT 2 Kembangan", "IBT", "KMBGN", "2", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_NBRJA_1", "IBT 1 New Balaraja", "IBT", "NBRJA", "1", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_NBRJA_2", "IBT 2 New Balaraja", "IBT", "NBRJA", "2", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
]

# Circuits  (code, name, type, from_code, to_code, kv, transformer_code, circuit_count,
#            single_phi, status, confidence, note)
# Only busbar-to-busbar connections. 150/20 transformers & capacitors are GI attributes.
CIRCUITS = [
    # -- IBT links (500/150 step-down at GITET) --
    ("IBT_KMBGN_1_LINK", "IBT 1 Kembangan 500/150", "IBT_LINK", "GITET_KMBGN", "KMBGN", 500, "IBT_KMBGN_1", None, False, "ENERGIZED", 1.0, None),
    ("IBT_KMBGN_2_LINK", "IBT 2 Kembangan 500/150", "IBT_LINK", "GITET_KMBGN", "KMBGN", 500, "IBT_KMBGN_2", None, False, "ENERGIZED", 1.0, None),
    ("IBT_NBRJA_1_LINK", "IBT 1 New Balaraja 500/150", "IBT_LINK", "GITET_NBRJA", "NBRJA", 500, "IBT_NBRJA_1", None, False, "ENERGIZED", 1.0, None),
    ("IBT_NBRJA_2_LINK", "IBT 2 New Balaraja 500/150", "IBT_LINK", "GITET_NBRJA", "NBRJA", 500, "IBT_NBRJA_2", None, False, "ENERGIZED", 1.0, None),

    # ================= Kembangan side (SLD hal.69) =================
    ("PHT_KMBGN_MTLAN", "Kembangan - Metland", "SKTT", "KMBGN", "MTLAN", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("SKTT_KMBGN_NSYAN", "Kembangan - New Senayan", "SKTT", "KMBGN", "NSYAN", 150, None, 1, False, "ENERGIZED", 1.0, "Kerawanan #2: pembebanan 72%, N-1 tak terpenuhi"),
    ("PHT_KMBGN_DKSBI", "Kembangan - Durikosambi", "SKTT", "KMBGN", "DKSBI", 150, None, 2, False, "ENERGIZED", 0.5, "DKSBI boundary stub"),
    ("PHT_KMBGN_PKTGN", "Kembangan - Petukangan", "SKTT", "KMBGN", "PKTGN", 150, None, 2, False, "ENERGIZED", 0.5, "traced"),
    ("SKTT_NSYAN_SNYAN", "New Senayan - Senayan", "SKTT", "NSYAN", "SNYAN", 150, None, 1, False, "ENERGIZED", 1.0, "Kerawanan #6: GIS Senayan ZDT, radial"),
    ("PHT_NSYAN_CLDUG", "New Senayan - Ciledug", "SKTT", "NSYAN", "CLDUG", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_NSYAN_ULJMI", "New Senayan - Ulujami", "SKTT", "NSYAN", "ULJMI", 150, None, 2, False, "ENERGIZED", 0.6, "Ulujami dead-end load"),
    ("SKTT_PKTGN_SNYAN", "Petukangan - Senayan", "SKTT", "PKTGN", "SNYAN", 150, None, 1, False, "DE_ENERGIZED", 0.5, "Kabel eksisting rusak (teks p8/p87)"),
    ("PHT_SNYAN_DNYSA", "Senayan - Danayasa", "SKTT", "SNYAN", "DNYSA", 150, None, 2, False, "ENERGIZED", 0.5, "DNYSA boundary -> Gandul 2,4"),
    ("PHT_SNYAN_ABDGP", "Senayan - Abadi Guna Papan", "SKTT", "SNYAN", "ABDGP", 150, None, 1, False, "PLANNED", 0.4, "Abu di SLD = perencanaan"),
    ("PHT_CLDUG_ALTRA", "Ciledug - Alam Sutera", "SKTT", "CLDUG", "ALTRA", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_ALTRA_SGS", "Alam Sutera - Summarecon Gading Serpong", "SKTT", "ALTRA", "SGS", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_SGS_CURUG", "Summarecon Gading Serpong - Curug", "SKTT", "SGS", "CURUG", 150, None, 2, False, "ENERGIZED", 0.5, "traced"),
    ("PHT_DNYSA_ABDGP", "Danayasa - Abadi Guna Papan", "SKTT", "DNYSA", "ABDGP", 150, None, 2, False, "ENERGIZED", 0.5, "Ruas Mampang-AGP-Danayasa (teks p91)"),
    ("PHT_ABDGP_MPANG", "Abadi Guna Papan - Mampang", "SKTT", "ABDGP", "MPANG", 150, None, 2, False, "ENERGIZED", 0.5, "SKTT baru 1000A (teks p91)"),
    ("PHT_CKUPA_SVRNA", "Cikupa - Suvarna Sutra", "SKTT", "CKUPA", "SVRNA", 150, None, 2, False, "ENERGIZED", 0.6, "spur"),
    ("PHT_CKUPA_PSKMS", "Cikupa - Pasar Kemis", "SKTT", "CKUPA", "PSKMS", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("SUTT_CKUPA_JTAKE", "Cikupa - Jatake", "SKTT", "CKUPA", "JTAKE", 150, None, 2, False, "ENERGIZED", 1.0, "Kerawanan #4: overload saat N-1-1/N-2 ruas Lontar-Tangerang Baru"),
    ("PHT_JTAKE_MAXIM", "Jatake - Maxim", "SKTT", "JTAKE", "MAXIM", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_JTAKE_JTKBR", "Jatake - Jatake Baru", "SKTT", "JTAKE", "JTKBR", 150, None, 2, False, "ENERGIZED", 0.8, "Jatake T5 -> Jatake Baru T6 (sisi Kembangan)"),

    # ================= Balaraja / Lontar side (SLD hal.70) =================
    ("PHT_NBRJA_BLRJA", "New Balaraja - Balaraja", "SKTT", "NBRJA", "BLRJA", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_LTKNG_SDJYA", "Lontar - Sindang Jaya", "SKTT", "LTKNG", "SDJYA", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_LTKNG_TLKNG2", "Lontar - Teluknaga 2 / Dadap", "SKTT", "LTKNG", "TLKNG2_DADAP", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_LTKNG_TGBRU", "Lontar - Tangerang Baru", "SKTT", "LTKNG", "TGBRU", 150, None, 2, False, "ENERGIZED", 0.7, "Ruas Lontar-Tangerang Baru (disebut di kerawanan #4)"),
    ("PHT_LTKNG_TGBRU3", "Lontar - Tangerang Baru 3", "SKTT", "LTKNG", "TGBRU_3", 150, None, 2, False, "NEW_NOT_ENERGIZED", 0.4, "TGBRU 3 belum energize"),
    ("PHT_BLRJA_CKNDE", "Balaraja - Cikande", "SKTT", "BLRJA", "CKNDE", 150, None, 2, False, "ENERGIZED", 0.5, "CKNDE boundary -> Cilegon"),
    ("PHT_BLRJA_SVRNA", "Balaraja - Suvarna Sutra", "SKTT", "BLRJA", "SVRNA", 150, None, 2, False, "ENERGIZED", 0.5, "traced (cross-routing di SLD)"),
    ("PHT_SDJYA_SVRNA", "Sindang Jaya - Suvarna Sutra", "SKTT", "SDJYA", "SVRNA", 150, None, 2, False, "ENERGIZED", 0.4, "traced"),
    ("PHT_TLKNG2_TLKGA", "Teluknaga 2 / Dadap - Teluknaga", "SKTT", "TLKNG2_DADAP", "TLKGA", 150, None, 2, False, "ENERGIZED", 0.5, "traced"),
    ("PHT_TGBRU_CKBRU", "Tangerang Baru - Cikupa Baru", "SKTT", "TGBRU", "CKBRU", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("PHT_TGBRU_ITS", "Tangerang Baru - KTT ITS", "SKTT", "TGBRU", "ITS", 150, None, 1, False, "ENERGIZED", 0.4, "KTT ITS external"),
    ("PHT_SVRNA_CKUPA", "Suvarna Sutra - Cikupa", "SKTT", "SVRNA", "CKUPA", 150, None, 2, False, "ENERGIZED", 0.6, "traced (irisan)"),
    ("PHT_TLKGA_SPTAN", "Teluknaga - Sepatan", "SKTT", "TLKGA", "SPTAN", 150, None, 2, False, "ENERGIZED", 0.5, "traced"),
    ("SUTT_CKBRU_CNKNG", "Cikupa Baru - Cengkareng", "SKTT", "CKBRU", "CNKNG", 150, None, 2, False, "ENERGIZED", 0.6, "terkait kerawanan #5"),
    ("PHT_CKBRU_BSH", "Cikupa Baru - BSH", "SKTT", "CKBRU", "BSH", 150, None, 1, False, "ENERGIZED", 0.5, "BSH milik KTT"),
    ("SUTT_DKSBI_CNKNG", "Durikosambi - Cengkareng", "SKTT", "DKSBI", "CNKNG", 150, None, 2, False, "ENERGIZED", 1.0, "Kerawanan #5: N-1 tak terpenuhi saat GI Jatake/Jatake Baru/Tangerang/Cengkareng dipasok SS Muarakarang"),
    ("PHT_NCKUPA_JTAKE", "GITET New Cikupa - Jatake (rencana)", "IBT_LINK", "NCKUPA", "JTAKE", 500, None, 2, False, "NEW_NOT_ENERGIZED", 0.4,
     "Future: saat GITET New Cikupa COD, menyuntik di area Cikupa-Jatake. Belum energize."),
    ("PHT_SPTAN_PSKBR", "Sepatan - Pasar Kemis Baru", "SKTT", "SPTAN", "PSKBR", 150, None, 2, False, "ENERGIZED", 0.5, "traced"),
    ("PHT_SPTAN_SPTAN2", "Sepatan - Sepatan 2", "SKTT", "SPTAN", "SPTAN2", 150, None, 2, False, "ENERGIZED", 0.5, "Sepatan 2 dead-end"),
    ("SUTT_PSKMS_PSKBR", "Pasar Kemis - Pasar Kemis Baru", "SKTT", "PSKMS", "PSKBR", 150, None, 1, True, "ENERGIZED", 1.0, "Kerawanan #3: single phi Pasar Kemis Baru-Gajah Tunggal-Pasar Kemis"),
    ("SUTT_PSKBR_GJTGL", "Pasar Kemis Baru - Gajah Tunggal", "SKTT", "PSKBR", "GJTGL", 150, None, 1, True, "ENERGIZED", 1.0, "Kerawanan #3: single phi; KTT Gajah Tunggal padam saat N-1-1"),
    ("SUTT_GJTGL_PSKMS", "Gajah Tunggal - Pasar Kemis", "SKTT", "GJTGL", "PSKMS", 150, None, 1, True, "ENERGIZED", 0.7, "Kerawanan #3: garis tipis semi-hilang di SLD, menutup loop single-phi"),
    ("PHT_CNKNG_TGRNG", "Cengkareng - Tangerang", "SKTT", "CNKNG", "TGRNG", 150, None, 2, False, "ENERGIZED", 0.5, "Hotspot #5"),
    ("PHT_TGRNG_JTKBR", "Tangerang - Jatake Baru", "SKTT", "TGRNG", "JTKBR", 150, None, 2, False, "ENERGIZED", 0.5, "traced"),
    ("PHT_TGRNG_JTAKE", "Tangerang - Jatake", "SKTT", "TGRNG", "JTAKE", 150, None, 2, False, "ENERGIZED", 0.5, "Jatake sebagai output bay dari sisi Balaraja (label PDF blur 'ITAKE' = JTAKE)"),
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
    side_of: dict[str, str] = {}
    role_in_ss: dict[str, str] = {}
    tier_in_ss: dict[str, int] = {}
    for (code, name, stype, kv, status, bcfg, bnote, role, ext_ss, tier, side,
         has_tx, has_cap, sym_note, note) in SUBSTATIONS:
        s = Substation(
            code=code, name=name, substation_type=stype, voltage_kv=kv, status=status,
            busbar_config=bcfg, busbar_note=bnote,
            has_transformer=has_tx, has_shunt_capacitor=has_cap, symbol_note=sym_note,
            apb="UP2B Jakarta & Banten", uit="JBB", note=note, confidence=1.0,
        )
        db.add(s)
        subs[code] = s
        side_of[code] = "KB" if code == "JTAKE" else side
        role_in_ss[code] = role
        tier_in_ss[code] = tier
        db.flush()
        db.add(SubsystemMembership(
            subsystem_id=ss.id, node_kind="SUBSTATION", node_id=s.id,
            role=role, external_subsystem=ext_ss, display_order=tier,
        ))

    gens: dict[str, GeneratingUnit] = {}
    for (code, name, utype, kv, mw, ucnt, outlet, op) in GENERATORS:
        g = GeneratingUnit(
            code=code, name=name, unit_type=utype, voltage_kv=kv, rated_mw=mw,
            unit_count=ucnt, outlet_substation_id=subs[outlet].id, operator=op,
        )
        db.add(g)
        gens[code] = g
    db.flush()
    for code in gens:
        db.add(SubsystemMembership(
            subsystem_id=ss.id, node_kind="GENERATING_UNIT", node_id=gens[code].id,
            role="SOURCE", display_order=1,
        ))

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
    for (code, name, ctype, fr, to, kv, txcode, ccnt, sphi, status, conf, note) in CIRCUITS:
        c = Circuit(
            code=code, name=name, circuit_type=ctype, voltage_kv=kv,
            from_substation_id=subs[fr].id, to_substation_id=subs[to].id,
            transformer_id=txs[txcode].id if txcode else None,
            circuit_count=ccnt, single_phi=sphi, status=status, scenario_id="NORMAL",
            source_document_id=doc.id,
            note=("NEEDS_REVIEW; " + (note or "")) if conf < 0.9 else note,
            confidence=conf,
        )
        db.add(c)
        circuits[code] = c
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

    # ---- analytical views: 2 layout projections of the same SS graph -------
    v_kem = AnalyticalView(
        view_key=f"{SS_CODE}_KEMBANGAN", view_type="SUBSYSTEM",
        name="SS Lontar-Balaraja-Kembangan - sisi Kembangan (SLD hal.69)",
        rule_profile="SUBSYSTEM_150", subsystem_id=ss.id, layout_hint="KEMBANGAN_SIDE",
    )
    v_bal = AnalyticalView(
        view_key=f"{SS_CODE}_BALARAJA", view_type="SUBSYSTEM",
        name="SS Lontar-Balaraja-Kembangan - sisi Balaraja/Lontar (SLD hal.70)",
        rule_profile="SUBSYSTEM_150", subsystem_id=ss.id, layout_hint="BALARAJA_SIDE",
    )
    v_all = AnalyticalView(
        view_key=f"{SS_CODE}_FULL", view_type="SUBSYSTEM",
        name="SS Lontar-Balaraja-Kembangan - gabungan",
        rule_profile="SUBSYSTEM_150", subsystem_id=ss.id, layout_hint="MERGED",
    )
    db.add_all([v_kem, v_bal, v_all])
    db.flush()

    def add_view_members(view: AnalyticalView, sides: set[str]):
        for code, s in subs.items():
            sd = side_of[code]
            if not (sd in sides or sd == "KB" or sides == {"K", "B"}):
                continue
            role = role_in_ss[code]
            seed = 1 if role == "SOURCE" and tier_in_ss[code] == 1 else None
            db.add(ViewMembership(
                view_id=view.id, node_kind="SUBSTATION", node_id=s.id,
                role=role, tier_seed=seed, display_order=tier_in_ss[code],
            ))
        for code, g in gens.items():
            db.add(ViewMembership(
                view_id=view.id, node_kind="GENERATING_UNIT", node_id=g.id,
                role="SOURCE", tier_seed=1, display_order=1,
            ))

    add_view_members(v_kem, {"K"})
    add_view_members(v_bal, {"B"})
    add_view_members(v_all, {"K", "B"})

    db.commit()
