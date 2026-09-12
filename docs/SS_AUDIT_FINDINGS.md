# Per-SS audit: render against the book figure

One section per subsystem, smallest first. Each entry lists only what the
figure and the workbook disagree about. A finding is recorded before it is
fixed, so a wrong call can be argued with rather than discovered later.

Method: `python scripts/render_one.py samples/ss_<x>_ingest.xlsx`, then compare
with the section's Peta Kerawanan at high zoom. The tool also prints the tier
from the Excel beside the tier the renderer used, which separates a workbook
fault from an engine fault.

---

## SS_GNDUL24 -- Gandul 2,4 (Sec 2.13, Gambar 2.12) -- FIXED

| # | Finding | Evidence | Fix |
|---|---|---|---|
| 1 | ASARI modelled as a Tier-3 **busbar** | Gambar 2.12 draws it as two dashed arrows off the KMANG bus, the same symbol as SWGAN/CRNDE | bay on KMANG |
| 2 | CSW modelled as a Tier-4 **busbar** | drawn as one dashed arrow off the SAMBAS bus, inside the "Aset milik KTT" box | bay on SAMBAS |
| 3 | Gandul - Pondok Indah typed **SUTT** | it is a cable, like Gandul - Kemang which risk 1 names as SKTT | name says SKTT |

Effect: 4 tiers dropped to 3, 5 ruas to 3. Findings 1 and 2 had invented a
whole tier. The parser derives circuit type from the penghantar name, so
finding 3 was fixed by naming it, not by a new column.

---

## SS_DKGD -- Durikosambi 2 - Gandul 1,3 (Sec 2.9, Gambar 2.8)

Reported by the user: "tidak ada relasi Gandul-Kembangan". Confirmed.

| # | Finding | Evidence | Status |
|---|---|---|---|
| 1 | `GNDUL -> KMBGN` does not exist | On the figure the GNDUL Tier-1 bar **ends** before KMBGN, with a clear break, and KMBGN's two circuits rise to the **DKSBI** bar. Kembangan is fed from the Durikosambi side. | to fix: drop the edge |
| 2 | `SWGAN`, `CRNDU`, `KMBGN`, `GRGBR` modelled as Tier-2 busbars | Correct -- all four are drawn as real busbars with their own load transformers, not as stubs. | no change |
| 3 | `LKONG2` and `SNYAN` as bays | Correct -- LKONG2 is a plain arrow pair off SRPNG, SNYAN a grey dashed pair off PTKGN. | no change |
| 4 | Capacitors at GNDUL, SRPNG, PTKGN | The figure draws a 50 MVAr capacitor symbol at each. The workbook records none, so they are missing from the drawing. | to check |

Still to verify on this sheet: whether `KMBGN -> PTKGN` and `GRGBR -> GROGOL`
are really SKTT, and whether BNTRO is fed from both SRPNG and PTKGN as the
workbook claims.
