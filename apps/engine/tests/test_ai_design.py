"""M1.3 — AI design pipeline tests.

Covers the toolbox (engine capabilities as tools), the deterministic stub
design flow, the Claude tool-calling loop (scripted fake client), and the
offline MVP story through the HTTP API.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from engineerforge_engine.adapters.ai.claude import ClaudeProvider
from engineerforge_engine.adapters.ai.stub import StubProvider, parse_bracket_request
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.application.ai_tools import AiToolbox
from engineerforge_engine.application.parts_service import PartsService
from engineerforge_engine.domain.ai import ChatMessage, ChatRequest, Role
from engineerforge_engine.domain.errors import InvalidRequestError
from engineerforge_engine.templates import default_registry
from fastapi.testclient import TestClient

from helpers import bracket_volume


@pytest.fixture
def toolbox() -> AiToolbox:
    return AiToolbox(PartsService(CadQueryKernel(), default_registry()))


class TestToolbox:
    def test_definitions_shape(self, toolbox: AiToolbox) -> None:
        defs = toolbox.definitions()
        names = {d["name"] for d in defs}
        assert names == {
            "list_part_templates",
            "create_part_from_template",
            "update_part_parameters",
        }
        for d in defs:
            assert d["input_schema"]["type"] == "object"

    def test_create_and_propose_update_flow(self, toolbox: AiToolbox) -> None:
        created = toolbox.execute(
            "create_part_from_template",
            {"templateId": "bracket-l", "values": {"W": 50, "R": 0}, "materialId": "pla"},
        )
        assert created.action.ok
        assert created.action.part_id is not None
        assert "50" in created.model_output and "cm³" in created.model_output

        proposed = toolbox.execute(
            "update_part_parameters",
            {"partId": created.action.part_id, "values": {"H": 80}},
        )
        # a proposal validates and returns a diff but does NOT mutate the part
        assert proposed.action.ok
        assert proposed.action.part_id == created.action.part_id
        assert proposed.action.pending is True
        assert len(proposed.action.diff) == 1
        assert proposed.action.diff[0].param_id == "H"
        assert proposed.action.diff[0].new_value == 80
        assert "pending" in proposed.model_output.lower()

        unchanged = toolbox._parts.get(created.action.part_id)
        current_h = unchanged.program.parameter_by_id("H").value
        assert current_h != 80

        no_op = toolbox.execute(
            "update_part_parameters",
            {"partId": created.action.part_id, "values": {"H": current_h}},
        )
        assert no_op.action.ok
        assert no_op.action.pending is False
        assert no_op.action.diff == []

    def test_failures_are_reported_not_raised(self, toolbox: AiToolbox) -> None:
        unknown = toolbox.execute("teleport_part", {})
        assert not unknown.action.ok

        bad_template = toolbox.execute("create_part_from_template", {"templateId": "nope"})
        assert not bad_template.action.ok
        assert "unknown template" in bad_template.model_output

        bad_value = toolbox.execute(
            "create_part_from_template",
            {"templateId": "bracket-l", "values": {"T": 0.1}},
        )
        assert not bad_value.action.ok
        assert "≥" in bad_value.model_output

    def test_preview_params_validates_without_mutating(self, toolbox: AiToolbox) -> None:
        parts = toolbox._parts
        detail = parts.create_from_template("bracket-l", {"W": 50, "R": 0})
        original_w = detail.program.parameter_by_id("W").value

        diff = parts.preview_params(detail.part_id, {"W": 65})
        assert len(diff) == 1
        assert diff[0].param_id == "W"
        assert diff[0].old_value == original_w
        assert diff[0].new_value == 65
        assert diff[0].unit == "mm"
        # part is untouched — no recompile, no mutation
        assert parts.get(detail.part_id).program.parameter_by_id("W").value == original_w

        # no-op values are omitted from the diff
        assert parts.preview_params(detail.part_id, {"W": original_w}) == []

        # invalid values still raise (validation is shared with patch_params)
        with pytest.raises(InvalidRequestError):
            parts.preview_params(detail.part_id, {"T": 0.1})
        with pytest.raises(InvalidRequestError):
            parts.preview_params(detail.part_id, {"NOPE": 1})

    def test_list_templates_describes_parameters(self, toolbox: AiToolbox) -> None:
        listed = toolbox.execute("list_part_templates", {})
        assert listed.action.ok
        assert "bracket-l" in listed.model_output
        assert "W=40" in listed.model_output


class TestStubDesignFlow:
    def test_prompt_parsing(self) -> None:
        values = parse_bracket_request(
            "Design a bracket 50x70, 3 mm thick, with 3 holes please"
        )
        assert values == {"W": 50.0, "H": 70.0, "T": 3.0, "HC": 3.0}
        assert parse_bracket_request("how strong is PETG?") is None

    async def test_design_prompt_creates_a_real_part(self, toolbox: AiToolbox) -> None:
        provider = StubProvider()
        response = await provider.chat(
            ChatRequest(
                messages=[
                    ChatMessage(role=Role.user, content="Design a bracket 50x70 in petg")
                ]
            ),
            toolbox,
        )
        assert len(response.actions) == 1
        action = response.actions[0]
        assert action.ok and action.part_id
        assert "Created" in response.content

    async def test_non_design_prompt_stays_conversational(self, toolbox: AiToolbox) -> None:
        response = await StubProvider().chat(
            ChatRequest(messages=[ChatMessage(role=Role.user, content="hello")]),
            toolbox,
        )
        assert response.actions == []


class _FakeAnthropicClient:
    """Scripted responses emulating the Claude SDK message surface."""

    def __init__(self, responses: list[Any]) -> None:
        self._responses = responses
        self.calls: list[dict[str, Any]] = []
        self.messages = SimpleNamespace(create=self._create)

    async def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self._responses[min(len(self.calls) - 1, len(self._responses) - 1)]


def _block(**kw: Any) -> SimpleNamespace:
    return SimpleNamespace(**kw)


class TestClaudeToolLoop:
    async def test_executes_tools_and_returns_actions(self, toolbox: AiToolbox) -> None:
        tool_turn = SimpleNamespace(
            content=[
                _block(type="text", text="Creating your bracket now."),
                _block(
                    type="tool_use",
                    id="toolu_1",
                    name="create_part_from_template",
                    input={"templateId": "bracket-l", "values": {"W": 55, "R": 0}},
                ),
            ],
            stop_reason="tool_use",
            model="claude-opus-4-8",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        final_turn = SimpleNamespace(
            content=[_block(type="text", text=" Done — 55 mm wide, editable in the panel.")],
            stop_reason="end_turn",
            model="claude-opus-4-8",
            usage=SimpleNamespace(input_tokens=20, output_tokens=8),
        )
        fake = _FakeAnthropicClient([tool_turn, final_turn])
        provider = ClaudeProvider(api_key="sk-test")
        provider._client = fake  # inject the scripted client

        response = await provider.chat(
            ChatRequest(messages=[ChatMessage(role=Role.user, content="bracket 55 wide")]),
            toolbox,
        )

        assert len(fake.calls) == 2
        # second call carries assistant echo + tool_result with matching id
        followup = fake.calls[1]["messages"]
        assert followup[-1]["role"] == "user"
        assert followup[-1]["content"][0]["tool_use_id"] == "toolu_1"
        assert followup[-1]["content"][0]["is_error"] is False
        # tools were offered
        assert any(t["name"] == "create_part_from_template" for t in fake.calls[0]["tools"])

        assert len(response.actions) == 1
        assert response.actions[0].ok and response.actions[0].part_id
        assert "Done" in response.content
        assert response.usage.input_tokens == 30  # summed across iterations

    async def test_update_proposes_a_pending_diff(self, toolbox: AiToolbox) -> None:
        # seed a part the model can edit
        seed = toolbox.execute(
            "create_part_from_template",
            {"templateId": "bracket-l", "values": {"W": 50, "R": 0}},
        )
        part_id = seed.action.part_id
        assert part_id is not None

        tool_turn = SimpleNamespace(
            content=[
                _block(
                    type="tool_use",
                    id="toolu_u",
                    name="update_part_parameters",
                    input={"partId": part_id, "values": {"W": 70}},
                ),
            ],
            stop_reason="tool_use",
            model="claude-opus-4-8",
            usage=SimpleNamespace(input_tokens=3, output_tokens=2),
        )
        final_turn = SimpleNamespace(
            content=[_block(type="text", text="I've proposed widening it to 70 mm.")],
            stop_reason="end_turn",
            model="claude-opus-4-8",
            usage=SimpleNamespace(input_tokens=3, output_tokens=2),
        )
        fake = _FakeAnthropicClient([tool_turn, final_turn])
        provider = ClaudeProvider(api_key="sk-test")
        provider._client = fake

        response = await provider.chat(
            ChatRequest(messages=[ChatMessage(role=Role.user, content="make it 70 wide")]),
            toolbox,
        )
        action = response.actions[0]
        assert action.ok and action.pending is True
        assert action.part_id == part_id
        assert action.diff[0].param_id == "W" and action.diff[0].new_value == 70
        # the tool_result fed back to Claude signals the pending state, not a done edit
        assert "pending" in fake.calls[1]["messages"][-1]["content"][0]["content"].lower()
        # the part was NOT mutated by the proposal
        assert toolbox._parts.get(part_id).program.parameter_by_id("W").value == 50

    async def test_tool_failure_flows_back_as_error_result(self, toolbox: AiToolbox) -> None:
        tool_turn = SimpleNamespace(
            content=[
                _block(
                    type="tool_use",
                    id="toolu_9",
                    name="create_part_from_template",
                    input={"templateId": "does-not-exist"},
                ),
            ],
            stop_reason="tool_use",
            model="m",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        final_turn = SimpleNamespace(
            content=[_block(type="text", text="That template does not exist.")],
            stop_reason="end_turn",
            model="m",
            usage=SimpleNamespace(input_tokens=1, output_tokens=1),
        )
        fake = _FakeAnthropicClient([tool_turn, final_turn])
        provider = ClaudeProvider(api_key="sk-test")
        provider._client = fake

        response = await provider.chat(
            ChatRequest(messages=[ChatMessage(role=Role.user, content="x")]), toolbox
        )
        assert response.actions[0].ok is False
        assert fake.calls[1]["messages"][-1]["content"][0]["is_error"] is True


class _FakeStream:
    """One scripted streaming turn: text deltas then a final message."""

    def __init__(self, texts: list[str], final: Any) -> None:
        self._texts = texts
        self._final = final

    async def __aenter__(self) -> _FakeStream:
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    @property
    def text_stream(self) -> Any:
        async def gen() -> Any:
            for t in self._texts:
                yield t

        return gen()

    async def get_final_message(self) -> Any:
        return self._final


class _FakeStreamingClient:
    """Emulates client.messages.stream(...) as an async context manager."""

    def __init__(self, scripted: list[tuple[list[str], Any]]) -> None:
        self._scripted = scripted
        self.calls: list[dict[str, Any]] = []
        self.messages = SimpleNamespace(stream=self._stream)

    def _stream(self, **kwargs: Any) -> _FakeStream:
        self.calls.append(kwargs)
        texts, final = self._scripted[min(len(self.calls) - 1, len(self._scripted) - 1)]
        return _FakeStream(texts, final)


async def _collect(stream: Any) -> list[Any]:
    return [event async for event in stream]


class TestStreaming:
    async def test_stub_streams_words_then_done(self, toolbox: AiToolbox) -> None:
        events = await _collect(
            StubProvider().stream(
                ChatRequest(messages=[ChatMessage(role=Role.user, content="hello")]),
                toolbox,
            )
        )
        deltas = [e for e in events if e.type == "delta"]
        assert len(deltas) > 1  # actually chunked, not one blob
        assert events[-1].type == "done"
        # reassembled deltas are byte-identical to the final content
        assert "".join(d.text for d in deltas) == events[-1].response.content

    async def test_stub_stream_emits_action_for_a_design_prompt(
        self, toolbox: AiToolbox
    ) -> None:
        events = await _collect(
            StubProvider().stream(
                ChatRequest(
                    messages=[ChatMessage(role=Role.user, content="Design a bracket 50x70")]
                ),
                toolbox,
            )
        )
        actions = [e for e in events if e.type == "action"]
        assert len(actions) == 1 and actions[0].action.ok
        assert events[-1].type == "done"
        assert events[-1].response.actions[0].part_id

    async def test_claude_stream_forwards_deltas_and_runs_the_tool_loop(
        self, toolbox: AiToolbox
    ) -> None:
        tool_final = SimpleNamespace(
            content=[
                _block(type="text", text="Creating your bracket."),
                _block(
                    type="tool_use",
                    id="toolu_s",
                    name="create_part_from_template",
                    input={"templateId": "bracket-l", "values": {"W": 55, "R": 0}},
                ),
            ],
            stop_reason="tool_use",
            model="claude-opus-4-8",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        end_final = SimpleNamespace(
            content=[_block(type="text", text=" Done.")],
            stop_reason="end_turn",
            model="claude-opus-4-8",
            usage=SimpleNamespace(input_tokens=20, output_tokens=8),
        )
        fake = _FakeStreamingClient(
            [(["Creating ", "your bracket."], tool_final), ([" Done."], end_final)]
        )
        provider = ClaudeProvider(api_key="sk-test")
        provider._client = fake

        events = await _collect(
            provider.stream(
                ChatRequest(messages=[ChatMessage(role=Role.user, content="bracket 55")]),
                toolbox,
            )
        )
        deltas = [e.text for e in events if e.type == "delta"]
        assert deltas == ["Creating ", "your bracket.", " Done."]
        action_events = [e for e in events if e.type == "action"]
        assert len(action_events) == 1 and action_events[0].action.ok
        done = events[-1]
        assert done.type == "done"
        assert done.response.content == "Creating your bracket. Done."
        assert done.response.actions[0].part_id
        assert done.response.usage.input_tokens == 30  # summed across iterations
        assert len(fake.calls) == 2  # streamed twice (tool loop)

    async def test_claude_stream_reports_unavailable_as_error_event(self) -> None:
        # no key configured → provider unavailable, surfaced as a terminal event
        events = await _collect(
            ClaudeProvider(api_key=None).stream(
                ChatRequest(messages=[ChatMessage(role=Role.user, content="hi")])
            )
        )
        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].code == "AI_PROVIDER_UNAVAILABLE"

    def test_stream_endpoint_yields_ndjson_offline(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/ai/chat/stream",
            json={
                "messages": [
                    {"role": "user", "content": "Design a bracket 50x70, in petg"}
                ]
            },
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/x-ndjson")
        lines = [json.loads(ln) for ln in resp.text.splitlines() if ln.strip()]
        assert lines, "stream produced no events"
        assert {ln["type"] for ln in lines} >= {"delta", "done"}
        done = lines[-1]
        assert done["type"] == "done"
        assert done["response"]["actions"][0]["partId"]

    def test_stream_endpoint_rejects_empty_messages(self, client: TestClient) -> None:
        resp = client.post("/api/v1/ai/chat/stream", json={"messages": []})
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_REQUEST"


class TestMvpStoryOffline:
    """The MVP user story, end to end over HTTP, fully offline."""

    def test_design_edit_flow(self, client: TestClient) -> None:
        chat = client.post(
            "/api/v1/ai/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Design a bracket 50x70, 4 mm thick, with 2 holes, in petg",
                    }
                ]
            },
        )
        assert chat.status_code == 200
        body = chat.json()
        assert body["actions"], "chat should have created a part"
        action = body["actions"][0]
        assert action["ok"] is True
        part_id = action["partId"]

        part = client.get(f"/api/v1/parts/{part_id}").json()
        expected = bracket_volume(50, 70, 40, 4, 5, 2)
        assert abs(part["compiled"]["massProps"]["volumeMm3"] - expected) < 0.01
        assert part["compiled"]["massProps"]["materialId"] == "petg"

        # the part stays editable — the parametric loop continues from chat
        patched = client.patch(
            f"/api/v1/parts/{part_id}/params", json={"values": {"W": 60}}
        )
        assert patched.status_code == 200
