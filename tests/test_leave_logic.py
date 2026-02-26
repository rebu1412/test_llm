from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, UserRole
from backend.services.leave import calculate_range_leave_days, run_monthly_accrual


def test_range_skips_weekend():
    days = calculate_range_leave_days(date(2026, 2, 20), date(2026, 2, 23), "AM", "PM")
    assert days == 2


def test_monthly_accrual_idempotent():
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSession()
    db.add(User(username="u1", password_hash="x", role=UserRole.USER, leave_balance=0, is_active=True))
    db.commit()

    first = run_monthly_accrual(db, execute_date=date(2026, 1, 21))
    second = run_monthly_accrual(db, execute_date=date(2026, 1, 21))
    user = db.query(User).filter(User.username == "u1").first()

    assert first is True
    assert second is False
    assert float(user.leave_balance) == 1.2
