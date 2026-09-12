# Near-continuation routing handover — 12 September 2026

The router now checks completed offset conductors before committing a bundle.
Visibility-grid edge costs alone missed long horizontal runs that became
ambiguous after simplification and conductor offsets. On failure the candidate
horizontal corridor is excluded and routing is retried; existing route-order
negotiation handles blocked candidates. Geometry invariants are unchanged.

## Verified fixes

- GUCL: ASAHI–POLMA / CLBRU–MENES; MNA–KRWTU / CLGON–MITSUI.
- Pelabuhan Ratu, Salak view: SALAK–SLBRU / PRATU–CBDRU.
- Backbone 500: GNDUL–DEPOK / KMBNG–DKSBI.
- Separate IBT 500 draft: IDMYU–MDCAN / LNGKG–GNDUL (two wires),
  and IDMYU–MDCAN / KMBNG–GNDUL (one wire).

`python -m pytest -q`: 77 passed. Four workbook regression cases exercise full
geometry validation. `python scripts/audit_sample_workbooks.py`: 36 input files
PASS (includes JSON/XLSX copies, not 36 distinct subsystems), including the IBT
workbook. GUCL, Salak and Backbone crops were inspected
with browser-rendered screenshots; crossing bridges remain visible.

Implementation: `app/services/sld_layout.py`, `app/services/sld_renderer.py`.
Regression: `tests/test_sld_geometry.py`.
Report: `.render_tmp/sample-audit/WORKBOOK_AUDIT.md`.
Review SVGs/screenshots: `tmp/*-routing.svg`, `tmp/*-routing-review.png`.
Static build command:
`python scripts/build_static_site.py .render_tmp/routing-reviewed-site`.
Build completed successfully after the IBT projection was added: all 42
exported SVG views also pass geometry validation against the combined snapshot
database.

This routing fix does not edit workbook data and does not certify electrical
topology, missing future bays, or AI-extracted source accuracy. Existing IBT and
SS data-review notes remain applicable.
