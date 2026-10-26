"""LLM tool-calling orchestration for TripMate."""
import json
import logging
from openai import OpenAI, OpenAIError, AuthenticationError, RateLimitError, NotFoundError
from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
from tools.destination_rag import search_destination_guide
from tools.weather import get_weather_forecast

logger = logging.getLogger("tripmate")

MAX_QUERY_CHARS = 1000
SUPPORTED_DESTINATIONS = "Tokyo, Reykjavik, Bangkok and Barcelona"

SYSTEM_PROMPT = f"""You are TripMate, a travel-information assistant.
Supported destinations: {SUPPORTED_DESTINATIONS}.

Tool use:
- Use search_destination_guide for visa/entry, local customs, packing, best time to visit and safety.
- Use get_weather_forecast for weather in a city and month/date.
- For packing questions about a city and time of year, call BOTH tools so the advice
  combines guide tips with the weather.
- For every tool call, fill the optional "reason" argument with one short sentence
  explaining why you are calling that tool.
- Call no tools for greetings or requests you cannot do.

Rules:
- You cannot book flights or hotels, make reservations, or do transactions. Say so
  clearly and never pretend an action happened.
- If the user asks about a destination other than the supported ones, say it is not
  covered. Do not substitute information from a different city.
- If the question is too vague (for example no city or no month where needed), ask one
  short clarifying question instead of guessing.
- Refuse unrelated topics politely and steer back to trip planning.
- Never invent guide facts. Weather data is MOCK illustrative data, not a live forecast;
  say so when you use it. Visa and safety notes are simplified assessment data and must
  be verified before travel.
- If a tool returns an error or no data, tell the user plainly what is missing."""

_REASON = {"type": "string", "description": "One short sentence: why this tool is being called"}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_destination_guide",
            "description": "Search the supplied destination guides (Tokyo, Reykjavik, Bangkok, Barcelona) for visa/entry, customs, best time to visit, packing, or safety information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural-language question or topic; include the city name"},
                    "top_k": {"type": "integer", "description": "Number of relevant chunks, from 1 to 5", "minimum": 1, "maximum": 5},
                    "reason": _REASON,
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get illustrative mock weather (conditions and temperature range in C) for a supported city and a month or date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "date_or_month": {"type": "string", "description": "Month name (e.g. March) or an ISO date"},
                    "reason": _REASON,
                },
                "required": ["city", "date_or_month"],
                "additionalProperties": False,
            },
        },
    },
]


def execute_tool(name: str, arguments: dict):
    """Validate and execute only tools explicitly registered here."""
    if name == "search_destination_guide":
        query = str(arguments.get("query", "")).strip()
        if not query:
            return {"error": "The search query cannot be empty."}
        try:
            top_k = max(1, min(5, int(arguments.get("top_k", 3))))
        except (TypeError, ValueError):
            top_k = 3
        results = search_destination_guide(query, top_k=top_k)
        if not results:
            return {
                "results": [],
                "message": f"No guide content found. Covered destinations: {SUPPORTED_DESTINATIONS}.",
            }
        return results
    if name == "get_weather_forecast":
        return get_weather_forecast(
            str(arguments.get("city", "")),
            str(arguments.get("date_or_month", "")),
        )
    return {"error": f"Unsupported tool: {name}"}


def _llm_error_message(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "The AI service rejected the API key. Please check OPENAI_API_KEY in your .env file."
    if isinstance(exc, RateLimitError):
        return "The AI service is rate-limited or out of credit. Please try again later."
    if isinstance(exc, NotFoundError):
        return "The configured AI model was not found. Please check OPENAI_MODEL in your .env file."
    return "The AI service is unavailable right now. Please try again in a moment."


def run_agent(query: str, client=None, max_tool_rounds: int = 5) -> dict:
    """Run a bounded tool-calling loop and return the answer plus a visible trace."""
    query = (query or "").strip()
    if not query:
        return {"answer": "Please enter a travel question.", "trace": []}
    if len(query) > MAX_QUERY_CHARS:
        return {"answer": f"That question is too long. Please keep it under {MAX_QUERY_CHARS} characters.", "trace": []}
    if client is None:
        if not OPENAI_API_KEY:
            return {
                "answer": "LLM is not configured. Copy .env.example to .env and set OPENAI_API_KEY.",
                "trace": [],
            }
        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, timeout=30.0, max_retries=2)

    logger.info("user_query", extra={"query": query})
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    trace = []
    for _ in range(max_tool_rounds):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )
        except OpenAIError as exc:
            logger.error("llm_error", extra={"error_type": type(exc).__name__, "detail": str(exc)[:300]})
            return {"answer": _llm_error_message(exc), "trace": trace}
        message = response.choices[0].message
        if not message.tool_calls:
            logger.info("final_answer", extra={"tools_used": [t["tool"] for t in trace]})
            return {"answer": message.content or "I could not produce an answer.", "trace": trace}
        messages.append(message.model_dump(exclude_none=True))
        for call in message.tool_calls:
            name = call.function.name
            reason = None
            try:
                arguments = json.loads(call.function.arguments or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")
                reason = arguments.pop("reason", None)
                logger.info("tool_call", extra={"tool": name, "arguments": arguments, "reason": reason})
                result = execute_tool(name, arguments)
                trace.append({"tool": name, "arguments": arguments, "reason": reason, "result": result})
                logger.info("tool_result", extra={"tool": name, "result": result})
            except Exception as exc:
                result = {"error": f"Tool execution failed: {type(exc).__name__}"}
                trace.append({"tool": name, "arguments": call.function.arguments, "reason": reason, "result": result})
                logger.error("tool_error", extra={"tool": name, "error_type": type(exc).__name__}, exc_info=True)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
    logger.warning("tool_round_limit_reached", extra={"tools_used": [t["tool"] for t in trace]})
    return {
        "answer": "I reached the tool-call limit. Please narrow your question and try again.",
        "trace": trace,
    }
