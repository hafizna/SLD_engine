# MANTAPS Topology Engine

> **Status:** runnable engine with a real vertical slice.  
> The canonical electrical model, the GI-aware Tier engine, the reconciliation
> model, the analytical-view model, the JSON API, the Corporate Topology Register
> (Excel) round-trip, and a starter SLD renderer are all implemented and proven
> end-to-end on one real P2B subsystem — **SS Lontar–Balaraja 1,2–Kembangan 1,2**
> from the *Buku Kerawanan SJB 2026* (section 2.5). See [`SS_LBK_SLICE.md`](SS_LBK_SLICE.md).  
> **Next:** field-review the traced topology, extend to all of Jakarta–Banten,
> then the full engineering bus/bay/CB renderer and the NMM/CIM adapter.

## Try it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload        # http://localhost:8000  (Swagger at /docs)
```

- `GET /`                         — view selector + SLD + risk / defense-scheme overlay panel
- `GET /api/views/{id}/graph`     — the JSON contract a web viewer should consume (nodes with computed Tier + role, edges, overlays)
- `GET /api/views/{id}/sld.svg`   — starter SLD
- `GET /api/register.xlsx`        — Corporate Topology Register export

```bash
docker compose up --build            # same, in a container
python scripts/build_static_site.py  # frozen snapshot -> ./site/  (for GitHub Pages)
pytest -q                            # 14 tests
```

Hosting notes (GitHub Pages static snapshot, Docker, Render, ngrok): [`DEPLOY.md`](DEPLOY.md).

---

## 1. Why this repository exists

The current P2B/MANTAPS use case is not simply “draw an SLD in a web page”. The required system must solve several different problems at the same time:

1. Existing SLDs are largely drawing/document based and may arrive as screenshots, PDF pages, SVG/vector drawings, or spreadsheets.
2. The **same physical asset** can appear in multiple drawings and multiple risk contexts.
3. There are **different analytical risk views**, not one universal risk map.
4. Subsystem SLDs are **multi-voltage and overlapping**: a 150 kV subsystem can be sourced from a GITET/IBT 500/150 kV and/or a 150 kV generating outlet, then continue to 70/30/20 kV context.
5. Tier rules are different by analytical context and should not be hard-coded into the drawing.
6. The final SLD must be generated from topology data, while Tier/Risk/AHI/Defense Scheme are **semantic overlays**.
7. The long-term corporate source is expected to move toward NMM/CIM, so the engine must not be tightly coupled to Excel or screenshots.

The repository therefore follows one central principle:

> **One canonical physical topology, multiple analytical projections, multiple evidence sources, multiple risk contexts.**

---

## 2. The most important conceptual distinction

A screenshot, PDF, Excel file, Maximo record, or future NMM/CIM object is **not automatically the canonical topology**.

Instead:

```text
SOURCE / EVIDENCE
Screenshot / PDF / SVG / Excel / Maximo / NMM
                │
                ▼
       OBSERVED / IMPORTED DATA
ObservedObject + ObservedConnection
                │
                ▼
        RECONCILIATION ENGINE
 match / review / conflict resolution
                │
                ▼
       CANONICAL PHYSICAL MODEL
 Substation + GeneratingUnit + Transformer + Circuit
                │
                ▼
        ANALYTICAL PROJECTIONS
 BACKBONE_500 / IBT_500_150 / SUBSYSTEM_150
                │
                ▼
          GENERATED BASE SLD
                │
                ▼
       SEMANTIC WEB OVERLAYS
 Tier / Risk / AHI / Defense Scheme
