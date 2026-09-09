"""Seed: Subsistem Balaraja 3,4 - Lengkong 1,2  (SS_BLL).

Source: Buku Kerawanan SJB 2026, section 2.6
    - hal. 72  SLD (Gambar 2.5)  -- ONE drawing (no K/B split like SS_LBK)
    - Tabel 2.4 (hal. 71-72)     -- 1 titik kerawanan

Two independent Tier-1 sources -- the hallmark of a proper subsystem, each from
a different GITET:
    GITET New Balaraja (IBT 3,4)  ->  bus New Balaraja (NBRJA)
    GITET Lengkong     (IBT 1,2)  ->  bus Lengkong Baru (LKBRU)
They are NOT tied at Tier-1. The two halves meet only far downstream, at Tier-5,
through a normal 2-sirkit penghantar Citra Habitat - Sinar Sahabat (bukan
bus-tie).

Edge confidence:
    1.0  = stated in the vulnerability table or unambiguous in the SLD
    0.7  = traced from the SLD and confirmed with the user
    0.6  = traced from the SLD, plausible
    0.5  = traced from the SLD, uncertain  -> NEEDS_REVIEW
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    AnalyticalView,
    Bay,
    ChangeSet,
    Circuit,
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

SS_CODE = "SS_BLL"

# ---------------------------------------------------------------------------
# Substations. `tier` = the Tier band the GI's busbar sits in on the SLD
# (hal.72). The book's drawing is the authority for the risk map -- we
# reproduce it, we do not recompute it.
#   fields: code, name, type, voltage, status, busbar_config, busbar_note,
#           role, external_subsystem, tier, has_transformer, has_capacitor,
#           symbol_note, note
# `role` SOURCE  -> Tier-1 seed;  EXTERNAL_CONTEXT -> context stub (bay only).
# ---------------------------------------------------------------------------
SUBSTATIONS = [
    # --- 500 kV sources (GITET) ---
    dict(code="GITET_NBRJA", name="GITET New Balaraja", type="GITET", voltage=500, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET 500 kV, 2x IBT 500/150 (unit 3,4) ke bus New Balaraja 150."),
    dict(code="GITET_LKONG", name="GITET Lengkong", type="GITET", voltage=500, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET 500 kV, 2x IBT 500/150 (unit 1,2) ke bus Lengkong Baru 150."),

    # --- Tier 1 (150 kV injection points) ---
    dict(code="NBRJA", name="New Balaraja", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Bus 150 kV disuplai IBT-3,4 New Balaraja (SS Lontar). "
              "TIDAK tersambung ke Lengkong Baru di Tier-1 -- sumber SS harus berbeda."),
    dict(code="LKBRU", name="Lengkong Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Bus 150 kV disuplai IBT-1,2 GITET Lengkong."),

    # --- Tier 2 ---
    dict(code="LSTEL", name="Lautan Steel", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=False, symbol_note="KTT LSI 129,6 MVA (kotak dashed)",
         note="Sisi Balaraja. KTT Lautan Steel Indonesia 129,6 MVA nyantol (konsumen)."),
    dict(code="LKONG", name="Lengkong", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=True, symbol_note="1 kapasitor NON-AKTIF (abu di SLD)",
         note="Sisi Lengkong. Kapasitor digambar abu = non-aktif."),
    dict(code="SRPNG", name="Serpong", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=True, symbol_note="1 kapasitor aktif",
         note="Sisi Lengkong. Kerawanan #1: bottleneck MTU bay Lengkong II sirkit 2 "
              "(I nom 1858 A derating 1000 A, CT masih 1000 A). Fleksibilitas pasokan lewat "
              "SS Gandul 1,3-Durikosambi 2 dan SS Lontar (via New Balaraja)."),

    # --- Tier 3 ---
    dict(code="SPMIL", name="Spinmill", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=3,
         has_transformer=True, has_capacitor=False, symbol_note="KTT SPNML 50 MVA (kotak dashed)",
         note="Sisi Balaraja (dari Lautan Steel). KTT Spinmill 50 MVA nyantol."),
    dict(code="BSD", name="BSD", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=3,
         has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Sisi Lengkong (dari Lengkong)."),

    # --- Tier 4 ---
    dict(code="MLNUM", name="Millenium", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=4,
         has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Dari Spinmill. Punya PHT ke GI Citra Habitat (Tier-5)."),
    dict(code="LEGOK", name="Legok", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=4,
         has_transformer=True, has_capacitor=True, symbol_note="2 kapasitor aktif + 1 trafo",
         note="Dari BSD. Hanya menyuplai GI Sinar Sahabat."),

    # --- Tier 5 (the two SS halves meet here, via a normal penghantar) ---
    dict(code="CITRA", name="Citra Habitat", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=5,
         has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Sisi Balaraja (dari Millenium). Terhubung ke Sinar Sahabat lewat penghantar "
              "2 sirkit NORMAL (bukan bus-tie). Menyuplai GI Tigaraksa."),
    dict(code="SSBAT", name="Sinar Sahabat", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=5,
         has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Sisi Lengkong (dari Legok). Terhubung ke Citra Habitat lewat penghantar "
              "2 sirkit NORMAL (bukan bus-tie) -- titik temu dua sisi SS."),

    # --- Tier 6 ---
    dict(code="TGRSA", name="Tigaraksa", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=6,
         has_transformer=True, has_capacitor=True, symbol_note="1 kapasitor + 1 trafo",
         note="Dari Citra Habitat."),
    dict(code="TGRSA2", name="Tigaraksa 2", type="GI", voltage=150, status="NEW_NOT_ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=6,
         has_transformer=True, has_capacitor=False, symbol_note=None,
         note="Busbar hitam di SLD = belum energize. Digantung di bawah Tigaraksa (2 sirkit hitam)."),

    # --- bay-only GIs (drawn as a stub, no busbar of their own) ---
    dict(code="BLRJA", name="Balaraja", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Digambar sbg bay menggantung di bus New Balaraja (GI masuk SS lain juga)."),
    dict(code="SWGAN", name="Sawangan", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None, tier=2,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Digambar sbg bay menggantung di bus Serpong (GI masuk SS lain juga)."),
    dict(code="BNTRO", name="Bintaro", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None, tier=2,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Digambar sbg bay menggantung di bus Serpong (GI masuk SS lain juga)."),
]

# Transformers  (code, name, type, substation_code, unit_no, rating_mva, windings[(no,kv,role)])
TRANSFORMERS = [
    ("IBT_NBRJA_3", "IBT 3 New Balaraja", "IBT", "NBRJA", "3", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_NBRJA_4", "IBT 4 New Balaraja", "IBT", "NBRJA", "4", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_LKONG_1", "IBT 1 Lengkong", "IBT", "LKBRU", "1", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_LKONG_2", "IBT 2 Lengkong", "IBT", "LKBRU", "2", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
]

# Circuits  (code, name, type, from_code, to_code, kv, transformer_code, circuit_count,
#            single_phi, status, confidence, note)
# Only busbar-to-busbar. 150/20 transformers & capacitors are GI attributes.
CIRCUITS = [
    # -- IBT links (500/150 step-down at the GITETs) --
    ("IBT_NBRJA_3_LINK", "IBT 3 New Balaraja 500/150", "IBT_LINK", "GITET_NBRJA", "NBRJA", 500, "IBT_NBRJA_3", None, False, "ENERGIZED", 1.0, None),
    ("IBT_NBRJA_4_LINK", "IBT 4 New Balaraja 500/150", "IBT_LINK", "GITET_NBRJA", "NBRJA", 500, "IBT_NBRJA_4", None, False, "ENERGIZED", 1.0, None),
    ("IBT_LKONG_1_LINK", "IBT 1 Lengkong 500/150", "IBT_LINK", "GITET_LKONG", "LKBRU", 500, "IBT_LKONG_1", None, False, "ENERGIZED", 1.0, None),
    ("IBT_LKONG_2_LINK", "IBT 2 Lengkong 500/150", "IBT_LINK", "GITET_LKONG", "LKBRU", 500, "IBT_LKONG_2", None, False, "ENERGIZED", 1.0, None),

    # ================= sisi Balaraja (New Balaraja) =================
    ("SUTT_NBRJA_LSTEL", "New Balaraja - Lautan Steel", "SUTT", "NBRJA", "LSTEL", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("SUTT_LSTEL_SPMIL", "Lautan Steel - Spinmill", "SUTT", "LSTEL", "SPMIL", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("SUTT_SPMIL_MLNUM", "Spinmill - Millenium", "SUTT", "SPMIL", "MLNUM", 150, None, 2, False, "ENERGIZED", 0.7, "dikonfirmasi user"),
    ("SUTT_MLNUM_CITRA", "Millenium - Citra Habitat", "SUTT", "MLNUM", "CITRA", 150, None, 2, False, "ENERGIZED", 0.7, "PHT Millenium-Citra Habitat (dikonfirmasi user)"),
    ("SUTT_CITRA_TGRSA", "Citra Habitat - Tigaraksa", "SUTT", "CITRA", "TGRSA", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("SUTT_TGRSA_TGRSA2", "Tigaraksa - Tigaraksa 2", "SUTT", "TGRSA", "TGRSA2", 150, None, 2, False, "NEW_NOT_ENERGIZED", 0.5, "TGRSA2 belum energize (busbar & garis hitam)"),

    # ================= sisi Lengkong (Lengkong Baru) =================
    ("SUTT_LKBRU_LKONG", "Lengkong Baru - Lengkong", "SUTT", "LKBRU", "LKONG", 150, None, 2, False, "ENERGIZED", 0.6, "traced (ruas Lengkong I)"),
    ("SUTT_LKBRU_SRPNG", "Lengkong Baru - Serpong", "SUTT", "LKBRU", "SRPNG", 150, None, 2, False, "ENERGIZED", 1.0,
     "Ruas Lengkong II. Kerawanan #1: bottleneck MTU di bay Lengkong II sirkit 2 di GI Serpong. "
     "Dioperasikan radial sesuai kemampuan penghantar eksisting."),
    ("SUTT_LKONG_BSD", "Lengkong - BSD", "SUTT", "LKONG", "BSD", 150, None, 2, False, "ENERGIZED", 0.6, "traced"),
    ("SUTT_BSD_LEGOK", "BSD - Legok", "SUTT", "BSD", "LEGOK", 150, None, 2, False, "ENERGIZED", 0.7, "Legok dapat dari BSD (dikonfirmasi user)"),
    ("SUTT_LEGOK_SSBAT", "Legok - Sinar Sahabat", "SUTT", "LEGOK", "SSBAT", 150, None, 2, False, "ENERGIZED", 0.7, "Legok hanya menyuplai Sinar Sahabat (dikonfirmasi user)"),

    # ================= titik temu dua sisi (Tier-5) =================
    ("SUTT_CITRA_SSBAT", "Citra Habitat - Sinar Sahabat", "SUTT", "CITRA", "SSBAT", 150, None, 2, False, "ENERGIZED", 0.8,
     "Penghantar 2 sirkit NORMAL antara sisi Balaraja (Citra Habitat) dan sisi Lengkong (Sinar Sahabat). "
     "BUKAN bus-tie. Siapa menyuplai siapa tergantung pola operasi -- di luar lingkup model ini."),
]

# Risk records  (seq, title, condition, impact, mitigation, follow_up, priority,
#                attach_kind, attach_code)
RISKS = [
    (1, "Bottleneck MTU di GI Serpong bay Lengkong II sirkit 2",
     "Terdapat bottle neck ruas transmisi karena keterbatasan kapasitas MTU "
     "(I nominal 1858 A derating menjadi 1000 A dikarenakan CT masih 1000 A) di "
     "GI 150 kV Serpong bay Lengkong II sirkit 2. Fleksibilitas pasokan beban melalui "
     "GI Serpong (SS Gandul 1,3-Durikosambi 2) dan GI New Balaraja (SS Lontar).",
     "Fleksibilitas operasi antara Sub Sistem Balaraja 3,4-Lengkong 1,2 dengan Sub Sistem "
     "Gandul 1,3-Durikosambi 2 menjadi berkurang.",
     "1. Pengoperasian radial SUTT Lengkong II-Serpong sesuai dengan kemampuan penghantar eksisting. "
     "2. Pemeliharaan SUTT dilaksanakan saat periode beban rendah.",
     "Jangka Pendek: Usulan penggantian MTU di GI Serpong bay Lengkong II sesuai kapasitas "
     "penghantar SUTT 150 kV Lengkong II-Serpong (diusulkan COD 2027).",
     "Medium", "CIRCUIT", "SUTT_LKBRU_SRPNG"),
]

# Bays: a small GI drawn only as a stub on a feeder busbar (no busbar of its own).
#   (gi_code, feeder_code, status, note)
BAYS = [
    ("BLRJA", "NBRJA", "ENERGIZED", "Bay Balaraja menggantung di bus New Balaraja"),
    ("SWGAN", "SRPNG", "ENERGIZED", "Bay Sawangan menggantung di bus Serpong"),
    ("BNTRO", "SRPNG", "ENERGIZED", "Bay Bintaro menggantung di bus Serpong"),
]


def seed_ss_bll(db: Session) -> None:
    if db.query(Subsystem).filter(Subsystem.code == SS_CODE).first():
        return

    doc = SourceDocument(
        filename="Buku Kerawanan SJB Tahun 2026.pdf",
        document_type="SLD_PDF_PAGE",
        analytical_hint="SUBSYSTEM_150",
        source_ref="Buku Kerawanan SJB 2026 hal.71-72 (Sec 2.6)",
        effective_date="2026-06-30",
    )
    db.add(doc)
    db.flush()

    ss = Subsystem(
        code=SS_CODE,
        name="Balaraja 3,4 - Lengkong 1,2",
        apb="UP2B Jakarta & Banten",
        source_ref="Buku Kerawanan SJB 2026 Sec 2.6",
    )
    db.add(ss)
    db.flush()

    tv = TopologyVersion(
        version_key="TV-SS_BLL-2026-06",
        status="ACTIVE",
        effective_date="2026-06-30",
        description="Baseline SS Balaraja 3,4-Lengkong 1,2 dari Buku Kerawanan SJB 2026 Sec 2.6 "
        "(traced from Gambar 2.5 hal.72; edge confidence-tagged, pending field review).",
    )
    db.add(tv)
    db.flush()
    db.add(ChangeSet(
        change_key="CR-SS_BLL-001", version_id=tv.id, action="MODEL",
        target_kind="SUBSTATION", target_ref="TGRSA2",
        description="GI Tigaraksa 2 belum energize (busbar hitam). Saat COD = perubahan struktural "
        "via change request, bukan toggle. Tidak dihitung Tier pada kondisi sekarang.",
        status="PROPOSED",
    ))

    # A GI can be shared across subsystems -- New Balaraja / Balaraja are also
    # Tier-1 in SS_LBK. Reuse the existing canonical Substation when present;
    # only add this subsystem's own membership + view row for it. Same for a
    # shared transformer.
    subs: dict[str, Substation] = {}
    role_in_ss: dict[str, str] = {}
    tier_of: dict[str, int | None] = {}
    for d in SUBSTATIONS:
        s = db.query(Substation).filter(Substation.code == d["code"]).first()
        if s is None:
            s = Substation(
                code=d["code"], name=d["name"], substation_type=d["type"], voltage_kv=d["voltage"],
                status=d["status"], busbar_config=d["busbar_config"], busbar_note=d["busbar_note"],
                has_transformer=d["has_transformer"], has_shunt_capacitor=d["has_capacitor"],
                symbol_note=d["symbol_note"], apb="UP2B Jakarta & Banten", uit="JBB",
                note=d["note"], confidence=1.0,
            )
            db.add(s)
            db.flush()
        subs[d["code"]] = s
        role_in_ss[d["code"]] = d["role"]
        tier_of[d["code"]] = d["tier"]
        db.add(SubsystemMembership(
            subsystem_id=ss.id, node_kind="SUBSTATION", node_id=s.id,
            role=d["role"], external_subsystem=d["external_subsystem"],
            display_order=d["tier"],
        ))

    txs: dict[str, Transformer] = {}
    for (code, name, ttype, scode, unit, mva, windings) in TRANSFORMERS:
        t = db.query(Transformer).filter(Transformer.code == code).first()
        if t is None:
            t = Transformer(
                code=code, name=name, transformer_type=ttype, substation_id=subs[scode].id,
                unit_no=unit, rating_mva=mva, winding_count=len(windings),
            )
            db.add(t)
            db.flush()
            for (wno, wkv, wrole) in windings:
                db.add(TransformerWinding(transformer_id=t.id, winding_no=wno, voltage_kv=wkv, role=wrole))
        txs[code] = t
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
            drawing_side=None, source_document_id=doc.id,
            note=("NEEDS_REVIEW; " + (note or "")) if conf < 0.9 else note,
            confidence=conf,
        )
        db.add(c)
        circuits[code] = c
    db.flush()

    for (gi, feeder, status, note) in BAYS:
        db.add(Bay(
            substation_id=subs[gi].id, feeder_substation_id=subs[feeder].id,
            subsystem_id=ss.id,
            name=f"Bay {subs[gi].name} @ {subs[feeder].name}", bay_type="LINE",
            drawing_side=None, status=status, note=note,
        ))
    db.flush()

    def resolve(kind: str, code: str):
        return {"SUBSTATION": subs, "TRANSFORMER": txs, "CIRCUIT": circuits}.get(kind, {}).get(code)

    for (seq, title, cond, impact, mit, fu, prio, akind, acode) in RISKS:
        obj = resolve(akind, acode)
        db.add(RiskRecord(
            risk_key=f"RISK-{SS_CODE}-{seq:02d}",
            subsystem_id=ss.id, seq_no=seq, uit="JBB",
            attach_kind=akind, attach_id=(obj.id if obj else None), attach_label=acode,
            title=title, condition=cond, impact=impact, mitigation=mit, follow_up=fu,
            priority=prio, status="OPEN", source_document_id=doc.id,
        ))

    # ---- analytical view: ONE layout projection (the SLD is a single drawing) ----
    view = AnalyticalView(
        view_key=f"{SS_CODE}_FULL", view_type="SUBSYSTEM",
        name="SS Balaraja 3,4 - Lengkong 1,2 (SLD hal.72)",
        rule_profile="SUBSYSTEM_150", subsystem_id=ss.id,
        layout_hint="MERGED", drawing_side=None,
    )
    db.add(view)
    db.flush()

    for code, s in subs.items():
        db.add(ViewMembership(
            view_id=view.id, node_kind="SUBSTATION", node_id=s.id,
            role=role_in_ss[code],
            tier_seed=tier_of[code],
            display_order=tier_of[code],
        ))

    db.commit()
