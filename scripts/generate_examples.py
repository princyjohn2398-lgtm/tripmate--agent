"""Run sample queries through the real agent and write the results into README.md.

Usage (from the project root, with .venv active and .env set up):
    python scripts/generate_examples.py
It fills the section between the EXAMPLE_RUNS markers and the TOOL_SCHEMAS markers.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import TOOLS, run_agent  # noqa: E402
from logging_setup import setup_logging  # noqa: E402

README = ROOT / "README.md"
RAG, WEATHER = "search_destination_guide", "get_weather_forecast"

EXAMPLES = [
    ("Single tool: destination guide", "What are the local customs in Tokyo?", {RAG}),
    ("Multi-tool: guide + weather (packing)", "What should I pack for Tokyo in March?", {RAG, WEATHER}),
    ("Out of scope: booking request", "Can you book a flight to Barcelona?", set()),
    ("Unsupported destination", "What is the weather in Paris in May?", {WEATHER}),
]
ERROR_MARKERS = ("AI service", "AI model", "LLM is not configured")
MAX_RESULT_CHARS = 450


def _short(value) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    return text if len(text) <= MAX_RESULT_CHARS else text[:MAX_RESULT_CHARS] + " ...(truncated)"


def build_examples(client=None):
    """Return (markdown, problems). Runs every example query through the agent."""
    parts, problems = [], []
    for number, (title, query, expected) in enumerate(EXAMPLES, start=1):
        result = run_agent(query, client=client)
        if any(marker in result["answer"] for marker in ERROR_MARKERS):
            problems.append(f"Example {number} failed: {result['answer']}")
        used = {item["tool"] for item in result["trace"]}
        if used != expected:
            problems.append(f"Example {number} used tools {sorted(used)}, expected {sorted(expected)}")
        lines = [f"### Example {number}: {title}", "", f"**Input:** `{query}`", "", "```text"]
        if result["trace"]:
            for item in result["trace"]:
                lines += [
                    f"Tool:      {item['tool']}",
                    f"Why:       {item.get('reason') or '(not given)'}",
                    f"Arguments: {item['arguments']}",
                    f"Result:    {_short(item['result'])}",
                    "",
                ]
        else:
            lines += ["(no tools called)", ""]
        lines += ["```", "", f"**Answer:** {result['answer']}", ""]
        parts.append("\n".join(lines))
    return "\n".join(parts), problems


def _inject(text: str, start: str, end: str, body: str) -> str:
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + "\n" + body.strip() + "\n" + text[b:]


def main():
    setup_logging()
    print("Running example queries against the real LLM (this takes a few seconds)...")
    examples_md, problems = build_examples()
    for problem in problems:
        print("WARNING:", problem)
    if any("failed" in p for p in problems):
        print("\nThe LLM call failed, so README.md was NOT changed. Fix the error above and run again.")
        return
    schemas = "```json\n" + json.dumps([t["function"] for t in TOOLS], indent=2) + "\n```"
    text = README.read_text(encoding="utf-8")
    text = _inject(text, "<!-- EXAMPLE_RUNS_START -->", "<!-- EXAMPLE_RUNS_END -->", examples_md)
    text = _inject(text, "<!-- TOOL_SCHEMAS_START -->", "<!-- TOOL_SCHEMAS_END -->", schemas)
    README.write_text(text, encoding="utf-8")
    print("README.md updated with real example runs and tool schemas.")
    if problems:
        print("Check the warnings above: the model chose different tools than expected for some examples.")


if __name__ == "__main__":
    main()
