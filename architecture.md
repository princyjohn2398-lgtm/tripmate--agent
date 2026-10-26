# TripMate architecture

```mermaid
flowchart LR
    U([User]) -->|question| CLI[app.py<br/>CLI]
    CLI --> A

    subgraph Orchestration
        A[agent.py<br/>tool-calling loop<br/>validation, logging, error handling]
    end

    A <-->|messages + tool schemas<br/>tool calls / final answer| L[(LLM provider<br/>OpenAI-compatible API)]

    A -->|search_destination_guide| R[tools/destination_rag.py<br/>chunk, TF-IDF, city filter]
    R --> V[(In-memory TF-IDF index<br/>built from data/destinations/*.txt)]

    A -->|get_weather_forecast| W[tools/weather.py<br/>month parsing + lookup]
    W --> M[(Mock weather table<br/>4 cities x 12 months)]

    A --> LOG[(logs/tripmate.log<br/>JSON lines)]
    A -->|answer + visible tool trace| CLI
    CLI -->|response| U
```

## How a request flows

1. The user types a question in the CLI (`app.py`).
2. `agent.py` validates it (not empty, not too long) and sends it to the LLM together with the tool schemas.
3. The LLM decides, per question, which tools to call (none, one or both) and with what arguments.
4. `agent.py` validates the arguments and runs only registered tools. Each call, result and error is logged as JSON.
5. Tool results go back to the LLM, which can call more tools or write the final answer.
6. The CLI prints the answer and the visible tool trace (tool, reason, arguments, result).

## Layers

| Layer | Files | Responsibility |
|---|---|---|
| Interface | `app.py` | Read input, print answer and trace |
| Orchestration | `agent.py` | LLM loop, tool dispatch, validation, error handling |
| Tools | `tools/destination_rag.py`, `tools/weather.py` | Business logic, no LLM code |
| Config and logging | `config.py`, `logging_setup.py` | Environment settings, JSON logs |
| Data | `data/destinations/*.txt` | Destination guides for Tokyo, Reykjavik, Bangkok, Barcelona |
