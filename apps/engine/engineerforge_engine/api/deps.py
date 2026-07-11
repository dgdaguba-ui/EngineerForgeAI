"""FastAPI dependencies: container access + optional bearer-token auth."""

from __future__ import annotations

from fastapi import Header, Request

from ..application.chat_service import ChatService
from ..config import Settings
from ..di.container import Container
from ..domain.errors import EngineError


class UnauthorizedError(EngineError):
    code = "UNAUTHORIZED"
    http_status = 401


def get_container(request: Request) -> Container:
    return request.app.state.container  # type: ignore[no-any-return]


def get_settings_dep(request: Request) -> Settings:
    return get_container(request).settings


def get_chat_service(request: Request) -> ChatService:
    return get_container(request).chat_service


async def require_auth(
    request: Request,
    authorization: str | None = Header(default=None),
) -> None:
    """Enforce the per-session bearer token when EFC_ENGINE_TOKEN is configured.

    In desktop mode the main process mints the token and passes it to the
    sidecar at spawn. When unset (local dev/tests), auth is a no-op.
    """
    token = get_container(request).settings.engine_token
    if token is None:
        return
    expected = token.get_secret_value()
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("missing bearer token")
    if authorization[len("Bearer ") :] != expected:
        raise UnauthorizedError("invalid bearer token")
