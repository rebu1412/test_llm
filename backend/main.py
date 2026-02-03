from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.routers.chat import router as chat_router


app = FastAPI(title="Chatbot Comparator", version="0.1.0")
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"

if frontend_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=frontend_dir, html=True), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(chat_router)

@app.get("/")
async def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/ui/")


@app.get("/healthz")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
