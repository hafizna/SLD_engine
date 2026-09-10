import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.db import Base, SessionLocal, engine
from app.services.seed import seed_demo

Base.metadata.create_all(bind=engine)
with SessionLocal() as _db:
    seed_demo(_db)

app = FastAPI(
    title="MANTAPS Topology Engine",
    version="0.2.0",
    description="Canonical transmission topology + analytical projections + "
    "semantic overlays. Vertical slice: SS Lontar-Balaraja-Kembangan.",
)

# CORS: allow a separately-hosted web viewer to call the JSON API.
# Set ALLOWED_ORIGINS to a comma-separated list in production; "*" for the demo.
_origins = os.getenv("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _origins == "*" else [o.strip() for o in _origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/editor")
def editor_page():
    return FileResponse(STATIC_DIR / "editor.html")


@app.get("/ingest")
def ingest_page():
    return FileResponse(STATIC_DIR / "ingest.html")