```

This separation is what allows two different screenshots to describe the **same IBT**, without creating two physical IBT records.

---

# 3. P2B analytical contexts that the engine must differentiate

The engine is designed around **three main analytical projections**.

## 3.1 `BACKBONE_500` — 500 kV backbone / SUTET risk view

### Primary question

> Which part of the 500 kV backbone is vulnerable?

### Core analytical objects

- GITET / 500 kV nodes
- SUTET 500 kV corridors / circuits
- 500 kV generating source context
- supporting 500 kV equipment where needed

### Primary risk object

Usually the **SUTET / corridor / backbone path**.

### Example

```text
500 kV generator
      ~
      │
   GITET A
      │
      ├══════ SUTET A-B ══════ GITET B
      │
      └══════ SUTET A-C ══════ GITET C
```

An IBT may appear here, but normally as a **boundary/context object**, not necessarily as the main risk object.

---

## 3.2 `IBT_500_150` — 500/150 kV interface risk view

### Primary question

> Which IBT/interface between the 500 kV and 150 kV systems is vulnerable, and what downstream system is exposed?

### Required context

Both voltage domains must be visible:

```text
       500 kV side
━━━━━━━━━━━━━━━━━━━━
          │
         CB
          │
      IBT 500/150       ← primary risk object
          │
         CB
          │
━━━━━━━━━━━━━━━━━━━━
       150 kV side
          │
     downstream SS
```

### Primary risk object

- IBT 500/150 kV

### Supporting context

- upstream GITET / 500 kV bus
- parallel IBT arrangement
- bus section configuration
- downstream 150 kV subsystem exposure

This view is **not simply a zoomed-in BACKBONE_500 view**. It has a different analytical purpose and may use a different display template.

---

## 3.3 `SUBSYSTEM_150` — subsystem risk view

### Primary question

> Within one subsystem, where are the vulnerable points and how is the subsystem supplied and distributed?

This is the most complex projection because the subsystem can intersect multiple voltage domains.

### Possible source paths

#### From GITET / IBT

```text
GITET 500
   │
IBT 500/150
   │
   ▼
150 kV subsystem
```

#### From 150 kV generation

```text
150 kV generator outlet
        │
        ▼
  150 kV subsystem
```

#### Combined source condition

```text
          GITET 500
              │
         IBT 500/150
              │
              ├───────────────┐
              ▼               │
          150 kV core ◄── 150 kV KIT
              │
             SUTT
              │
            GI 150
              │
       ┌──────┴────────┐
       │               │
   150/20          IBT 150/70
       │               │
     20 kV           BUS 70
                       │
                    70/20
                       │
                     20 kV
```

### Important rule

A subsystem is therefore **not equal to a single voltage level**.

Instead each object in a subsystem projection has a role.

Suggested roles:

- `SOURCE`
- `SOURCE_BOUNDARY`
- `CORE`
- `RISK_OBJECT`
- `BOUNDARY`
- `DOWNSTREAM_CONTEXT`
- `EXTERNAL_CONTEXT`

Example:

| Physical object | Voltage | Role in SS Krian view |
|---|---:|---|
| GITET Krian bus | 500 kV | `EXTERNAL_CONTEXT` or source context |
| IBT Krian 1 | 500/150 kV | `SOURCE_BOUNDARY` |
| Bus Krian 150 | 150 kV | `CORE` |
| SUTT Krian–Mojoagung | 150 kV | `CORE` |
| GI Mojoagung | 150 kV | `CORE` |
| Trafo 150/20 | 150/20 kV | `DOWNSTREAM_CONTEXT` |
| 20 kV bus | 20 kV | `DOWNSTREAM_CONTEXT` |

---

# 4. One physical object can have several analytical roles

This is the key behavior for cases where the same IBT appears in different P2B drawings.

Example canonical asset:

```text
IBT_KRIAN_1
```

It can simultaneously have these memberships:

```text
BACKBONE_500
└─ IBT_KRIAN_1 → BOUNDARY

IBT_500_150
└─ IBT_KRIAN_1 → RISK_OBJECT

