"""Materialise reviewed XLSX fixtures into a demo/static snapshot.

Unlike the public /ingest endpoint, this loader permits physical substations
to be shared by multiple subsystem fixtures. Every workbook is still audited
individually by scripts/audit_sample_workbooks.py before it is listed here.
"""
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Subsystem
from app.services import ingest, ingest_parser


def seed_xlsx_fixture(db: Session, path: Path) -> dict:
    payload = ingest_parser.parse_upload(path.read_bytes(), path.name)
    code = payload["subsystem"]["code"]
    if db.query(Subsystem).filter(Subsystem.code == code).first():
        return {"subsystem_code": code, "already": True}
    draft = ingest.build_draft(db, payload)
    # Reviewed bundled fixtures are allowed to reuse canonical GI/GITET rows.
    # Public uploads retain the stricter duplicate-subsystem validation.
    view = ingest._materialise(
        db, draft, code, payload["subsystem"]["name"],
        payload["meta"].get("effective_date"), for_publish=True,
    )
    db.commit()
    return {"subsystem_code": code, "view_id": view.id}
