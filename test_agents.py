import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
WEATHER_URL = "http://localhost:8000/api/weather"

def test_weather_agent():
    print("\n--- Testing Weather Agent ---")
    try:
        response = requests.get(f"{WEATHER_URL}/Mumbai")
        if response.status_code == 200:
            data = response.json()
            print("✅ Weather Agent Active")
            print(f"   Condition: {data.get('condition')}")
            print(f"   Temp: {data.get('temperature_celsius')}°C")
            print(f"   Risk Multipliers: {json.dumps(data.get('disease_multipliers'), indent=2)}")
        else:
            print(f"❌ Weather Agent Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Weather Agent Error: {e}")

def test_health_check():
    print("\n--- Testing System Health ---")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ API Gateway Active")
            print(f"   Status: {response.json().get('status')}")
        else:
            print(f"❌ API Gateway Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Gateway Error: {e}")

if __name__ == "__main__":
    test_health_check()
    test_weather_agent()
