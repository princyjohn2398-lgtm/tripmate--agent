"""Agent tests. A scripted fake LLM replaces the real one, so no API key is needed."""
import json
from types import SimpleNamespace

import openai

from agent import TOOLS, execute_tool, run_agent


# ---------- helpers: a scripted fake LLM ----------
def _call(call_id, name, args):
    return SimpleNamespace(
        id=call_id, type="function",
        function=SimpleNamespace(name=name, arguments=args if isinstance(args, str) else json.dumps(args)),
    )


def _assistant(tool_calls=None, content=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    message.model_dump = lambda exclude_none=True: {
        "role": "assistant",
        "content": content,
        "tool_calls": [
            {"id": c.id, "type": "function",
             "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in (tool_calls or [])
        ],
    }
    return message


class FakeClient:
    """Returns the given assistant messages one by one (or raises an exception)."""

    def __init__(self, *messages, error=None):
        self._responses = [SimpleNamespace(choices=[SimpleNamespace(message=m)]) for m in messages]
        self._error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        if self._error:
            raise self._error
        return self._responses.pop(0)


def _tools_used(result):
    return [item["tool"] for item in result["trace"]]


RAG = "search_destination_guide"
WEATHER = "get_weather_forecast"


# ---------- schema and tool execution ----------
def test_tool_schemas_include_both_tools():
    assert {t["function"]["name"] for t in TOOLS} == {RAG, WEATHER}


def test_execute_weather_tool():
    result = execute_tool(WEATHER, {"city": "Bangkok", "date_or_month": "December"})
    assert result["source"] == "mock"


def test_execute_rag_tool_returns_chunks():
    result = execute_tool(RAG, {"query": "Bangkok temple customs"})
    assert isinstance(result, list) and result


def test_execute_unknown_tool_is_rejected():
    assert "error" in execute_tool("delete_everything", {})


# ---------- tool selection: single, multi and no-tool flows ----------
def test_single_tool_guide_only():
    client = FakeClient(
        _assistant([_call("c1", RAG, {"query": "Bangkok customs", "reason": "customs question"})]),
        _assistant(content="Dress modestly at temples."),
    )
    result = run_agent("What are the customs in Bangkok?", client=client)
    assert _tools_used(result) == [RAG]
    assert result["trace"][0]["reason"] == "customs question"
    assert "reason" not in result["trace"][0]["arguments"]


def test_single_tool_weather_only():
    client = FakeClient(
        _assistant([_call("c1", WEATHER, {"city": "Reykjavik", "date_or_month": "December"})]),
        _assistant(content="Cold, around -3 to 3 C (mock data)."),
    )
    result = run_agent("Weather in Reykjavik in December?", client=client)
    assert _tools_used(result) == [WEATHER]


def test_multi_tool_packing_flow():
    client = FakeClient(
        _assistant([
            _call("c1", RAG, {"query": "Bangkok packing tips", "top_k": 2}),
            _call("c2", WEATHER, {"city": "Bangkok", "date_or_month": "December"}),
        ]),
        _assistant(content="Pack light clothing and a temple cover-up. Mock data suggests warm weather."),
    )
    result = run_agent("What should I pack for Bangkok in December?", client=client)
    assert set(_tools_used(result)) == {RAG, WEATHER}
    assert "Pack light clothing" in result["answer"]


def test_no_tool_out_of_scope_request():
    client = FakeClient(_assistant(content="I can't book flights, but I can help with trip information."))
    result = run_agent("Can you book a flight to Barcelona?", client=client)
    assert result["trace"] == []
    assert "can't book" in result["answer"]


# ---------- error handling ----------
def test_empty_query_does_not_call_llm():
    result = run_agent("   ", client=object())
    assert result["trace"] == []
    assert "enter" in result["answer"].lower()


def test_too_long_query_is_rejected():
    result = run_agent("a" * 5000, client=object())
    assert "too long" in result["answer"].lower()


def test_unknown_city_weather_error_reaches_trace():
    client = FakeClient(
        _assistant([_call("c1", WEATHER, {"city": "Atlantis", "date_or_month": "June"})]),
        _assistant(content="I have no weather data for Atlantis."),
    )
    result = run_agent("Weather in Atlantis in June?", client=client)
    assert "error" in result["trace"][0]["result"]


def test_malformed_tool_arguments_are_handled():
    client = FakeClient(
        _assistant([_call("c1", RAG, "this is not json")]),
        _assistant(content="Sorry, something went wrong with that lookup."),
    )
    result = run_agent("Tell me about Tokyo", client=client)
    assert "error" in result["trace"][0]["result"]
    assert result["answer"]


def test_llm_failure_returns_friendly_message():
    client = FakeClient(error=openai.OpenAIError("boom"))
    result = run_agent("What are the customs in Tokyo?", client=client)
    assert "unavailable" in result["answer"].lower()
    assert result["trace"] == []
