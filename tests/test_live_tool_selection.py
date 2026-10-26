"""Optional live check of the real LLM's tool choices. Skipped when no API key is set."""
import pytest

from agent import run_agent
from config import OPENAI_API_KEY

pytestmark = pytest.mark.skipif(not OPENAI_API_KEY, reason="OPENAI_API_KEY not set")

RAG = "search_destination_guide"
WEATHER = "get_weather_forecast"


@pytest.mark.parametrize("query, expected", [
    ("What are the local customs in Bangkok?", {RAG}),
    ("What is the weather in Reykjavik in December?", {WEATHER}),
    ("What should I pack for Tokyo in March?", {RAG, WEATHER}),
    ("Can you book a flight to Barcelona?", set()),
])
def test_real_llm_picks_expected_tools(query, expected):
    result = run_agent(query)
    assert {item["tool"] for item in result["trace"]} == expected
