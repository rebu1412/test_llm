from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth import hash_password, require_admin
from backend.config import settings
from backend.database import get_db
from backend.models import LeaveRecord, TransactionSource, User, UserRole
from backend.schemas import (
    AdminCreateUserRequest,
    AdminPatchUserRequest,
    AdjustLeaveRequest,
    PaginatedLeaveResponse,
    UserOut,
)
from backend.services.leave import apply_balance_change

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", response_model=UserOut)
def create_user(payload: AdminCreateUserRequest, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=UserRole(payload.role),
        leave_balance=payload.leave_balance,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserOut])
def get_users(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def patch_user(user_id: int, payload: AdminPatchUserRequest, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role = UserRole(payload.role)
    if payload.leave_balance is not None:
        user.leave_balance = payload.leave_balance
    if payload.reset_password:
        user.password_hash = hash_password(payload.reset_password)

    db.commit()
    db.refresh(user)
    return user


@router.post("/adjust-leave")
def adjust_leave(payload: AdjustLeaveRequest, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    apply_balance_change(db, user, payload.change_amount, TransactionSource.ADMIN_ADJUST, None)
    db.commit()
    return {"message": "Leave adjusted", "balance": float(user.leave_balance)}


@router.get("/all-records", response_model=PaginatedLeaveResponse)
def all_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.page_size_default, ge=1, le=settings.page_size_max),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(LeaveRecord).filter(LeaveRecord.deleted_at.is_(None))
    total = q.count()
    items = q.order_by(LeaveRecord.start_datetime.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedLeaveResponse(items=items, total=total, page=page, page_size=page_size)
