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
