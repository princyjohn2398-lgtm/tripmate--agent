"""Mock weather tool for the assessment. These values are illustrative, not live forecasts."""
from datetime import datetime

# Clearly labelled mock examples. Expand the table as needed for the demo.
MOCK_WEATHER = {
    "reykjavik": {
        "december": {"conditions": "cold, windy; possible snow", "temp_range_c": [-3, 3]},
        "january": {"conditions": "cold, windy; possible snow", "temp_range_c": [-4, 2]},
        "june": {"conditions": "cool, often cloudy", "temp_range_c": [7, 13]},
        "july": {"conditions": "mild, changeable", "temp_range_c": [9, 15]},
    },
    "barcelona": {
        "december": {"conditions": "mild, sometimes rainy", "temp_range_c": [8, 15]},
        "june": {"conditions": "warm and mostly sunny", "temp_range_c": [20, 27]},
        "july": {"conditions": "hot and mostly sunny", "temp_range_c": [23, 30]},
        "october": {"conditions": "mild, occasional rain", "temp_range_c": [16, 23]},
    },
    "bangkok": {
        "december": {"conditions": "warm and relatively dry", "temp_range_c": [23, 32]},
        "january": {"conditions": "warm and relatively dry", "temp_range_c": [22, 32]},
        "july": {"conditions": "hot, humid, with possible heavy showers", "temp_range_c": [25, 33]},
        "october": {"conditions": "hot and humid; rain possible", "temp_range_c": [24, 32]},
    },
    # This is illustrative mock data, not information from a supplied Tokyo guide.
    "tokyo": {
        "december": {"conditions": "cool, generally dry (mock estimate)", "temp_range_c": [3, 12]},
        "july": {"conditions": "hot and humid (mock estimate)", "temp_range_c": [22, 30]},
    },
}

def get_weather_forecast(city: str, date_or_month: str) -> dict:
    """Return mock weather for a supported city/month; never claims to be live data."""
    city_key = (city or "").strip().lower()
    period = (date_or_month or "").strip().lower()
    if not city_key or not period:
        return {"error": "Please provide both a city and a date or month.", "source": "mock"}
    # Match month name if user passes a full date such as '2026-12-10'.
    month_names = {
        "01": "january", "02": "february", "03": "march", "04": "april",
        "05": "may", "06": "june", "07": "july", "08": "august",
        "09": "september", "10": "october", "11": "november", "12": "december",
    }
    try:
        parsed = datetime.strptime(period[:10], "%Y-%m-%d")
        period_key = parsed.strftime("%B").lower()
    except ValueError:
        period_key = next((m for m in month_names.values() if m in period), period)
        if period.isdigit() and period in month_names:
            period_key = month_names[period]
    city_data = MOCK_WEATHER.get(city_key)
    if not city_data:
        return {"error": f"No mock weather data available for {city}.", "source": "mock"}
    result = city_data.get(period_key)
    if not result:
        return {
            "error": f"No mock weather data available for {city.title()} in {period}.",
            "available_months": sorted(city_data.keys()),
            "source": "mock",
        }
    return {"city": city_key.title(), "period": period_key.title(), **result, "source": "mock"}
