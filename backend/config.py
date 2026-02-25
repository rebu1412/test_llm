import os
from dataclasses import dataclass


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    return value


@dataclass
class Settings:
    app_name: str = "Leave Management"
    database_url: str = get_env("DATABASE_URL", "sqlite:///./leave_app.db") or "sqlite:///./leave_app.db"
    jwt_secret: str = get_env("JWT_SECRET", "change-me-in-prod") or "change-me-in-prod"
    jwt_algo: str = "HS256"
    token_expire_minutes: int = int(get_env("TOKEN_EXPIRE_MINUTES", "720") or "720")
    accrual_amount: float = float(get_env("ACCRUAL_AMOUNT", "1.2") or "1.2")
    timezone: str = "Asia/Ho_Chi_Minh"
    page_size_default: int = int(get_env("PAGE_SIZE_DEFAULT", "20") or "20")
    page_size_max: int = int(get_env("PAGE_SIZE_MAX", "100") or "100")


settings = Settings()
