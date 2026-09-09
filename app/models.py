"""MANTAPS canonical topology model.

Design principle (see README + ARCHITECTURE.md):
    One canonical physical topology, many analytical projections,
    many evidence sources, many risk contexts.

Granularity for the risk-map use case is GI-node + circuit-edge:
    - Substation / GeneratingUnit / Transformer  -> nodes
    - Circuit (penghantar / IBT link)            -> edges
    - Tier / Risk / AHI / Defense Scheme         -> semantic overlays, never baked in

Engineering detail (BusSection / Bay / Device) is kept as a NULLABLE
attachment so the schema stays CIM/NMM-compatible, but the risk map does
not require it. GI internal busbar config is stored as an attribute, not
as a graph of sections.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

# ---------------------------------------------------------------------------
# Controlled vocabularies (kept as plain strings in the DB for portability)
# ---------------------------------------------------------------------------

# Substation.substation_type
SUBSTATION_TYPES = ("GITET", "GI", "GIS", "GISTET", "SWITCHING", "KTT")

# Substation.status / Circuit.status  -- derived from SLD colour convention
#   ENERGIZED           red  busbar/line, in service
#   NEW_NOT_ENERGIZED   black, built or nearly built but not yet energised
#   PLANNED             grey, still in planning (e.g. SKTT not yet built)
#   DE_ENERGIZED        temporarily out of service
#   OWNED_BY_CUSTOMER   asset inside a "milik KTT" dashed box
ASSET_STATUSES = (
    "ENERGIZED",
    "NEW_NOT_ENERGIZED",
    "PLANNED",
    "DE_ENERGIZED",
    "OWNED_BY_CUSTOMER",
)

# Substation.busbar_config
BUSBAR_CONFIGS = ("SINGLE", "DOUBLE_1CB", "DOUBLE_SECTIONALIZED", "BREAKER_AND_HALF", "UNKNOWN")

# Circuit.circuit_type
CIRCUIT_TYPES = ("SUTET", "SUTT", "SKTT", "SKLT", "IBT_LINK", "BUS_COUPLER", "BUS_TIE", "GSU_LINK")

# SubsystemMembership.role / ViewMembership.role
MEMBERSHIP_ROLES = (
    "SOURCE",
    "SOURCE_BOUNDARY",
    "CORE",
    "RISK_OBJECT",
    "BOUNDARY",
    "DOWNSTREAM_CONTEXT",
    "EXTERNAL_CONTEXT",
)

# DSRelation.role
DS_RELATION_ROLES = ("TRIGGER", "ACTION", "TRIGGER_ACTION", "PARTICIPANT", "AFFECTED_ONLY")


# ===========================================================================
# 1. Provenance / evidence layer
# ===========================================================================

class SourceDocument(Base):
    """A screenshot, PDF page, SVG, Excel sheet, Maximo export, or NMM pull."""

    __tablename__ = "source_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    document_type: Mapped[str] = mapped_column(String(50), default="SLD_PDF_PAGE")
    analytical_hint: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "Buku Kerawanan SJB 2026 hal.69"
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    file_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ObservedObject(Base):
    """A node as read from ONE source document, before reconciliation."""

    __tablename__ = "observed_object"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    external_key: Mapped[str | None] = mapped_column(String(100), nullable=True)
    object_type: Mapped[str] = mapped_column(String(50))
    raw_label: Mapped[str] = mapped_column(String(255))
    normalized_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    voltage_hv_kv: Mapped[float | None] = mapped_column(Float, nullable=True)
    voltage_lv_kv: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tier_hint: Mapped[int | None] = mapped_column(Integer, nullable=True)  # tier band drawn on the SLD
    status_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)  # from colour
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    # resolution target once reconciled:
    canonical_kind: Mapped[str | None] = mapped_column(String(30), nullable=True)  # SUBSTATION / GENERATING_UNIT / TRANSFORMER
    canonical_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ObservedConnection(Base):
    """An edge as read from ONE source document."""

    __tablename__ = "observed_connection"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("source_document.id"))
    from_observed_id: Mapped[int] = mapped_column(ForeignKey("observed_object.id"))
    to_observed_id: Mapped[int] = mapped_column(ForeignKey("observed_object.id"))
    relation_type: Mapped[str] = mapped_column(String(50), default="CONNECTED_TO")
    circuit_type_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


# ===========================================================================
# 2. Canonical physical model  (GI-node + circuit-edge)
# ===========================================================================

class Substation(Base):
    """A GI / GITET / GIS / switching yard / customer HV substation.

    Stored ONCE even when it appears in several SLDs and several subsystems.
    """

    __tablename__ = "substation"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)          # e.g. "KMBGN"
    name: Mapped[str] = mapped_column(String(255))                     # e.g. "Kembangan"
    substation_type: Mapped[str] = mapped_column(String(20), default="GI")
    voltage_kv: Mapped[float] = mapped_column(Float, default=150.0)    # highest voltage present
    apb: Mapped[str | None] = mapped_column(String(120), nullable=True)  # UP2B / operating area
    uit: Mapped[str | None] = mapped_column(String(30), nullable=True)   # JBB / JBT / JBM
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ENERGIZED")
    busbar_config: Mapped[str] = mapped_column(String(30), default="UNKNOWN")
    busbar_note: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "Bus 1A / 2A / 1B / 2B"
    # SLD-symbol attributes (not engineering detail -- just what the drawing shows)
    has_transformer: Mapped[bool] = mapped_column(Boolean, default=True)   # 150/20 load transformer drawn
    has_shunt_capacitor: Mapped[bool] = mapped_column(Boolean, default=False)
    symbol_note: Mapped[str | None] = mapped_column(String(255), nullable=True)  # e.g. "3 trafo di SLD"
    asset_id: Mapped[str | None] = mapped_column(String(100), nullable=True)     # NIA / Maximo
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class GeneratingUnit(Base):
    """A generating unit / plant complex connection point (PLTU, PLTGU, ...)."""

    __tablename__ = "generating_unit"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    unit_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # PLTU / PLTGU / PLTA / ...
    voltage_kv: Mapped[float] = mapped_column(Float, default=150.0)
    rated_mw: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # connection point: the substation this plant feeds via its GSU / outlet
    outlet_substation_id: Mapped[int | None] = mapped_column(ForeignKey("substation.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ENERGIZED")
    operator: Mapped[str | None] = mapped_column(String(60), nullable=True)  # PIP / PNP / IPP
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Transformer(Base):
    """A transformer / IBT. Multi-winding via TransformerWinding.

    Not hard-coded per voltage pair (no IBT500150 / TR15020 tables) -- one
    schema covers IBT 500/150, IBT 150/70, trafo 150/20, 3-winding, etc.
    """

    __tablename__ = "transformer"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)         # e.g. "IBT_KMBGN_1"
    name: Mapped[str] = mapped_column(String(255))
    transformer_type: Mapped[str] = mapped_column(String(20), default="IBT")  # IBT / TRAFO / GSU
    substation_id: Mapped[int] = mapped_column(ForeignKey("substation.id"))
    unit_no: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rating_mva: Mapped[float | None] = mapped_column(Float, nullable=True)
    winding_count: Mapped[int] = mapped_column(Integer, default=2)
    status: Mapped[str] = mapped_column(String(30), default="ENERGIZED")
    asset_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TransformerWinding(Base):
    __tablename__ = "transformer_winding"

    id: Mapped[int] = mapped_column(primary_key=True)
    transformer_id: Mapped[int] = mapped_column(ForeignKey("transformer.id"))
    winding_no: Mapped[int] = mapped_column(Integer)
    voltage_kv: Mapped[float] = mapped_column(Float)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)  # HV / MV / LV / TERTIARY
    __table_args__ = (UniqueConstraint("transformer_id", "winding_no", name="uq_tx_winding"),)


class Circuit(Base):
    """A transmission circuit / line / cable / IBT link  --  a graph EDGE.

    Endpoints are substations (GI-node granularity). Bay-level endpoints are
    optional and live in `from_bay_id` / `to_bay_id` for later CIM alignment.
    """

    __tablename__ = "circuit"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)         # e.g. "PHT_CKUPA_JTAKE"
    name: Mapped[str] = mapped_column(String(255))                    # e.g. "Cikupa - Jatake"
    circuit_type: Mapped[str] = mapped_column(String(20), default="SUTT")
    voltage_kv: Mapped[float] = mapped_column(Float, default=150.0)
    from_substation_id: Mapped[int] = mapped_column(ForeignKey("substation.id"))
    to_substation_id: Mapped[int] = mapped_column(ForeignKey("substation.id"))
    # optional: the transformer this edge represents (IBT link) instead of a line
    transformer_id: Mapped[int | None] = mapped_column(ForeignKey("transformer.id"), nullable=True)
    circuit_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # sirkit count
    length_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    single_phi: Mapped[bool] = mapped_column(Boolean, default=False)   # "single phi" configuration
    status: Mapped[str] = mapped_column(String(30), default="ENERGIZED")
    scenario_id: Mapped[str] = mapped_column(String(40), default="NORMAL")
    from_bay_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    to_bay_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------------------------------------------------------------------------
# 2b. CIM/PLMS-compatible engineering detail  --  NULLABLE, unused by risk map
# ---------------------------------------------------------------------------

class BusSection(Base):
    __tablename__ = "bus_section"

    id: Mapped[int] = mapped_column(primary_key=True)
    substation_id: Mapped[int] = mapped_column(ForeignKey("substation.id"))
    name: Mapped[str] = mapped_column(String(60))
    voltage_kv: Mapped[float] = mapped_column(Float, default=150.0)
    bus_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Bay(Base):
    __tablename__ = "bay"

    id: Mapped[int] = mapped_column(primary_key=True)
    substation_id: Mapped[int] = mapped_column(ForeignKey("substation.id"))
    bus_section_id: Mapped[int | None] = mapped_column(ForeignKey("bus_section.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(80))
    bay_type: Mapped[str] = mapped_column(String(20), default="LINE")  # LINE / TRAFO / COUPLER / GENERATOR
    circuit_id: Mapped[int | None] = mapped_column(ForeignKey("circuit.id"), nullable=True)
    bay_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Device(Base):
    __tablename__ = "device"

    id: Mapped[int] = mapped_column(primary_key=True)
    bay_id: Mapped[int | None] = mapped_column(ForeignKey("bay.id"), nullable=True)
    device_type: Mapped[str] = mapped_column(String(20), default="CB")  # CB / PMS / ES
    normal_state: Mapped[str] = mapped_column(String(10), default="CLOSED")
    asset_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ===========================================================================
# 3. Subsystem membership  (one physical GI -> several subsystems / roles)
# ===========================================================================

class Subsystem(Base):
    __tablename__ = "subsystem"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)       # e.g. "SS_LBK"
    name: Mapped[str] = mapped_column(String(255))                  # "Lontar - Balaraja 1,2 - Kembangan 1,2"
    apb: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "Buku Kerawanan SJB 2026 §2.5"
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class SubsystemMembership(Base):
    __tablename__ = "subsystem_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    subsystem_id: Mapped[int] = mapped_column(ForeignKey("subsystem.id"))
    node_kind: Mapped[str] = mapped_column(String(20))  # SUBSTATION / GENERATING_UNIT / TRANSFORMER
    node_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(30), default="CORE")
    external_subsystem: Mapped[str | None] = mapped_column(String(120), nullable=True)  # for BOUNDARY: which SS it "belongs to"
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    __table_args__ = (
        UniqueConstraint("subsystem_id", "node_kind", "node_id", name="uq_ss_node"),
    )


# ===========================================================================
# 4. Analytical projections  (BACKBONE_500 / IBT_500_150 / SUBSYSTEM_150)
# ===========================================================================

class AnalyticalView(Base):
    __tablename__ = "analytical_view"

    id: Mapped[int] = mapped_column(primary_key=True)
    view_key: Mapped[str] = mapped_column(String(80), unique=True)
    view_type: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(255))
    rule_profile: Mapped[str] = mapped_column(String(40))            # BACKBONE_500 / IBT_500_150 / SUBSYSTEM_150
    subsystem_id: Mapped[int | None] = mapped_column(ForeignKey("subsystem.id"), nullable=True)
    scenario_id: Mapped[str] = mapped_column(String(40), default="NORMAL")
    layout_hint: Mapped[str | None] = mapped_column(String(40), nullable=True)  # e.g. "KEMBANGAN_SIDE" / "BALARAJA_SIDE"


class ViewMembership(Base):
    __tablename__ = "view_membership"

    id: Mapped[int] = mapped_column(primary_key=True)
    view_id: Mapped[int] = mapped_column(ForeignKey("analytical_view.id"))
    node_kind: Mapped[str] = mapped_column(String(20))
    node_id: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(30))
    tier_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)  # explicit tier-1 seed
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    __table_args__ = (
        UniqueConstraint("view_id", "node_kind", "node_id", name="uq_view_node"),
    )


# ===========================================================================
# 5. Semantic overlays  (never baked into the base SLD)
# ===========================================================================

class RiskRecord(Base):
    """Contextual risk -- attached to an object WITHIN an analytical view."""

    __tablename__ = "risk_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    risk_key: Mapped[str] = mapped_column(String(80), unique=True)   # e.g. "RISK-SS_LBK-01"
    subsystem_id: Mapped[int | None] = mapped_column(ForeignKey("subsystem.id"), nullable=True)
    view_id: Mapped[int | None] = mapped_column(ForeignKey("analytical_view.id"), nullable=True)
    seq_no: Mapped[int | None] = mapped_column(Integer, nullable=True)  # "No" column in the book table
    uit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # what it attaches to (GI, circuit, transformer, ...)
    attach_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)
    attach_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attach_label: Mapped[str | None] = mapped_column(String(255), nullable=True)  # free text when not resolvable
    title: Mapped[str] = mapped_column(String(255), default="")
    condition: Mapped[str] = mapped_column(Text, default="")     # Kondisi / Permasalahan
    impact: Mapped[str] = mapped_column(Text, default="")        # Dampak
    mitigation: Mapped[str] = mapped_column(Text, default="")    # Mitigasi
    follow_up: Mapped[str] = mapped_column(Text, default="")     # Usulan / Solusi
    horizon: Mapped[str | None] = mapped_column(String(30), nullable=True)  # PENDEK / MENENGAH / PANJANG
    priority: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="OPEN")
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("source_document.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class AhiRecord(Base):
    __tablename__ = "ahi_record"

    id: Mapped[int] = mapped_column(primary_key=True)
    ahi_key: Mapped[str] = mapped_column(String(60), unique=True)
    attach_kind: Mapped[str] = mapped_column(String(20))  # TRANSFORMER / DEVICE / SUBSTATION
    attach_id: Mapped[int] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ahi_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Good / Mod / Poor
    driver: Mapped[str | None] = mapped_column(String(120), nullable=True)
    inspection_date: Mapped[str | None] = mapped_column(String(20), nullable=True)


class DefenseScheme(Base):
    __tablename__ = "defense_scheme"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_key: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    scheme_type: Mapped[str] = mapped_column(String(20))  # OLS / OGS / ADS / UFR / BUSPRO
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE / STANDBY / PLANNED
    scope_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # LOCAL / REGIONAL / CROSS_APB
    target_mw: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_mw_planned: Mapped[float | None] = mapped_column(Float, nullable=True)
    stages: Mapped[str | None] = mapped_column(String(120), nullable=True)  # "tahap 1 sd 4"
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)  # "Buku DS 2025"
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class DSRelation(Base):
    """A scheme touches one or many topology objects, possibly across subsystems."""

    __tablename__ = "ds_relation"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("defense_scheme.id"))
    subsystem_id: Mapped[int | None] = mapped_column(ForeignKey("subsystem.id"), nullable=True)
    attach_kind: Mapped[str] = mapped_column(String(20))  # SUBSTATION / CIRCUIT / TRANSFORMER / GENERATING_UNIT
    attach_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attach_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="PARTICIPANT")
    coverage_note: Mapped[str | None] = mapped_column(String(120), nullable=True)  # "7 SS | 2 APB"


# ===========================================================================
# 6. Governance  (topology versions + change sets)
# ===========================================================================

class TopologyVersion(Base):
    __tablename__ = "topology_version"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_key: Mapped[str] = mapped_column(String(60), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED")  # PROPOSED / ACTIVE / SUPERSEDED
    effective_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    reviewer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    approver: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChangeSet(Base):
    __tablename__ = "change_set"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_key: Mapped[str] = mapped_column(String(60), unique=True)
    version_id: Mapped[int | None] = mapped_column(ForeignKey("topology_version.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(30))  # ADD_GI / ADD_BAY / COMMISSION_LINE / MOVE_BAY / MODEL / ...
    target_kind: Mapped[str | None] = mapped_column(String(30), nullable=True)
    target_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED")
