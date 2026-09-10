"""Seed: Subsistem Cawang 2,3 - Depok 1  (SS_CWD).

Source: Buku Kerawanan SJB 2026, section 2.7
    - SLD  (Gambar 2.6)  -- ONE drawing, tidak ada split K/B
    - Tabel 2.5          -- 4 titik kerawanan (semua UIT JBB)

*** PARSER TEST -- traced AS-IS from the drawing + table, no topology
correction. Relations traced aggressively (garis nyilang & dashed di buku
tetap ditarik sebagai edge). Anything genuinely unreadable is left out and
falls into the mapping-audit strip. This file is NOT wired into seed.py. ***

Two independent Tier-1 sources:
    GITET Depok  (IBT 1)      ->  bus Depok (DEPOK)
    GITET Cawang (IBT 2 & 3)  ->  bus Cawang Baru (CWBRU)

Edge confidence:
    1.0  = stated in the vulnerability table
    0.6  = traced from the SLD, garis penuh, arah jelas
    0.5  = traced from the SLD, garis dashed / nyilang / arah ambigu -> NEEDS_REVIEW
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

SS_CODE = "SS_CWD"

# ---------------------------------------------------------------------------
# Substations. `tier` = the Tier band the GI's busbar sits in on the SLD.
#   fields: code, name, type, voltage, status, busbar_config, busbar_note,
#           role, external_subsystem, tier, has_transformer, has_capacitor,
#           symbol_note, note
# ---------------------------------------------------------------------------
SUBSTATIONS = [
    # --- 500 kV sources (GITET) ---
    dict(code="GITET_DEPOK", name="GITET Depok", type="GITET", voltage=500, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET 500 kV. 1x IBT 500/150 (unit 1) ke bus Depok 150 kV."),
    dict(code="GITET_CWANG", name="GITET Cawang", type="GITET", voltage=500, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GITET 500 kV. 2x IBT 500/150 (unit 2,3) ke bus Cawang Baru 150 kV. "
              "Bintang kerawanan #1 di kedua IBT."),

    # --- Tier 1 (150 kV injection points) ---
    dict(code="DEPOK", name="Depok", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Bus 150 kV disuplai IBT-1 Depok. Busbar biru di SLD = 500 kV di atasnya, "
              "bus 150 kV Depok di Tier-1."),
    dict(code="CWBRU", name="Cawang Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="SOURCE", external_subsystem=None, tier=1,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Bus 150 kV disuplai IBT-2,3 Cawang. Bintang kerawanan #1 (IBT 2-3 Cawang vs "
              "IBT 1 Depok tidak seimbang -> tidak memenuhi N-1)."),

    # --- Tier 2 ---
    dict(code="CWANG", name="Cawang Lama", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="DOUBLE_1CB", busbar_note="ada kopel (kotak putih di SLD)",
         role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=True,
         symbol_note="3x kapasitor 50 MVAr + 1 trafo. Bay LKONG2 menggantung.",
         note="Cawang Lama. Bintang kerawanan #2 di ruas Depok-Cawang Lama (SUTT ACSR Drake "
              "T.1-10, 17 km, pembebanan >60% -> tidak N-1)."),
    dict(code="TRSNA", name="Taman Rasuna", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo",
         note="Taman Rasuna. Disebut di kerawanan #3 (ruas Cawang Baru-Taman Rasuna, N-2)."),
    dict(code="DRNTG", name="Duren Tiga", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo",
         note="Duren Tiga. Beberapa ruas ke/dari Duren Tiga digambar garis putus-putus (dashed) "
              "di buku."),
    dict(code="ABDGP", name="Abadi Guna Papan", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=2,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo",
         note="Abadi Guna Papan (AGP). Bintang kerawanan #3 di area bus AGP. Bottleneck MTU "
              "GIS Danayasa / GIS AGP / GIS Mampang Baru (CT & line bay 600 A vs rencana uprating "
              "SKTT 1000 A)."),

    # --- Tier 3 ---
    dict(code="STBDI", name="Setiabudi", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=3,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo. Bay DKTAS menggantung.",
         note="Setiabudi. Bintang kerawanan #4 di ruas Setiabudi-Dukuh Atas (I nominal kecil "
              "480 A -> tidak N-1 saat GIS 150 kV Dukuh Atas dipasok SS Cawang 2,3-Depok 1)."),
    dict(code="MPLMA", name="Mampang Lama", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=3,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo. Bay KRLMA menggantung.",
         note="Mampang Lama (di SLD 'MPLMA'; aslinya GI Mampang, dibedakan dari Mampang Baru)."),
    dict(code="MPBRU", name="Mampang Baru", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=3,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo",
         note="Mampang Baru. GIS. Termasuk bottleneck MTU di kerawanan #3."),
    dict(code="DNYSA", name="Danayasa", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="CORE", external_subsystem=None, tier=3,
         has_transformer=True, has_capacitor=False, symbol_note="1 trafo",
         note="Danayasa. GIS. Bintang kerawanan #3 di bus Danayasa. Termasuk bottleneck MTU "
              "(CT & line bay 600 A)."),

    # --- bay-only GIs (drawn as a stub under a Tier-3 busbar) ---
    dict(code="LKONG2", name="Lengkong 2", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None, tier=2,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Digambar sbg bay menggantung di bus Cawang Lama."),
    dict(code="KRLMA", name="Karet Lama", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None, tier=3,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="Digambar sbg bay menggantung di bus Mampang Lama."),
    dict(code="DKTAS", name="Dukuh Atas", type="GI", voltage=150, status="ENERGIZED",
         busbar_config="UNKNOWN", busbar_note=None, role="EXTERNAL_CONTEXT", external_subsystem=None, tier=3,
         has_transformer=False, has_capacitor=False, symbol_note=None,
         note="GIS 150 kV Dukuh Atas. Digambar sbg bay menggantung di bus Setiabudi. "
              "Kerawanan #4."),
]

# Transformers  (code, name, type, substation_code, unit_no, rating_mva, windings)
TRANSFORMERS = [
    ("IBT_DEPOK_1", "IBT 1 Depok", "IBT", "DEPOK", "1", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_CWANG_2", "IBT 2 Cawang", "IBT", "CWBRU", "2", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
    ("IBT_CWANG_3", "IBT 3 Cawang", "IBT", "CWBRU", "3", 500.0, [(1, 500, "HV"), (2, 150, "LV")]),
]

# Circuits  (code, name, type, from_code, to_code, kv, transformer_code,
#            circuit_count, single_phi, status, confidence, note)
CIRCUITS = [
    # -- IBT links (500/150 step-down at the GITETs) --
    ("IBT_DEPOK_1_LINK", "IBT 1 Depok 500/150", "IBT_LINK", "GITET_DEPOK", "DEPOK", 500, "IBT_DEPOK_1", None, False, "ENERGIZED", 1.0, None),
    ("IBT_CWANG_2_LINK", "IBT 2 Cawang 500/150", "IBT_LINK", "GITET_CWANG", "CWBRU", 500, "IBT_CWANG_2", None, False, "ENERGIZED", 1.0, None),
    ("IBT_CWANG_3_LINK", "IBT 3 Cawang 500/150", "IBT_LINK", "GITET_CWANG", "CWBRU", 500, "IBT_CWANG_3", None, False, "ENERGIZED", 1.0, None),

    # ================= dari Depok (Tier-1 -> Tier-2) =================
    ("SUTT_DEPOK_CWANG", "Depok - Cawang Lama", "SUTT", "DEPOK", "CWANG", 150, None, 2, False, "ENERGIZED", 1.0,
     "SUTT 150 kV Depok-Cawang Lama, ACSR Drake T.1-10 (17 km), I nominal 1230 A. "
     "Kerawanan #2: pembebanan >60% -> tidak memenuhi N-1."),

    # ================= dari Cawang Baru (Tier-1 -> Tier-2) =================
    ("SUTT_CWBRU_TRSNA", "Cawang Baru - Taman Rasuna", "SUTT", "CWBRU", "TRSNA", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD (garis dari area Cawang Baru turun ke Taman Rasuna). Disebut di "
     "kerawanan #3 (ruas Cawang Baru-Taman Rasuna, kondisi N-2)."),
    ("SUTT_CWBRU_DRNTG", "Cawang Baru - Duren Tiga", "SUTT", "CWBRU", "DRNTG", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD, garis putus-putus (dashed) di buku antara Cawang Baru dan Duren Tiga."),

    # ================= Tier-2 sehadap (same tier) =================
    ("SUTT_CWANG_TRSNA", "Cawang Lama - Taman Rasuna", "SUTT", "CWANG", "TRSNA", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD (garis mendatar Tier-2 Cawang Lama <-> Taman Rasuna). Arah/POV ambigu."),
    ("SUTT_DRNTG_ABDGP", "Duren Tiga - Abadi Guna Papan", "SUTT", "DRNTG", "ABDGP", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD (garis mendatar Tier-2 Duren Tiga <-> AGP), sebagian dashed."),

    # ================= Tier-2 -> Tier-3 =================
    ("SUTT_CWANG_STBDI", "Cawang Lama - Setiabudi", "SUTT", "CWANG", "STBDI", 150, None, 2, False, "ENERGIZED", 0.6,
     "Ditarik dari SLD (2 sirkit turun dari Cawang Lama ke Setiabudi)."),
    ("SUTT_DRNTG_MPLMA", "Duren Tiga - Mampang Lama", "SUTT", "DRNTG", "MPLMA", 150, None, 2, False, "ENERGIZED", 0.6,
     "Ditarik dari SLD (2 sirkit turun dari Duren Tiga ke Mampang Lama)."),
    ("SUTT_ABDGP_MPBRU", "Abadi Guna Papan - Mampang Baru", "SUTT", "ABDGP", "MPBRU", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD (turun dari AGP ke Mampang Baru), garis dashed. Bottleneck MTU (kerawanan #3)."),
    ("SUTT_ABDGP_DNYSA", "Abadi Guna Papan - Danayasa", "SUTT", "ABDGP", "DNYSA", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD (turun dari AGP ke Danayasa). Bottleneck MTU (kerawanan #3)."),

    # ================= Tier-3 sehadap =================
    ("SUTT_MPLMA_MPBRU", "Mampang Lama - Mampang Baru", "SUTT", "MPLMA", "MPBRU", 150, None, 2, False, "ENERGIZED", 0.5,
     "Ditarik dari SLD (garis mendatar Tier-3 Mampang Lama <-> Mampang Baru), garis dashed. "
     "Ruas pht Mampang-AGP-Danayasa disebut di kerawanan #3 (rencana uprating 1000 A)."),
]

# Risk records  (seq, title, condition, impact, mitigation, follow_up, priority,
#                attach_kind, attach_code)
RISKS = [
    (1, "Pembebanan IBT 2-3 Cawang dengan IBT 1 Depok tidak seimbang -> tidak N-1",
     "Pembebanan IBT 2-3 Cawang dengan IBT 1 Depok tidak seimbang sehingga tidak memenuhi kriteria N-1.",
     "1. Pemeliharaan IBT 2 atau 3 Cawang sulit dilakukan. "
     "2. Terjadi Overload pada IBT 2 atau 3 Cawang jika terjadi gangguan N-1.",
     "1. Penjadwalan pemeliharaan dilakukan pada periode beban rendah. "
     "2. Looping dengan Sub Sistem Muarakarang saat terdapat pekerjaan IBT di Sub sistem terkait. "
     "3. Telah terpasang skema OLS pada IBT-2,3 Cawang-Depok 1 tahap 1-4 dengan total target 294 MW "
     "(berdasarkan buku DS Tahun 2025). "
     "4. Rencana penambahan skema OLS pada OLS IBT-2,3 Cawang-Depok 1 dengan total target 388 MW "
     "(berdasarkan buku DS Tahun 2025).",
     "Jangka Pendek: 1. Percepatan pembangunan Proyek Uprating SUTT/SKTT ex-70 kV ke SUTT/SKTT 150 kV "
     "Ragunan-Cawang Baru (RUPTL 2025-2034, COD 2026). "
     "2. Pembangunan GITET Citeureup beserta outlet (RUPTL 2025-2034 COD 2028).",
     "High", "TRANSFORMER", "IBT_CWANG_2"),

    (2, "SUTT Depok-Cawang Lama (ACSR Drake, 17 km) pembebanan >60% -> tidak N-1",
     "Sebagian penghantar berjenis ACSR Drake T.1-10 (17 km) I nominal 1230 A dan saat ini "
     "pembebanan SUTT 150 kV Depok-Cawang Lama diatas 60% sehingga tidak memenuhi kriteria N-1.",
     "Terjadi Overload pada SUTT Depok-Cawang Lama jika terjadi trip 1 sirkit pada salah satu ruas tersebut.",
     "1. Penjadwalan pemeliharaan periode beban rendah. "
     "2. Telah terpasang skema OLS pada SUTT 150 kV Depok-Cawang Lama tahap 1-4 dengan total target 294 MW "
     "(berdasarkan buku DS Tahun 2025). "
     "3. Rencana penambahan skema OLS dengan total target 319 MW (berdasarkan buku DS Tahun 2025).",
     "Jangka Pendek: Percepatan pembangunan Proyek Uprating SUTT/SKTT ex-70 kV ke SUTT/SKTT 150 kV "
     "Ragunan-Cawang Baru (RUPTL 2025-2034, COD 2026).",
     "High", "CIRCUIT", "SUTT_DEPOK_CWANG"),

    (3, "Bottleneck MTU GIS Danayasa, GIS AGP, GIS Mampang Baru (CT & line bay 600 A)",
     "Terdapat Bottleneck di MTU GIS Danayasa, GIS AGP dan GIS Mampang Baru dimana CT dan Line bay "
     "masih berkapasitas 600 A sedangkan Rencana Uprating SKTT menjadi 1000 A.",
     "1. Kesulitan dalam melakukan pemeliharaan. "
     "2. Berpotensi overload pada ruas pht AGP-Danayasa. "
     "3. Berpotensi overload pada ruas pht Mampang-AGP saat terjadi N-1 dan N-2 pada ruas "
     "Cawang Baru-AGP dan Cawang Baru-Taman Rasuna.",
     "1. Pemeliharaan dilaksanakan pada beban rendah dengan melakukan manuver beban di 20 kV. "
     "2. Pengalihan Beban GI Mampang ke Sub Sistem Muarakarang.",
     "Jangka Pendek: Uprating ruas pht Mampang-AGP-Danayasa menjadi 1000 A (RUPTL 2025-2034 COD 2026). "
     "(update AGP-Mampang sudah kabel baru SKTT 1000 A).",
     "High", "SUBSTATION", "DNYSA"),

    (4, "Ruas Setiabudi-Dukuh Atas I nominal kecil (480 A) -> tidak N-1",
     "Ruas penghantar Setiabudi-Dukuh Atas memiliki I Nominal yang masih kecil (In 480 A) dan tidak "
     "memenuhi kriteria N-1 saat beban GIS 150 kV Dukuh Atas dipasok Sub Sistem Cawang 2,3-Depok 1.",
     "1. Kesulitan dalam melakukan pemeliharaan. "
     "2. Berpotensi terjadi pemadaman saat terjadi kondisi N-1 pada ruas tersebut.",
     "1. Pemeliharaan dilaksanakan pada beban rendah dengan melakukan manuver beban di 20 kV. "
     "2. Pengalihan Beban GI Dukuh Atas ke Sub Sistem Priok-Cawang 1-Bekasi 2,4.",
     "Jangka Menengah: Usulan uprating ruas penghantar Setiabudi-Dukuh Atas menjadi 1000 A "
     "(diusulkan COD Tahun 2029).",
     "High", "SUBSTATION", "STBDI"),
]

# Bays: a small GI drawn only as a stub on a feeder busbar.
#   (gi_code, feeder_code, status, note)
BAYS = [
    ("LKONG2", "CWANG", "ENERGIZED", "Bay Lengkong 2 menggantung di bus Cawang Lama"),
    ("KRLMA", "MPLMA", "ENERGIZED", "Bay Karet Lama menggantung di bus Mampang Lama"),
    ("DKTAS", "STBDI", "ENERGIZED", "Bay GIS Dukuh Atas menggantung di bus Setiabudi"),
]


def seed_ss_cwd(db: Session) -> None:
    if db.query(Subsystem).filter(Subsystem.code == SS_CODE).first():
        return

    doc = SourceDocument(
        filename="Buku Kerawanan SJB Tahun 2026.pdf",
        document_type="SLD_PDF_PAGE",
        analytical_hint="SUBSYSTEM_150",
        source_ref="Buku Kerawanan SJB 2026 Sec 2.7 (Gambar 2.6 + Tabel 2.5)",
        effective_date="2026-06-30",
    )
    db.add(doc)
    db.flush()

    ss = Subsystem(
        code=SS_CODE,
        name="Cawang 2,3 - Depok 1",
        apb="UP2B Jakarta & Banten",
        source_ref="Buku Kerawanan SJB 2026 Sec 2.7",
    )
    db.add(ss)
    db.flush()

    tv = TopologyVersion(
        version_key="TV-SS_CWD-2026-06",
        status="ACTIVE",
        effective_date="2026-06-30",
        description="Baseline SS Cawang 2,3-Depok 1 dari Buku Kerawanan SJB 2026 Sec 2.7 "
        "(traced AS-IS dari Gambar 2.6; parser test, belum field review).",
    )
    db.add(tv)
    db.flush()
    db.add(ChangeSet(
        change_key="CR-SS_CWD-001", version_id=tv.id, action="MODEL",
        target_kind="SUBSYSTEM", target_ref=SS_CODE,
        description="Relasi antar-Tier ditarik agresif dari SLD. Ruas dengan confidence < 0.9 "
        "ditandai NEEDS_REVIEW -- perlu konfirmasi lapangan.",
        status="PROPOSED",
    ))

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
            subsystem_id=ss.id,
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

    view = AnalyticalView(
        view_key=f"{SS_CODE}_FULL", view_type="SUBSYSTEM",
        name="SLD lengkap",
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