SS_KRIAN_3456
└─ IBT_KRIAN_1 → SOURCE_BOUNDARY
```

The physical asset is stored **once**. The analytical role is stored in `ViewMembership`.

This prevents duplicated asset records and allows risk to be contextual rather than globally attached to an object.

---

# 5. Risk is contextual, not a global asset attribute

Do not model:

```text
IBT_KRIAN_1
Risk = HIGH
```

because the same IBT may participate in different risk conditions.

Prefer:

```text
RiskRecord
├─ risk_key
├─ analytical_view
├─ attach_object
├─ description
├─ impact
├─ mitigation
├─ follow_up
└─ priority
```

Example:

```text
RISK-IBT-001
View        = IBT_KRIAN
Attach      = IBT_KRIAN_1
Context     = IBT interface vulnerability
```

and separately:

```text
RISK-SS-001
View        = SS_KRIAN_3456
Attach      = IBT_KRIAN_1
Context     = IBT as a source-side vulnerability for the subsystem
```

Same physical object, different risk record and different interpretation.

---

# 6. Multi-source screenshot / document ingestion

The intended engine must be capable of receiving multiple drawings at different times.

Example:

```text
Day 1: upload IBT risk screenshot
      detects "IBT Krian 1"

Day 2: upload SS Krian SLD
      detects "IBT 1" at Krian

Day 3: upload 500 kV backbone drawing
      detects Krian GITET and the same IBT boundary
```

These must not automatically create three IBTs.

The ingestion model is:

```text
SourceDocument
   │
   ├─ ObservedObject
   └─ ObservedConnection
```

Observed data keeps:

- original source document
- raw label
- detected type
- site/location context
- HV/LV voltage
- unit number
- confidence
- extracted connection evidence

The reconciliation engine then proposes a canonical match.

---

# 7. Entity reconciliation

The same physical object may be written differently:

```text
IBT KRIAN 1
IBT-1 Krian
KRIAN IBT1
IBT 1
```

The current starter reconciliation engine scores candidate matches using:

- equipment/object type
- site/substation
- HV voltage
- LV voltage
- unit number
- normalized-name similarity

Current starter thresholds:

```text
score >= 0.85    AUTO_MATCH candidate
0.65 - 0.85      REVIEW
score < 0.65     CREATE_NEW candidate
```

For production, this should also include:

- connected bus
- neighboring objects
- asset ID / NIA / Maximo ID
- topology signature
- effective date/version
- source-document confidence

### Important safety rule

Low-confidence engineering matches must not silently merge topology.

Possible outcomes:

- `AUTO_MATCH`
- `REVIEW`
- `CREATE_NEW`
- `CONFLICT`

---

# 8. Topology conflict and provenance

Two drawings can disagree because they may represent:

- different years
- different commissioning states
- normal vs maintenance topology
- split bus configuration
- temporary operating configuration
- drawing error

Therefore every imported relation should eventually support:

```text
relation
├─ source_document
├─ effective_date
├─ topology_version
├─ scenario
├─ confidence
└─ validation_status
```

If one drawing says:

```text
IBT 1 → Bus A
```

and another says:

```text
IBT 1 → Bus B
```

production behavior should be:

```text
⚠ TOPOLOGY CONFLICT
```

not “pick the newest-looking line automatically”.

---

# 9. Physical topology model required for real SLD generation

The canonical model is now explicit — `Substation`, `GeneratingUnit`,
`Transformer` + `TransformerWinding`, and `Circuit` (the graph edge) — at the
GI-node granularity the risk map needs. `BusSection` / `Bay` / `Device` exist as
**nullable** tables so the schema stays CIM/NMM-compatible without forcing
bay-level detail that the risk map does not use.

Expected fuller hierarchy (partially in place, `⬜` = still a nullable stub):

```text
SUBSTATION / GITET
    │
    ├─ VOLTAGE_LEVEL
    │    ├─ BUS_SECTION
    │    ├─ BAY
    │    │    ├─ CB / PMT
    │    │    ├─ PMS
    │    │    └─ other bay devices
    │    └─ SHUNT / REACTOR / CAPACITOR
    │
    ├─ CIRCUIT
    │    ├─ SUTET
    │    ├─ SUTT
    │    ├─ SKTT
    │    └─ other line/cable types
    │
    ├─ TRANSFORMER
    │    ├─ IBT 500/150
    │    ├─ IBT 150/70
    │    ├─ transformer 150/20
    │    ├─ transformer 70/20
    │    └─ other multi-winding combinations
    │
    └─ GENERATING_UNIT
         ├─ GT
         ├─ ST
         ├─ PLTU / PLTA / etc.
         └─ GSU / generator transformer connection
