"""AI domain models — the vendor-neutral contract every provider speaks."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from .feature_program import ParamDiffEntry


class Role(StrEnum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatRequest(BaseModel):
    """A provider-agnostic chat request.

    ``system`` is kept separate from ``messages`` because several providers
    (Anthropic among them) take the system prompt as a distinct parameter.
    Sampling params are intentionally absent: the default provider (Claude
    Opus 4.8) rejects ``temperature``/``top_p``/``top_k``.
    """

    messages: list[ChatMessage]
    system: str | None = None
    model: str | None = None
    max_tokens: int | None = None


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0


class ChatAction(BaseModel):
    """An engine capability the AI invoked during this chat turn.

    The UI uses these to react (e.g. load a created part into the viewport).
    Numbers/geometry always originate from tools, never from free text
    (ADR-0003).
    """

    tool: str
    ok: bool
    summary: str
    part_id: str | None = Field(default=None, alias="partId")
    diff: list[ParamDiffEntry] = Field(default_factory=list)
    pending: bool = False

    model_config = {"populate_by_name": True}


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    stop_reason: str | None = None
    thinking: str | None = None
    usage: Usage = Field(default_factory=Usage)
    actions: list[ChatAction] = Field(default_factory=list)


class ChatStreamEvent(BaseModel):
    """One event in a streamed chat turn (serialized as NDJSON on the wire).

    * ``delta``  — an incremental chunk of assistant text (``text``);
    * ``action`` — a tool the AI just invoked (``action``), so the UI can react
      as it happens rather than only at the end;
    * ``done``   — the turn finished; ``response`` carries the authoritative
      final :class:`ChatResponse` (content, actions, usage, provider, model);
    * ``error``  — the turn failed; ``error``/``code``/``retryable`` mirror the
      REST error envelope so the client can queue-and-retry identically.
    """

    type: Literal["delta", "action", "done", "error"]
    text: str | None = None
    action: ChatAction | None = None
    response: ChatResponse | None = None
    error: str | None = None
    code: str | None = None
    retryable: bool = False

    model_config = {"populate_by_name": True}


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    detail: str = ""
