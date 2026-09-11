# Near-continuation blockers (geometry gate)

Status as of commit `5fdca3a`. Every remaining geometry-gate failure across all
fixtures is **one defect class**: `near-continuation`. There are five findings in
four views. Everything else passes.

Reproduce with:

```
python scripts/audit_sample_workbooks.py
```

On Windows the audit crashes during temp-dir cleanup (SQLite file still locked).
The results are already computed when it does; to audit a subset, monkeypatch
`tempfile.TemporaryDirectory` to a non-deleting contextmanager.

## What the invariant rejects

`tests/test_sld_geometry.py::geometry_errors`, the branch at the `axis == 1`
test: two **horizontal** segments belonging to **different** circuits, each
longer than 120px, whose vertical spacing is `< 40` and whose horizontal gap is
`0 <= gap < 40`, and which share no busbar endpoint. Such a pair reads as one
continuous conductor even though the two circuits are unrelated, so an operator
can trace a path that does not exist. The check is correct; do not relax it.

## The five findings, with the exact segments

| View | Circuit A (horizontal seg) | Circuit B (horizontal seg) | dy | x-gap |
|---|---|---|---:|---:|
| `SS_GUCL_FULL` | `SUTT_ASAHI_POLMA` y=473, x 1850→2552 | `SUTT_CLBRU_MENES` y=512, x 1650→1811 | 39 | 39.0 |
| `SS_GUCL_FULL` | `SUTT_MNA_KRWTU` y=660, x 2176→2387 | `SUTT_CLGON_MITSUI` y=685, x 1972→2141 | 25 | 35.2 |
| `SS_PRBC_PRIOK` | `SUTT_PLPNG20_PKRNG` y=977, x 2647→2814 | `SUTT_PLPRU_MGBSR` y=963, x 2450→2608 | 14 | 38.6 |
| `BACKBONE_500_JB_BACKBONE500` | `SUTT_GNDUL_DEPOK` y=1557, x 993→1228 | `SUTT_KMBNG_DKSBI` y=1589, x 795→977 | 32 | 15.3 |
| `SS_PLBRATU_SALAK` | `SUTT_SALAK_SLBRU` y=297, x 1064→1348 | `SUTT_PRATU_CBDRU` y=315, x 798→1027 | 18 | 37.0 |

The shape is the same in all five: two long horizontal runs at almost the same
height, sitting **end to end** with a small horizontal gap between them. They
never overlap in x, which is why the router does not treat them as competing for
the same channel.

`SS_PRBC_PRIOK` is the clearest specimen -- dy=14 on two sibling drops -- and is
the one to fix first.

## What has already been tried

Commit `da05e4e` widened the router's discouraged `soft_bands` by `NEAR_CONT_GAP`
(40) past each route's own span, in `route_bundles`
(`app/services/sld_layout.py`). Rationale: the band previously covered only the
other route's own x-range, so an end-to-end neighbour fell outside it entirely.

That fixed **three** near-continuations on `SS_BALI` (now PASS, no longer
"accepted visual review") and **one** on `SS_GUCL`. The five above survive it.

**Do not** also raise the penalty threshold in `OrthogonalRouter.penalty` from
`CHANNEL_PITCH` (32) to `NEAR_CONT_GAP` (40). It was tried: it re-routes
fixtures that already satisfy the invariant and regressed `SS_KSGHN` from PASS to
FAIL, for no net gain. There is a comment in the code marking this.

## Why widening the soft band did not clear these five

Measured, not assumed. Instrumenting `OrthogonalRouter._cost` while rendering
`SS_PRBC_PRIOK` and logging every horizontal segment evaluated at the offending
y (963, and the whole 940-1000 band) gives **zero evaluations**:

```
segments evaluated at y=963: 0   of which soft-penalised: 0
long horizontal candidates the router evaluated near y 940-1000:  (none)
```

So the y-coordinate that the geometry invariant rejects is **not a coordinate the
router ever costed**. `soft_bands` -- and therefore any change to
`COLLINEAR_TOUCH_PENALTY` or to the band width -- cannot influence it. That is
the real reason `da05e4e` helped `SS_BALI` and `SS_GUCL` but not these five.

The final wire y differs from the routed centreline: a bundle's wires are laid
out around the centreline at `WIRE_PITCH` (14) offsets, and the reported
`SUTT_PLPNG20_PKRNG` y=977 / `SUTT_PLPRU_MGBSR` y=963 pair is 14 apart --
exactly one wire pitch. The near-continuation is therefore produced **after**
routing, when bundle centrelines that were far enough apart have their individual
wires fanned out toward each other.

Dumping the individual wires of the two PRBC bundles confirms it:

```
SUTT_PLPNG20_PKRNG   wire runs: y=963 x 2661->2828
                                y=977 x 2647->2814
SUTT_PLPRU_MGBSR     wire runs: y=963 x 2450->2608
                                y=977 x 2436->2594
```

Both bundles fan out to the **same two y values**, 963 and 977. Their
centrelines were routed to the same channel, and each then placed its two wires
at the identical `+/- WIRE_PITCH/2` offsets. The invariant then compares bundle
A's y=963 wire with bundle B's y=963 wire -- dy=0 -- and with its y=977 wire --
dy=14. Both are under the 40 threshold, and the x-gap between the two bundles is
38.6, so it fires.

This is the mechanism to fix. The router kept the two bundles apart **in x**
(gap 38.6) but put them in the **same horizontal channel**, which is legal for
non-overlapping spans and only becomes misleading once they are long runs nearly
end to end. So the fix belongs in whatever assigns the channel y to a bundle --
it needs to know that a channel already carries another circuit's long
horizontal run whose x-span ends within `NEAR_CONT_GAP` of this one -- not in
the per-wire fan-out, which is doing the right thing.

Note this also means the pair is genuinely misleading on screen: four wires at
two shared heights reading straight across. It is not a checker artefact, and
`tests/test_sld_geometry.py` should not be relaxed to accept it.

## Acceptance

`python scripts/audit_sample_workbooks.py` exits 0 with every fixture PASS, and
`python -m pytest -q` stays green (66 passed at `5fdca3a`). Any fixture that
still fails must be reported as a specific blocker with its SVG and root cause --
not counted as passing, and not fixed by loosening
`tests/test_sld_geometry.py`.
