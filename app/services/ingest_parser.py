"""Parse an uploaded evidence file into a normalised ingest payload.

Two real formats:

  * **Excel template (primary)** -- the 3-sheet PLN subsystem template
    (`Jalur_Transmisi`, `Gardu_Induk_dan_Aset`, `Data_Kerawanan_Detail`), the
    same one the sister dashboard uses to author an SLD. `parse_xlsx`.
    MANTAPS adds an optional `Info` sheet (SS code/name), an optional `Bay`
    sheet (hanging stubs + feeder), and reads a `Bus 150 kV` column on the
    `IBT n-Winding` rows to say which busbar an IBT feeds when it differs from
    the GITET code (GITET Cawang -> CWBRU, not CWANG).
  * **JSON hand-off (secondary/internal)** -- `parse_json`; the blob shape the
    engine passes around. `samples/ss_cwd_ingest.json` is an example.

`parse_upload` dispatches on the file. PDF / vector-SVG / vision extraction are
declared seams, not built (the Buku Kerawanan PDF is internal; no vision
pipeline here).

The normalised payload (a plain dict):
    {
      "meta":      {filename, document_type, analytical_hint, source_ref, effective_date},
      "subsystem": {code, name, apb},
      "objects":   [ {external_key, object_type, raw_label, site_name, voltage_hv_kv,
                      voltage_lv_kv, unit_no, tier_hint, status_hint, confidence,
                      is_bay, bay_feeder_key, has_transformer, has_capacitor}, ... ],
      "connections": [ {from_external_key, to_external_key, relation_type,
                        circuit_type_hint, status_hint, circuit_count, unit_no,
                        confidence, note}, ... ],
      "risks":     [ {seq_no, uit, category, priority, title, condition, impact,
                      mitigation, follow_up, pin_kind, pin_key}, ... ],
    }
"""
from __future__ import annotations

import json


class IngestParseError(ValueError):
    """The uploaded file could not be parsed into an ingest payload."""


# ---- format seams (not implemented) ---------------------------------------

class VectorPdfExtractor:
    def extract(self, file_bytes: bytes):  # pragma: no cover - seam
        raise NotImplementedError(
            "Vector-PDF SLD extraction is not built. Upload the structured JSON "
            "hand-off instead (see samples/ss_cwd_ingest.json)."
        )


class VisionExtractor:
    def extract(self, file_bytes: bytes):  # pragma: no cover - seam
        raise NotImplementedError(
            "Vision-model SLD extraction is not built. Upload the structured JSON "
            "hand-off instead (see samples/ss_cwd_ingest.json)."
        )


# ---- the one real path: structured JSON ----------------------------------

_NODE_DEFAULTS = {
    "site_name": None, "voltage_hv_kv": None, "voltage_lv_kv": None,
    "unit_no": None, "tier_hint": None, "status_hint": "ENERGIZED",
    "confidence": 1.0, "is_bay": False, "bay_feeder_key": None,
    "has_transformer": False, "has_capacitor": False,
    "transformer_count": None, "capacitor_count": None, "symbol_note": None,
    "view_keys": [], "outlet_key": None, "bay_circuit_count": None,
    "role_hint": None, "bay_view_keys": [], "latitude": None, "longitude": None,
}
_CONN_DEFAULTS = {
    "relation_type": "CONNECTED_TO", "circuit_type_hint": "SUTT",
    "status_hint": "ENERGIZED", "circuit_count": 2, "unit_no": None,
    "confidence": 0.5, "note": None,
    "view_keys": [], "single_phi": False,
}
_RISK_DEFAULTS = {
    "seq_no": None, "uit": "JBB", "category": "N-1", "priority": "High",
    "title": "", "condition": "", "impact": "", "mitigation": "", "follow_up": "",
    "pin_kind": None, "pin_key": None,
}


