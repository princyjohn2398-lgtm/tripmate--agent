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
