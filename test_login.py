import requests

def test_login():
    url = "http://localhost:8000/api/auth/login"
    payload = {
        "email": "test@epispy.ai",
        "password": "Test@1234"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
