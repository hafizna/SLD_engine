"""Seed entry point. Delegates to per-subsystem seeders.

The old generic Krian demo is dropped -- SS_LBK (Lontar-Balaraja-Kembangan)
from the Buku Kerawanan SJB 2026 is the real vertical-slice fixture.
"""
from sqlalchemy.orm import Session

from app.services.seed_ss_lbk import seed_ss_lbk


def seed_demo(db: Session) -> None:
    seed_ss_lbk(db)
