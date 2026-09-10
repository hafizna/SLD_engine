# MANTAPS Topology Engine

The data layer under **Peta Kerawanan**. It turns a **structured description of
one transmission subsystem** — GI list, GI-to-GI relations, kerawanan table —
into a PLN-style single-line diagram with the Tier engine and the kerawanan
overlay, and holds it as one canonical relational model per UP2B.

```
per UP2B
  └─ subsystem (SS)
       └─ point of view (a book SLD page / "sisi X")
            ├─ generated SLD  (busbars, bays, IBT/trafo/capacitor symbols, parallel orthogonal routing, crossing gaps)
            ├─ Tier            (computed per view from the sources, drawn as an overlay, never stored)
            └─ kerawanan       (N-1 / N-2 / N-1-1 / N-0 points pinned to an object, from the Buku Kerawanan table)
```

## Run it

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

| URL | What |
|---|---|
| `http://localhost:8000/` | **Peta Kerawanan** — UP2B → SS → point-of-view tree, SLD viewer, layer toggles (Tier / kerawanan / defense scheme / audit), click a busbar / line / bay for detail, pan & zoom |
| `http://localhost:8000/ingest` | **Add a subsystem** — upload the Excel template, check & confirm what the parser read, watch the SLD preview redraw, publish. Nothing is written to the DB until *Terbitkan*. |
| `http://localhost:8000/editor` | **Change an existing subsystem** — ChangeRequest workflow (add / remove / patch GI & lines → validate → impact preview → publish a new `TopologyVersion`); kerawanan is a direct-edit overlay |
| `http://localhost:8000/docs` | Swagger |

```bash
pytest -q                             # 37 tests
python scripts/build_static_site.py   # frozen view-only snapshot -> ./site/  (GitHub Pages; no /ingest, no /editor)
```

For a local renderer review using the **current database**, run:

```bash
python scripts/review_sld.py --database mantaps.db --baseline HEAD
```

Open `.render_tmp/sld-review/index.html` for the before/after comparison and
individual SVGs. The command copies SQLite into memory through a read-only
connection; it does not start the app, seed data, or publish an ingest draft.

The renderer now orders the complete layered graph, aligns radial **ports**,
reserves routing space around busbars/symbols, and offsets complete orthogonal
bundles at a consistent 14 SVG-unit conductor pitch. Related circuit records
share a bundle while keeping their own IDs, styles and generator taps. White
clearance around a semicircular bridge means **no electrical connection**. Geometry regression
tests cover both LBK views, Balaraja–Lengkong and Cawang–Depok.

Long routes reserve channels first within a tier gap. Soft reservations and a
small proximity penalty discourage unrelated runs from reading as one line.
Crossing detection handles both route orders; the vertical wire owns the bridge.
Generator taps sit halfway along the routed conductor. `single_phi` metadata is
preserved and does not change stroke width within a two-circuit corridor.

Bus coupler glyphs are omitted until bay-to-bus-section mapping and an operating
scenario are available; `busbar_config` metadata is retained. Transformer and
capacitor counts accept optional `Jumlah Trafo`, `Jumlah Kapasitor`, and
`Catatan Simbol` Excel columns and can be reviewed before publishing new assets.
Legacy explicit counts in symbol notes are also rendered. Reviewed symbol-only
data corrections are listed in `samples/sld_symbol_corrections.json`; run
`python scripts/repair_sld_symbols.py` to inspect differences, or add `--apply`
to apply them with a SQLite backup. These observations are drawing inventories,
not verified physical equipment registers.

Template compatibility is separate from layout: the current Excel parser still
does not import a `Views` sheet or per-row `Sudut Pandang`. Existing LBK views
are rendered separately from their stored view membership. A new multi-view
workbook needs that parser/materialisation extension before it can faithfully
create multiple views; the renderer must not infer or merge those contexts.

Hosting (Hugging Face Spaces, Render, Docker, ngrok, GitHub Pages): [`DEPLOY.md`](DEPLOY.md).

## What works today

