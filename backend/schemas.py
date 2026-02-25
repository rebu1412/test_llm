from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=6, max_length=120)


class LoginRequest(RegisterRequest):
    pass


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=120)


class UserOut(BaseModel):
    id: int
    username: str
    role: Literal["admin", "user"]
    leave_balance: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LeaveCreateRequest(BaseModel):
    record_type: Literal["FULL_DAY", "HALF_AM", "HALF_PM", "RANGE", "LATE", "EARLY"]
    start_date: datetime | None = None
    end_date: datetime | None = None
    start_half: Literal["AM", "PM"] | None = None
    end_half: Literal["AM", "PM"] | None = None
    minutes: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=1000)


class LeaveUpdateRequest(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    start_half: Literal["AM", "PM"] | None = None
    end_half: Literal["AM", "PM"] | None = None
    minutes: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=1000)


class LeaveOut(BaseModel):
    id: int
    user_id: int
    record_type: str
    start_datetime: datetime
    end_datetime: datetime
    total_leave_days: float
    minutes: int | None
    note: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaveBalanceResponse(BaseModel):
    leave_balance: float


class PaginatedLeaveResponse(BaseModel):
    items: list[LeaveOut]
    total: int
    page: int
    page_size: int


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=6, max_length=120)
    role: Literal["admin", "user"] = "user"
    leave_balance: float = Field(default=0, ge=0)


class AdminPatchUserRequest(BaseModel):
    is_active: bool | None = None
    role: Literal["admin", "user"] | None = None
    leave_balance: float | None = Field(default=None, ge=0)
    reset_password: str | None = Field(default=None, min_length=6, max_length=120)


class AdjustLeaveRequest(BaseModel):
    user_id: int
    change_amount: float
    note: str | None = None


class MessageResponse(BaseModel):
    message: str
