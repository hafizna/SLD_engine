# Review: `samples/system_ibt_500_ingest.xlsx`

Findings only. Nothing in this file has been changed; the questions below need
a decision before any edit.

## What the fixture claims to be

The view renders with the title **"SS Sistem Jamali 500 kV - Kerawanan IBT
500/150 kV"** and is the `IBT` entry under the product's Sistem 500 kV menu,
the counterpart to `Transmisi`.

## What it actually contains

Parsed with the production parser:

```
objects 64   GITET 46, GENERATING_UNIT 18
connections 73
IBT_LINK connections: 0
```

**Zero IBT links.** A view whose whole subject is the 500/150 kV transformers
contains no transformer. The rendered SVG matches: an all-blue 500 kV network
with generators on Tier-1 and no IBT symbol anywhere.

## It is the backbone topology under another name

Comparing against `samples/backbone_500_ingest.xlsx`:

```
backbone objects 64   ibt objects 64   identical? True
backbone conns   73   ibt conns   73   identical? True
risks backbone   31   risks ibt   38
SS code: BACKBONE_500_JB   vs   SYSTEM_IBT_500
```

The object set and the connection set are identical. The two fixtures differ
only in subsystem code, title and risk count. So the IBT view is currently the
Transmisi view relabelled, which is why it looks wrong: it is drawing the
right network for the wrong question.

## Why no IBT can be expressed in this file

Its `Gardu_Induk_dan_Aset` sheet has **11 columns**:

```
No | Nama Asset / GI | Kode Singkatan | Tipe Asset | Tier (Mulai 0) |
Tegangan | No IBT | Status Kerawanan | No Kerawanan | Wilayah | Sudut Pandang
```

There is no `Bus HV` and no `Bus LV`, and no row of type `IBT 3-Winding`. The
file predates the IBT endpoint contract in `docs/IBT_MULTIVIEW_AUDIT.md`, so
the parser has nothing to build an `IBT_LINK` from even in principle. Compare
`_ss_xlsx_common.ASSET_HEADER`, which now emits 20 columns including both
endpoints.

## The two review sheets are a worklist, not data

`Target_Kerawanan_IBT` (45 rows) and `IBT_Unit_Review` (58 rows) both carry
`PERLU REVIEW` on **every** row. They are Codex's to-do list for confirming
which IBT unit each risk points at, not confirmed content.

`IBT_Unit_Review` also captured `Unit = '1'` for banks the book names as pairs,
because it was generated before the unit-list fix. Those values are stale:
43 IBT banks now carry their full list (`1,2`, `3,4`, `3,4,5`, `1,7`).

## Answer: both causes, and they are layered

The question "is it the registration in the Excel, or are columns missing?" has
a measured answer: **both**, and fixing only the columns produces broken IBTs.

**Cause 1 -- the schema (mechanical blocker).** The sheet has 11 columns and is
missing ten, including `Bus HV` and `Bus LV`. Adding just those two and one
`IBT 3-Winding` row is enough to make the parser emit an `IBT_LINK`:

```
IBT_LINK setelah kolom ditambah: 1
    SRLYA -> SRLYA unit 1,2
```

**Cause 2 -- the registration (why it would still be wrong).** Note the result
above is `SRLYA -> SRLYA`, a self-link. Every busbar in the file is 500 kV:

```
Kelas tegangan busbar yang ada: {'500 kV'}
```

There is no 150 kV bus for any IBT to land on, so the LV endpoint falls back to
the HV bus. An IBT 500/150 needs **two** buses registered per GITET, the 500 kV
side and the 150 kV side, exactly as the SS sheets do it (`PEDAN7` + `PEDAN`,
`BKASI7` + `BKASI`). Register the second bus and the link resolves properly:

```
IBT_LINK: 1
    SRLYA -> SRLYA5 unit 1,2
```

So the fix is: add the columns **and** register the 150 kV bus per GITET. The
columns alone give a transformer wired to itself.

This is also the concrete form of the "same GI name" problem: one physical
GITET legitimately needs two bus rows at two voltages, and today the file has
only one.

## Open questions

1. **What should the IBT view draw?** Section 1.5 of the book, "Kerawanan
   IBT 500/150 kV", is a risk table rather than its own single-line diagram.
   The natural drawing is each GITET with its 500/150 kV banks and the 150 kV
   bus each one feeds -- which is information the SS sheets already hold, since
   every SS fixture carries its own GITET and IBT rows.
2. **Should it be derived rather than authored?** Building it by hand risks a
   third copy of the same GITET set drifting from the other two. Deriving the
   IBT view from the IBT rows already present across the SS workbooks would
   keep one source of truth. That is the "GI with the same name registered
   twice" problem the user raised: the same GITET currently exists in the
   backbone fixture, in this fixture, and in each SS sheet.
3. **Does the generator need a rule change?** Unclear until (1) is settled. If
   the view is derived, no new authoring rule is needed; if it is authored, the
   workbook needs the `Bus HV`/`Bus LV` columns and `IBT 3-Winding` rows the
   current file lacks.
