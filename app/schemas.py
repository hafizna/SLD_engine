from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


# ---- observation import (adapter contract) --------------------------------

class ObservedObjectIn(BaseModel):
    external_key: Optional[str] = None
    object_type: str
    raw_label: str
    site_name: Optional[str] = None
    voltage_hv_kv: Optional[float] = None
    voltage_lv_kv: Optional[float] = None
    unit_no: Optional[str] = None
    tier_hint: Optional[int] = None
    status_hint: Optional[str] = None
    confidence: float = 1.0


class ObservedConnectionIn(BaseModel):
    from_external_key: str
    to_external_key: str
    relation_type: str = "CONNECTED_TO"
    circuit_type_hint: Optional[str] = None
    status_hint: Optional[str] = None
    confidence: float = 1.0


class ObservationBatchIn(BaseModel):
    filename: str
    document_type: str = "SLD_SCREENSHOT"
    analytical_hint: Optional[str] = None
    source_ref: Optional[str] = None
    effective_date: Optional[str] = None
    objects: List[ObservedObjectIn]
    connections: List[ObservedConnectionIn] = []


class CreateViewIn(BaseModel):
    view_key: str
    view_type: str
    name: str
    rule_profile: str
    subsystem_id: Optional[int] = None
    scenario_id: str = "NORMAL"
    layout_hint: Optional[str] = None


# ---- diagram layout (drag-and-drop persistence) --------------------------

class NodePositionIn(BaseModel):
    node_kind: str = "SUBSTATION"   # SUBSTATION / GENERATING_UNIT / TRANSFORMER
    node_id: int
    x: float
    y: float
    pinned: bool = True


class LayoutPatchIn(BaseModel):
    positions: List[NodePositionIn]
    updated_by: Optional[str] = None
    # when true, positions not listed in this patch are cleared (full replace);
    # when false (default) it is an upsert of just the listed nodes.
    replace: bool = False


# ---- topology change requests (PROBIS_KONSEP.md) -----------------------
# A structural change is proposed as a ChangeRequest with one or more lines;
# it is validated, previewed, reviewed, then published as a TopologyVersion.

class CRCreateIn(BaseModel):
    title: str
    kind: str = "STRUCTURAL"                # STRUCTURAL / OPERATING
    effective_date: Optional[str] = None    # "berlaku sejak" YYYY-MM-DD
    source_ref: Optional[str] = None        # RUPTL / surat / DS
    submitted_by: Optional[str] = None


class CRLineIn(BaseModel):
    # SET_STATUS / ADD_CIRCUIT / REMOVE_CIRCUIT / PATCH_CIRCUIT / ADD_GI /
    # REMOVE_GI / PATCH_GI / MOVE_MEMBERSHIP / ADD_SUBSYSTEM
    action: str
    target_kind: Optional[str] = None       # SUBSTATION / CIRCUIT / SUBSYSTEM
    target_ref: Optional[str] = None        # code of the object being changed
    payload: dict = {}
    description: str = ""


class CRReviewIn(BaseModel):
    reviewed_by: Optional[str] = None


class CRRejectIn(BaseModel):
    reason: Optional[str] = None


# ---- kerawanan editor -------------------------------------------------

CONTINGENCY_CATEGORIES = ("N-1", "N-2", "N-1-1", "N-0")   # N-0 = non-kontingensi


class RiskIn(BaseModel):
    seq_no: Optional[int] = None                 # nomor titik kerawanan
    category: str = "N-1"                         # N-1 / N-2 / N-1-1 / N-0
    title: str = ""
    condition: str = ""                           # Kondisi / Permasalahan
    impact: str = ""                              # Dampak
    mitigation: str = ""                          # Mitigasi
    follow_up: str = ""                           # Usulan / Solusi
    horizon: Optional[str] = None                 # PENDEK / MENENGAH / PANJANG
    priority: Optional[str] = None                # High / Medium / Low
    status: str = "OPEN"
    attach_kind: Optional[str] = None             # SUBSTATION / CIRCUIT / TRANSFORMER
    attach_code: Optional[str] = None             # code of the object it pins to


class RiskPatch(BaseModel):
    seq_no: Optional[int] = None
    category: Optional[str] = None
    title: Optional[str] = None
    condition: Optional[str] = None
    impact: Optional[str] = None
    mitigation: Optional[str] = None
    follow_up: Optional[str] = None
    horizon: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    attach_kind: Optional[str] = None
    attach_code: Optional[str] = None
