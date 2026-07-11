"""Engine error hierarchy. The API layer maps these to a single error envelope."""

from __future__ import annotations

from typing import Any


class EngineError(Exception):
    """Base class for all domain/application errors."""

    code: str = "ENGINE_ERROR"
    http_status: int = 500

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        self.details = details or {}


class InvalidRequestError(EngineError):
    code = "INVALID_REQUEST"
    http_status = 400


class AIProviderError(EngineError):
    code = "AI_PROVIDER_ERROR"
    http_status = 502


class ProviderUnavailableError(EngineError):
    code = "AI_PROVIDER_UNAVAILABLE"
    http_status = 503


class CapabilityNotAvailableError(EngineError):
    """A requested feature exists on the roadmap but is not implemented yet.

    Used instead of fake/placeholder behavior — the API tells the truth.
    """

    code = "CAPABILITY_NOT_AVAILABLE"
    http_status = 501


class FileOperationError(EngineError):
    code = "FILE_OPERATION_ERROR"
    http_status = 400
