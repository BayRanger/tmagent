#!/usr/bin/env python3
"""Weather lookup script using wttr.in."""

import sys
import urllib.request
import json


def get_weather(city: str) -> str:
    """Get weather for a city using wttr.in."""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        current = data["current_condition"][0]
        location = data["nearest_area"][0]["areaName"][0]["value"]
        
        temp_c = current["temp_C"]
        temp_f = current["temp_F"]
        condition = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        
        return f"""
📍 Location: {location}
🌡️  Temperature: {temp_c}°C / {temp_f}°F
☁️  Condition: {condition}
💧 Humidity: {humidity}%
"""
    except Exception as e:
        return f"Error getting weather: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python weather.py <city>")
        print("Example: python weather.py New York")
        sys.exit(1)
    
    city = " ".join(sys.argv[1:])
    print(get_weather(city))
