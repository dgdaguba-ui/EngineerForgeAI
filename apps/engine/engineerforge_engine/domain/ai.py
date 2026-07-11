"""AI domain models — the vendor-neutral contract every provider speaks."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


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


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    stop_reason: str | None = None
    thinking: str | None = None
    usage: Usage = Field(default_factory=Usage)


class ProviderHealth(BaseModel):
    provider: str
    available: bool
    detail: str = ""