def parse_upload(file_bytes: bytes, filename: str) -> dict:
    name = (filename or "").lower()
    if name.endswith((".xlsx", ".xlsm")) or file_bytes[:2] == b"PK":
        return parse_xlsx(file_bytes, filename)
    if name.endswith(".json") or _looks_like_json(file_bytes):
        return parse_json(file_bytes, filename)
    raise IngestParseError(
        "Format tidak dikenali. Unggah template Excel subsistem PLN (.xlsx) "
        "atau file hand-off JSON. PDF/vision belum diimplementasi."
    )


def parse_json(file_bytes: bytes, filename: str) -> dict:
    try:
        raw = json.loads(file_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise IngestParseError(f"JSON tidak valid: {e}") from e
    return normalise(raw, filename)


def normalise(raw: dict, filename: str | None = None, *, drop_bad_edges: bool = False) -> dict:
    if not isinstance(raw, dict):
        raise IngestParseError("payload harus objek JSON")
    ss = raw.get("subsystem") or {}
    if not ss.get("code") or not ss.get("name"):
        raise IngestParseError("subsystem.code dan subsystem.name wajib diisi")

    objs = raw.get("objects") or []
    conns = raw.get("connections") or []
    if not objs:
        raise IngestParseError("tidak ada objek (nodes) di file")

    keys = set()
    norm_objs = []
    for i, o in enumerate(objs):
        k = o.get("external_key")
        if not k:
            raise IngestParseError(f"objek ke-{i} tidak punya external_key")
        if k in keys:
            raise IngestParseError(f"external_key ganda: {k}")
        keys.add(k)
        row = {**_NODE_DEFAULTS, **{kk: vv for kk, vv in o.items() if kk in _NODE_DEFAULTS}}
        row["external_key"] = k
        row["object_type"] = (o.get("object_type") or "GI").upper()
        row["raw_label"] = o.get("raw_label") or k
        norm_objs.append(row)

    norm_conns = []
    dropped = []
    for i, c in enumerate(conns):
        a, b = c.get("from_external_key"), c.get("to_external_key")
        if a not in keys or b not in keys:
            if drop_bad_edges:
                dropped.append(f"{a}->{b}")
                continue
            raise IngestParseError(
                f"koneksi ke-{i} menunjuk endpoint tak dikenal: {a} -> {b}"
            )
        row = {**_CONN_DEFAULTS, **{kk: vv for kk, vv in c.items() if kk in _CONN_DEFAULTS}}
        row["from_external_key"] = a
        row["to_external_key"] = b
        norm_conns.append(row)

    norm_risks = []
    for r in (raw.get("risks") or []):
        row = {**_RISK_DEFAULTS, **{kk: vv for kk, vv in r.items() if kk in _RISK_DEFAULTS}}
        norm_risks.append(row)

    return {
        "meta": {
            "filename": raw.get("filename") or filename or f"{ss['code']}.json",
            "document_type": raw.get("document_type") or "SLD_HANDOFF_JSON",
            "analytical_hint": raw.get("analytical_hint") or "SUBSYSTEM_150",
            "source_ref": raw.get("source_ref"),
            "effective_date": raw.get("effective_date"),
            "dropped_edges": dropped,
        },
        "subsystem": {"code": ss["code"], "name": ss["name"], "apb": ss.get("apb"),
                      "views": [dict(v) for v in (ss.get("views") or []) if isinstance(v, dict)]},
        "objects": norm_objs,
        "connections": norm_conns,
        "risks": norm_risks,
    }


def _looks_like_json(b: bytes) -> bool:
    head = b.lstrip()[:1]
    return head in (b"{", b"[")


# ===========================================================================
# Excel template (primary format) -- the 3-sheet PLN subsystem template
# ===========================================================================
#
#   Jalur_Transmisi          -> connections  (Dari GI / Ke GI + Tier Dari/Ke)
#   Gardu_Induk_dan_Aset      -> objects      (Busbar GITET / Busbar GI / IBT n-Winding)
#   Data_Kerawanan_Detail    -> risks
#
# The template carries the relations explicitly (Dari GI -> Ke GI), so the
# "adjacency" is whatever the author typed -- no library lookup.

_ASSET_TYPE_MAP = {
    "busbar gitet": ("GITET", False),
    "busbar gistet": ("GISTET", False),
    "busbar gi": ("GI", False),
    "busbar gis": ("GIS", False),
    "gi": ("GI", False),
    "gitet": ("GITET", False),
    "bay": ("GI", True),
    "spur": ("GI", True),
    "pembangkit": ("GENERATING_UNIT", False),
    "generating unit": ("GENERATING_UNIT", False),
}
_STATUS_MAP = {
    "beroperasi": "ENERGIZED", "operasi": "ENERGIZED", "energized": "ENERGIZED",
    "belum operasi": "NEW_NOT_ENERGIZED", "belum energize": "NEW_NOT_ENERGIZED",
    "rencana": "PLANNED", "planned": "PLANNED",
    "padam": "DE_ENERGIZED", "de-energized": "DE_ENERGIZED",
}
_RAWAN_CONF = {   # "Tingkat Kerawanan" -> a rough confidence for a traced ruas
    "normal": 0.85, "rawan": 0.8, "sangat rawan": 0.8, "waspada": 0.8,
}


def _kv(v) -> float | None:
    if v is None:
        return None
    s = str(v).lower().replace("kv", "").split("/")[0].strip().replace(",", ".")
    try:
        return float("".join(ch for ch in s if ch.isdigit() or ch == "."))
    except ValueError:
        return None


def _coordinate(v, low: float, high: float) -> float | None:
    if v is None or str(v).strip() == "":
        return None
    try:
        value = float(str(v).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None
    return value if low <= value <= high else None


def _norm(s) -> str:
    return str(s or "").strip().lower()


def _tokens(value) -> list[str]:
    return [part.strip().upper() for part in str(value or "").replace(",", ";").split(";") if part.strip()]


def _risk_numbers(value) -> list[int]:
    result = []
    for token in _tokens(value):
        try:
            result.append(int(float(token)))
        except ValueError:
            continue
    return result


def parse_xlsx(file_bytes: bytes, filename: str) -> dict:
    try:
        import openpyxl
    except ImportError as e:  # pragma: no cover
        raise IngestParseError("openpyxl tidak terpasang") from e
    import io

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
    except Exception as e:  # noqa: BLE001
        raise IngestParseError(f"tidak bisa membaca .xlsx: {e}") from e

    def _sheet(*names):
        for n in names:
            for sn in wb.sheetnames:
                if _norm(sn) == _norm(n):
                    return wb[sn]
        return None

    ws_asset = _sheet("Gardu_Induk_dan_Aset", "Gardu Induk dan Aset", "Aset")
    ws_line = _sheet("Jalur_Transmisi", "Jalur Transmisi", "Penghantar")
    ws_risk = _sheet("Data_Kerawanan_Detail", "Data Kerawanan Detail", "Kerawanan")
    if ws_asset is None or ws_line is None:
        raise IngestParseError(
            "Template Excel harus punya sheet 'Gardu_Induk_dan_Aset' dan 'Jalur_Transmisi'."
        )

    def _rows(ws):
        it = ws.iter_rows(values_only=True)
        header = None
        for r in it:
            if r and any(c is not None for c in r):
                header = [_norm(c) for c in r]
                break
        if not header:
            return
        for r in it:
            if r and any(c is not None for c in r):
                yield {header[i]: r[i] for i in range(min(len(header), len(r)))}

    def _get(row: dict, *keys):
        for k in keys:
            for hk, v in row.items():
                if hk == _norm(k):
                    return v
        return None

    # ---- read every non-IBT asset row first, so we can spot a GITET busbar and
    #      a GI busbar sharing one code (the template's 500/150 split) ----
    raw_rows = []
    for row in _rows(ws_asset):
        code = _get(row, "Kode Singkatan", "Kode", "Code")
        atype = _norm(_get(row, "Tipe Asset", "Tipe", "Type"))
        if not code or "ibt" in atype or "winding" in atype:
            continue
        raw_rows.append((str(code).strip(), atype, row))

    gitet_codes = {c for c, at, _ in raw_rows if _ASSET_TYPE_MAP.get(at, ("GI", 0))[0] in ("GITET", "GISTET")}
    lv_of_gitet = {c for c, at, _ in raw_rows
                   if c in gitet_codes and _ASSET_TYPE_MAP.get(at, ("GI", 0))[0] not in ("GITET", "GISTET")}
    # a code that is BOTH a GITET busbar and a GI busbar -> rename the GITET row
    key_remap: dict[str, str] = {}   # original code -> GITET_<code> for the 500 kV row

    objects: list[dict] = []
    seen: set[str] = set()
    for code, atype, row in raw_rows:
        name = _get(row, "Nama Asset / GI", "Nama Asset", "Nama GI", "Name")
        kind, is_bay = _ASSET_TYPE_MAP.get(atype, ("GI", False))
        ext = code
        if kind in ("GITET", "GISTET") and code in lv_of_gitet:
            ext = f"GITET_{code}"
            key_remap[code] = ext
        if ext in seen:
            continue
        seen.add(ext)
        tier_zero_based = _norm("Tier (Mulai 0)") in row
        tier = _get(row, "Tier (Mulai 0)", "Tier", "Tier (Mulai 1)")
        try:
            tier = int(tier) if tier is not None and str(tier).strip() != "" else None
        except (TypeError, ValueError):
            tier = None
        if tier is not None and tier_zero_based:
            # The workbook writers store every display tier as ``tier - 1``.
            # Convert the whole zero-based column back, not just its first row;
            # otherwise workbook tiers 1..n collapse one level upward.
            tier += 1
        status = _STATUS_MAP.get(_norm(_get(row, "Status Operasi", "Status")), "ENERGIZED")
        no_kerawanan = _get(row, "No Kerawanan", "No. Kerawanan")
        objects.append({
            "external_key": ext,
            "object_type": kind,
            "raw_label": str(name or code),
            "site_name": str(name or code),
            "voltage_hv_kv": _kv(_get(row, "Tegangan", "Voltage")),
            "tier_hint": tier,
            "status_hint": status,
            "confidence": 0.9 if kind in ("GITET", "GISTET") else 0.8,
            "is_bay": is_bay,
            "bay_feeder_key": (str(_get(row, "Feeder (GI Induk)", "Feeder", "GI Induk", "Induk")).strip()
                               if _get(row, "Feeder (GI Induk)", "Feeder", "GI Induk", "Induk") else None),
            "has_transformer": _bool_cell(_get(row, "Ada Trafo", "Has Transformer")),
            "has_capacitor": _bool_cell(_get(row, "Ada Kapasitor", "Has Capacitor")),
            "transformer_count": _get(row, "Jumlah Trafo", "Transformer Count"),
            "capacitor_count": _get(row, "Jumlah Kapasitor", "Capacitor Count"),
            "symbol_note": _get(row, "Catatan Simbol", "Symbol Note"),
            "view_keys": _tokens(_get(row, "Sudut Pandang", "View", "View Key")),
            "outlet_key": (str(_get(row, "Bus Terhubung", "Outlet Bus", "Terhubung ke Bus")).strip()
                           if _get(row, "Bus Terhubung", "Outlet Bus", "Terhubung ke Bus") else None),
            "bay_circuit_count": _int_or_none(_get(row, "Jumlah Sirkit Bay", "Jumlah Sirkit", "Sirkit", "Circuit Count")),
            "role_hint": (str(_get(row, "Role", "Peran", "Peran SLD") or "").strip().upper() or None),
            "latitude": _coordinate(_get(row, "Latitude", "Lat", "Lintang"), -90, 90),
            "longitude": _coordinate(_get(row, "Longitude", "Lon", "Long", "Bujur"), -180, 180),
            "bay_view_keys": [],
            "_no_kerawanan": _risk_numbers(no_kerawanan),
        })

    # IBT unit numbers per GITET, from the "IBT n-Winding" rows.
    #   * the GITET is the last token of the IBT code ("IBT 2 CWANG" -> CWANG)
    #     -> its (possibly remapped) key GITET_CWANG
    #   * the 150 kV bus it feeds is the "Bus 150 kV" column if given, else the
    #     same code as the GITET (New Balaraja style: 500 & 150 share "NBRJA")
    _gitet_ext = {o["external_key"] for o in objects if o["object_type"] in ("GITET", "GISTET")}
    _all_ext = {o["external_key"] for o in objects}
    ibt_units: dict[str, dict] = {}
    ibt_pins: dict[int, tuple[str, str]] = {}   # No Kerawanan -> (GITET key, unit)
    for row in _rows(ws_asset):
        atype = _norm(_get(row, "Tipe Asset", "Tipe", "Type"))
        if "ibt" not in atype and "winding" not in atype:
            continue
        unit = str(_get(row, "No IBT", "Unit", "No Unit") or "1").strip()
        raw = str(_get(row, "Kode Singkatan", "Kode", "Code") or "")
        tok = raw.split()[-1].strip().upper() if raw else None
        if not tok:
            continue
        # the GITET node key
        gk = f"GITET_{tok}" if f"GITET_{tok}" in _gitet_ext else (tok if tok in _gitet_ext else key_remap.get(tok, tok))
        # the 150 kV bus it feeds
        lv = _get(row, "Bus 150 kV", "Bus 150kV", "Bus LV", "Ke Bus", "Bus")
        lv = str(lv).strip().upper() if lv else None
        if not lv or lv not in _all_ext:
            lv = tok if tok in _all_ext else gk
        raw_status = _get(row, "Status Operasi", "Status")
        gitet_status = next((o["status_hint"] for o in objects if o["external_key"] == gk), "ENERGIZED")
        link_status = (_STATUS_MAP.get(_norm(raw_status), "ENERGIZED")
                       if raw_status not in (None, "") else gitet_status)
        ibt_units.setdefault(gk, {"lv": lv, "units": []})["units"].append(
            {"unit": unit, "status": link_status,
             "view_keys": _tokens(_get(row, "Sudut Pandang", "View", "View Key"))})
        for nk in _risk_numbers(_get(row, "No Kerawanan", "No. Kerawanan")):
            ibt_pins[nk] = (gk, unit)

    # ---- Bay sheet (MANTAPS extension: GI drawn as a stub + its feeder) ----
    ws_bay = _sheet("Bay", "Bays", "Bay_Menggantung")
    if ws_bay is not None:
        existing = {o["external_key"] for o in objects}
        for row in _rows(ws_bay):
            code = _get(row, "Kode GI", "Kode", "Code")
            feeder = _get(row, "Feeder (GI Induk)", "Feeder", "GI Induk", "Induk")
            if not code or not feeder:
                continue
            code, feeder = str(code).strip(), str(feeder).strip()
            row_obj = {
                "external_key": code, "object_type": "GI",
                "raw_label": str(_get(row, "Nama GI", "Nama") or code),
                "site_name": str(_get(row, "Nama GI", "Nama") or code),
                "voltage_hv_kv": _kv(_get(row, "Tegangan")),
                "tier_hint": None,
                "status_hint": _STATUS_MAP.get(_norm(_get(row, "Status Operasi", "Status")), "ENERGIZED"),
                "confidence": 0.7, "is_bay": True, "bay_feeder_key": feeder,
                "has_transformer": False,
                "bay_circuit_count": _int_or_none(_get(row, "Jumlah Sirkit", "Sirkit", "Circuit Count")),
                "bay_view_keys": _tokens(_get(row, "Sudut Pandang", "View", "View Key")),
                "view_keys": _tokens(_get(row, "Sudut Pandang", "View", "View Key")),
                "_no_kerawanan": _risk_numbers(_get(row, "No Kerawanan", "No. Kerawanan")),
            }
            if code in existing:
                for o in objects:
                    if o["external_key"] == code:
                        # Existing full-bus assets may be rendered as a bay in
                        # only one view. Keep the physical node full and scope
                        # the Bay appearance separately.
                        o.update({"bay_feeder_key": feeder,
                                  "bay_circuit_count": row_obj["bay_circuit_count"],
                                  "bay_view_keys": row_obj["bay_view_keys"]})
            else:
                objects.append(row_obj)
                existing.add(code)

    obj_keys = {o["external_key"] for o in objects}

    # ---- connections ----
    connections: list[dict] = []
    for row in _rows(ws_line):
        fr = _get(row, "Dari GI", "Dari", "From")
        to = _get(row, "Ke GI", "Ke", "To")
        if not fr or not to:
            continue
        fr, to = str(fr).strip(), str(to).strip()
        if fr not in obj_keys or to not in obj_keys:
            # keep it but flag low confidence -- the author may fix the code
            pass
        rawan = _norm(_get(row, "Tingkat Kerawanan", "Kerawanan"))
        try:
            cnt = int(_get(row, "Jumlah Sirkit", "Sirkit") or 2)
        except (TypeError, ValueError):
            cnt = 2
        connections.append({
            "from_external_key": fr, "to_external_key": to,
            "circuit_type_hint": _line_type(_get(row, "Nama Penghantar", "Nama", "Name"),
                                            _kv(_get(row, "Tegangan"))),
            "status_hint": _STATUS_MAP.get(_norm(_get(row, "Status Operasi", "Status")), "ENERGIZED"),
            "circuit_count": cnt,
            "single_phi": _bool_cell(_get(row, "Single Phi", "Single-phi", "Single Phase")),
            "confidence": _RAWAN_CONF.get(rawan, 0.8),
            "note": str(_get(row, "Nama Penghantar", "Nama") or "").strip() or None,
            "view_keys": _tokens(_get(row, "Sudut Pandang", "View", "View Key")),
            "_no_kerawanan": _risk_numbers(_get(row, "No Kerawanan", "No. Kerawanan")),
        })

    # ---- IBT-link connections (GITET -> its 150 kV bus), one per unit ----
    for gk, info in ibt_units.items():
        lv = info["lv"]
        if gk not in obj_keys or lv not in obj_keys:
            continue
        for unit_info in info["units"]:
            u = unit_info["unit"]
            connections.append({
                "from_external_key": gk, "to_external_key": lv,
                "relation_type": "IBT_LINK", "circuit_type_hint": "IBT_LINK",
                "status_hint": unit_info["status"], "circuit_count": 1,
                "unit_no": u, "confidence": 1.0,
                "view_keys": unit_info["view_keys"],
            })

    # auto-pin: template marks "No Kerawanan" on the asset / line / IBT it belongs to
    pin_by_seq: dict[int, tuple[str, str]] = {}
    for o in objects:
        for nk in o.pop("_no_kerawanan", []):
            pin_by_seq[nk] = ("SUBSTATION", o["external_key"])
    for c in connections:
        for nk in c.pop("_no_kerawanan", []):
            pin_by_seq[nk] = ("CIRCUIT", f"{c['from_external_key']}-{c['to_external_key']}")
    for nk, (gk, unit) in ibt_pins.items():
        pin_by_seq[nk] = ("TRANSFORMER", f"{gk}:{unit}")

    # ---- risks ----
    risks: list[dict] = []
    if ws_risk is not None:
        for row in _rows(ws_risk):
            no = _get(row, "No", "Seq")
            if no is None and not _get(row, "Kondisi / Permasalahan", "Kondisi"):
                continue
            seq = _int_or_none(no)
            pk = pin_by_seq.get(seq, (None, None))
            risks.append({
                "seq_no": seq,
                "uit": str(_get(row, "UIT") or "JBB").strip(),
                "category": "N-1",
                "priority": "High",
                "title": _first_line(_get(row, "Kondisi / Permasalahan", "Kondisi")),
                "condition": str(_get(row, "Kondisi / Permasalahan", "Kondisi") or "").strip(),
                "impact": str(_get(row, "Dampak") or "").strip(),
                "mitigation": str(_get(row, "Mitigasi") or "").strip(),
                "follow_up": str(_get(row, "Usulan / Solusi", "Usulan", "Solusi") or "").strip(),
                "pin_kind": pk[0], "pin_key": pk[1],
            })
    # strip the private key from any objects/connections that had no risk
    for o in objects:
        o.pop("_no_kerawanan", None)
    for c in connections:
        c.pop("_no_kerawanan", None)

    # optional Info sheet: "Kode Subsistem" / "Nama Subsistem" / "APB"
    ss_code = ss_name = ss_apb = None
    rule_profile = None
    ws_info = _sheet("Info", "Informasi", "Subsistem", "Header")
    if ws_info is not None:
        kv = {}
        for r in ws_info.iter_rows(values_only=True):
            if r and r[0] is not None:
                kv[_norm(r[0])] = r[1] if len(r) > 1 else None
        ss_code = kv.get("kode subsistem") or kv.get("kode")
        ss_name = kv.get("nama subsistem") or kv.get("nama")
        ss_apb = kv.get("apb") or kv.get("up2b")
        rule_profile = kv.get("rule profile") or kv.get("profil aturan")
    # Optional multi-SLD manifest. Rows identify independent analytical views;
    # assets/connections remain shared and are never merged by the parser.
    ws_views = _sheet("Views", "Sudut Pandang", "SLD Views")
    view_rows = []
    if ws_views is not None:
        for row in _rows(ws_views):
            vk = _get(row, "View Key", "Kunci View", "Kode View", "Sudut Pandang")
            if vk:
                view_rows.append({
                    "view_key": str(vk).strip().upper(),
                    "name": str(_get(row, "Nama View", "Nama SLD", "Name") or vk).strip(),
                    "description": str(_get(row, "Keterangan", "Description") or "").strip(),
                    "source_keys": _tokens(_get(row, "Sumber Tier-1 (kode GI, pisah ;)", "Sumber Tier-1", "Source Keys")),
                    "source_page": _get(row, "Halaman Buku", "Page"),
                })
    ss_name = str(ss_name).strip() if ss_name else _guess_ss_name(filename)
    ss_code = str(ss_code).strip().upper() if ss_code else _guess_ss_code(ss_name, filename)

    return normalise({
        "filename": filename,
        "document_type": "SLD_TEMPLATE_XLSX",
        "analytical_hint": str(rule_profile or "SUBSYSTEM_500_150").strip().upper(),
        "source_ref": f"Template subsistem PLN ({filename})",
        "subsystem": {"code": ss_code, "name": ss_name,
                      "apb": str(ss_apb).strip() if ss_apb else "UP2B Jakarta & Banten",
                      "views": view_rows},
        "objects": objects,
        "connections": connections,
        "risks": risks,
    }, filename, drop_bad_edges=True)


def _line_type(name, kv) -> str:
    n = _norm(name)
    if "sktt" in n or "kabel" in n:
        return "SKTT"
    return "SUTT"


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _bool_cell(value):
    return str(value or '').strip().lower() in ('1', 'true', 'yes', 'ya', 'ada')


def _first_line(v) -> str:
    s = str(v or "").strip()
    for sep in ("\n", ". ", ";"):
        if sep in s:
            return s.split(sep)[0].strip().lstrip("0123456789. ")[:180]
    return s[:180]


def _guess_ss_name(filename: str) -> str:
    base = (filename or "subsistem").rsplit(".", 1)[0]
    base = base.replace("template_sld_subsistem_pln_", "").replace("template_", "")
    base = base.replace("_", " ").replace("-", " ").strip()
    # drop a trailing " (1)" etc
    base = base.split("(")[0].strip()
    return base.title() or "Subsistem"


def _guess_ss_code(name: str, filename: str) -> str:
    toks = [t for t in name.replace("-", " ").split() if t.isalpha()]
    if len(toks) >= 2:
        return ("SS_" + toks[0][:3] + toks[1][:3]).upper()
    return "SS_" + (toks[0][:4].upper() if toks else "NEW")
