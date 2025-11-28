from fastapi import APIRouter, HTTPException
from .weather_service import WeatherService

router = APIRouter(prefix="/api/weather", tags=["Weather"])

@router.get("/{city}")
async def get_weather(city: str):
    weather_service = WeatherService()
    try:
        weather = await weather_service.get_current_weather(city)
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather fetch failed: {str(e)}")

@router.get("/{city}/forecast")
async def get_forecast(city: str):
    weather_service = WeatherService()
    try:
        forecast = await weather_service.get_7day_forecast(city)
        return {"city": city, "forecast": forecast}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast fetch failed: {str(e)}")
