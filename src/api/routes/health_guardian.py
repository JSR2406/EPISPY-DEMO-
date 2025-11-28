from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from src.agents.health_guardian_agent import HealthAgents
from src.utils.logger import api_logger
from src.integrations.weather_service import WeatherService

router = APIRouter()

# Instantiate globally
health_agents = HealthAgents()
weather_service = WeatherService()

class HealthInput(BaseModel):
    age: int
    bmi: float
    bp_systolic: int
    symptoms: str
    location: Optional[str] = "New York"

class PredictionResponse(BaseModel):
    risks: Dict[str, float]
    recommendations: str
    processed_symptoms: str
    analysis: Optional[str] = None

@router.post("/predict", response_model=PredictionResponse)
async def predict_health_risks(input_data: HealthInput):
    try:
        # Fetch weather if location is provided
        weather_context = None
        if input_data.location:
            weather_context = weather_service.get_weather(input_data.location)
            if weather_context:
                api_logger.info(f"Weather fetched for {input_data.location}: {weather_context}")

        result = health_agents.run_agent_swarm(
            age=input_data.age,
            bmi=input_data.bmi,
            bp_systolic=input_data.bp_systolic,
            symptoms=input_data.symptoms,
            weather_context=weather_context
        )
        return result
    except Exception as e:
        api_logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
