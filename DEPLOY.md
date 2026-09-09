# Deploy (demo)

The engine is a FastAPI + Python app, so it needs a running server -- it cannot
go on GitHub Pages (that only serves static files, which is why the sister
project's React `dist/` works there). Vercel is a poor fit too: it is
serverless/stateless, and this app seeds a DB on boot and holds it in memory.

## Hugging Face Spaces (free, no credit card) -- recommended

1. Create an account at <https://huggingface.co> (free).
2. **New** &rarr; **Space**.
3. Owner: your username. Space name: e.g. `sld-engine`.
   SDK: **Docker**. Visibility: Public (or Private).
4. Create the Space. It gives you a git repo URL like
   `https://huggingface.co/spaces/<user>/sld-engine`.
5. Push this project to that repo:
   ```bash
   git remote add hf https://huggingface.co/spaces/<user>/sld-engine
   git push hf main
   ```
   (or, on the Space page, **Files** &rarr; link the GitHub repo).
6. The Space builds the `Dockerfile` and serves on port 7860. URL:
   `https://<user>-sld-engine.hf.space`.

The HF config lives in the YAML block at the top of `README.md`
(`sdk: docker`, `app_port: 7860`). SQLite is seeded on boot; the free CPU Space
sleeps after ~48 h idle and re-seeds on wake (deterministic data).

## Render.com (free, may ask for verification)

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

## Static snapshot -> GitHub Pages (free, no account, no CC)

A frozen snapshot: every view's SVG + graph JSON + the register, plus a small
viewer. Same hosting model as the sister dashboard, but the topology comes from
the canonical engine. No live API.

Build locally:

```bash
python scripts/build_static_site.py site
# open site/index.html
```

Auto-publish on every push to `main`:

1. Add `scripts/pages.yml` to the repo as `.github/workflows/pages.yml`
   (GitHub web UI: **Add file -> Create new file**, paste, path
   `.github/workflows/pages.yml`). It cannot be pushed by an OAuth app without
   `workflow` scope, hence the manual step.
2. **Settings -> Pages -> Build and deployment -> Source = GitHub Actions**.
3. Push anything to `main`; the workflow builds `site/` and deploys.
4. URL: `https://hafizna.github.io/SLD_engine/`.

## Local via Docker

```bash
docker compose up --build          # SQLite, http://localhost:8000
docker compose --profile postgres up --build   # against Postgres
```

## Local via Python

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
```

Share a local instance briefly: `ngrok http 8000`.

---

_Static demo: https://hafizna.github.io/SLD_engine/ (published by `.github/workflows/pages.yml` on each push to `main`)._
