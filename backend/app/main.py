from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.chat import router as chat_router
from app.api.v1.routes.tools import router as tools_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context for startup/shutdown hooks."""
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Live AI Assistant backend", extra={"env": settings.env})
    yield
    logger.info("Shutting down Live AI Assistant backend")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Live AI Assistant API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS (relaxed for now; can be tightened per deployment)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(tools_router, prefix="/api/v1")

    return app


app = create_app()

