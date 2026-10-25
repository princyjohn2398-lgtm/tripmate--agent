# TripMate — Agentic AI Travel Assistant

## Overview
TripMate is a command-line travel assistant prototype. An LLM dynamically chooses between a destination-guide retrieval tool and a weather tool, combines tool results, and returns a final answer. It logs tool names, arguments, results, and errors.

## Important data note
The assessment README lists four guides: Tokyo, Reykjavik, Bangkok, and Barcelona. The initial uploaded files in this project include Reykjavik, Bangkok, and Barcelona. Add the official `tokyo.txt` supplied by the assessment organizer to `data/destinations/` when available. The Tokyo weather entry is illustrative mock data only. All weather data in this prototype is mock data, not a live forecast. The destination guides are simplified assessment references, not authoritative current visa advice.

## Requirements
- Python 3.10+
- An OpenAI API key with API access for live agent runs

## Setup (Windows PowerShell / VS Code terminal)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env` and set `OPENAI_API_KEY`. Never commit `.env` or share the key. Set `OPENAI_MODEL` to a model available to your API account.

## Run
```powershell
python app.py
```
Try:
- `What are the local customs in Bangkok?`
- `What is the weather in Reykjavik in December?`
- `What should I pack for Bangkok in December?`
- `Can you book a flight to Barcelona?`
Type `exit` to quit.

## Tests
```powershell
pytest -q
```
The multi-tool integration test uses a fake LLM response, so it does not need an API key.

## Tools exposed to the LLM
1. `search_destination_guide(query, top_k=3)`: retrieves relevant text chunks from the supplied destination documents using TF-IDF similarity.
2. `get_weather_forecast(city, date_or_month)`: returns illustrative mock conditions and temperature ranges for supported city/month pairs.

The LLM receives tool descriptions and JSON parameter schemas. It may choose one or both tools. Python executes only registered tool names, returns tool results to the model, and allows a final answer.

## Visible trace and logging
The CLI displays each tool name, arguments, and result. Python logging also records tool calls and failures. This is an observable tool-decision trace, not hidden chain-of-thought.

## Design decisions
- Native OpenAI function calling keeps the orchestration loop visible and easy to explain.
- TF-IDF is used for lightweight local retrieval rather than a hosted vector database or embedding model.
- Mock weather data avoids API keys and network failures for weather; it is not a real forecast.
- The CLI keeps the assessment focused on agent logic instead of UI work.
- Tool calls are bounded to avoid an endless loop.

## Error handling and limitations
- Empty user input is handled.
- Unknown cities and unsupported city/month combinations return clear errors from the weather tool.
- Tool execution exceptions are logged and returned as errors.
- LLM configuration and provider/network errors may still need to be handled by the caller in a future iteration.
- The simplified reference guides may be incomplete or outdated. Users should verify visa, safety, and health advice with authoritative sources.
- TF-IDF is lexical retrieval and may miss semantically related questions; it is not a production-scale vector RAG system.
- Weather values are mock examples and must not be presented as live data.

## Example runs
Run the CLI with the queries above and copy the actual output and visible tool traces here before submitting. Do not claim an example succeeded unless you ran it.

## Scalability discussion
- For hundreds of cities, use robust document ingestion, metadata such as city/section/source, chunking, and an embedding model plus a vector database (for example, FAISS or Chroma); consider hybrid lexical/vector retrieval and reranking.
- Cache retrieval results and deterministic weather responses using normalized city/month keys. Cache final LLM answers only when freshness and user-specific context allow it.
- Reduce LLM costs through smaller models for straightforward requests, concise context, prompt caching where available, token limits, and avoiding unnecessary tool calls.
- Keep tool selection fast by writing concise tool descriptions, exposing only relevant tools when possible, measuring latency, and routing by structured metadata without replacing the LLM's ability to decide dynamically.
