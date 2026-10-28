"""AI Sentinel — API v1 router."""
from fastapi import APIRouter

from app.api.v1 import alerts, ask, bulletins, chat, files, items, library, research, rivalry, trends, watch

api_router = APIRouter()

api_router.include_router(items.router)
api_router.include_router(rivalry.router)
api_router.include_router(trends.router)
api_router.include_router(research.router)
api_router.include_router(ask.router)
api_router.include_router(chat.router)
api_router.include_router(files.router)
api_router.include_router(bulletins.router)
api_router.include_router(alerts.router)
api_router.include_router(watch.router)
api_router.include_router(library.router)
