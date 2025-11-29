from fastapi import UploadFile
import json
import os
from typing import Dict
# import pytesseract # Commented out until tesseract is installed on system
# from PIL import Image
# import io

class ReportService:
    """
    Upload, OCR, and AI-analyze medical reports
    """
    
    async def upload_and_analyze_report(
        self,
        patient_id: str,
        file: UploadFile,
        report_type: str
    ) -> Dict:
        # 1. Mock Upload
        file_url = f"https://mock-s3.amazonaws.com/reports/{patient_id}/{file.filename}"
        
        # 2. Mock OCR & Analysis (Dynamic based on filename for demo)
        filename_lower = file.filename.lower()
        
        if "dengue" in filename_lower or "platelet" in filename_lower:
            extracted_data = {
                "hemoglobin": 14.0,
                "platelet_count": 45000, # Critical low
                "wbc_count": 3500, # Low
                "hematocrit": 45
            }
            ai_analysis = {
                "risk_assessment": {
                    "dengue_risk": {"level": "CRITICAL", "probability": 0.92, "reason": "Severe Thrombocytopenia detected"},
                    "internal_bleeding_risk": {"level": "HIGH", "probability": 0.75}
                },
                "summary": "CRITICAL ALERT: Platelet count is dangerously low (45,000). High probability of Dengue Hemorrhagic Fever.",
                "recommendations": [
                    "IMMEDIATE hospitalization required",
                    "Monitor for bleeding gums or nose",
                    "Do NOT take Aspirin or Ibuprofen",
                    "Hydrate with ORS immediately"
                ]
            }
        elif "malaria" in filename_lower:
            extracted_data = {
                "hemoglobin": 10.2,
                "platelet_count": 110000,
                "parasite_density": "High",
                "wbc_count": 5500
            }
            ai_analysis = {
                "risk_assessment": {
                    "malaria_risk": {"level": "HIGH", "probability": 0.88, "reason": "Plasmodium parasites detected"},
                    "anemia_risk": {"level": "MODERATE", "probability": 0.45}
                },
                "summary": "Positive for Malaria. Moderate anemia observed.",
                "recommendations": [
                    "Start Antimalarial medication as prescribed",
                    "Monitor body temperature every 4 hours",
                    "Increase iron intake"
                ]
            }
        else:
            # Normal/Healthy Report
            extracted_data = {
                "hemoglobin": 13.5,
                "platelet_count": 250000,
                "wbc_count": 7000,
                "blood_sugar": 95
            }
            ai_analysis = {
                "risk_assessment": {
                    "general_health": {"level": "GOOD", "probability": 0.95},
                    "infection_risk": {"level": "LOW", "probability": 0.05}
                },
                "summary": "All vital parameters are within normal range. No significant health risks detected.",
                "recommendations": [
                    "Maintain current healthy lifestyle",
                    "Regular annual checkup recommended",
                    "Stay hydrated"
                ]
            }
        
        return {
            "report_id": "rep-" + os.urandom(4).hex(),
            "file_url": file_url,
            "extracted_data": extracted_data,
            "risk_assessment": ai_analysis, # Renamed for frontend consistency
            "status": "completed"
        }
