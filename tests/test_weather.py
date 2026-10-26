from tools.weather import get_weather_forecast

def test_supported_city_and_month():
    result = get_weather_forecast("Bangkok", "December")
    assert result["city"] == "Bangkok"
    assert result["source"] == "mock"
    assert "temp_range_c" in result

def test_unknown_city_returns_error():
    assert "error" in get_weather_forecast("Atlantis", "December")

def test_missing_input_returns_error():
    assert "error" in get_weather_forecast("", "December")


def test_month_formats_are_understood():
    for value in ["March", "Mar", "3", "2026-03-10"]:
        assert get_weather_forecast("Tokyo", value)["period"] == "March"


def test_invalid_month_returns_error():
    assert "error" in get_weather_forecast("Tokyo", "banana")
