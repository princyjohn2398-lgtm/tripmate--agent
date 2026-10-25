"""LLM tool-calling orchestration for TripMate."""
import json
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL
from tools.destination_rag import search_destination_guide
from tools.weather import get_weather_forecast

logger = logging.getLogger("tripmate")

SYSTEM_PROMPT = """You are TripMate, a travel-information assistant.
Use search_destination_guide for destination guide questions such as visa/entry,
customs, packing, best time to visit, and safety. Use get_weather_forecast for
weather by city and date/month. For packing questions involving a city and time,
normally call BOTH tools so advice uses guide information and mock weather data.
You may call no tools for unsupported requests. You cannot book flights or hotels,
make reservations, or perform transactions; say so clearly and do not pretend.
Do not invent guide facts. The weather tool returns MOCK illustrative data, not a
live forecast; say that when relevant. Visa and safety information is simplified
assessment data and must be independently checked before travel.
Do not reveal hidden chain-of-thought. The visible trace should report tool names,
arguments, and outcomes only."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_destination_guide",
            "description": "Search supplied destination guide documents for visa, customs, best time to visit, packing, or safety information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language question or topic"},
                    "top_k": {"type": "integer", "description": "Number of relevant chunks, from 1 to 5", "minimum": 1, "maximum": 5}
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get illustrative mock weather data for a supported city and month/date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date_or_month": {"type": "string"}
                },
                "required": ["city", "date_or_month"],
                "additionalProperties": False
            }
        }
    }
]

def execute_tool(name: str, arguments: dict):
    """Validate and execute only tools explicitly registered here."""
    if name == "search_destination_guide":
        query = str(arguments.get("query", "")).strip()
        top_k = arguments.get("top_k", 3)
        if not query:
            return {"error": "The search query cannot be empty."}
        try:
            top_k = max(1, min(5, int(top_k)))
        except (TypeError, ValueError):
            top_k = 3
        return search_destination_guide(query, top_k=top_k)
    if name == "get_weather_forecast":
        return get_weather_forecast(
            str(arguments.get("city", "")),
            str(arguments.get("date_or_month", ""))
        )
    return {"error": f"Unsupported tool: {name}"}

def run_agent(query: str, client=None, max_tool_rounds: int = 5) -> dict:
    """Run a bounded OpenAI tool-calling loop and return answer plus visible trace."""
    query = (query or "").strip()
    if not query:
        return {"answer": "Please enter a travel question.", "trace": []}
    if client is None:
        if not OPENAI_API_KEY:
            return {
                "answer": "LLM is not configured. Copy .env.example to .env and set OPENAI_API_KEY.",
                "trace": []
            }
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    trace = []
    for _ in range(max_tool_rounds):
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return {"answer": message.content or "I could not produce an answer.", "trace": trace}
        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            name = call.function.name
            try:
                arguments = json.loads(call.function.arguments or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")
                logger.info("tool_call name=%s arguments=%s", name, arguments)
                result = execute_tool(name, arguments)
                trace.append({"tool": name, "arguments": arguments, "result": result})
                logger.info("tool_result name=%s result=%s", name, result)
            except Exception as exc:
                result = {"error": f"Tool execution failed: {type(exc).__name__}"}
                trace.append({"tool": name, "arguments": call.function.arguments, "result": result})
                logger.exception("tool_error name=%s", name)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
    return {
        "answer": "I reached the tool-call limit. Please narrow your question and try again.",
        "trace": trace
    }
