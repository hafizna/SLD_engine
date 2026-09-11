"""Pull the `Tabel x.y: Kerawanan Subsistem ...` rows straight out of the book.

The risk tables in `Buku Kerawanan SJB Tahun 2026.pdf` are real PDF tables, so
pdfplumber gets them verbatim -- no retyping, no paraphrase. Two wrinkles:

* A risk row often spans a page break, and the repeated page header/footer text
  ("No. Dokumen ... Berlaku efektif ... Halaman N dari 198", the WMT copyright
  block, and a repeat of the column headings) lands *inside* the continued cell.
  `_strip_chrome` removes those runs so the cell reads as written.
* Only a row whose col-0 is a number AND whose col-1 is a UIT code (JBB/JBT/JBM)
  starts a new risk; everything else is a continuation of the row above.

Used by scripts/make_ss_*_xlsx.py so the workbook's Data_Kerawanan_Detail sheet
is the book's own wording.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "Buku Kerawanan SJB Tahun 2026.pdf"

UIT_CODES = ("JBB", "JBT", "JBM")

# Page furniture that bleeds into cells continued across a page break.
_CHROME = [
    r"No\.\s*Dokumen\s*Berlaku\s*efektif\s*Revisi\s*Halaman",
    r"No\.\s*Dokumen\s*\d+/RK/P2B-OPS-ANV/\d+",
    r"Kondisi\s*/\s*Permasalahan(\s*Dampak\s*Mitigasi\s*Usulan\s*/\s*Solusi)?",
    r"PT\s*PLN\s*\(Persero\)",
    r"UNIT\s*INDUK\s*PUSAT\s*PENGATUR\s*BEBAN",
    r"JAWA,\s*MADURA\s*DAN\s*BALI",
    r"Jl\.\s*JCC,\s*Cinere\s*-?\s*Depok\.?\s*\d*",
    r"SISTEM\s*MANAJEMEN\s*TERINTEGRASI",
    r"Kerawanan\s*Sistem\s*&\s*Subsistem\s*Jawa,\s*Madura\s*dan\s*Bali\s*Tahun\s*\d+",
    r"Dokumen\s*ini\s*milik\s*PT\s*PLN\s*\(Persero\)\s*UIP2BJAMALI",
    r"Dilarang\s*menyalin\s*atau\s*memperbanyak\s*dokumen\s*kepada",
    r"pihak\s*lain\s*tanpa\s*seijin\s*dari\s*WMT",
    r"Berlaku\s*efektif",
    r"Halaman\s*\d+\s*dari\s*\d+",
    r"Revisi\s*0+",
    r"\b\d+\s*Juni\s*\d{4}\b",
    r"Tabel\s*\d+\.\d+\s*:?\s*Kerawanan[^|]{0,80}",
    r"\bNo\s+UIT\b",
    # Header fragments that survive when a cell is split mid-table: the bare
    # document number, the "215dari198" page stamp, and a lone repeated column
    # heading trailing the continued text.
    r"\d{3}/RK/P2B-OPS-ANV/\d{4}",
    r"\b\d+\s*dari\s*\d+\b",
    r"(?<=\s)(Dampak|Mitigasi|Usulan\s*/\s*Solusi)\s*$",
    r"^\s*0{2}\s+",
    r"\s+0{2}(?=\s+\d)",
]
_CHROME_RE = re.compile("|".join(_CHROME), re.IGNORECASE)


# The book writes "N-1" with a real en-dash and uses a few other typographic
# marks; fold them to ASCII so the workbook text stays greppable.
_PUNCT = {"–": "-", "—": "-", "‘": "'", "’": "'",
          "“": '"', "”": '"', " ": " ", "�": "-"}


def clean(value: str | None) -> str:
    """Normalise whitespace and fold typographic punctuation to ASCII."""
    text = value or ""
    for src, dst in _PUNCT.items():
        text = text.replace(src, dst)
    return re.sub(r"\s+", " ", text).strip()


def _strip_chrome(text: str) -> str:
    """Remove page furniture, repeatedly -- one pass can expose the next.

    e.g. "... IBT. 011/RK/P2B-OPS-ANV/2026 00 215dari198 Dampak" only ends in a
    bare column heading once the document number and page stamp are gone.
    """
    for _ in range(4):
        stripped = re.sub(r"\s+", " ", _CHROME_RE.sub(" ", text)).strip(" -;:.")
        if stripped == text:
            break
        text = stripped
    return text


def risk_rows(page_from: int, page_to: int) -> list[list[str]]:
    """Rows of [no, uit, kondisi, dampak, mitigasi, usulan] for a 1-based page range."""
    records: list[list[str]] = []
    current: list[str] | None = None
    with pdfplumber.open(PDF) as pdf:
        for pno in range(page_from, page_to + 1):
            for table in pdf.pages[pno - 1].extract_tables():
                for raw in table:
                    row = list(raw) + [None] * (6 - len(raw))
                    first, second = clean(row[0]), clean(row[1])
                    if first.isdigit() and second in UIT_CODES:
                        if current:
                            records.append(current)
                        current = [clean(cell) for cell in row[:6]]
                    elif current:
                        for idx in range(2, 6):
                            extra = clean(row[idx])
                            if extra:
                                current[idx] = clean(f"{current[idx]} {extra}")
    if current:
        records.append(current)
    for rec in records:
        for idx in range(2, 6):
            rec[idx] = _strip_chrome(rec[idx])
    return records


def as_risk_dicts(page_from: int, page_to: int, expected: int | None = None) -> list[dict]:
    """risk_rows() shaped for `_ss_xlsx_common.build_workbook`'s `risks` key."""
    rows = risk_rows(page_from, page_to)
    if expected is not None and len(rows) != expected:
        raise SystemExit(
            f"expected {expected} risk rows on PDF p.{page_from}-{page_to}, got {len(rows)}: "
            f"{[r[0] for r in rows]}"
        )
    return [
        dict(no=int(no), uit=uit, kondisi=kondisi, dampak=dampak,
             mitigasi=mitigasi, usulan=usulan)
        for no, uit, kondisi, dampak, mitigasi, usulan in rows
    ]