```

### Voltage differentiation

The final model must distinguish, at minimum where relevant:

- 500 kV
- 150 kV
- 70 kV
- 30 kV
- 20 kV

A subsystem projection can include more than one of them.

---

# 10. Transformer model

Transformers should not be hard-coded into separate tables such as `IBT500150`, `IBT15070`, `TR15020`, etc.

Recommended production pattern:

```text
Transformer
├─ transformer_id
├─ transformer_type
├─ site
├─ rating_mva
└─ winding_count

TransformerWinding
├─ transformer_id
├─ winding_no
├─ voltage_level
├─ connected_bus
└─ role
```

This can represent:

```text
IBT 500/150
Trafo 150/20
IBT 150/70
Trafo 70/20
three-winding transformer
```

without changing the schema each time.

---

# 11. Generation/source model

The subsystem Tier source cannot be represented forever as an artificial `source = bus X` flag.

Production should explicitly model generating units and their connection points:

```text
GeneratingUnit
├─ plant_id
├─ unit_id
├─ unit_type
├─ rated_mw
└─ connection / bay
```

Examples:

```text
GT 1.1
   │
  GSU
   │
  CB
   │
150 kV bus
```

or a direct source path relevant to the analytical model.

This allows the engine to determine whether a 150 kV GI is directly supplied by a generating outlet and therefore can become a Tier-1 source path.

---

# 12. Tier is an analytical result, not a permanent part of the SLD

Tier has two roles:

1. **analytical metadata** calculated by a rule profile;
2. **optional layout constraint** used to arrange the SLD.

Tier should **not** be permanently drawn into the base SLD.

Production composition:

```text
Base SLD SVG
   │
   ├─ Tier overlay
   ├─ Risk overlay
   ├─ AHI overlay
   └─ Defense Scheme overlay
```

This is required to support zooming and semantic display behavior.

---

# 13. Tier rule profiles

Tier logic must be selected by analytical view.

The starter contains these profile names:

```text
BACKBONE_500
IBT_500_150
SUBSYSTEM_150
```

## `BACKBONE_500`

Conceptually:

```text
500 kV generating/outlet source
      ↓
first GITET / backbone level
      ↓
next GITET
      ↓
next GITET
```

The production implementation should increment Tier according to the P2B network semantics, not every auxiliary equipment node.

## `IBT_500_150`

This view does not necessarily need its own Tier calculation. It can inherit/contextualize:

- upstream 500 kV Tier
- IBT identity
- downstream subsystem exposure

## `SUBSYSTEM_150`

Source conditions include:

- direct 150 kV generating outlet
- GITET → IBT 500/150 → first 150 kV GI

Then Tier should progress through the **150 kV core network**.

Important:

```text
GI Tier 3
   │
Trafo 150/20
   │
20 kV
```

must **not** automatically become Tier 4 simply because the graph has another edge.

Downstream load context is not the same as Tier progression.

> The current starter implementation still uses simplified graph-hop logic. Production GI/core-aware traversal remains a planned upgrade.

---

# 14. Topology scenarios: normal, split bus, maintenance, island, etc.

The canonical physical network and the operating topology are not always identical.

Examples:

```text
NORMAL
Bus A ── CB CLOSED ── Bus B
```

```text
SPLIT_BUS
Bus A     CB OPEN      Bus B
```

The same physical equipment exists in both scenarios, but connectivity changes.

Expected scenario support:

- `NORMAL`
- `SPLIT_BUS`
- `MAINTENANCE`
- `LOOPING`
- `ISLAND`
- other approved operating configurations

The `Circuit.scenario_id` field is the starter hook for this capability.

---

# 15. Base SLD generation requirements

The final renderer must not look like a generic graph library output.

The engineering grammar should be:

```text
BUS A
━━━━━━━━━━━━━━━━
       │
      CB
       │
       └──────────────┐
                      │
                      │
                     CB
                      │
               ━━━━━━━━━━━━━━━
                    BUS B
