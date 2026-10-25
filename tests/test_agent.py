from types import SimpleNamespace
from agent import execute_tool, run_agent, TOOLS

def test_tool_schemas_include_both_tools():
    names = {tool["function"]["name"] for tool in TOOLS}
    assert names == {"search_destination_guide", "get_weather_forecast"}

def test_execute_weather_tool():
    result = execute_tool("get_weather_forecast", {
        "city": "Bangkok", "date_or_month": "December"
    })
    assert result["source"] == "mock"

def test_empty_agent_query_does_not_call_llm():
    result = run_agent("   ", client=object())
    assert result["trace"] == []
    assert "enter" in result["answer"].lower()

def test_mocked_multi_tool_integration():
    # Fake LLM response 1 requests both tools; response 2 synthesizes their outputs.
    def tool_call(call_id, name, arguments):
        return SimpleNamespace(
            id=call_id,
            type="function",
            function=SimpleNamespace(name=name, arguments=arguments)
        )
    first_message = SimpleNamespace(
        content=None,
        tool_calls=[
            tool_call("call_rag", "search_destination_guide",
                      '{"query":"Bangkok packing tips","top_k":2}'),
            tool_call("call_weather", "get_weather_forecast",
                      '{"city":"Bangkok","date_or_month":"December"}'),
        ],
        model_dump=lambda exclude_none=True: {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id":"call_rag","type":"function","function":{"name":"search_destination_guide","arguments":'{"query":"Bangkok packing tips","top_k":2}'}},
                {"id":"call_weather","type":"function","function":{"name":"get_weather_forecast","arguments":'{"city":"Bangkok","date_or_month":"December}'}}
            ]
        }
    )
    second_message = SimpleNamespace(content="Pack light clothing and a temple cover-up. Mock data suggests warm weather.", tool_calls=None)
    responses = [
        SimpleNamespace(choices=[SimpleNamespace(message=first_message)]),
        SimpleNamespace(choices=[SimpleNamespace(message=second_message)]),
    ]
    class FakeCompletions:
        def __init__(self):
            self.index = 0
        def create(self, **kwargs):
            response = responses[self.index]
            self.index += 1
            return response
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    result = run_agent("What should I pack for Bangkok in December?", client=fake_client)
    assert len(result["trace"]) == 2
    assert {item["tool"] for item in result["trace"]} == {
        "search_destination_guide", "get_weather_forecast"
    }
    assert "Pack light clothing" in result["answer"]
