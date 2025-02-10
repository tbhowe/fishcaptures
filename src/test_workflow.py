import requests
import uuid
import argparse
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:5001"
PASSWORD = "password123"

def generate_unique_user():
    unique_str = str(uuid.uuid4())[:8]
    username = f"alice_{unique_str}"
    email = f"{username}@example.com"
    return username, email

def register_user(username, email, is_admin=False):
    url = f"{BASE_URL}/register"
    payload = {"username": username, "password": PASSWORD, "email": email}
    if is_admin:
        payload["is_admin"] = True
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
    parser = argparse.ArgumentParser(description="Test workflow for user or admin")
    parser.add_argument("--admin", action="store_true", help="Run admin workflow")
    args = parser.parse_args()

    if args.admin:
        # Admin workflow using fixed credentials.
        admin_username = "admin"
        admin_email = "admin@example.com"
        # Try logging in first.
        token = login_user(admin_username)
        if not token:
            print("Admin login failed, attempting to register admin.")
            register_user(admin_username, admin_email, is_admin=True)
            token = login_user(admin_username)
        if token:
            submit_timestamp(token)
            view_my_data(token)
            view_all_data(token)
        else:
            print("Failed to retrieve admin token. Aborting.")
    else:
        # Normal user workflow.
        username, email = generate_unique_user()
        register_user(username, email)
        token = login_user(username)
        if token:
            submit_timestamp(token)
            view_my_data(token)
            # For a non-admin, this should return an error.
            view_all_data(token)
        else:
            print("Failed to retrieve token. Aborting.")

if __name__ == "__main__":
    main()
