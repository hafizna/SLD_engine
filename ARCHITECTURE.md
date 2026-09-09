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
                         ┌─────────────────────────────┐
                         │     CANONICAL PHYSICAL       │
                         │          TOPOLOGY           │
                         │ Substation · GeneratingUnit │
                         │ Transformer · Circuit(edge) │
                         └──────────────┬──────────────┘
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
GI Jatake  (one Substation row)
├─ SS_LBK, sisi Balaraja  → Tier 5, role CORE
└─ SS_LBK, sisi Kembangan → drawn, but not fed by any Kembangan-side seed

GI Durikosambi (one Substation row)
├─ SS Lontar-Balaraja-Kembangan → role BOUNDARY
└─ SS Muarakarang               → role CORE   (not ingested in the slice)
```

The canonical object is not duplicated. Tier is computed per view, never stored
on the object. See `SS_LBK_SLICE.md`.

## Implemented

The canonical model, the GI-aware Tier engine, reconciliation, the JSON view
contract (`/api/views/{id}/graph`), the Corporate Topology Register (Excel)
round-trip, a starter SVG renderer, and governance tables are in place and
exercised by the SS Lontar-Balaraja-Kembangan slice (`app/services/seed_ss_lbk.py`,
14 tests). Detailed status: `README.md` &sect;22.

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
