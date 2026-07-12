"""M1.3 — AI design pipeline tests.

Covers the toolbox (engine capabilities as tools), the deterministic stub
design flow, the Claude tool-calling loop (scripted fake client), and the
offline MVP story through the HTTP API.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from engineerforge_engine.adapters.ai.claude import ClaudeProvider
from engineerforge_engine.adapters.ai.stub import StubProvider, parse_bracket_request
from engineerforge_engine.adapters.cad.cadquery_kernel import CadQueryKernel
from engineerforge_engine.application.ai_tools import AiToolbox
from engineerforge_engine.application.parts_service import PartsService
from engineerforge_engine.domain.ai import ChatMessage, ChatRequest, Role
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

    def test_create_and_update_flow(self, toolbox: AiToolbox) -> None:
        created = toolbox.execute(
            "create_part_from_template",
            {"templateId": "bracket-l", "values": {"W": 50, "R": 0}, "materialId": "pla"},
        )
        assert created.action.ok
        assert created.action.part_id is not None
        assert "50" in created.model_output and "cm³" in created.model_output

        updated = toolbox.execute(
            "update_part_parameters",
            {"partId": created.action.part_id, "values": {"H": 80}},
        )
        assert updated.action.ok
        assert updated.action.part_id == created.action.part_id

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
