"""Read-only voltage and source-connectivity audit for all ingest workbooks.

This intentionally does not repair data. It reports deterministic defects and
review candidates before a person edits an individual subsystem workbook.

Run::

    python scripts/audit_voltage_consistency.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ingest_parser import parse_upload  # noqa: E402

OUT_DIR = ROOT / ".render_tmp" / "voltage-audit"


def _site_name(value: str | None) -> str:
    text = (value or "").upper()
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b(?:GITET|GISTET|GIS|GI|BUS|TEGANGAN|KV)\b", " ", text)
    text = re.sub(r"\b(?:500|150|70|66|30|25|20|15|13|11|10)(?:[.,]\d+)?\b", " ", text)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def _finding(severity, rule, workbook, subsystem, subject, message, suggestion):
    return {
        "severity": severity,
        "rule": rule,
        "workbook": Path(workbook).name,
        "subsystem": subsystem,
        "subject": subject,
        "message": message,
        "suggestion": suggestion,
    }


def audit_payloads(records: list[tuple[Path, dict]]) -> list[dict]:
    findings = []
    occurrences = defaultdict(list)
    site_occurrences = defaultdict(list)

    for path, payload in records:
        ss = payload["subsystem"].get("code") or path.stem
        objects = payload.get("objects") or []
        edges = payload.get("connections") or []
        by_key = {o["external_key"]: o for o in objects}

        for o in objects:
            key = str(o["external_key"]).strip().upper()
            kv = o.get("voltage_hv_kv")
            kind = o.get("object_type")
            if kind != "GENERATING_UNIT":
                occurrences[key].append((path, ss, kv, o))
                site = _site_name(o.get("site_name") or o.get("raw_label"))
                if site:
                    site_occurrences[site].append((path, ss, kv, o))
            if kind in {"GI", "GIS", "GITET", "GISTET", "KTT"} and kv is None:
                findings.append(_finding(
                    "HIGH", "BUS_VOLTAGE_MISSING", path, ss, key,
                    "Bus tidak memiliki level tegangan; warna renderer akan memakai default.",
                    "Isi kolom Tegangan pada Gardu_Induk_dan_Aset.",
                ))

        for e in edges:
            a = by_key.get(e["from_external_key"])
            b = by_key.get(e["to_external_key"])
            subject = f"{e['from_external_key']}–{e['to_external_key']}"
            if not a or not b:
                findings.append(_finding(
                    "HIGH", "ENDPOINT_UNKNOWN", path, ss, subject,
                    "Salah satu endpoint penghantar tidak terdaftar sebagai aset.",
                    "Samakan kode Dari GI/Ke GI dengan Kode Singkatan aset.",
                ))
                continue
            ct = (e.get("circuit_type_hint") or "SUTT").upper()
            is_ibt = ct == "IBT_LINK" or e.get("relation_type") == "IBT_LINK"
            av, bv, ev = a.get("voltage_hv_kv"), b.get("voltage_hv_kv"), e.get("voltage_hv_kv")
            if not is_ibt and av is not None and bv is not None and abs(float(av) - float(bv)) > .1:
                findings.append(_finding(
                    "HIGH", "ENDPOINT_VOLTAGE_MISMATCH", path, ss, subject,
                    f"Penghantar biasa menghubungkan bus {av:g} kV dan {bv:g} kV.",
                    "Pilih bus pada level yang sama atau ubah relasi menjadi IBT_LINK.",
                ))
            if not is_ibt and ev is not None:
                mismatched = sorted({float(v) for v in (av, bv) if v is not None and abs(float(v) - float(ev)) > .1})
                if mismatched:
                    findings.append(_finding(
                        "HIGH", "LINE_BUS_VOLTAGE_MISMATCH", path, ss, subject,
                        f"Penghantar tercatat {ev:g} kV tetapi endpoint mencatat "
                        + "/".join(f"{v:g}" for v in mismatched) + " kV.",
                        "Koreksi Tegangan penghantar atau arahkan ke kode bus yang benar.",
                    ))
            if is_ibt and av is not None and bv is not None and abs(float(av) - float(bv)) <= .1:
                findings.append(_finding(
                    "HIGH", "IBT_SAME_VOLTAGE", path, ss, subject,
                    f"IBT menghubungkan dua bus yang sama-sama {av:g} kV.",
                    "Periksa Bus HV dan Bus LV pada baris transformer.",
                ))

        incident = defaultdict(int)
        for e in edges:
            incident[e["from_external_key"]] += 1
            incident[e["to_external_key"]] += 1
        for o in objects:
            if o.get("object_type") != "GENERATING_UNIT":
                continue
            key = o["external_key"]
            outlet = o.get("outlet_key")
            if not (outlet in by_key or incident[key]):
                findings.append(_finding(
                    "HIGH", "GENERATOR_WITHOUT_OUTLET", path, ss, key,
                    "Pembangkit tidak mempunyai Bus Terhubung maupun relasi penghantar.",
                    "Isi Bus Terhubung dengan kode bus pada titik representasi generator.",
                ))
            elif outlet and outlet not in by_key:
                findings.append(_finding(
                    "HIGH", "GENERATOR_OUTLET_UNKNOWN", path, ss, key,
                    f"Bus Terhubung '{outlet}' tidak ditemukan pada workbook.",
                    "Gunakan Kode Singkatan bus yang terdaftar.",
                ))

    for code, rows in occurrences.items():
        volts = sorted({float(kv) for _, _, kv, _ in rows if kv is not None})
        if len(volts) > 1:
            locations = "; ".join(f"{p.name}:{ss}:{kv:g}kV" for p, ss, kv, _ in rows if kv is not None)
            findings.append(_finding(
                "HIGH", "CROSS_WORKBOOK_CODE_VOLTAGE_COLLISION", rows[0][0],
                ", ".join(sorted({r[1] for r in rows})), code,
                f"Kode identik dipakai pada beberapa tegangan ({locations}).",
                "Beri kode bus canonical bertegangan/berwilayah; pertahankan label tampilan pendek.",
            ))

    for site, rows in site_occurrences.items():
        volts = sorted({float(kv) for _, _, kv, _ in rows if kv is not None})
        codes = sorted({str(o["external_key"]).upper() for _, _, _, o in rows})
        if len(volts) > 1 and len(codes) > 1:
            findings.append(_finding(
                "INFO", "MULTI_VOLTAGE_SITE", rows[0][0],
                ", ".join(sorted({r[1] for r in rows})), site,
                f"Nama site muncul sebagai bus {', '.join(f'{v:g}' for v in volts)} kV "
                f"dengan kode {', '.join(codes)}.",
                "Pastikan bus berbeda ini dihubungkan transformer bila berada dalam satu kompleks.",
            ))

    order = {"HIGH": 0, "MEDIUM": 1, "INFO": 2}
    return sorted(findings, key=lambda f: (order.get(f["severity"], 9), f["rule"], f["workbook"], f["subject"]))


def main() -> int:
    paths = sorted((ROOT / "samples").glob("*_ingest.xlsx"))
    records = []
    parse_failures = []
    for path in paths:
        try:
            records.append((path, parse_upload(path.read_bytes(), path.name)))
        except Exception as exc:
            parse_failures.append(_finding(
                "HIGH", "PARSE_FAILURE", path, path.stem, path.name,
                f"{type(exc).__name__}: {exc}", "Perbaiki struktur workbook sebelum audit data.",
            ))
    findings = parse_failures + audit_payloads(records)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "workbooks": len(paths), "parsed": len(records), "findings": len(findings),
        "by_severity": {s: sum(f["severity"] == s for f in findings) for s in ("HIGH", "MEDIUM", "INFO")},
        "items": findings,
    }
    (OUT_DIR / "voltage-audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Voltage consistency audit", "",
        "Read-only report generated by `python scripts/audit_voltage_consistency.py`.",
        "No workbook is changed by this audit.", "",
        f"Workbooks: {len(paths)}; parsed: {len(records)}; findings: {len(findings)} "
        f"(HIGH {summary['by_severity']['HIGH']}, INFO {summary['by_severity']['INFO']}).", "",
        "| Severity | Rule | Workbook | Subsystem | Subject | Finding | Suggested action |",
        "|---|---|---|---|---|---|---|",
    ]
    for f in findings:
        clean = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(clean(f[k]) for k in
                     ("severity", "rule", "workbook", "subsystem", "subject", "message", "suggestion")) + " |")
    (OUT_DIR / "VOLTAGE_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[5])
    print(OUT_DIR / "VOLTAGE_AUDIT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
