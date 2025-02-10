import requests

BASE_URL = "http://127.0.0.1:5001"
USERNAME = "alice"
PASSWORD = "password123"
EMAIL = "alice@example.com"

def register_user():
    url = f"{BASE_URL}/register"
    payload = {"username": USERNAME, "password": PASSWORD, "email": EMAIL}
    response = requests.post(url, json=payload)
    print("Register response:", response.json())
    return response

def login_user():
    url = f"{BASE_URL}/login"
    payload = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(url, json=payload)
    data = response.json()
    print("Login response:", data)
    token = data.get("token")
    return token

def submit_timestamp(token):
    url = f"{BASE_URL}/submit_timestamp"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "timestamp": "2025-02-10T08:00:00",
        "lat": 50.220564,
        "lng": -4.801677
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Submit Timestamp response:", response.json())

def main():
    # Optionally register a user (if already registered this may fail; ignore error)
    register_user()
    
    token = login_user()
    if token:
        submit_timestamp(token)
    else:
        print("Failed to retrieve token. Aborting.")

if __name__ == "__main__":
    main()
