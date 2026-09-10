"""Seed entry point. Delegates to per-subsystem seeders.

The old generic Krian demo is dropped -- the Buku Kerawanan SJB 2026 subsystems
are the real vertical-slice fixtures:
  * SS_LBK  Lontar - Balaraja 1,2 - Kembangan 1,2  (Sec 2.5, two SLD sides)
  * SS_BLL  Balaraja 3,4 - Lengkong 1,2            (Sec 2.6, one SLD)

SS_CWD (Cawang 2,3 - Depok 1, Sec 2.7) is NOT seeded here on purpose: the
/ingest test suite publishes a fresh subsystem under that exact code, so a
pre-seeded SS_CWD would make those tests fail with "sudah tercatat". The static
snapshot builder seeds it separately (see scripts/build_static_site.py).
"""
from sqlalchemy.orm import Session

from app.services.seed_ss_bll import seed_ss_bll
from app.services.seed_ss_lbk import seed_ss_lbk


def seed_demo(db: Session) -> None:
    seed_ss_lbk(db)
    seed_ss_bll(db)
