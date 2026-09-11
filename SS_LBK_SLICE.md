# Vertical slice: SS Lontar &ndash; Balaraja 1,2 &ndash; Kembangan 1,2

Source: **Buku Kerawanan SJB 2026**, section 2.5
- hal. 69 &mdash; SLD sisi Kembangan
- hal. 70 &mdash; SLD sisi Balaraja / Lontar
- Tabel 2.3 &mdash; 6 titik kerawanan

This slice proves the canonical model end-to-end on one real P2B subsystem
(acceptance criteria, README &sect;27) before scaling to all of Jakarta-Banten.

## What it demonstrates

| Principle | How this slice shows it |
|---|---|
| One canonical GI graph, many projections | 41 GI stored once; three views (`SS_LBK_KEMBANGAN`, `SS_LBK_BALARAJA`, `SS_LBK_FULL`) |
| Tier is computed per-projection, never stored | GI **Jatake** = Tier 5 traced from the Balaraja seed, unreachable from the Kembangan SLD alone. `Substation` has no `tier` column. |
| One physical GI, several subsystem roles | Durikosambi = `BOUNDARY` here, `CORE` in SS Muarakarang. Danayasa/AGP/Mampang = `BOUNDARY` &rarr; SS Gandul 2,4. |
| Risk is contextual, attached in a view | 6 `RiskRecord`s attached to the correct transformer / circuit / substation |
| Tier / Risk / DS are overlays, not baked in | SVG has separate `<g id="overlay-tier">` / `<g id="overlay-risk">`; API returns `overlays` block |
| Status from the SLD colour convention | red = `ENERGIZED`, black = `NEW_NOT_ENERGIZED` (GITET New Cikupa, Tangerang Baru 3), grey = `PLANNED` (Senayan&ndash;AGP feeder) |
| Not-yet-energised projects are informational | GITET New Cikupa is a node with a `TopologyVersion` + `ChangeSet`, but is **not** in the Tier graph. When it is commissioned that is a structural change via change request, not a toggle. |
| Provenance | every `Circuit` carries `source_document_id` + `confidence`; traced-but-uncertain edges are tagged `NEEDS_REVIEW` |

## SLD symbol convention (this book)

| Symbol | Meaning |
|---|---|
| Double circle (red/orange) | 150/20 kV load transformer &mdash; marks *that the GI has a transformer*, not how many |
| Triple circle | IBT (e.g. 500/150 at a GITET) |
| Busbar blue / light-blue / bright-yellow / orange / red / black | 500 / 275 / 70 / 20 / 150-energised / 150-not-yet-energised kV |
| `//` + ground | shunt capacitor |
| Only a line between two horizontal busbars | a `Circuit` (edge). Anything hanging down = a GI attribute. |

## Known items to review with the field team (next week, full Jakarta-Banten)

- Many circuits are traced from the SLD at confidence 0.4&ndash;0.7 &mdash; see `note LIKE '%NEEDS_REVIEW%'`
- `busbar_config` for Durikosambi recorded as `DOUBLE_SECTIONALIZED` (Bus 1A/2A/1B/2B) but bays not split
- Maxim drawn with 3 transformers &mdash; confirm with OSL whether the count is meaningful
- The unlabeled load GI on the left of the Kembangan Tier-1 bus is skipped

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- `GET /` &mdash; view selector + SLD + risk/DS overlay panel
- `GET /api/views/{id}/graph` &mdash; JSON contract for a web viewer (nodes+tier+role, edges, overlays)
- `GET /api/views/{id}/sld.svg` &mdash; starter SVG
- `GET /api/register.xlsx` &mdash; Corporate Topology Register export (18-ish sheets)

```bash
python -m pytest -q
```
