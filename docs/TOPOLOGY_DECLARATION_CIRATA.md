# Topology declaration - SS Cirata 1,2,3

Status: pre-Excel review. This document records the topology assumption first;
it does not change `ss_cirata_ingest.xlsx`.

## Rules used

- One bus node represents one voltage level. A site with 150 kV and 70 kV has
  two bus nodes joined by transformer units.
- A short label is not a canonical identity. `CURUG` in UP2B Jawa Barat at
  70 kV is distinct from `CURUG` in Jakarta-Banten at 150 kV.
- A 150/70 kV transformer is drawn as two coupled circles: red on the 150 kV
  side and yellow on the 70 kV side. A 150/20 kV load transformer is
  red/orange. A 70/20 kV load transformer is yellow/orange.
- Generator colour follows the represented terminal voltage. A generator-side
  terminal around 11 kV is light green. If the simplified source is represented
  after its GSU at the grid bus voltage, its lead uses that bus voltage colour.
- A node is a stub only when the source view shows a bay/arrow at its feeder or
  explicitly marks it as a neighbouring subsystem. Degree one by itself is not
  sufficient.

## Proposed bus inventory

| Internal identity | Display label | Voltage | Form | Assumption |
|---|---|---:|---|---|
| `CRATA_500` | GITET CRATA | 500 kV | one GITET bus | full bus/source |
| `CRATA_150_12` | CRATA 1,2 | 150 kV | GI bus section | supplied by IBT 1,2 |
| `CRATA_150_3` | CRATA 3 | 150 kV | GI bus section | supplied by IBT 3 |
| `CRATA_70` | CRATA | 70 kV | GI bus | full bus |
| `JTLHR_150` | JTLHR | 150 kV | GI bus | full bus |
| `JTLHR_70` | JTLHR | 70 kV | GI bus | full bus; missing today |
| `PWKTA_150` | PWKTA | 150 kV | GI bus | full bus |
| `PWKTA_70` | PWKTA | 70 kV | GI bus | full bus |
| `CURUG_JBR_70` | CURUG | 70 kV | GI bus | full bus; never reuse Jakban CURUG |

All other red buses in Gambar 3.5 remain 150 kV. All other yellow buses remain
70 kV unless a detailed SLD contradicts the overview.

## Proposed transformer relations

| From | To | Units | Drawing |
|---|---|---:|---|
| `CRATA_500` | `CRATA_150_12` | IBT 1,2 | 500/150 IBT symbols |
| `CRATA_500` | `CRATA_150_3` | IBT 3 | 500/150 IBT symbol |
| Cirata 150 kV section | `CRATA_70` | to confirm | red/yellow two-winding symbol |
| `PWKTA_150` | `PWKTA_70` | 2 shown in risk figure | red/yellow two-winding symbols |
| `JTLHR_150` | `JTLHR_70` | 3 shown in detailed SLD crop | red/yellow two-winding symbols |

There is one physical GITET Cirata. The 1,2 and 3 labels distinguish IBT groups
landing on different 150 kV bus sections at GI Cirata; they do not identify two
GITET sites. The Jatiluhur relation is the structural correction that prevents
its 70 kV branch from disappearing.

## Proposed network relations

The existing 150 kV relations remain provisional as currently traced:
PTUHA-CRATA, JTLHR-TTJBR, CRATA-PDLRU, CRATA-CKMPY,
CRATA-PWKTA, LGDAR-CGRLG, PDLRU-BDUTR, PDLRU-CBBRU, CKMPY-CBBAT,
CKMPY-IDRMA, CKMPY-PBRAN, BDUTR-DGPKR, and DGPKR-UBRNG.

The 70 kV declaration is:

- `PWKTA_70` to IDRMA 70, SPFIC 70, KSBRU 70, and SBANG 70;
- IDRMA 70 to INDCI 70;
- SPFIC 70 to CGNEA 70;
- KSBRU 70 to IDBRT 70, PNDLI 70, and RDSLK 70;
- from `JTLHR_70`, the 70 kV network branches toward CGNEA and
  `CURUG_JBR_70`; those branches subsequently continue and meet the Cirata-side
  70 kV network again;
- `CRATA_70` connects first to `PWKTA_70`, then the Purwakarta 70 kV network
  continues toward Subang. There is no direct Cirata-Subang relation;
- `KSBRU-CURUG` is retained provisionally as the return side of the 70 kV mesh.

## Stub/full-bus declaration

Full buses: every CRATA, JTLHR, PWKTA and CURUG voltage node above, plus the
internal Tier buses shown with their own horizontal busbar.

Provisional boundary stubs in this SS view:

- TTJBR at JTLHR 150 kV;
- CGRLG at LGDAR 150 kV;
- UBRNG at DGPKR 150 kV;
- PNDLI and RDSLK at the 70 kV feeder confirmed from the detailed SLD.

These objects may be full buses in their owning SS. Stub/full is therefore a
view appearance, not a permanent property of the physical GI.

## Generator declaration

- PTUHA/PLTA Cirata and PLTA Jatiluhur must use their recorded terminal voltage,
  not a global green generator style.
- PLTS Cirata keeps the photovoltaic symbol. Its lead is light green only if
  the declared point is the low-voltage generator terminal; it is red if the
  simplified SLD represents the post-GSU 150 kV connection point.
- No terminal voltage is to be inferred from `PLTA`, `PLTU`, `PLTS`, or another
  technology label.

## Confirmation still needed before rewriting the Cirata workbook

1. Which Cirata 150 kV section supplies the Cirata 70 kV transformer group.
2. Circuit counts and any intermediate endpoints on both Jatiluhur 70 kV
   branches toward Ciganea and Curug.
3. Whether the existing KSBRU 70-CURUG 70 relation is the correct return path.
4. Whether the generator symbols at PTUHA, JTLHR and PLTS Cirata represent the
   generator terminal or the post-GSU grid connection.
