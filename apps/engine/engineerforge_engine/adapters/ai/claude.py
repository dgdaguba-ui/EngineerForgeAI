"""Anthropic Claude provider.

Follows current Claude API guidance for Opus 4.8:
  * default model ``claude-opus-4-8``;
  * adaptive thinking (``{"type": "adaptive"}``) — no ``budget_tokens``;
  * **no** ``temperature``/``top_p``/``top_k`` (they return 400 on 4.8);
  * ``system`` passed as a top-level parameter, not inside ``messages``.

The Anthropic SDK is imported lazily so the engine boots even if the package
or a key is missing — in that case the provider simply reports itself
unavailable and the registry falls back to the StubProvider.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from ...domain.ai import (
    ChatAction,
    ChatRequest,
    ChatResponse,
    ChatStreamEvent,
    ProviderHealth,
    Role,
    Usage,
)
from ...domain.errors import (
    AIProviderError,
    EngineError,
    InvalidRequestError,
    ProviderUnavailableError,
)
from ...ports.ai_provider import AIProvider

if TYPE_CHECKING:
    from ...application.ai_tools import AiToolbox

MAX_TOOL_ITERATIONS = 6

try:  # optional dependency / import-time resilience
    import anthropic

    _ANTHROPIC_IMPORT_ERROR: str | None = None
except Exception as exc:  # pragma: no cover - defensive
    anthropic = None  # type: ignore[assignment]
    _ANTHROPIC_IMPORT_ERROR = str(exc)


def split_system_and_messages(
    request: ChatRequest,
) -> tuple[str | None, list[dict[str, str]]]:
    """Split a ChatRequest into (system_prompt, anthropic_messages).

    Pure and unit-tested: system-role messages are merged into the system
    prompt; only user/assistant turns go into the messages array (tool turns
    are ignored until tool-calling lands).
    """
    system_parts: list[str] = []
    if request.system:
        system_parts.append(request.system)
    messages: list[dict[str, str]] = []
    for m in request.messages:
        if m.role == Role.system:
            system_parts.append(m.content)
        elif m.role in (Role.user, Role.assistant):
            messages.append({"role": m.role.value, "content": m.content})
    system = "\n\n".join(p for p in system_parts if p.strip()) or None
    return system, messages


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "claude-opus-4-8",
        max_tokens: int = 8192,
        thinking: str = "adaptive",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens
        self._thinking = thinking
        self._client: object | None = None

    def _get_client(self) -> object:
        if anthropic is None:
            raise ProviderUnavailableError(
                f"anthropic SDK unavailable: {_ANTHROPIC_IMPORT_ERROR}"
            )
        if not self._api_key:
            raise ProviderUnavailableError("ANTHROPIC_API_KEY is not set")
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    def _thinking_param(self) -> dict[str, str] | None:
        if self._thinking == "off":
            return {"type": "disabled"}
        # adaptive (recommended for an engineering assistant); summarized so the
        # UI can optionally surface reasoning instead of a silent pause.
        return {"type": "adaptive", "display": "summarized"}

    def _base_kwargs(
        self, request: ChatRequest, toolbox: AiToolbox | None
    ) -> tuple[dict[str, object], list[dict[str, Any]], str]:
        system, messages = split_system_and_messages(request)
        if not messages:
            raise InvalidRequestError("request contains no user/assistant messages")
        model = request.model or self._model
        base_kwargs: dict[str, object] = {
            "model": model,
            "max_tokens": request.max_tokens or self._max_tokens,
        }
        if system:
            base_kwargs["system"] = system
        thinking = self._thinking_param()
        if thinking is not None:
            base_kwargs["thinking"] = thinking
        if toolbox is not None:
            base_kwargs["tools"] = toolbox.definitions()
        return base_kwargs, list(messages), model

    @staticmethod
    def _collect_blocks(
        resp: Any, text_parts: list[str], thinking_parts: list[str]
    ) -> list[Any]:
        """Split a message's content blocks, appending text/thinking and
        returning the tool_use blocks."""
        tool_uses: list[Any] = []
        for block in getattr(resp, "content", []) or []:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(getattr(block, "text", ""))
            elif btype == "thinking":
                t = getattr(block, "thinking", "") or ""
                if t:
                    thinking_parts.append(t)
            elif btype == "tool_use":
                tool_uses.append(block)
        return tool_uses

    def _answer_tool_uses(
        self,
        conversation: list[dict[str, Any]],
        resp: Any,
        tool_uses: list[Any],
        toolbox: AiToolbox,
        actions: list[ChatAction],
    ) -> list[ChatAction]:
        """Echo the assistant turn and answer every tool call in one user turn.
        Returns the actions produced this round (also appended to ``actions``)."""
        conversation.append({"role": "assistant", "content": getattr(resp, "content", [])})
        results: list[dict[str, Any]] = []
        round_actions: list[ChatAction] = []
        for tool_use in tool_uses:
            execution = toolbox.execute(
                getattr(tool_use, "name", ""),
                dict(getattr(tool_use, "input", {}) or {}),
            )
            actions.append(execution.action)
            round_actions.append(execution.action)
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": getattr(tool_use, "id", ""),
                    "content": execution.model_output,
                    "is_error": not execution.action.ok,
                }
            )
        conversation.append({"role": "user", "content": results})
        return round_actions

    def _assemble(
        self,
        resp: Any,
        model: str,
        text_parts: list[str],
        thinking_parts: list[str],
        total_in: int,
        total_out: int,
        actions: list[ChatAction],
    ) -> ChatResponse:
        content = "".join(text_parts)
        stop_reason = getattr(resp, "stop_reason", None) if resp is not None else None
        if stop_reason == "refusal" and not content:
            content = "[Claude declined to respond to this request.]"
        return ChatResponse(
            content=content,
            provider=self.name,
            model=getattr(resp, "model", model) if resp is not None else model,
            stop_reason=stop_reason,
            thinking="\n".join(thinking_parts) or None,
            usage=Usage(input_tokens=total_in, output_tokens=total_out),
            actions=actions,
        )

    async def chat(
        self, request: ChatRequest, toolbox: AiToolbox | None = None
    ) -> ChatResponse:
        client = self._get_client()
        base_kwargs, conversation, model = self._base_kwargs(request, toolbox)

        actions: list[ChatAction] = []
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        total_in = 0
        total_out = 0
        resp: Any = None

        # Manual tool loop (ADR-0003): execute engine tools until Claude stops
        # asking for them, or the iteration cap is hit.
        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                resp = await client.messages.create(  # type: ignore[attr-defined]
                    **base_kwargs, messages=conversation
                )
            except Exception as exc:  # map SDK errors → engine errors
                raise self._map_error(exc) from exc

            usage_obj = getattr(resp, "usage", None)
            total_in += getattr(usage_obj, "input_tokens", 0) or 0
            total_out += getattr(usage_obj, "output_tokens", 0) or 0

            tool_uses = self._collect_blocks(resp, text_parts, thinking_parts)
            if getattr(resp, "stop_reason", None) != "tool_use" or not tool_uses:
                break
            if toolbox is None:  # defensive: model requested tools we never offered
                break
            self._answer_tool_uses(conversation, resp, tool_uses, toolbox, actions)

        return self._assemble(
            resp, model, text_parts, thinking_parts, total_in, total_out, actions
        )

    async def stream(
        self, request: ChatRequest, toolbox: AiToolbox | None = None
    ) -> AsyncIterator[ChatStreamEvent]:
        """Stream a Claude turn, forwarding text deltas as they arrive.

        The manual tool loop is preserved: each iteration opens a streaming
        request, forwards text_stream deltas, then resolves the final message —
        if it asked for tools we execute them (emitting ``action`` events) and
        loop, otherwise we finish with a ``done`` event carrying the assembled
        response. SDK errors become a terminal ``error`` event.
        """
        try:
            client = self._get_client()
            base_kwargs, conversation, model = self._base_kwargs(request, toolbox)
        except EngineError as exc:
            yield ChatStreamEvent(
                type="error", error=exc.message, code=exc.code, retryable=exc.retryable
            )
            return

        actions: list[ChatAction] = []
        text_parts: list[str] = []
        thinking_parts: list[str] = []
        total_in = 0
        total_out = 0
        resp: Any = None

        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                async with client.messages.stream(  # type: ignore[attr-defined]
                    **base_kwargs, messages=conversation
                ) as stream:
                    async for text in stream.text_stream:
                        if text:
                            yield ChatStreamEvent(type="delta", text=text)
                    resp = await stream.get_final_message()
            except Exception as exc:  # map SDK errors → terminal error event
                mapped = self._map_error(exc)
                yield ChatStreamEvent(
                    type="error",
                    error=mapped.message,
                    code=mapped.code,
                    retryable=mapped.retryable,
                )
                return

            usage_obj = getattr(resp, "usage", None)
            total_in += getattr(usage_obj, "input_tokens", 0) or 0
            total_out += getattr(usage_obj, "output_tokens", 0) or 0

            # text_stream already surfaced the text; collect blocks for thinking
            # + tool_use (drop text_parts collected here to avoid double-count).
            block_text: list[str] = []
            tool_uses = self._collect_blocks(resp, block_text, thinking_parts)
            text_parts.extend(block_text)

            if getattr(resp, "stop_reason", None) != "tool_use" or not tool_uses:
                break
            if toolbox is None:
                break
            for action in self._answer_tool_uses(
                conversation, resp, tool_uses, toolbox, actions
            ):
                yield ChatStreamEvent(type="action", action=action)

        yield ChatStreamEvent(
            type="done",
            response=self._assemble(
                resp, model, text_parts, thinking_parts, total_in, total_out, actions
            ),
        )

    def _map_error(self, exc: Exception) -> AIProviderError:
        retryable = False
        if anthropic is not None:
            retryable = isinstance(
                exc,
                (
                    anthropic.RateLimitError,
                    anthropic.APIConnectionError,
                    anthropic.InternalServerError,
                ),
            )
        return AIProviderError(
            f"Claude request failed: {exc}", retryable=retryable, details={"model": self._model}
        )

    async def health(self) -> ProviderHealth:
        if anthropic is None:
            return ProviderHealth(
                provider=self.name,
                available=False,
                detail=f"anthropic SDK not importable: {_ANTHROPIC_IMPORT_ERROR}",
            )
        if not self._api_key:
            return ProviderHealth(
                provider=self.name,
                available=False,
                detail="ANTHROPIC_API_KEY not set",
            )
        return ProviderHealth(
            provider=self.name,
            available=True,
            detail=f"ready (model={self._model}, thinking={self._thinking})",
        )
