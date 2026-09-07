def execute_weather_tool(query: str = "") -> dict:
    """Returns the weather forecast data for the requested location."""
    return {"temperature": "72F", "condition": "Sunny", "status": "Clear skies"}

def register_tool():
    """Registers weather_tool with Aria's lab."""
    return "weather_tool", execute_weather_tool

if __name__ == "__main__":
    t_name, t_fn = register_tool()
    print(f"Testing {t_name}:", t_fn())