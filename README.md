# MANTAPS Topology Engine

> **Status:** architecture + runnable starter repository for a corporate transmission topology / analytical-SLD platform.  
> **Current focus:** prove the data model, reconciliation model, analytical-view model, tier profiles, API flow, and generated-SLD flow before connecting to NMM/CIM and before implementing a production-grade screenshot parser.

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
 CanonicalObject + CanonicalConnection
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

The current generic `CanonicalObject` model is enough for the starter architecture, but the production physical model should expand into explicit engineering structures.

Expected hierarchy:

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

The `CanonicalConnection.scenario_id` field is the starter hook for this capability.

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

| Capability | Status | Current implementation |
|---|---|---|
| FastAPI application | ✅ Starter works | `app/main.py` |
| SQLite local database | ✅ | `app/db.py` |
| PostgreSQL Docker configuration | ✅ Starter config | `docker-compose.yml` |
| Source document model | ✅ | `SourceDocument` |
| Observed object model | ✅ | `ObservedObject` |
| Observed connection model | ✅ | `ObservedConnection` |
| Canonical object model | ✅ Generic | `CanonicalObject` |
| Canonical connection model | ✅ Generic | `CanonicalConnection` |
| Analytical views | ✅ | `AnalyticalView` |
| View membership / analytical role | ✅ | `ViewMembership` |
| Contextual risk record | ✅ | `RiskRecord` |
| Topology version hook | ✅ Starter | `TopologyVersion` |
| Reconciliation scoring | ✅ Starter | `services/reconciliation.py` |
| Structured observation import | ✅ | `/api/observations/import` |
| Candidate match API | ✅ | `/api/observations/{id}/candidates` |
| Three analytical rule-profile names | ✅ | `BACKBONE_500`, `IBT_500_150`, `SUBSYSTEM_150` |
| Demo views for same IBT in different roles | ✅ | `services/seed.py` |
| Generated SVG view | ✅ Starter | `services/sld_renderer.py` |
| Minimal web view selector | ✅ | `app/static/index.html` |
| Screenshot/vision parser | 🟡 Interface only | `VisionExtractor` |
| Vector PDF/SVG parser | ⬜ Planned | — |
| Full engineering bus/bay/CB renderer | ⬜ Planned | — |
| Explicit voltage-level model | ⬜ Planned | — |
| Explicit bay/device model | ⬜ Planned | — |
| Transformer winding model | ⬜ Planned | — |
| Generating unit/GSU model | ⬜ Planned | — |
| GI/core-aware P2B Tier algorithm | ⬜ Planned | simplified hops currently |
| Topology conflict review UI | ⬜ Planned | — |
| AHI overlay model | ⬜ Planned in repo | design defined |
| DS/ADS relationship model | ⬜ Planned in repo | design defined |
| Semantic web overlays | ⬜ Planned in this repo | prototype existed separately |
| Approval/change workflow | ⬜ Planned | topology-version hook exists |
| NMM/CIM adapter | ⬜ Future | — |

This table is important: the repo is **not claiming that every domain requirement is already coded**.

---

# 23. Repository structure

```text
mantaps-topology-engine/
├─ app/
│  ├─ main.py
│  ├─ db.py
│  ├─ models.py
│  ├─ schemas.py
│  ├─ api/
│  │  └─ routes.py
│  ├─ services/
│  │  ├─ ingestion.py
│  │  ├─ reconciliation.py
│  │  ├─ topology.py
│  │  ├─ sld_renderer.py
│  │  └─ seed.py
│  └─ static/
│     └─ index.html
├─ examples/
│  └─ sample_observations.json
├─ tests/
│  ├─ test_reconciliation.py
│  └─ test_topology.py
├─ .github/workflows/ci.yml
├─ ARCHITECTURE.md
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
└─ README.md
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

## Docker + PostgreSQL

```bash
docker compose up --build
```

---

# 25. API starter examples

## Health

```bash
curl http://localhost:8000/api/health
```

## Import structured observations

This represents what a future screenshot/vector parser should produce:

```bash
curl -X POST http://localhost:8000/api/observations/import \
  -H "Content-Type: application/json" \
  --data @examples/sample_observations.json
```

## Candidate canonical match

```bash
curl http://localhost:8000/api/observations/1/candidates
```

## List analytical views

```bash
curl http://localhost:8000/api/views
```

## Render a view

```text
GET /api/views/{view_id}/sld.svg
```

---

# 26. Recommended implementation order from this point

The next work should stay focused on making the physical topology / SLD path credible before adding too many dashboard features.

### Phase 1 — canonical electrical model

Add explicit:

- voltage level
- bus section
- bay
- CB/PMS
- circuit endpoints
- transformer + winding
- generating unit + connection

### Phase 2 — engineering SLD renderer

Implement:

- busbars
- bay stubs
- CB symbols
- CB at both circuit ends
- IBT / transformer symbols
- generator symbols
- orthogonal line routing
- deterministic placement
- layout override

### Phase 3 — analytical projection engine

Fully implement:

- 500 kV backbone rule profile
- IBT interface projection
- SS multi-voltage projection
- proper P2B Tier traversal

### Phase 4 — reconciliation / import workflow

Implement:

- vector PDF/SVG parser
- vision parser
- confidence review
- topology conflict detection
- merge/create canonical object workflow

### Phase 5 — semantic web application

Add:

- pan / zoom
- Tier overlay
- Risk overlay
- AHI overlay
- DS/ADS overlay
- click-through detail panels
- topology scenario selector

### Phase 6 — corporate governance / integration

Add:

- change request
- reviewer / approver
- effective date
- topology version publication
- Maximo/NIA mapping
- NMM/CIM adapter

---

# 27. Acceptance criteria for the real PoC

Before calling the topology engine useful for production development, one real P2B case should be reproduced end-to-end.

Suggested test:

1. take one actual existing subsystem SLD;
2. encode/extract every relevant source, bus, bay, CB, IBT/transformer, line, and GI;
3. reconcile repeated physical objects with at least one other P2B drawing;
4. generate the clean base SLD from structured topology;
5. compare the generated electrical relationships against the original SLD;
6. apply Tier as an overlay;
7. attach P2B risk records to the correct objects/context;
8. prove that one IBT can simultaneously appear in an IBT risk view and as the source boundary of a subsystem view;
9. test a topology scenario such as bus splitting;
10. preserve source-document provenance for every imported relationship.

The purpose is not pixel-perfect reproduction of an old drawing. The purpose is to prove that the structured model reproduces the **same electrical meaning** and can generate a maintainable web SLD.

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
