# IBT and multiview audit — 2026-09-11

## Engine changes

- Excel IBT rows accept explicit `Bus HV` (aliases: `Bus Primer`, `GITET Induk`) and `Bus LV` (legacy `Bus 150 kV` remains supported).
- LV endpoint belongs to each unit, not to the whole source GITET. Units can feed different buses and appear in different views.
- Unknown IBT endpoints fail parsing rather than being replaced or discarded. Self-links and equal-voltage IBT links fail draft validation.
- Reused circuits retain unit-specific lookup keys for view membership and risk attachment.
- Three-view regression uses one canonical source shared by two views with different branches. Number of views must not create duplicate physical assets.

## Confirmed workbook defects, not router defects

`samples/ss_muarakarang_durikosambi_ingest.xlsx` parses to three GITET objects (`GITET_MKBRU`, `GITET_GIS MKBRU`, `GITET_DKSBI`) and zero IBT links. The user confirms only one GITET Muarakarang Baru belongs in this subsystem drawing. Exact LV endpoint and unit identities still need confirmation before merging or inventing connections.

DMGOT belongs to both views but only DKSBI–DMGOT exists, scoped to DURIKOSAMBI. The Muarakarang view therefore has an isolated DMGOT. User identifies it as a continuation involving PIK and Durikosambi; confirm endpoints and circuit counts before editing the physical network.

`samples/ss_prbc_ingest.xlsx` defines BEKASI and PRIOK only, with Cawang Baru combined into PRIOK. Angke–Ancol is absent in parsed connections (no dropped edges). User requests three drawings: Bekasi, Priok, Cawang Baru. Separate view membership and continuation terminals without declaring an operational split or deleting physical links. Trace all cross-view connections from supplied source drawings before regenerating the workbook.

## Remaining work

1. DONE 2026-09-12: user confirms GIS MKBRU is the LV outlet; GI MKBRU remains an incomer. PDF91-92 confirms MKBRU IBT1,2 and DKSBI IBT1. Removed only duplicate Muarakarang GITET, retained Durikosambi GITET. Added GIS–GI connection and corrected GIS Daan Mogot–PIK (formerly incorrectly KBJRK–PINKA). Reciprocal view-scoped Bay records preserve physical endpoints. Both views pass geometry audit. Fixed floating-point nontermination in the renderer's empty-strip compaction, exposed by this topology.
2. DONE 2026-09-12: PRBC has BEKASI, PRIOK, CAWANG views, explicit Angke–Ancol, Marunda–Kelapa Baru and Harapan Indah/Kandang Sapi–Plumpang continuation connections. Multiple Bay appearances per canonical GI now survive parsing/materialisation. The source workbook still contains other inherited relations; this is not a complete electrical audit of every workbook row.
3. Render every affected view and inspect IBTs, continuation labels, circuit counts and risk anchors.
4. Run workbook geometry audits. GUCL, PRBC, backbone and Pelabuhan Ratu findings remain open; parser tests do not clear them.
5. Rebuild static output only after data corrections and visual review. These engine changes alone do not fix published screenshots.

## Follow-up: projection ownership and four-bay grouping

- Explicit CIRCUIT memberships now override the original circuit owner's subsystem/drawing side. Scenario and active-state filters remain; unlisted circuits remain excluded. Regression covers shared circuits without importing their neighbours.
- Four circuits encoded in one row use the same pair spacing as two rows of two, including hanging bays. This is visual grouping, not a new physical identity assignment.
- Pemalang source writer had added 500 kV outgoing bays from the full-system appendix, not from persistent DB leakage. Removed those from this SS fixture, represented IBT1 and IBT2 separately, and restored the direct NBTNG–WLERI single circuit shown in the user's risk-map reference.
- Future bays missing from the workbook were not invented. Their source extraction remains a separate data task.
- Geometry audit passed all three PRBC views, Pemalang, and Paiton123 (Banyuwangi–Gilimanuk four-conductor case) before final snapshot integration checks.
