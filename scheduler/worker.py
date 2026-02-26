import logging
import time

from backend.database import SessionLocal
from backend.services.leave import run_monthly_accrual

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("scheduler")


if __name__ == "__main__":
    while True:
        db = SessionLocal()
        try:
            changed = run_monthly_accrual(db)
            logger.info("daily-check complete, accrual_run=%s", changed)
        except Exception:
            logger.exception("Scheduler job failed")
            db.rollback()
        finally:
            db.close()
        time.sleep(24 * 60 * 60)
