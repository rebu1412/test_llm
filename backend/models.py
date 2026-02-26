from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class RecordType(str, Enum):
    FULL_DAY = "FULL_DAY"
    HALF_AM = "HALF_AM"
    HALF_PM = "HALF_PM"
    RANGE = "RANGE"
    LATE = "LATE"
    EARLY = "EARLY"


class TransactionSource(str, Enum):
    MONTHLY_ACCRUAL = "MONTHLY_ACCRUAL"
    LEAVE_USED = "LEAVE_USED"
    ADMIN_ADJUST = "ADMIN_ADJUST"
    DELETE_RECORD = "DELETE_RECORD"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    leave_balance = Column(Numeric(8, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    leave_records = relationship("LeaveRecord", back_populates="user")


class LeaveRecord(Base):
    __tablename__ = "leave_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    record_type = Column(SQLEnum(RecordType), nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    total_leave_days = Column(Float, default=0, nullable=False)
    minutes = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="leave_records")


class LeaveTransaction(Base):
    __tablename__ = "leave_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    change_amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    source = Column(SQLEnum(TransactionSource), nullable=False)
    reference_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SystemJob(Base):
    __tablename__ = "system_jobs"
    __table_args__ = (UniqueConstraint("job_name", "run_month", "run_year", name="uq_job_month"),)

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(100), nullable=False)
    run_month = Column(Integer, nullable=False)
    run_year = Column(Integer, nullable=False)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