```

Required rendering behavior:

- real busbar representation
- bay-specific connection points
- CB on both ends of a line/circuit where applicable
- transformer / IBT symbols
- generator symbols
- orthogonal routing
- 90-degree elbows
- no arbitrary diagonal generic graph lines
- deterministic layout
- optional manual layout override
- multi-voltage visual differentiation

The current `sld_renderer.py` is only a **starter projection renderer**, not yet the final engineering SLD renderer.

---

# 16. SLD overlays and semantic zoom

The web application should treat overlays independently.

Suggested layer controls:

```text
☑ Topology
☐ Tier Sistem
☐ Kerawanan Sistem
☐ Asset Health (AHI)
☐ Defense Scheme
```

### Semantic Tier zoom

Example behavior:

```text
zoom <= 1.4x     Tier band + label
1.4x - 2.4x      Tier line + label
2.4x - 3.5x      Tier label only
> 3.5x            Tier hidden
```

Risk/AHI/DS markers can use similar semantic zoom behavior so the detailed bay view remains readable.

---

# 17. AHI and risk are related but not the same thing

Conceptually:

```text
AHI
→ physical condition of apparatus

System vulnerability
→ importance/vulnerability of its network context

Defense Scheme
→ mitigation/protection coverage and availability
```

They should not overwrite each other.

A future prioritization layer may identify combinations such as:

```text
Poor AHI + high system vulnerability
→ priority asset

Poor AHI + high system vulnerability + degraded DS
→ critical convergence
```

but the engine should preserve the original dimensions separately.

---

# 18. Defense Scheme relationship model

A DS/ADS is **not owned exclusively by one subsystem**.

Correct conceptual relationship:

```text
Defense Scheme
      ↕
Relay / Bay / Equipment
      ↕
Physical topology
      ↕
one or many subsystems
```

Therefore a single relay/scheme may appear in multiple SS views.

Example roles:

- `TRIGGER`
- `ACTION`
- `TRIGGER_ACTION`
- `PARTICIPANT`
- `AFFECTED_ONLY`

A wide-area ADS should be modeled as one regional object with multiple topology relations rather than duplicated for each SS.

> DS tables are not yet fully implemented in this starter repo; this is part of the intended canonical model extension.

---

# 19. Initial migration vs BAU corporate workflow

## Initial migration/bootstrap

Existing drawings can be used to build the first canonical model:

```text
Upload existing SLD
      ↓
vector/vision extraction
      ↓
candidate topology
      ↓
reconciliation
      ↓
human validation
      ↓
canonical baseline
```

Excel can also be used as an import/review format during this phase.

## BAU after baseline exists

The desired corporate process is **not**:

```text
edit drawing → upload new drawing → replace old drawing
```

It should be:

```text
Topology Change Request
      ↓
structured topology change
      ↓
validation
      ↓
preview generated SLD
      ↓
technical review
      ↓
approval + effective date
      ↓
