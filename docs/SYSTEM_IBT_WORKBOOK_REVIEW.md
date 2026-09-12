# Sistem 500 kV–IBT workbook

File: `samples/system_ibt_500_ingest.xlsx`.
Builder: `python scripts/make_system_ibt_500_xlsx.py`.

This is a draft input for user review, separate from transmission-risk and SS
workbooks. No SS files are changed by this builder. It is seeded into the
dashboard as the separate Sistem 500 kV > IBT view.

- Map: existing 500 kV backbone topology, profile `IBT_500_150`.
- Risks: 38 records extracted from Table 1.2, PDF pages 41–64, numbered 1–38.
- Targets: 45 rows, including related GITETs. One primary GITET pin per risk
  is imported today; secondary targets remain explicit review metadata.
- Units: `IBT_Unit_Review` snapshots parsed 500 kV IBT links from available SS
  workbooks, with filename and SHA256. It is not an authoritative inventory:
  collapsed unit rows and aliases still require SS-by-SS confirmation.
- Categories: candidates extracted only from condition text. Missing explicit
  contingency is `BELUM_DITETAPKAN`; mixed cases remain visible for review.

The map deliberately retains 500 kV topology. Review inventory does not create
unconfirmed 150 kV buses/links on that map. User review should confirm primary
pin placement, secondary targets, units and endpoint identity before publication.

Validation: parser and draft validation passed with 64 objects, 73 connections,
38 risks and no dropped endpoints. The three near-continuations at IDMYU–MDCAN
against LNGKG–GNDUL (two wires) and KMBNG–GNDUL (one wire) were reproduced and
resolved by the router on 12 September 2026. Full geometry audit now passes;
the workbook is covered by a regression test. Electrical-data and target review
above remains required; geometry PASS is not confirmation of that inventory.
