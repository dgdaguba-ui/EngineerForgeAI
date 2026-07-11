"""Provider selection. Encodes the offline-first fallback policy in one place."""

from __future__ import annotations

import logging

from ...config import Settings
from ...ports.ai_provider import AIProvider
from .claude import ClaudeProvider
from .stub import StubProvider

logger = logging.getLogger(__name__)


def build_ai_provider(settings: Settings) -> AIProvider:
    """Resolve the configured AIProvider, falling back to Stub when needed.

    ``EFC_AI_PROVIDER``:
      * ``stub``   → always the offline StubProvider.
      * ``claude`` → ClaudeProvider (falls back to Stub if no key, with a warning).
      * ``auto``   → Claude when a key is present, otherwise Stub.
    """
    choice = (settings.ai_provider or "auto").strip().lower()

    def make_claude() -> ClaudeProvider:
        return ClaudeProvider(
            api_key=(
                settings.anthropic_api_key.get_secret_value()
                if settings.anthropic_api_key
                else None
            ),
            model=settings.ai_model,
            max_tokens=settings.ai_max_tokens,
            thinking=settings.ai_thinking,
        )

    if choice == "stub":
        return StubProvider()

    if choice == "claude":
        if settings.has_anthropic_key:
            return make_claude()
        logger.warning(
            "EFC_AI_PROVIDER=claude but ANTHROPIC_API_KEY is unset - using StubProvider."
        )
        return StubProvider()

    # auto (default)
    if choice not in ("auto", ""):
        logger.warning("Unknown EFC_AI_PROVIDER=%r — defaulting to 'auto'.", settings.ai_provider)
    if settings.has_anthropic_key:
        return make_claude()
    logger.info("No ANTHROPIC_API_KEY found - running offline with StubProvider.")
    return StubProvider()
