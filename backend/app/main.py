"""AI Sentinel — FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings

logging.basicConfig(level=settings.log_level)
log = logging.getLogger("ai_sentinel")

app = FastAPI(
    title="AI Sentinel API",
    description="رصد فناوری/اخبار هوش مصنوعی + دستیار پژوهشی",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": "ai-sentinel-backend"}
