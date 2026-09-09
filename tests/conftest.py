import os
import tempfile

import pytest


@pytest.fixture()
def db():
    """A fresh seeded SQLite DB per test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{path}"

    # import after DATABASE_URL is set so the engine binds to the temp file
    import importlib

    import app.db as db_mod
    importlib.reload(db_mod)
    import app.models as models_mod
    importlib.reload(models_mod)
    import app.services.topology as topo_mod
    importlib.reload(topo_mod)
    import app.services.reconciliation as rec_mod
    importlib.reload(rec_mod)
    import app.services.sld_renderer as rend_mod
    importlib.reload(rend_mod)
    import app.services.seed_ss_lbk as seed_mod
    importlib.reload(seed_mod)

    db_mod.Base.metadata.create_all(bind=db_mod.engine)
    session = db_mod.SessionLocal()
    seed_mod.seed_ss_lbk(session)
    try:
        yield session
    finally:
        session.close()
        try:
            os.unlink(path)
        except OSError:
            pass
