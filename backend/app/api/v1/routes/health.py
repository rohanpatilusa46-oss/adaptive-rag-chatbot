from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "env": settings.env,
        "service": "live-ai-assistant-backend",
    }

