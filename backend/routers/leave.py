from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import settings
from backend.database import get_db
from backend.models import LeaveRecord, RecordType, TransactionSource, User
from backend.schemas import LeaveBalanceResponse, LeaveCreateRequest, LeaveOut, LeaveUpdateRequest, PaginatedLeaveResponse
from backend.services.leave import apply_balance_change, build_leave_payload, soft_delete_record

router = APIRouter(prefix="/leave", tags=["leave"])


@router.post("", response_model=LeaveOut)
def create_leave(payload: LeaveCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record_type = RecordType(payload.record_type)
    start_dt, end_dt, total_leave_days = build_leave_payload(
        record_type, payload.start_date, payload.end_date, payload.start_half, payload.end_half, payload.minutes
    )

    if total_leave_days > 0:
        apply_balance_change(db, current_user, -total_leave_days, TransactionSource.LEAVE_USED, None)

    record = LeaveRecord(
        user_id=current_user.id,
        record_type=record_type,
        start_datetime=start_dt,
        end_datetime=end_dt,
        total_leave_days=total_leave_days,
        minutes=payload.minutes,
        note=payload.note,
    )
    db.add(record)
    db.flush()
    db.commit()
    db.refresh(record)
    return record


@router.get("/my", response_model=PaginatedLeaveResponse)
def my_leaves(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.page_size_default, ge=1, le=settings.page_size_max),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(LeaveRecord).filter(LeaveRecord.user_id == current_user.id, LeaveRecord.deleted_at.is_(None))
    total = q.count()
    items = q.order_by(LeaveRecord.start_datetime.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedLeaveResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/balance", response_model=LeaveBalanceResponse)
def balance(current_user: User = Depends(get_current_user)):
    return LeaveBalanceResponse(leave_balance=float(current_user.leave_balance))


@router.put("/{record_id}", response_model=LeaveOut)
def update_leave(record_id: int, payload: LeaveUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = (
        db.query(LeaveRecord)
        .filter(LeaveRecord.id == record_id, LeaveRecord.user_id == current_user.id, LeaveRecord.deleted_at.is_(None))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    prev_days = record.total_leave_days
    start_dt, end_dt, total_leave_days = build_leave_payload(
        record.record_type,
        payload.start_date or record.start_datetime,
        payload.end_date or record.end_datetime,
        payload.start_half,
        payload.end_half,
        payload.minutes or record.minutes,
    )

    delta = prev_days - total_leave_days
    if abs(delta) > 1e-9:
        apply_balance_change(db, current_user, delta, TransactionSource.ADMIN_ADJUST, record.id)

    record.start_datetime = start_dt
    record.end_datetime = end_dt
    record.total_leave_days = total_leave_days
    record.minutes = payload.minutes if payload.minutes is not None else record.minutes
    record.note = payload.note if payload.note is not None else record.note
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{record_id}")
def delete_leave(record_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = (
        db.query(LeaveRecord)
        .filter(LeaveRecord.id == record_id, LeaveRecord.user_id == current_user.id, LeaveRecord.deleted_at.is_(None))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    if record.total_leave_days > 0:
        apply_balance_change(db, current_user, record.total_leave_days, TransactionSource.DELETE_RECORD, record.id)

    soft_delete_record(db, record)
    db.commit()
    return {"message": "Record deleted"}
