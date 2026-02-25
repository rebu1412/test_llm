import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import Base, engine
from backend.routers.admin import router as admin_router
from backend.routers.auth import router as auth_router
from backend.routers.leave import router as leave_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("leave-app")

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled error: %s %s", request.method, request.url.path)
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.2f ms)", request.method, request.url.path, response.status_code, duration_ms)
    return response


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router)
app.include_router(leave_router)
app.include_router(admin_router)


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
