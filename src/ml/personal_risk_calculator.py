from typing import Dict, List
import numpy as np

class PersonalRiskCalculator:
    """
    Calculate personalized health risks
    """
    
    async def calculate_comprehensive_risk(
        self,
        patient_id: str,
        city: str
    ) -> Dict:
        from ..weather.weather_service import WeatherService
        from ..hospital.hospital_service import HospitalService
        
        weather_service = WeatherService()
        hospital_service = HospitalService()
        
        # 1. Get Context Data
        weather = await weather_service.get_current_weather(city)
        hospital_trends = await hospital_service.get_disease_trends(city)
        
        # 2. Calculate Base Risks
        base_risks = self._calculate_base_risks(weather, hospital_trends)
        
        # 3. Personalize (Mock for now)
        predictions = self._generate_predictions(base_risks)
        
        return {
            "patient_id": patient_id,
            "predictions": predictions,
            "weather_impact": weather
        }
    
    def _calculate_base_risks(self, weather: Dict, hospital_trends: Dict) -> Dict:
        risks = {}
        weather_multipliers = weather.get("disease_multipliers", {})
        
        for disease, trend_data in hospital_trends.items():
            trend_factor = 1 + (trend_data["trend_percentage"] / 100)
            weather_mult = weather_multipliers.get(disease, 1.0)
            
            base_risk = trend_factor * weather_mult
            risks[disease] = {
                "base_probability": min(base_risk * 0.1, 0.95),
                "risk_level": "HIGH" if base_risk * 0.1 > 0.5 else "LOW"
            }
        return risks

    def _generate_predictions(self, risks: Dict) -> List[Dict]:
        predictions = []
        for disease, data in risks.items():
            predictions.append({
                "disease": disease,
                "probability": data["base_probability"],
                "risk_level": data["risk_level"],
                "recommendations": [f"Monitor for {disease} symptoms"]
            })
        return predictions
