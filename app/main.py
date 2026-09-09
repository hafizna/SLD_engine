from pathlib import Path

from fastapi import FastAPI
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
app.include_router(router)

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")
