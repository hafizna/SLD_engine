"""Risk counts in the published fixtures equal the reference documents.

The dashboard counts one RiskRecord per numbered row of a kerawanan table, so
every fixture must carry exactly as many risks as its table in Buku Kerawanan
SJB 2026 or the Kerawanan Sumatera September 2026 deck. The expected numbers
were read off each table's own No column and are recorded in
scripts/_kerawanan_sections.py and scripts/_kerawanan_sumatera.py (the PDF and
PPTX themselves are not in the repo).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from _kerawanan_sections import SECTIONS, SYSTEM_TABLES  # noqa: E402
from _kerawanan_sumatera import SECTIONS as SUMATERA  # noqa: E402

# book section -> the fixture build_static_site.py publishes for it
JAMALI = {
    "2.3": "ss_slcg_ingest.xlsx", "2.4": "ss_gucl_ingest.xlsx",
    "2.5": "ss_lbk_ingest.xlsx", "2.6": "seed_ss_bll", "2.7": "seed_ss_cwd",
    "2.8": "ss_muarakarang_durikosambi_ingest.xlsx", "2.9": "ss_dkgd_ingest.xlsx",
    "2.10": "ss_prbc_ingest.xlsx", "2.11": "ss_plbratu_ingest.xlsx",
    "2.12": "ss_bksi_cbng_ingest.xlsx", "2.13": "ss_gndul24_ingest.xlsx",
    "3.3": "ss_cbatu34_mdrcn_ingest.xlsx", "3.4": "ss_cirata_ingest.xlsx",
    "3.5": "ss_cbatu12_dltms_ingest.xlsx", "3.6": "ss_bdgsel_nubrg_ingest.xlsx",
    "3.7": "ss_tasik_ingest.xlsx", "3.8": "ss_ntmbn_ingest.xlsx",
    "3.9": "ss_sktni_ingest.xlsx",
    "4.3": "ss_tjati_ungaran3_ingest.xlsx", "4.4": "ss_ungaran12_ingest.xlsx",
    "4.5": "ss_pedan12_ingest.xlsx", "4.6": "ss_pedan34_ingest.xlsx",
    "4.7": "ss_ksghn_ingest.xlsx", "4.8": "ss_pmlng_ingest.xlsx",
    "4.9": "ss_byoli_ingest.xlsx",
    "5.3": "ss_krian12_gresik_ingest.xlsx", "5.4": "ss_krian3456_ingest.xlsx",
    "5.5": "ss_ngimbang_ingest.xlsx", "5.6": "ss_kediri12_ingest.xlsx",
    "5.7": "ss_kediri34_ingest.xlsx", "5.8": "ss_grati_ingest.xlsx",
    "5.9": "ss_paiton123_ingest.xlsx",
    "6.3": "ss_bali_ingest.json",
}
SYSTEM = {"Tabel 1.1.A Kerawanan SUTET 500 kV": "backbone_500_ingest.xlsx",
          "Tabel 1.2 Kerawanan IBT 500/150 kV": "system_ibt_500_ingest.xlsx",
          # no object to pin: published as the book's own tables
          "Tabel 1.3 Kerawanan Peralatan": "system_tables_jamali.json#PERALATAN",
          "Tabel 1.4 Kerawanan Pembangkit": "system_tables_jamali.json#PEMBANGKIT"}
SUMATERA_FIXTURES = {
    "BACKBONE": "backbone_sumatera_ingest.xlsx", "SUMSEL": "ss_sumsel_ingest.xlsx",
    "LAMPUNG": "ss_lampung_ingest.xlsx", "BENGKULU": "ss_bengkulu_ingest.xlsx",
    "SUMBAGTENG": "ss_sumbagteng_ingest.xlsx", "SUMBAGUT": "ss_sumbagut_ingest.xlsx",
}


def risk_count(fixture: str) -> int:
    if fixture.startswith("seed_"):
        # BLL and CWD are published from their hand-written seeders
        module = __import__(f"app.services.{fixture}", fromlist=["RISKS"])
        return len(module.RISKS)
    fixture, _, table = fixture.partition("#")
    path = ROOT / "samples" / fixture
    if table:
        data = json.loads(path.read_text(encoding="utf-8"))
        return len(next(t for t in data["tables"] if t["key"] == table)["rows"])
    if path.suffix == ".json":
        return len(json.loads(path.read_text(encoding="utf-8"))["risks"])
    ws = openpyxl.load_workbook(path, read_only=True)["Data_Kerawanan_Detail"]
    return sum(1 for row in ws.iter_rows(min_row=2, values_only=True)
               if any(v not in (None, "") for v in row))


BOOK = {sec: n for _label, sec, _fig, _pages, n in SECTIONS}


@pytest.mark.parametrize("section", sorted(JAMALI))
def test_jamali_subsystem_matches_its_book_table(section):
    assert risk_count(JAMALI[section]) == BOOK[section]


@pytest.mark.parametrize("table", sorted(SYSTEM))
def test_jamali_system_table_matches_the_book(table):
    expected = next(n for label, _pages, n, _f in SYSTEM_TABLES if label == table)
    assert risk_count(SYSTEM[table]) == expected


@pytest.mark.parametrize("section", sorted(SUMATERA_FIXTURES))
def test_sumatera_section_matches_the_deck(section):
    assert risk_count(SUMATERA_FIXTURES[section]) == SUMATERA[section]["expected"]


def test_every_book_section_has_a_fixture_and_the_totals_hold():
    # Nothing in the book is silently unmapped, and the headline numbers the
    # landing page shows are the book's own: 277 subsystem + 103 in Bab 1
    # (SUTET 31 + IBT 38 on SLDs, Peralatan 20 + Pembangkit 14 as tables).
    assert set(JAMALI) == set(BOOK)
    assert set(SYSTEM) == {label for label, *_ in SYSTEM_TABLES}
    assert sum(BOOK.values()) == 277
    assert sum(n for _l, _p, n, _f in SYSTEM_TABLES) == 103
    assert sum(s["expected"] for s in SUMATERA.values()) == 87
