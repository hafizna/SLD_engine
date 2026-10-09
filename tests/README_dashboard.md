# Dashboard interaction checks

Run `python -m pytest -q` for the API, topology, ingest, SVG, and label regressions.
`test_api.py` checks unique GI counts across views and independently selectable,
category-coloured badges at a shared location.

`dashboard_browser.cjs` uses Playwright against both a running FastAPI app and
the static snapshot. The live database must contain the same reviewed samples
as the snapshot, including Sumsel, PRBC, LBK, and Sumbagteng Gabungan. The normal
three-view demo alone does not contain those fixtures. Use a local fixture DB;
the test changes only browser preferences and selections.

Build the snapshot with `python scripts/build_static_site.py`, then serve it
with `python -m http.server 8766 --bind 127.0.0.1 --directory site`. Start FastAPI
on port 8767 with `DATABASE_URL` pointing at the reviewed fixture database.

PowerShell, from the repository root:

```powershell
npm install --prefix scratchpad playwright
$env:NODE_PATH = (Resolve-Path scratchpad/node_modules).Path
node tests/dashboard_browser.cjs
```

On Windows the test uses installed Microsoft Edge in headless mode. On other
platforms install Playwright Chromium and set `DASHBOARD_BROWSER_CHANNEL` to
`chromium`. Set `DASHBOARD_LIVE_URL` or `DASHBOARD_STATIC_URL` for different ports.
`DASHBOARD_ONLY=live` or `DASHBOARD_ONLY=static` runs just one target.

Checks cover independent panel toggles, defaults and persistence, physical
scale and centre preservation, object and risk selection, category counts and
marker filtering, overlapping-location badges, minimum label and hit-target
sizes, hover cards, keyboard selection, off-view item navigation, responsive
resizing, SS map cards, and complete print contents. Screenshots are saved in
`.render_tmp/dashboard-browser/`. The four views are explicitly asserted after
navigation, so a hash-only navigation cannot accidentally test the previous SS.

Printed risk details include every SS item regardless of panel state, category
filter, or active selection. Fields absent in source data are omitted. Tier
ranges exclude missing Tier; Tier is a network position, not a severity rank.
