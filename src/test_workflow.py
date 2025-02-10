import requests
import uuid
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:5001"
PASSWORD = "password123"

def generate_unique_user():
    unique_str = str(uuid.uuid4())[:8]
    username = f"alice_{unique_str}"
    email = f"{username}@example.com"
    return username, email

def register_user(username, email):
    url = f"{BASE_URL}/register"
    payload = {"username": username, "password": PASSWORD, "email": email}
    response = requests.post(url, json=payload)
    print("Register response:", response.json())
    return response

def login_user(username):
    url = f"{BASE_URL}/login"
    payload = {"username": username, "password": PASSWORD}
    response = requests.post(url, json=payload)
    data = response.json()
    print("Login response:", data)
    token = data.get("token")
    return token

def submit_timestamp(token):
    url = f"{BASE_URL}/submit_timestamp"
    headers = {"Authorization": f"Bearer {token}"}
    # Get the current UTC time without microseconds
    utc_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "timestamp": utc_timestamp,
        "lat": 50.220564,
        "lng": -4.801677
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Submit Timestamp response:", response.json())

def view_my_data(token):
    url = f"{BASE_URL}/my_data"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print("My Data response:", response.json())

def view_all_data(token):
    url = f"{BASE_URL}/all_data"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    print("All Data response:", response.json())

def main():
    username, email = generate_unique_user()
    register_user(username, email)
    
    token = login_user(username)
    if token:
        submit_timestamp(token)
        view_my_data(token)
        # Attempt to view all data. For a non-admin user, this should return an error.
        view_all_data(token)
    else:
        print("Failed to retrieve token. Aborting.")

if __name__ == "__main__":
    main()
