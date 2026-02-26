from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models import LeaveRecord, LeaveTransaction, RecordType, SystemJob, TransactionSource, User

VN_TZ = ZoneInfo(settings.timezone)


def vn_now() -> datetime:
    return datetime.now(tz=VN_TZ)


def normalize_date(dt: datetime | None) -> date:
    if dt is None:
        return vn_now().date()
    if dt.tzinfo is None:
        return dt.date()
    return dt.astimezone(VN_TZ).date()


def day_weight(day: date) -> float:
    return 0 if day.weekday() >= 5 else 1


def calculate_range_leave_days(start: date, end: date, start_half: str, end_half: str) -> float:
    if end < start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date must be >= start_date")
    total = 0.0
    cursor = start
    while cursor <= end:
        total += day_weight(cursor)
        cursor += timedelta(days=1)

    if day_weight(start) == 1 and start_half == "PM":
        total -= 0.5
    if day_weight(end) == 1 and end_half == "AM":
        total -= 0.5

    return max(total, 0)


def build_leave_payload(record_type: RecordType, start_date: datetime | None, end_date: datetime | None, start_half: str | None, end_half: str | None, minutes: int | None) -> tuple[datetime, datetime, float]:
    sd = normalize_date(start_date)
    ed = normalize_date(end_date) if end_date else sd

    start_dt = datetime.combine(sd, time(8, 0))
    end_dt = datetime.combine(ed, time(17, 0))

    if record_type == RecordType.FULL_DAY:
        return start_dt, end_dt, day_weight(sd)
    if record_type == RecordType.HALF_AM:
        return start_dt, datetime.combine(sd, time(12, 0)), 0.5 if day_weight(sd) else 0
    if record_type == RecordType.HALF_PM:
        return datetime.combine(sd, time(13, 0)), end_dt, 0.5 if day_weight(sd) else 0
    if record_type == RecordType.RANGE:
        s_half = start_half or "AM"
        e_half = end_half or "PM"
        return start_dt, end_dt, calculate_range_leave_days(sd, ed, s_half, e_half)
    if record_type in (RecordType.LATE, RecordType.EARLY):
        if not minutes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="minutes is required for LATE/EARLY")
        return start_dt, start_dt, 0
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported record type")


def apply_balance_change(db: Session, user: User, change_amount: float, source: TransactionSource, reference_id: int | None):
    new_balance = float(user.leave_balance) + change_amount
    if new_balance < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient leave balance")
    user.leave_balance = round(new_balance, 2)
    db.add(
        LeaveTransaction(
            user_id=user.id,
            change_amount=change_amount,
            balance_after=float(user.leave_balance),
            source=source,
            reference_id=reference_id,
        )
    )


def run_monthly_accrual(db: Session, execute_date: date | None = None) -> bool:
    current = execute_date or vn_now().date()
    if current.day != 21:
        return False

    existing = (
        db.query(SystemJob)
        .filter(SystemJob.job_name == "monthly_accrual", SystemJob.run_month == current.month, SystemJob.run_year == current.year)
        .first()
    )
    if existing:
        return False

    active_users = db.query(User).filter(User.is_active.is_(True)).all()
    for user in active_users:
        apply_balance_change(db, user, settings.accrual_amount, TransactionSource.MONTHLY_ACCRUAL, None)

    db.add(SystemJob(job_name="monthly_accrual", run_month=current.month, run_year=current.year))
    db.commit()
    return True


def soft_delete_record(db: Session, record: LeaveRecord):
    if record.deleted_at:
        return
    record.deleted_at = datetime.utcnow()
