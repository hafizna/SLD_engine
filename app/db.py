import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mantaps.db")
kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    kwargs["connect_args"] = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, future=True, **kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
class Base(DeclarativeBase):
    pass
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def upgrade_bus_section_schema(bind):
    """Idempotent additive migration for existing installations (no data loss)."""
    from sqlalchemy import inspect, text

    additions = {
        "circuit": {"from_bus_section_id": "INTEGER REFERENCES bus_section(id)",
                    "to_bus_section_id": "INTEGER REFERENCES bus_section(id)",
                    "switch_state": "VARCHAR(10)"},
        "generating_unit": {"outlet_bus_section_id": "INTEGER REFERENCES bus_section(id)"},
    }
    with bind.begin() as connection:
        inspector = inspect(connection)
        for table, columns in additions.items():
            if not inspector.has_table(table):
                continue
            existing = {c['name'] for c in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {name} {definition}'))
