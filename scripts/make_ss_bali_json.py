"""Build the single UP2B Bali subsystem fixture from Buku Kerawanan 2026.

Risk text is extracted from Table 6.1 (PDF pages 239-246). Topology is traced
from Appendix 5 (PDF page 252) and the risk map on page 238. Connections whose
exact circuit labelling is hard to read remain confidence 0.8/NEEDS_REVIEW.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "Buku Kerawanan SJB Tahun 2026.pdf"
OUT = ROOT / "samples" / "ss_bali_ingest.json"


def clean(value):
    value = (value or "").replace("�", "-")
    return re.sub(r"\s+", " ", value).strip()


def table_risks():
    records = []
    current = None
    with pdfplumber.open(PDF) as pdf:
        for pno in range(239, 247):
            tables = pdf.pages[pno - 1].extract_tables()
            if len(tables) < 2:
                continue
            for row in tables[1][1:]:
                row = list(row) + [None] * (6 - len(row))
                if clean(row[0]).isdigit():
                    if current:
                        records.append(current)
                    current = [clean(cell) for cell in row[:6]]
                elif current:
                    for idx in range(2, 6):
                        extra = clean(row[idx])
                        if extra:
                            current[idx] = clean(current[idx] + " " + extra)
    if current:
        records.append(current)
    return records


def main():
    assets = [
        # code, name, type, tier, optional generator outlet
        ("GILIMANUK", "GI Gilimanuk", "GI", 1, None),
        ("CELUKAN_BAWANG", "GIS Celukan Bawang", "GIS", 1, None),
        ("PEMARON", "GI Pemaron", "GI", 1, None),
        ("PESANGGARAN", "GI Pesanggaran (AIS)", "GI", 1, None),
        ("GIS_PESANGGARAN", "GIS Pesanggaran", "GIS", 1, None),
        ("NEGARA", "GI Negara", "GI", 2, None),
        ("KAPAL", "GI Kapal", "GI", 2, None),
        ("BATURITI", "GI Baturiti", "GI", 2, None),
        ("PADANG_SAMBIAN", "GI Padang Sambian", "GI", 2, None),
        ("BANDARA", "GIS Bandara", "GIS", 2, None),
        ("NUSA_DUA", "GI Nusa Dua", "GI", 2, None),
        ("SANUR", "GI Sanur", "GI", 2, None),
        ("ANTOSARI", "GI Antosari", "GI", 3, None),
        ("TANAH_LOT", "GIS Tanah Lot", "GIS", 3, None),
        ("PAYANGAN", "GI Payangan", "GI", 3, None),
        ("PEMECUTAN_KELOD", "GI Pemecutan Kelod", "GI", 3, None),
        ("PECATU", "GIS Pecatu", "GIS", 3, None),
        ("GIANYAR", "GI Gianyar", "GI", 3, None),
        ("AMLAPURA", "GI Amlapura", "GI", 4, None),
        ("KUBU", "GI Kubu", "GI", 5, None),
        ("BANYUWANGI", "Transfer SKLT Banyuwangi", "GI", 0, None),
        ("PLTG_GILIMANUK", "PLTG Gilimanuk", "GENERATING_UNIT", 0, "GILIMANUK"),
        ("PLTU_CELUKAN_BAWANG", "PLTU Celukan Bawang 1-3", "GENERATING_UNIT", 0, "CELUKAN_BAWANG"),
        ("PLTG_PEMARON", "PLTG Pemaron 1-2", "GENERATING_UNIT", 0, "PEMARON"),
        ("PLTG_PESANGGARAN", "PLTG Pesanggaran 1-6", "GENERATING_UNIT", 0, "PESANGGARAN"),
        ("PLTDG_PESANGGARAN", "PLTDG Pesanggaran Blok 1-4", "GENERATING_UNIT", 0, "GIS_PESANGGARAN"),
        ("PLTD_SEWA_KUBU", "PLTD Sewa Tahap 3 170 MW", "GENERATING_UNIT", 0, "KUBU"),
    ]
    objects = []
    for code, name, kind, tier, outlet in assets:
        objects.append({
            "external_key": code, "object_type": kind, "raw_label": name,
            "site_name": name, "voltage_hv_kv": 150, "tier_hint": tier,
            "status_hint": "ENERGIZED", "confidence": 0.85,
            "outlet_key": outlet,
            "is_bay": False, "bay_feeder_key": None, "bay_circuit_count": None,
            "role_hint": "SOURCE_BOUNDARY" if code == "BANYUWANGI" else None,
        })

    links = [
        ("BANYUWANGI", "GILIMANUK", 2, "1,2"),
        ("BANYUWANGI", "GILIMANUK", 2, "3,4"),
        # Two AIS-GIS incomers shown on Single Line Bali 2026.
        ("GIS_PESANGGARAN", "PESANGGARAN", 2),
        ("GILIMANUK", "NEGARA", 2), ("GILIMANUK", "CELUKAN_BAWANG", 2),
        ("CELUKAN_BAWANG", "PEMARON", 2), ("CELUKAN_BAWANG", "KAPAL", 2),
        ("PEMARON", "BATURITI", 2), ("NEGARA", "ANTOSARI", 2),
        ("ANTOSARI", "TANAH_LOT", 2), ("TANAH_LOT", "KAPAL", 2),
        ("KAPAL", "BATURITI", 2), ("KAPAL", "PADANG_SAMBIAN", 2),
        ("KAPAL", "PEMECUTAN_KELOD", 1), ("BATURITI", "PAYANGAN", 2),
        ("BATURITI", "GIANYAR", 2), ("PAYANGAN", "GIANYAR", 2),
        ("PEMECUTAN_KELOD", "PADANG_SAMBIAN", 2),
        ("PEMECUTAN_KELOD", "NUSA_DUA", 2), ("PEMECUTAN_KELOD", "BANDARA", 2),
        ("NUSA_DUA", "PECATU", 2), ("BANDARA", "PECATU", 2),
        ("PESANGGARAN", "NUSA_DUA", 2), ("PESANGGARAN", "BANDARA", 2),
        ("PESANGGARAN", "PEMECUTAN_KELOD", 2),
        ("GIS_PESANGGARAN", "SANUR", 2), ("PESANGGARAN", "SANUR", 2),
        ("PADANG_SAMBIAN", "SANUR", 2), ("SANUR", "GIANYAR", 2),
        ("GIANYAR", "AMLAPURA", 2), ("AMLAPURA", "KUBU", 2),
    ]
    connections = []
    for link in links:
        a, b, count, *unit = link
        connections.append({
            "from_external_key": a, "to_external_key": b, "relation_type": "CONNECTED_TO",
            "circuit_type_hint": (
                "SKLT" if {a, b} == {"BANYUWANGI", "GILIMANUK"}
                else "SKTT" if {a, b} == {"GIS_PESANGGARAN", "PESANGGARAN"}
                else "SKTT" if {a, b} in ({"KAPAL", "PEMECUTAN_KELOD"}, {"NUSA_DUA", "PECATU"}, {"BANDARA", "PECATU"})
                else "SUTT"
            ),
            "status_hint": "PLANNED" if "PECATU" in (a, b) else "ENERGIZED",
            "circuit_count": count, "unit_no": unit[0] if unit else None,
            "confidence": 0.8,
            "note": "Traced from Appendix-5; verify circuit label against native SLD.",
        })

    titles = {
        1: "Defisit daya Subsistem Bali pada N-1/N-1-1 unit terbesar",
        2: "Ketergantungan pembangkit BBM saat PLTU Celukan Bawang outage",
        3: "Derating SKLT Banyuwangi-Gilimanuk 1 dan 2",
        4: "N-1 ruas Pemaron-Baturiti tidak terpenuhi",
        5: "Overload Kapal-Pemecutan Kelod saat N-2 Kapal-Padang Sambian",
        6: "Gangguan busbar GI Kapal berpotensi meluas",
        7: "Gangguan busbar GI Gilimanuk berpotensi island Bali",
        8: "N-1 trafo GI Gianyar tidak terpenuhi",
        9: "AIS Pesanggaran single busbar per section",
        10: "Kerawanan busbar GIS Pesanggaran",
        11: "Eskursi tegangan Pesanggaran-Sanur",
    }
    pins = {
        1: ("SUBSYSTEM", "SS_BALI"), 2: ("SUBSTATION", "CELUKAN_BAWANG"),
        3: ("CIRCUIT", "BANYUWANGI-GILIMANUK:1,2"), 4: ("CIRCUIT", "PEMARON-BATURITI"),
        5: ("CIRCUIT", "KAPAL-PEMECUTAN_KELOD"), 6: ("SUBSTATION", "KAPAL"),
        7: ("SUBSTATION", "GILIMANUK"), 8: ("SUBSTATION", "GIANYAR"),
        9: ("SUBSTATION", "PESANGGARAN"), 10: ("SUBSTATION", "GIS_PESANGGARAN"),
        11: ("CIRCUIT", "PESANGGARAN-SANUR"),
    }
    categories = {1: "N-1-1", 2: "N-1", 3: "N-1", 4: "N-1-1", 5: "N-2", 6: "N-1-1", 7: "N-1-1", 8: "N-1", 9: "N-1", 10: "N-1-1", 11: "N-1-1"}
    risks = []
    for no, uit, condition, impact, mitigation, follow_up in table_risks():
        seq = int(no)
        kind, key = pins[seq]
        risks.append({"seq_no": seq, "uit": uit, "category": categories[seq],
                      "priority": "High", "title": titles[seq], "condition": condition,
                      "impact": impact, "mitigation": mitigation, "follow_up": follow_up,
                      "pin_kind": kind, "pin_key": key})

    payload = {
        "meta": {"filename": OUT.name, "document_type": "SLD_HANDOFF_JSON",
                 "analytical_hint": "SUBSYSTEM_150", "effective_date": "2026-06-30",
                 "source_ref": "Buku Kerawanan SJB 2026 sec. 6.3, Table 6.1, Appendix-5"},
        "subsystem": {"code": "SS_BALI", "name": "Subsistem Bali", "apb": "UP2B Bali"},
        "objects": objects, "connections": connections, "risks": risks,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(objects)} objects, {len(connections)} connections, {len(risks)} risks")


if __name__ == "__main__":
    main()
