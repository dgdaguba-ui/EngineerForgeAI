"""Single error envelope for the whole API surface."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..domain.errors import EngineError

logger = logging.getLogger(__name__)


def error_body(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "retryable": retryable,
        }
    }


async def _engine_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, EngineError)
    if exc.http_status >= 500:
        logger.error("EngineError %s: %s", exc.code, exc.message)
    return JSONResponse(
        status_code=exc.http_status,
        content=error_body(
            exc.code, exc.message, details=exc.details, retryable=exc.retryable
        ),
    )


async def _unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "Internal server error"),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(EngineError, _engine_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
