import os
import requests
from src.utils.logger import api_logger

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("WEATHER_API_KEY")
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, location: str):
        """
        Fetch current weather for a given location (city name or 'lat,lon').
        """
        if not self.api_key:
            api_logger.warning("Weather API key not found.")
            return None

        try:
            params = {
                "q": location,
                "appid": self.api_key,
                "units": "metric"
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                "temp": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "condition": data["weather"][0]["description"],
                "location": data["name"]
            }
        except Exception as e:
            api_logger.error(f"Failed to fetch weather for {location}: {e}")
            return None

    def get_health_impact(self, weather_data):
        """
        Analyze potential health impacts based on weather conditions.
        """
        if not weather_data:
            return []

        impacts = []
        temp = weather_data["temp"]
        humidity = weather_data["humidity"]
        condition = weather_data["condition"].lower()

        if temp > 30:
            impacts.append("High heat: Risk of dehydration and heat exhaustion. Stay hydrated.")
        elif temp < 5:
            impacts.append("Low temperature: Risk of hypothermia and increased blood pressure. Keep warm.")
        
        if humidity > 70:
            impacts.append("High humidity: May aggravate asthma and respiratory conditions.")
        elif humidity < 30:
            impacts.append("Low humidity: May cause dry skin and respiratory irritation.")

        if "rain" in condition or "storm" in condition:
            impacts.append("Wet conditions: Increased risk of slips/falls and joint pain (arthritis).")
        
        return impacts
