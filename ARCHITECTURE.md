# MANTAPS Topology Engine — Architecture Summary

The detailed domain explanation is in `README.md`. This file is intentionally the compact technical map.

```text
                         ┌─────────────────────┐
                         │  SOURCE / EVIDENCE  │
                         │ PDF / Image / SVG   │
                         │ Excel / Maximo / NMM│
                         └──────────┬──────────┘
                                    │
                            extractor / adapter
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ OBSERVATION STAGING │
                         │ ObservedObject      │
                         │ ObservedConnection  │
                         └──────────┬──────────┘
                                    │
                         reconciliation / review
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ CANONICAL PHYSICAL  │
                         │      TOPOLOGY       │
                         │ object + connection │
                         └──────────┬──────────┘
                                    │
                          view projection engine
               ┌────────────────────┼─────────────────────┐
               ▼                    ▼                     ▼
       ┌──────────────┐     ┌───────────────┐     ┌────────────────┐
       │ BACKBONE_500 │     │ IBT_500_150   │     │ SUBSYSTEM_150  │
       │ SUTET context│     │ interface view│     │ multi-voltage  │
       └───────┬──────┘     └───────┬───────┘     └────────┬───────┘
               └────────────────────┼───────────────────────┘
                                    │
                             rule-profile Tier
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ CLEAN BASE SLD SVG  │
                         │ bus/bay/CB/circuit  │
                         │ IBT/trafo/generator │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ SEMANTIC WEB LAYERS │
                         │ Tier / Risk / AHI   │
                         │ Defense Scheme      │
                         └─────────────────────┘
```

## One-object / multi-context rule

```text
IBT_KRIAN_1
├─ BACKBONE_500  → BOUNDARY
├─ IBT view      → RISK_OBJECT
└─ SS Krian      → SOURCE_BOUNDARY
```

The canonical object is not duplicated.

## Persistence

Production recommendation:

- PostgreSQL/PostGIS → topology, views, risk, versions, relations
- S3/MinIO → uploaded evidence and generated files
- optional queue/cache → ingestion/reconciliation jobs

## Target integration

```text
Current adapters: screenshot / PDF / Excel
Future adapter: NMM / CIM

Both must produce the same canonical model contract.
```
