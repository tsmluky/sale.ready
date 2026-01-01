import requests
import json
import sys

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@tradercopilot.com"
ADMIN_PASSWORD = "admin123"

def debug_lite():
    # Login
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Lite Request
    payload = {
        "token": "BTC",
        "timeframe": "1h",
        "mode": "LITE"
    }
    print(f"Sending payload: {payload}")
    resp = requests.post(f"{BASE_URL}/analyze/lite", json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")

if __name__ == "__main__":
    debug_lite()
