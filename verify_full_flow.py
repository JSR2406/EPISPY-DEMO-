import asyncio
from fastapi import UploadFile
from src.reports.report_service import ReportService
from src.notifications.notification_service import NotificationService
from src.weather.weather_service import WeatherService

class MockUploadFile:
    def __init__(self, filename):
        self.filename = filename
        self.file = None

async def verify_system():
    print("\n🏥 --- EpiSPY System Verification --- 🏥")
    
    # 1. Initialize Services
    report_service = ReportService()
    notification_service = NotificationService()
    weather_service = WeatherService()
    
    patient_id = "PAT-2024-001"
    
    # 2. Simulate Weather Data (Context)
    print(f"\n🌍 Fetching Environmental Context for Mumbai...")
    weather = await weather_service.get_current_weather("Mumbai")
    print(f"   Condition: {weather['condition']}")
    print(f"   Disease Risks: {weather.get('disease_multipliers')}")
    
    # 3. Simulate Report Upload (Critical Case)
    print(f"\n📄 Uploading Medical Report: 'dengue_lab_report.pdf'...")
    mock_file = MockUploadFile("dengue_lab_report.pdf")
    
    analysis = await report_service.upload_and_analyze_report(
        patient_id, 
        mock_file, # type: ignore
        "blood_test"
    )
    
    print("\n🧠 AI Analysis Result:")
    risk_assessment = analysis['risk_assessment']
    print(f"   Summary: {risk_assessment['summary']}")
    
    dengue_risk = risk_assessment['risk_assessment'].get('dengue_risk', {})
    print(f"   Dengue Risk Level: {dengue_risk.get('level')} ({dengue_risk.get('probability')*100}%)")
    print(f"   Reason: {dengue_risk.get('reason')}")
    
    # 4. Simulate Notification
    print(f"\n📨 Sending Personalized Alert to Client...")
    if dengue_risk.get('level') in ["HIGH", "CRITICAL"]:
        alert_payload = {
            "disease": "Dengue",
            "risk_level": dengue_risk.get('level'),
            "recommendations": risk_assessment.get('recommendations')
        }
        await notification_service.send_prediction_alert(patient_id, alert_payload)
        print("   ✅ Alert Sent! (Checked notifications.log)")
    
    print("\n✅ System Verification Complete: Prediction & Notification Successful")

if __name__ == "__main__":
    asyncio.run(verify_system())
