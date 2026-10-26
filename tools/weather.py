"""Mock weather tool for the assessment. These values are illustrative, not live forecasts."""
import re
from datetime import datetime

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]

# Clearly labelled mock climate estimates (12 months per city), not live forecasts.
# Format per month: [conditions, [min_temp_c, max_temp_c]]
_RAW = {
    "reykjavik": {
        "january": ["cold, windy; possible snow", [-4, 2]],
        "february": ["cold, windy; snow or sleet possible", [-3, 3]],
        "march": ["cold and changeable; snow possible", [-2, 4]],
        "april": ["cool, changeable; occasional snow", [0, 7]],
        "may": ["cool, often bright; light showers", [3, 10]],
        "june": ["cool, often cloudy", [7, 13]],
        "july": ["mild, changeable", [9, 15]],
        "august": ["mild, changeable; some rain", [8, 14]],
        "september": ["cool, wetter and windier", [5, 10]],
        "october": ["cool, windy and wet", [2, 7]],
        "november": ["cold, windy; early snow possible", [-1, 4]],
        "december": ["cold, windy; possible snow", [-3, 3]],
    },
    "barcelona": {
        "january": ["cool and mostly dry", [6, 14]],
        "february": ["cool, mostly dry", [7, 15]],
        "march": ["mild, some rain", [9, 17]],
        "april": ["mild and pleasant, occasional rain", [11, 19]],
        "may": ["warm and mostly sunny", [15, 22]],
        "june": ["warm and mostly sunny", [20, 27]],
        "july": ["hot and mostly sunny", [23, 30]],
        "august": ["hot, sunny and humid", [23, 30]],
        "september": ["warm, with some heavy showers", [20, 26]],
        "october": ["mild, occasional rain", [16, 23]],
        "november": ["cool, rainy spells", [11, 18]],
        "december": ["mild, sometimes rainy", [8, 15]],
    },
    "bangkok": {
        "january": ["warm and relatively dry", [22, 32]],
        "february": ["hot and dry", [24, 33]],
        "march": ["very hot and dry", [26, 35]],
        "april": ["very hot and humid", [27, 36]],
        "may": ["hot, humid; rainy season begins", [26, 35]],
        "june": ["hot, humid, frequent showers", [26, 34]],
        "july": ["hot, humid, with possible heavy showers", [25, 33]],
        "august": ["hot, humid, frequent heavy showers", [25, 33]],
        "september": ["hot, humid; wettest month", [25, 32]],
        "october": ["hot and humid; rain possible", [24, 32]],
        "november": ["warm; drier and less humid", [23, 32]],
        "december": ["warm and relatively dry", [23, 32]],
    },
    # Illustrative mock estimates, not information from a supplied Tokyo guide.
    "tokyo": {
        "january": ["cold, dry and sunny (mock estimate)", [1, 10]],
        "february": ["cold, dry; occasional snow (mock estimate)", [2, 11]],
        "march": ["cool to mild, some rain (mock estimate)", [5, 14]],
        "april": ["mild and pleasant (mock estimate)", [10, 19]],
        "may": ["warm and mostly pleasant (mock estimate)", [15, 24]],
        "june": ["warm, humid; rainy season (mock estimate)", [19, 26]],
        "july": ["hot and humid (mock estimate)", [22, 30]],
        "august": ["very hot and humid (mock estimate)", [24, 32]],
        "september": ["warm, humid; typhoon risk (mock estimate)", [21, 28]],
        "october": ["mild, some rain (mock estimate)", [15, 22]],
        "november": ["cool, mostly dry (mock estimate)", [9, 17]],
        "december": ["cool, generally dry (mock estimate)", [3, 12]],
    },
}

MOCK_WEATHER = {
    city: {m: {"conditions": v[0], "temp_range_c": v[1]} for m, v in months.items()}
    for city, months in _RAW.items()
}


def _normalise_month(value: str) -> str:
    """Turn '2026-03-10', 'Mar', 'march 2026', '3' or '03' into a lowercase month name."""
    text = value.strip().lower()
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%B").lower()
    except ValueError:
        pass
    if text.isdigit() and 1 <= int(text) <= 12:
        return MONTHS[int(text) - 1]
    for token in re.findall(r"[a-z]+", text):
        if len(token) >= 3:
            for month in MONTHS:
                if month.startswith(token):
                    return month
    return text


def get_weather_forecast(city: str, date_or_month: str) -> dict:
    """Return mock weather for a supported city/month; never claims to be live data."""
    city_key = (city or "").strip().lower()
    period = (date_or_month or "").strip()
    if not city_key or not period:
        return {"error": "Please provide both a city and a date or month.", "source": "mock"}
    city_data = MOCK_WEATHER.get(city_key)
    if not city_data:
        return {
            "error": f"No mock weather data available for {city}.",
            "supported_cities": sorted(c.title() for c in MOCK_WEATHER),
            "source": "mock",
        }
    period_key = _normalise_month(period)
    result = city_data.get(period_key)
    if not result:
        return {
            "error": f"Could not understand the month '{date_or_month}' for {city.title()}.",
            "available_months": MONTHS,
            "source": "mock",
        }
    return {"city": city_key.title(), "period": period_key.title(), **result, "source": "mock"}