| Capability | Where |
|---|---|
| Canonical model: `Substation` / `GeneratingUnit` / `Transformer` + `TransformerWinding` / `Circuit`, at GI-node granularity | `app/models.py` |
| One physical GI in many subsystems / roles | `Subsystem`, `SubsystemMembership` |
| Analytical views + membership + rule profiles (`SUBSYSTEM_150`, `IBT_500_150`, `BACKBONE_500`) | `AnalyticalView`, `ViewMembership` |
| **Tier engine** — book Tier band when the drawing gives one, else a BFS hop count from the sources; per view, never stored; non-live objects excluded | `app/services/topology.py` |
| **SLD renderer** — busbars in Tier rows, bay stubs with GI codes, IBT/transformer/capacitor/generator symbols, shared parallel circuit routes, obstacle avoidance and crossing gaps, a mapping-audit strip so nothing from the parse vanishes silently | `app/services/sld_renderer.py` |
| Kerawanan overlay — `RiskRecord` with `category` (N-1 / N-2 / N-1-1 / N-0), pinned to a GI / line / transformer by code | `RiskRecord` |
| Defense scheme + relation (multi-object, cross-SS) | `DefenseScheme`, `DSRelation` |
| **`/ingest`** — stateless: the draft is a JSON blob in the browser; the parser reads the PLN Excel template (3 sheets + optional `Info` / `Bay`), reconciliation suggests matches to existing GIs, the preview renders inside a rolled-back DB savepoint, and only publish writes; blocks re-bootstrapping a subsystem that already exists (→ `/editor`) | `app/services/ingest.py`, `ingest_parser.py`, `app/static/ingest.html` |
| **`/editor`** — ChangeRequest workflow: `validate` (no GI newly isolated, seed Tier intact) → `impact` (apply on a savepoint, diff live network + Tier + affected kerawanan, roll back) → `publish` (new `TopologyVersion` ACTIVE, previous SUPERSEDED) | `app/services/editor.py`, `editor_risks.py`, `app/static/editor.html` |
| Reconciliation scoring (`AUTO_MATCH` / `REVIEW` / `CREATE_NEW`) | `app/services/reconciliation.py` |
| Corporate Topology Register (Excel) export + import round-trip | `app/services/excel_register.py`, `/api/register.xlsx` |
| Persisted per-view node positions (auto-layout is a seed; a dragged position wins) | `DiagramNodePosition`, `/api/views/{id}/layout` |
| JSON view contract for a web viewer | `/api/views/{id}/graph` |
| Governance tables | `TopologyVersion`, `ChangeSet` |

### Proven on real P2B subsystems (Buku Kerawanan SJB 2026)

| SS | Section | Shape it tests |
|---|---|---|
| **SS Lontar–Balaraja 1,2–Kembangan 1,2** | §2.5 | one SS drawn on two book pages, two points of view; a GI has a different Tier per view; relations on both pages so a downstream GI shows dual supply |
| **SS Balaraja 3,4–Lengkong 1,2** | §2.6 | one SLD, two independent Tier-1 sources that meet only far downstream via a normal circuit |
| **SS Cawang 2,3–Depok 1** | §2.7 | added through `/ingest` from the Excel template; a GITET with a single IBT link; a GITET whose 150 kV bus has a different code |

Traced circuits carry a **confidence tag**; anything below 0.9 is marked
`NEEDS_REVIEW` for the field team. See [`SS_LBK_SLICE.md`](SS_LBK_SLICE.md).

## What is NOT built

### Picture / PDF → structure  *(the big one)*

The engine does **not read an SLD from an image or PDF.** There is no OCR /
computer-vision / spatial-reasoning pipeline. The structured input is authored
by a person (the Excel template) or, for the built-in slices, hand-encoded from
the book.

Plain Python cannot do this. Two routes, both deferred:

- **AI vision agent** — send the image to a vision-capable model with a
  structured prompt, get back busbar / symbol / relation JSON, drop it into the
  `/ingest` draft flagged low-confidence for the user to correct. This is what a
  person does today reading the book by eye; wiring it to the webapp is the
  future task. Needs an API key and has a per-call cost; the output still must
  be confirmed.
- **Own CV pipeline** (OpenCV symbol detection + Tesseract OCR + line tracing)
  — months of work, needs labelled PLN SLDs, lower accuracy. Not planned.

### Other deferred items