new ACTIVE topology version
```

Examples:

- add GI/GITET
- add bay
- commission line
- move bay from Bus A to Bus B
- change normal bus-coupler state
- add IBT
- split subsystem

`TopologyVersion` is already present as the starter table for this future workflow.

---

# 20. Database and document storage concept

The database should store **structured topology**, not only uploaded drawings.

Recommended production persistence:

### PostgreSQL / PostGIS

- canonical objects
- canonical connectivity
- topology scenarios
- analytical views
- view membership
- risk records
- asset references
- topology versions
- reconciliation results
- change sets

### Object storage (S3 / MinIO / corporate equivalent)

- uploaded PDF
- screenshots
- SVG
- DWG/export files
- generated SLD SVG
- supporting evidence

The DB stores document metadata / URI / checksum / provenance instead of treating large image files as the topology itself.

---

# 21. NMM/CIM future integration

Excel and screenshot import are **temporary/source adapters**, not the long-term engine contract.

Target architecture:

```text
TODAY
Screenshot / Excel
       │
   adapters
       │
       ▼
Canonical topology
       │
       ▼
MANTAPS engine
```

```text
FUTURE
NMM / CIM
    │
NMM adapter
    │
    ▼
Canonical topology
    │
    ▼
Same MANTAPS engine
```

The web renderer, analytical views, risk attachment model, and application API should not need to be rebuilt simply because the authoritative source changes from spreadsheet to NMM.

---

# 22. What is implemented in this repository now

| Capability | Status | Where |
|---|---|---|
| FastAPI application | ✅ | `app/main.py` |
| SQLite local DB / PostgreSQL via `psycopg` | ✅ | `app/db.py`, `docker-compose.yml` (Postgres profile) |
| Provenance: source document + observed object/connection | ✅ | `SourceDocument`, `ObservedObject`, `ObservedConnection` |
| **Explicit canonical electrical model** | ✅ | `Substation`, `GeneratingUnit`, `Transformer` + `TransformerWinding`, `Circuit` |
| Engineering detail as nullable CIM-shaped stubs | ✅ | `BusSection`, `Bay`, `Device` (unused by the risk map) |
| One physical GI → many subsystems / roles | ✅ | `Subsystem`, `SubsystemMembership` (`role`, `external_subsystem`) |
| Analytical views + membership + rule profiles | ✅ | `AnalyticalView`, `ViewMembership`; `BACKBONE_500` / `IBT_500_150` / `SUBSYSTEM_150` |
| **GI/core-aware Tier algorithm** | ✅ | `services/topology.py` — BFS over the GI graph, load transformers do not add a Tier, not-yet-energised nodes excluded; Tier computed per-view, never stored |
| Contextual risk record (Kondisi/Dampak/Mitigasi/Solusi) | ✅ | `RiskRecord` |
| Defense Scheme + relation (multi-object, cross-SS) | ✅ | `DefenseScheme`, `DSRelation` |
| AHI record | ✅ schema | `AhiRecord` (no data in the slice) |
| Governance: topology version + change set | ✅ | `TopologyVersion`, `ChangeSet` |
| Reconciliation scoring + `AUTO_MATCH/REVIEW/CREATE_NEW` | ✅ Starter | `services/reconciliation.py` |
| Structured observation import + candidate API | ✅ | `/api/observations/import`, `/api/observations/{id}/candidates` |
| **JSON view contract for a web viewer** | ✅ | `/api/views/{id}/graph` (nodes+Tier+role, edges, overlays) |
| Starter SVG renderer with overlay layers | ✅ Starter | `services/sld_renderer.py` (`<g id="overlay-tier">`, `overlay-risk`) |
| Corporate Topology Register (Excel) export + round-trip | ✅ | `services/excel_register.py`, `/api/register.xlsx` |
| Web view selector + overlay panel | ✅ | `app/static/index.html` |
| Static snapshot build for GitHub Pages | ✅ | `scripts/build_static_site.py` |
| Real vertical slice seeded from the book | ✅ | `services/seed_ss_lbk.py` — 41 GI, 49 circuits, 6 risks, 3 DS, 3 views |
| SLD colour-convention status enum | ✅ | `ENERGIZED / NEW_NOT_ENERGIZED / PLANNED / DE_ENERGIZED / OWNED_BY_CUSTOMER` |
| Screenshot / vision parser | 🟡 Interface only | `VisionExtractor` |
| Vector PDF/SVG parser | ⬜ Planned | — |
| Full engineering bus/bay/CB renderer | ⬜ Planned | starter renderer only |
| Explicit voltage-level / bay / device *data* | ⬜ Planned | stubs exist, unpopulated |
| Topology conflict detection + review UI | ⬜ Planned | — |
| Semantic zoom on overlays | ⬜ Planned | — |
| Approval / change-request workflow (UI) | ⬜ Planned | `TopologyVersion` / `ChangeSet` tables exist |
| NMM/CIM adapter | ⬜ Future | — |

The traced topology in the slice carries **confidence tags** — many circuits are
at 0.4–0.7 and marked `NEEDS_REVIEW` pending the field team. See `SS_LBK_SLICE.md`.

---

# 23. Repository structure

```text
SLD_engine/
├─ app/
│  ├─ main.py                     FastAPI app + CORS + boot seed
│  ├─ db.py                       engine / session (SQLite or Postgres via DATABASE_URL)
│  ├─ models.py                   canonical model (see §22)
│  ├─ schemas.py                  observation-import + create-view payloads
│  ├─ api/routes.py               /api/views, /graph, /sld.svg, /register.xlsx, /observations
│  ├─ services/
│  │  ├─ topology.py              GI-aware Tier engine + view projection
│  │  ├─ reconciliation.py        observed → canonical scoring
│  │  ├─ ingestion.py             structured-observation adapter contract
│  │  ├─ sld_renderer.py          starter SVG (busbars in Tier bands + overlay layers)
│  │  ├─ excel_register.py        Corporate Topology Register export / import
│  │  ├─ seed.py                  seed entry point
│  │  └─ seed_ss_lbk.py           SS Lontar–Balaraja–Kembangan fixture
│  └─ static/index.html           view selector + SLD + overlay panel
├─ scripts/
│  ├─ build_static_site.py        render every view to ./site/ for GitHub Pages
│  ├─ static_index.html           the snapshot viewer
│  └─ pages.yml                   → copy to .github/workflows/pages.yml
├─ examples/
│  ├─ sample_observations.json    example import batch (SS_LBK)
│  └─ Corporate_Topology_Register_SLD_V2.xlsx   generated register
├─ tests/                         14 tests: topology, reconciliation, API contract
├─ SS_LBK_SLICE.md                what the slice proves + field-review items
├─ DEPLOY.md                      hosting options
├─ ARCHITECTURE.md                compact technical map
├─ Dockerfile / docker-compose.yml / render.yaml
└─ requirements.txt
```

---

# 24. Quick start

## Local SQLite

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
```

