"""Deterministic, offline AI provider.

Used for development, tests, and as the automatic fallback when no cloud
credentials are configured. It never touches the network, so the whole app
works with zero setup — the offline-first guarantee in code.
"""

from __future__ import annotations

from ...domain.ai import ChatRequest, ChatResponse, ProviderHealth, Role, Usage
from ...ports.ai_provider import AIProvider


class StubProvider(AIProvider):
    name = "stub"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == Role.user),
            "",
        )
        preview = last_user.strip()
        if len(preview) > 200:
            preview = preview[:200] + "…"
        body = (
            "[StubProvider — offline] "
            "No AI credentials are configured, so this is a deterministic local "
            "response. Set ANTHROPIC_API_KEY (and EFC_AI_PROVIDER=auto or claude) "
            "to enable Claude."
        )
        if preview:
            body += f'\n\nYou said: "{preview}"'
        # Rough, deterministic token estimate (~4 chars/token) — no tokenizer dependency.
        in_chars = sum(len(m.content) for m in request.messages) + len(request.system or "")
        return ChatResponse(
            content=body,
            provider=self.name,
            model="stub",
            stop_reason="end_turn",
            usage=Usage(input_tokens=in_chars // 4, output_tokens=len(body) // 4),
        )

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=True,
            detail="offline deterministic provider (always available)",
        )
