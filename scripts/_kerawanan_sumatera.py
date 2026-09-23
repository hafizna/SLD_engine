"""Risk tables of the Kerawanan Sistem Sumatera deck (UIP3B Sumatera, Sep 2026).

The deck's tables are real PowerPoint tables, so they are read straight from
the slide XML -- the counterpart of `_kerawanan_tables.py` for the SJB PDF.
Nothing here opens PowerPoint, and python-pptx is not needed.

Two things the XML does not say in plain text and this module rebuilds:

* **Auto-numbering.** "1. ... 2. ..." inside a cell is PowerPoint's
  `buAutoNum`, not typed text. Numbering runs on through a cell, across a
  "Jangka Menengah:" heading, exactly as PowerPoint renders it (slide 14 #1
  continues 1, 2 -> 3, 4), and restarts only at an explicit `startAt`.
* **Sub-rows.** Sumbagteng and Sumbagut split one risk over several rows,
  one per horizon (Jangka Pendek / Menengah / Panjang), with No..Mitigasi
  row-spanned. A risk starts at a row whose No cell is a number and is not a
  continuation (`vMerge`); every following continuation row belongs to it.

The deck has columns the ingest template does not: COD RUPTL, Progres and
Prioritas Sistem (P0 / P0'), and the backbone table calls Mitigasi
"Kontrol Eksisting". As agreed with the user (2026-09-23) nothing is added to
the schema: Kontrol Eksisting goes to Mitigasi, and each horizon's
COD / Progres / Prioritas is folded into Usulan right under that horizon.

The deck has no UIT column either; UIT carries the deck's own subsystem label
(SBS / SBT / SBU, as on slide 29).
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from _kerawanan_tables import contingency_of

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "Kerawanan Sumatera September 2026.pptx"

_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

# Section -> the slides its table runs over (1-based, as PowerPoint numbers
# them) and how many risks the slide's own numbered list says it has. Slides
# 31-36 come after "Terima Kasih" and are an older 18-item backbone list; the
# user chose the main body, so they are never read.
SECTIONS = {
    "BACKBONE": dict(slides=(7, 8, 9), expected=22),
    "SUMSEL": dict(slides=(12,), expected=7, uit="SBS"),
    "LAMPUNG": dict(slides=(14, 15), expected=10, uit="SBS"),
    "BENGKULU": dict(slides=(17,), expected=7, uit="SBS"),
    "SUMBAGTENG": dict(slides=(20, 21, 22, 23), expected=22, uit="SBT"),
    "SUMBAGUT": dict(slides=(26, 27, 28), expected=19, uit="SBU"),
}


# Backbone #21-#22 are on slide 10 as a PASTED PICTURE of a table (an EMF), not
# a PowerPoint table, so they cannot be read from XML. Transcribed from the
# slide as rendered; column split checked against the drawn cell borders.
_TRANSCRIBED = {
    "BACKBONE": {
        # slide -> rows in the table's own column order:
        # No, Kerawanan, Risiko & Dampak, Kontrol Eksisting, Mitigasi/Solusi,
        # COD (RUPTL), Progress, Prioritas Sistem
        10: [
            ["21",
             "Kendala Kesiapan PLTU Batubara di Subsistem SBUT yang masih rendah\n"
             "- PLTU Pangkalan Susu (EAF U1 59,2%, U2 58,3%, U3 60,8%, U4 66,0%)\n"
             "- PLTU Ombilin (EAF U1 24,5%, U2 56,9%)\n"
             "- PLTU Teluk Sirih (EAF U1 79,2%, U2 77,2%)\n"
             "- PLTU Tenayan (EAF U1 91,5%, U2 73,1%)\n"
             "- PLTU Labuhan Angin (EAF U1 0,0003%, U2 51,0%)",
             "1. Transfer dari Subsistem Selatan Tinggi\n"
             "2. Dapat Menimbulkan Pemadaman (Defisit Daya)\n"
             "3. Biaya Operasi Pembangkit Lebih Mahal di Subsistem SBUT\n"
             "4. Padam Maksimum 422 MW",
             "1. Penundaan Jadwal Pemeliharaan Pembangkit di Subsistem SBUT\n"
             "2. Pemeliharaan Transmisi Jalur Backbone dilakukan pada saat Beban "
             "Sistem Rendah (Hari Sabtu & Minggu)\n"
             "3. Pengoperasian PLTG dan PLTD Berbahan Bakar Minyak dengan Durasi "
             "yang lebih lama",
             "1. Koordinasi untuk Peningkatan Kesiapan PLTU Batubara kepada PLN IP, "
             "PLN NP dan PLN EP.\n"
             "2. Managemen Beban di sisi Pelanggan",
             "2026", "", ""],
            ["22",
             "Gangguan N-2 penghantar 275 kV Kiliran Jao - Payakumbuh",
             "1. Potensi overload di IBT 1 & 2 GITET Kiliran Jao dan GITET Payakumbuh\n"
             "2. Padam 700 MW",
             "1. Sudah dipasang OLS IBT Kiliran Jao dan IBT Payakumbuh",
             "1. Pembangunan SUTET 500 kV Muara Enim - Gumawang (P0' - RUPTL 2028)",
             "2028", "0 %", "P0'"],
        ],
    },
}


def _clean(text: str) -> str:
    text = (text.replace("–", "-").replace("—", "-")
                .replace("‘", "'").replace("’", "'")
                .replace(" ", " "))
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def _cell_text(tc) -> str:
    """A table cell as PowerPoint renders it, numbering included."""
    out: list[str] = []
    counters: dict[int, int] = {}
    body = tc.find(_A + "txBody")
    if body is None:
        return ""
    for p in body.findall(_A + "p"):
        parts = []
        for node in p:
            if node.tag == _A + "r" or node.tag == _A + "fld":
                t = node.find(_A + "t")
                parts.append(t.text or "" if t is not None else "")
            elif node.tag == _A + "br":
                parts.append("\n")
        text = "".join(parts)
        ppr = p.find(_A + "pPr")
        auto = ppr.find(_A + "buAutoNum") if ppr is not None else None
        if auto is not None and text.strip():
            lvl = int(ppr.get("lvl") or 0)
            start = auto.get("startAt")
            counters[lvl] = int(start) if start else counters.get(lvl, 0) + 1
            text = f"{counters[lvl]}. {text.strip()}"
        out.append(text)
    return _clean("\n".join(out))


def _rows(slide_no: int, deck: Path = DECK) -> list[list[tuple[str, bool]]]:
    """Every table row on a slide as [(text, is_continuation), ...] per column."""
    with zipfile.ZipFile(deck) as z:
        root = ET.fromstring(z.read(f"ppt/slides/slide{slide_no}.xml"))
    rows = []
    for tbl in root.iter(_A + "tbl"):
        for tr in tbl.findall(_A + "tr"):
            rows.append([(_cell_text(tc), tc.get("vMerge") == "1")
                         for tc in tr.findall(_A + "tc")])
    return rows


def _fold(usulan: str, cod: str, progres: str, prioritas: str) -> str:
    extra = []
    for label, value in (("COD RUPTL", cod), ("Progres", progres),
                         ("Prioritas", prioritas)):
        items = [re.sub(r"^\s*\d+\s*\.\s*", "", ln) for ln in value.split("\n")]
        if any(i.strip() for i in items):     # not just bare "1. 2." numbering
            extra.append(f"{label}: " + value.replace("\n", "; "))
    if not extra:
        return usulan
    return (usulan + "\n" if usulan else "") + "[" + " | ".join(extra) + "]"


def table(section: str, deck: Path = DECK) -> list[dict]:
    """One dict per risk: no, kondisi, dampak, mitigasi, usulan."""
    spec = SECTIONS[section]
    transcribed = _TRANSCRIBED.get(section, {})
    risks: list[dict] = []
    for slide in sorted(set(spec["slides"]) | set(transcribed)):
        rows = ([[(_clean(t), False) for t in r] for r in transcribed[slide]]
                if slide in transcribed else _rows(slide, deck))
        for row in rows:
            if len(row) != 8:
                raise SystemExit(f"slide {slide}: expected 8 columns, got {len(row)}")
            (no, cont), *_ = row
            texts = [t for t, _ in row]
            if not cont and texts[0].strip() == "No":
                continue                                   # header row
            if not any(texts):
                continue                                   # spacer row
            usulan = _fold(*texts[4:8])
            if not cont and no.strip().isdigit():
                risks.append(dict(no=int(no), kondisi=texts[1], dampak=texts[2],
                                  mitigasi=texts[3], usulan_parts=[usulan]))
            elif cont and risks:
                risks[-1]["usulan_parts"].append(usulan)
            else:
                raise SystemExit(f"slide {slide}: row belongs to no risk: {texts[:2]}")
    numbers = [r["no"] for r in risks]
    if numbers != list(range(1, len(numbers) + 1)):
        raise SystemExit(f"{section}: risk numbers are not a clean 1..N run: {numbers}")
    if len(risks) != spec["expected"]:
        raise SystemExit(f"{section}: expected {spec['expected']} risks, got {len(risks)}")
    for r in risks:
        r["usulan"] = "\n".join(p for p in r.pop("usulan_parts") if p)
    return risks


# The deck rarely writes "N-2"; it names the outage instead -- "Trip 2 Sirkit
# SUTT 150 kV Duri-Dumai", "Gangguan 2 sirkit radial", "Trip 1 PHT 150 kV ...".
# The user agreed (2026-09-23, as a trial) to read a 1-circuit trip as N-1 and
# a 2-circuit trip as N-2. Kondisi first, as for the SJB book; a radial
# configuration row ("... masih radial") states its outage only in Dampak
# ("Jika penghantar tersebut TRIP 2 sirkit ..."), so Dampak is the fallback.
# One word may sit in between: "gangguan permanen 2 sirkit" (Sumbagut #3).
_TRIP = re.compile(r"\b(?:trip|gangguan)(?:\s+[a-z]+)?\s+(1|2|satu|dua)\s+"
                   r"(?:sirkit|pht|penghantar)", re.I)


def category_of(kondisi: str, dampak: str = "") -> str:
    explicit = contingency_of(kondisi)
    if explicit != "BELUM_DITETAPKAN":
        return explicit
    for text in (kondisi, dampak):
        orders = {m.group(1).lower() for m in _TRIP.finditer(text or "")}
        if orders & {"2", "dua"}:
            return "N-2"
        if orders & {"1", "satu"}:
            return "N-1"
    return "BELUM_DITETAPKAN"


def as_risk_dicts(section: str, uit: dict[int, str] | None = None) -> list[dict]:
    """table() shaped for `_ss_xlsx_common.build_workbook`'s `risks` key.

    `uit` overrides the section's label per risk number -- the backbone spans
    all three subsystems, so its builder states where each finding sits."""
    default = SECTIONS[section].get("uit", "")
    return [
        dict(no=r["no"], uit=(uit or {}).get(r["no"], default),
             kondisi=r["kondisi"], dampak=r["dampak"], mitigasi=r["mitigasi"],
             usulan=r["usulan"], category=category_of(r["kondisi"], r["dampak"]))
        for r in table(section)
    ]


if __name__ == "__main__":
    import sys
    for name in sys.argv[1:] or SECTIONS:
        for r in table(name):
            print(f"--- {name} #{r['no']}  [{category_of(r['kondisi'], r['dampak'])}]")
            for key in ("kondisi", "dampak", "mitigasi", "usulan"):
                print(f"  {key.upper()}: " + r[key].replace("\n", "\n      "))
