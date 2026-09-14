"""Rebuild ingest samples from the user's reviewed Excel sources.

Keep audit prose as evidence, not as machine-readable view membership.
The original workbooks under samples/sources are never modified.
"""
from pathlib import Path

import openpyxl
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "SS_LBK": "JBB_SS_LBK_single_view_v1.xlsx",
    "SS_GUCL": "JBB_SS_GUCL_manual_audit_v2 (1).xlsx",
    "SS_PRBC": "JBB_SS_PBRC_single_view_v1.xlsx",
}


def build_reviewed(code: str, output_dir: Path | None = None) -> Path:
    source = ROOT / "samples" / "sources" / SOURCES[code]
    wb = openpyxl.load_workbook(source)
    for row in wb["Info"]:
        if row[0].value == "Kode Subsistem":
            row[1].value = code
    for name in ("Gardu_Induk_dan_Aset", "Jalur_Transmisi", "Bay"):
        ws = wb[name]
        headers = [c.value for c in ws[1]]
        if "Sudut Pandang" not in headers:
            continue
        column = headers.index("Sudut Pandang") + 1
        # Preserve the source annotation in place. The parser ignores this
        # explicitly named evidence column; all rows belong to the FULL view.
        ws.cell(1, column).value = "Catatan Sudut Pandang Sumber"
    if "Views" in wb:
        del wb["Views"]
    ws = wb.create_sheet("Views", 1)
    ws.append(["Kode View", "Nama View", "Sumber Tier-1 (kode GI, pisah ;)", "Halaman Buku"])
    roots = {"SS_LBK": "KMBGN;NBRJA;ILKNG",
             "SS_GUCL": "CLBRU;LBUAN",
             "SS_PRBC": "MKLMA;PRBRT;PRTMR;PRTRU;BKASI;MTWAR;CWBRU"}
    ws.append(["FULL", "SLD lengkap", roots[code], None])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for col, width in {"A": 16, "B": 24, "C": 65, "D": 18}.items():
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    output_dir = Path(output_dir) if output_dir else ROOT / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{code.lower()}_ingest.xlsx"
    wb.save(target)
    return target