Swagger API:

```text
http://localhost:8000/docs
```

## Docker

```bash
docker compose up --build                        # SQLite, no DB service
docker compose --profile postgres up --build     # against Postgres
```

## Static snapshot / GitHub Pages

```bash
python scripts/build_static_site.py site          # -> ./site/
```

Auto-published to `https://<user>.github.io/SLD_engine/` by
`.github/workflows/pages.yml` on each push to `main` (see `DEPLOY.md`).

---

# 25. API examples

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/subsystems
curl http://localhost:8000/api/views

# full contract for a web viewer: nodes (with Tier + role), edges, overlays
curl http://localhost:8000/api/views/3/graph | jq '.nodes[0], (.overlays.risk|length)'

curl http://localhost:8000/api/views/3/sld.svg -o view.svg
curl http://localhost:8000/api/register.xlsx -o register.xlsx

# stage an evidence source, then see reconciliation candidates
curl -X POST http://localhost:8000/api/observations/import \
  -H "Content-Type: application/json" --data @examples/sample_observations.json
curl http://localhost:8000/api/observations/1/candidates
```

---

# 26. Recommended implementation order from this point

**Done** (see §22): explicit canonical model (Substation / GeneratingUnit /
Transformer+Winding / Circuit), GI-aware Tier engine, three rule profiles,
reconciliation, JSON view contract, Excel register round-trip, starter renderer,
governance tables, and the SS_LBK vertical slice.

**Next:**

### Phase A — field-review + widen the data

- reconcile the SS_LBK traced circuits with the field team (`NEEDS_REVIEW` tags)
- extend to the rest of UP2B Jakarta–Banten, then the other UP2Bs
- populate `BusSection` / `Bay` / `Device` only where a risk case needs it

### Phase B — engineering SLD renderer

Real busbars, bay stubs, CB symbols with a CB on both ends of a circuit,
IBT/transformer/generator symbols, orthogonal routing, deterministic placement,
manual layout override. The current `sld_renderer.py` is a starter GI-graph
projection, not this.

### Phase C — reconciliation / import workflow

- vector PDF/SVG parser and a vision parser feeding the same observation contract
- topology conflict detection (drawing A: IBT→Bus A, drawing B: IBT→Bus B → ⚠)
- a merge / create-canonical review UI over the reconciliation candidates

### Phase D — semantic web application

Pan/zoom, layer toggles with semantic zoom for Tier / Risk / AHI / DS,
click-through detail panels, scenario selector. The JSON contract at
`/api/views/{id}/graph` already exists for a viewer to build on.

### Phase E — governance + integration

Change request → review → approval → effective date → published `TopologyVersion`;
Maximo/NIA mapping; the **NMM/CIM adapter** that replaces the screenshot/Excel
adapters without touching the engine, the views, or the API.

---

# 27. Acceptance criteria for the real PoC — status

One real P2B case reproduced end-to-end. **Done for SS Lontar–Balaraja–Kembangan**
(`SS_LBK_SLICE.md`):

| # | Criterion | Status |
|---|---|---|
| 1 | take one actual existing subsystem SLD | ✅ Buku Kerawanan SJB 2026 §2.5 (two SLDs, hal. 69–70) |
| 2 | encode every source, GI, IBT/transformer, line | ✅ 41 GI, 4 IBT, 1 generator, 49 circuits |
| 3 | reconcile repeated objects across drawings | ✅ intersection GIs stored once; reconciliation scoring + round-trip |
| 4 | generate a base SLD from structured topology | 🟡 starter renderer (engineering renderer = Phase B) |
| 5 | compare generated relationships vs the original | 🟡 pending field review of `NEEDS_REVIEW` circuits |
| 6 | apply Tier as an overlay | ✅ computed per view, drawn as `<g id="overlay-tier">` |
| 7 | attach P2B risk records to the correct objects | ✅ 6 risks on the right transformer / circuit / GI |
| 8 | one object, several analytical roles | ✅ GI Jatake: Tier 5 from the Balaraja seed, unreachable from the Kembangan SLD; Durikosambi: BOUNDARY here / CORE in SS Muarakarang |
| 9 | a topology scenario such as bus splitting | 🟡 `scenario_id` hook present; not populated (peta risiko is the non-dynamic ideal snapshot) |
| 10 | preserve provenance for every relationship | ✅ every circuit carries `source_document_id` + `confidence` |

The purpose is not pixel-perfect reproduction of an old drawing — it is proving
the structured model carries the **same electrical meaning** and can drive a
maintainable web SLD.

---

# 28. Short summary

If only one section of this README is remembered, it should be this:

```text
Do not build three separate topology databases.
Do not use screenshots as the permanent source of truth.
Do not bake Tier/Risk/AHI/DS into the SLD image.
Do not make one IBT record per analytical map.

Build one canonical physical topology.
Reconcile all imported evidence into that topology.
Project it differently for:
  1. 500 kV backbone risk,
  2. IBT 500/150 risk,
  3. subsystem risk.

Generate a clean engineering SLD from physical topology.
Add Tier/Risk/AHI/DS as semantic web layers.
Later replace screenshot/Excel adapters with NMM/CIM without replacing the engine.
```
