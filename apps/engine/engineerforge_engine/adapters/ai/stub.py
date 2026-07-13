"""Deterministic, offline AI provider.

Used for development, tests, and as the automatic fallback when no cloud
credentials are configured. It never touches the network, so the whole app
works with zero setup — the offline-first guarantee in code.

With a toolbox it performs a deterministic design flow: prompts that mention
a known template (e.g. "bracket") create a part, parsing simple dimension
phrases ("50x70", "3 mm thick", "3 holes", "in petg"). Real language
understanding is the cloud providers' job; this keeps the full pipeline
testable and usable offline.
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from ...domain.ai import (
    ChatAction,
    ChatRequest,
    ChatResponse,
    ChatStreamEvent,
    ProviderHealth,
    Role,
    Usage,
)
from ...ports.ai_provider import AIProvider

if TYPE_CHECKING:
    from ...application.ai_tools import AiToolbox

_DIMS_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*[x×]\s*(\d{1,3}(?:\.\d+)?)", re.IGNORECASE)
_THICK_RE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*mm\s+thick", re.IGNORECASE)
_HOLES_RE = re.compile(r"(\d)\s+holes?", re.IGNORECASE)
_HOLE_D_RE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*mm\s+holes?", re.IGNORECASE)
_MATERIAL_RE = re.compile(r"\bin\s+(pla|petg|abs|asa|pa|pc|tpu95a|pva|hips)\b", re.IGNORECASE)

OFFLINE_NOTE = (
    "[StubProvider — offline] No AI credentials are configured; this deterministic "
    "local assistant handles template design commands only. Set ANTHROPIC_API_KEY "
    "to enable Claude."
)


def parse_bracket_request(text: str) -> dict[str, float] | None:
    """Deterministically extract bracket parameters, or None if not a design ask."""
    if "bracket" not in text.lower():
        return None
    values: dict[str, float] = {}
    if m := _DIMS_RE.search(text):
        values["W"] = float(m.group(1))
        values["H"] = float(m.group(2))
    if m := _THICK_RE.search(text):
        values["T"] = float(m.group(1))
    if m := _HOLES_RE.search(text):
        values["HC"] = float(m.group(1))
    if m := _HOLE_D_RE.search(text):
        values["HD"] = float(m.group(1))
    return values


def parse_material(text: str) -> str | None:
    m = _MATERIAL_RE.search(text)
    return m.group(1).lower() if m else None


class StubProvider(AIProvider):
    name = "stub"

    async def chat(
        self, request: ChatRequest, toolbox: AiToolbox | None = None
    ) -> ChatResponse:
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == Role.user),
            "",
        )

        actions: list[ChatAction] = []
        body: str

        values = parse_bracket_request(last_user) if toolbox else None
        if toolbox is not None and values is not None:
            execution = toolbox.execute(
                "create_part_from_template",
                {
                    "templateId": "bracket-l",
                    "values": values,
                    "materialId": parse_material(last_user),
                },
            )
            actions.append(execution.action)
            if execution.action.ok:
                body = (
                    f"{execution.model_output}\n\nThe part is now in your viewport — "
                    "edit any parameter in the Parameters panel and it rebuilds live. "
                    f"\n\n{OFFLINE_NOTE}"
                )
            else:
                body = (
                    f"I tried to create the bracket but the kernel rejected it: "
                    f"{execution.model_output}\n\n{OFFLINE_NOTE}"
                )
        else:
            preview = last_user.strip()
            if len(preview) > 200:
                preview = preview[:200] + "…"
            body = OFFLINE_NOTE
            if toolbox is not None:
                body += ' Try: "Design a bracket 50x70, 4 mm thick, with 2 holes, in petg".'
            if preview:
                body += f'\n\nYou said: "{preview}"'

        in_chars = sum(len(m.content) for m in request.messages) + len(request.system or "")
        return ChatResponse(
            content=body,
            provider=self.name,
            model="stub",
            stop_reason="end_turn",
            usage=Usage(input_tokens=in_chars // 4, output_tokens=len(body) // 4),
            actions=actions,
        )

    async def stream(
        self, request: ChatRequest, toolbox: AiToolbox | None = None
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream the deterministic reply word-by-word.

        The content is identical to :meth:`chat`; it is simply chunked so the
        UI exercises the same streaming path it uses for Claude (and so the
        offline experience feels live). Actions are emitted before ``done``.
        """
        response = await self.chat(request, toolbox)
        # chunk on whitespace boundaries, keeping the separators so the
        # reassembled text is byte-identical to response.content
        for chunk in re.findall(r"\S+\s*", response.content):
            yield ChatStreamEvent(type="delta", text=chunk)
        for action in response.actions:
            yield ChatStreamEvent(type="action", action=action)
        yield ChatStreamEvent(type="done", response=response)

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            available=True,
            detail="offline deterministic provider (always available)",
        )
