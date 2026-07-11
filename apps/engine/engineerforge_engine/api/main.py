"""FastAPI application factory + composition root wiring."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import Settings, get_settings
from ..di.container import Container
from .errors import register_error_handlers
from .v1 import ai, blender, capabilities, convert, health

# Renderer runs on localhost (dev server) or is loaded from disk in the packaged
# Electron app (origin file:// / null). Restrict CORS to those.
_ALLOWED_ORIGIN_REGEX = r"^(http://(localhost|127\.0\.0\.1)(:\d+)?|file://.*|null)$"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = Container(settings)
        logging.getLogger(__name__).info(
            "Engine ready (provider=%s, model=%s)",
            app.state.container.chat_service.provider_name,
            settings.ai_model,
        )
        yield

    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=_ALLOWED_ORIGIN_REGEX,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(capabilities.router, prefix="/api/v1")
    app.include_router(ai.router, prefix="/api/v1")
    app.include_router(blender.router, prefix="/api/v1")
    app.include_router(convert.router, prefix="/api/v1")
    return app


app = create_app()
