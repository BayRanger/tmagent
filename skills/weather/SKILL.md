---
name: weather
description: "Get weather information for a location using weather APIs or commands."
---

# Weather Skill

Use this skill to get weather information.

## Using curl with wttr.in

Get weather from wttr.in (no API key needed):

```bash
curl "wttr.in/New+York"
curl "wttr.in/London?format=j1"
```

## Using Python with requests

```python
import requests

def get_weather(city: str) -> str:
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)
    data = response.json()
    current = data["current_condition"][0]
    return f"{city}: {current['temp_C']}°C, {current['weatherDesc'][0]['value']}"
```

## Scripts

- [scripts/weather.py](scripts/weather.py) - Weather lookup script
- [scripts/forecast.py](scripts/forecast.py) - Multi-day forecast
