# TripMate architecture

```text
User query
   |
   v
app.py (CLI)
   |
   v
agent.py (LLM orchestration / tool-calling loop)
   |                         |
   v                         v
search_destination_guide     get_weather_forecast
   |                         |
   v                         v
destination text files       mock city/month dictionary
   |                         |
   +------------+------------+
                |
                v
       Tool results returned to LLM
                |
                v
       Final answer + visible tool trace
```

The LLM selects tools using native function calling. Python validates and executes only registered tools. The destination tool uses TF-IDF similarity over the supplied text files. Weather results are mock examples, not live forecasts.
