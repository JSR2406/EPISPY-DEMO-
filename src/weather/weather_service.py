import aiohttp
import os
from typing import Dict, Optional
from datetime import datetime, timedelta
import json

class WeatherService:
    """
    Fetch and analyze weather data for disease risk correlation
    """
    
    def __init__(self):
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(self, city: str) -> Dict:
        # Check cache first (Mock cache for now)
        # In production, use DB
        
        # Fetch from APIs
        if not self.openweather_api_key:
            return self._get_mock_weather(city)

        try:
            async with aiohttp.ClientSession() as session:
                # Current weather
                weather_url = f"{self.base_url}/weather?q={city}&appid={self.openweather_api_key}&units=metric"
                async with session.get(weather_url) as response:
                    if response.status != 200:
                         return self._get_mock_weather(city)
                    weather_data = await response.json()
            
            # Parse weather data
            weather = {
                "city": city,
                "temperature_celsius": weather_data["main"]["temp"],
                "humidity_percent": weather_data["main"]["humidity"],
                "wind_speed_kmh": weather_data["wind"]["speed"] * 3.6,
                "rainfall_mm": weather_data.get("rain", {}).get("1h", 0),
                "condition": weather_data["weather"][0]["main"].lower(),
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            # Calculate disease multipliers
            weather["disease_multipliers"] = self._calculate_disease_multipliers(weather)
            
            return weather
        except Exception:
            return self._get_mock_weather(city)
    
    def _get_mock_weather(self, city: str) -> Dict:
        return {
            "city": city,
            "temperature_celsius": 28,
            "humidity_percent": 75,
            "wind_speed_kmh": 10,
            "rainfall_mm": 0,
            "condition": "cloudy",
            "disease_multipliers": {
                "dengue": 2.5,
                "malaria": 1.5,
                "flu": 1.0
            },
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _calculate_disease_multipliers(self, weather: Dict) -> Dict:
        multipliers = {}
        
        temp = weather["temperature_celsius"]
        humidity = weather["humidity_percent"]
        rainfall = weather["rainfall_mm"]
        
        # DENGUE
        dengue_mult = 1.0
        if humidity > 80: dengue_mult *= 4.2
        elif humidity > 70: dengue_mult *= 2.5
        if 25 <= temp <= 30: dengue_mult *= 3.5
        if rainfall > 10: dengue_mult *= 3.0
        multipliers["dengue"] = round(dengue_mult, 2)
        
        # MALARIA
        malaria_mult = 1.0
        if humidity > 75: malaria_mult *= 3.1
        if 20 <= temp <= 30: malaria_mult *= 2.8
        multipliers["malaria"] = round(malaria_mult, 2)
        
        # FLU
        flu_mult = 1.0
        if temp < 20: flu_mult *= 1.6
        if humidity < 40: flu_mult *= 1.8
        multipliers["flu"] = round(flu_mult, 2)
        
        return multipliers
    
    async def get_7day_forecast(self, city: str) -> list:
        # Mock forecast for now
        return [self._get_mock_weather(city) for _ in range(7)]
