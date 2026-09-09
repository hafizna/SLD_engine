# Deploy (demo)

The engine is a FastAPI + Python app, so it needs a running server -- it cannot
go on GitHub Pages (that only serves static files, which is why the sister
project's React `dist/` works there).

## Render.com (free, recommended)

Free web service, auto-deploys on every push to `main`. No credit card.
`render.yaml` in the repo root is the blueprint.

1. Create an account at <https://render.com> (sign in with GitHub).
2. **New +** &rarr; **Blueprint**.
3. Connect the `hafizna/SLD_engine` repo. Render reads `render.yaml`.
4. **Apply**. First build takes ~2-3 min.
5. The service gets a URL like `https://mantaps-topology-engine.onrender.com`.

What you get:
- `/` &mdash; view selector + SLD + risk/DS overlay panel
- `/docs` &mdash; interactive Swagger API
- `/api/views/{id}/graph` &mdash; JSON contract for a web viewer
- `/api/views/{id}/sld.svg` &mdash; starter SVG
- `/api/register.xlsx` &mdash; Corporate Topology Register export

Notes:
- Free tier **spins down after ~15 min idle**; the next request takes ~30 s to
  wake. Fine for a demo.
- SQLite lives in `/tmp` and is **re-seeded on every cold start** (deterministic
  data, so this is harmless). For data that must persist, add a Render Postgres
  instance and point `DATABASE_URL` at it (the code already speaks Postgres via
  `psycopg`).

## Railway / Fly.io

Same idea. Railway: "Deploy from GitHub repo", it auto-detects Python, set the
start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Fly.io: use
the existing `Dockerfile` with `fly launch`.

## Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
```

To share a local instance briefly without deploying: `ngrok http 8000`.

## Static snapshot (if you ever want a GitHub Pages URL too)

Not set up yet. It would mean a build step that renders every view's SVG + graph
JSON to files and ships a small static viewer -- ask and it can be added as a
GitHub Actions workflow publishing to `hafizna.github.io/SLD_engine`. The data
would be frozen (no live API).
