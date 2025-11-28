from typing import Dict
import random

class HospitalService:
    """
    Aggregate hospital disease trend data
    """
    
    async def get_disease_trends(self, city: str) -> Dict:
        # Mock data for now
        return {
            "dengue": {
                "case_count": random.randint(100, 500),
                "trend_percentage": random.randint(-10, 30),
                "trend_direction": "increasing"
            },
            "flu": {
                "case_count": random.randint(50, 200),
                "trend_percentage": random.randint(-5, 20),
                "trend_direction": "stable"
            },
            "covid": {
                "case_count": random.randint(200, 800),
                "trend_percentage": random.randint(-15, 10),
                "trend_direction": "decreasing"
            },
            "malaria": {
                "case_count": random.randint(30, 150),
                "trend_percentage": random.randint(-5, 25),
                "trend_direction": "increasing"
            }
        }