| Item | Note |
|---|---|
| Kerawanan-table PDF → draft rows | `pdfplumber` could pull the No/UIT/Kondisi/Dampak/Mitigasi/Usulan table; kerawanan is hand-entered for now |
| JavaScript port of parser + Tier + renderer | would let GitHub Pages preview a mapping with no backend, but means two renderers to keep identical while the Python one is still changing — deferred until the renderer is stable; for a live demo, deploy the engine |
| Explicit UP2B entity | grouping uses `Subsystem.apb` (a string); a real `UP2B` table with an FK is a later step |
| Engineering bus/bay/CB detail *data* | `BusSection` / `Bay` / `Device` tables exist as nullable stubs, unpopulated; the risk map does not need bay-level detail |
| Topology conflict detection | drawing A: IBT→Bus A, drawing B: IBT→Bus B → ⚠ ; not implemented |
| Operating scenarios (SPLIT_BUS, MAINTENANCE, …) | `Circuit.scenario_id` hook exists; the risk map is the normal-operation snapshot |
| AHI overlay | `AhiRecord` schema exists, no data |
| NMM / CIM adapter | the long-term corporate source; the engine, views and API are built so this replaces the Excel adapter without touching them |

## Future works — suggested order

1. **Field-review** the traced `NEEDS_REVIEW` circuits with the P2B team.
2. **Widen the data** — the rest of UP2B Jakarta–Banten via `/ingest`, then the other UP2Bs; add a real `UP2B` entity when there is more than one.
3. **Renderer hardening** — keep testing against new subsystem shapes and fixing layout misses (label collisions, routing, de-overlap) until it is stable.
4. **Picture → structure** — the AI-vision pre-mapping into `/ingest` (see above); optionally the kerawanan-table PDF parser first as the easy win.
5. **Governance UI polish** — the ChangeRequest review screens, effective dates, Maximo / NIA asset mapping.
6. **NMM / CIM adapter.**

## Repository map

```
app/
├─ main.py                    FastAPI app + boot seed; routes for /, /ingest, /editor
├─ models.py                  canonical model + staging + governance tables
├─ api/routes.py              /api/views, /graph, /sld.svg, /ingest/*, /change-requests/*, /risks/*, /register.xlsx
├─ services/
│  ├─ topology.py             Tier engine + view projection + layout classification
│  ├─ sld_renderer.py         the SLD generator (SVG, PLN drawing grammar)
│  ├─ ingest.py               /ingest: draft blob → validate → savepoint-render → publish
│  ├─ ingest_parser.py        Excel template (+ JSON hand-off) → normalised payload
│  ├─ editor.py               ChangeRequest workflow (validate / impact / publish)
│  ├─ editor_risks.py         kerawanan direct edit
│  ├─ reconciliation.py       observed → canonical scoring
│  ├─ excel_register.py       Corporate Topology Register export / import
│  ├─ seed.py                 seed entry point (SS_LBK + SS_BLL)
│  ├─ seed_ss_lbk.py          SS Lontar–Balaraja–Kembangan fixture
│  ├─ seed_ss_bll.py          SS Balaraja 3,4–Lengkong 1,2 fixture
│  └─ seed_ss_cwd.py          SS Cawang 2,3–Depok 1 (parser-test fixture; NOT wired into seed.py)
└─ static/                    index.html (viewer), ingest.html, editor.html
scripts/
├─ build_static_site.py       render every view to ./site/ for GitHub Pages
├─ static_index.html          the snapshot viewer
├─ make_ingest_sample_xlsx.py regenerate samples/ss_cwd_ingest.xlsx from the JSON
└─ pages.yml                  → copy to .github/workflows/pages.yml (needs `workflow` scope)
samples/
├─ ss_cwd_ingest.xlsx         a filled PLN template (the /ingest demo + `/api/ingest/sample`)
└─ ss_cwd_ingest.json         the same as a JSON hand-off
tests/                        47 tests: topology, reconciliation, API contract, /ingest, editor
CONCEPT.md                    the original design document (analytical contexts, why-this-exists, full model rationale)
PROBIS_KONSEP.md              the change-management business process (structural vs operating change)
SS_LBK_SLICE.md               what the SS_LBK slice proves + field-review items
ARCHITECTURE.md               compact technical map
DEPLOY.md                     hosting options
```

## Principles (from `CONCEPT.md`)

- One canonical physical topology; many analytical projections; many evidence sources; many risk contexts.
- A screenshot / Excel / NMM object is **not** automatically the canonical topology — it is staged, reconciled, then promoted.
- One physical asset is stored **once**; its analytical role lives in `ViewMembership`.
- Risk is **contextual** (a `RiskRecord` in a view), never a global attribute on an asset.
- Tier / Risk / AHI / Defense Scheme are **semantic overlays**, never baked into the base SLD.
- Structural change goes through a ChangeRequest → new `TopologyVersion`; operating-pattern change goes through `scenario_id`.
