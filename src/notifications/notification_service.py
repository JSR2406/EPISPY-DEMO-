from typing import Dict
from datetime import datetime

class NotificationService:
    """
    Multi-channel notification system
    """
    
    def __init__(self):
        self.log_file = "notifications.log"

    async def send_prediction_alert(self, patient_id: str, prediction: Dict):
        message = f"[{datetime.now()}] ALERT to {patient_id}: {prediction.get('disease', 'Health')} risk is {prediction.get('risk_level', 'UNKNOWN')}. {prediction.get('recommendations', [])}"
        print(message)
        self._log_to_file(message)

    async def send_emergency_alert(self, patient_id: str, symptoms: Dict):
        message = f"[{datetime.now()}] EMERGENCY SOS from {patient_id}. Symptoms: {symptoms}"
        print(message)
        self._log_to_file(message)
        
    def _log_to_file(self, message: str):
        with open(self.log_file, "a") as f:
            f.write(message + "\n")
