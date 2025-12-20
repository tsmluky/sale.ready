import requests
import json

BASE_URL = "https://tradercopilot-mvpfinal-production.up.railway.app"

def check_probe():
    print("\n--- Testing /auth/probe_deployment ---")
    try:
        r = requests.get(f"{BASE_URL}/auth/probe_deployment")
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_register():
    print("--- Testing /auth/register ---")
    # Trying a valid payload first
    payload = {
        "email": "test_debug_trace@example.com",
        "password": "password123",
        "name": "Debug User"
    }
    print(f"Sending payload: {payload}")
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=payload)
        print(f"Status: {r.status_code}")
        try:
            print(f"Response JSON: {json.dumps(r.json(), indent=2)}")
        except:
            print(f"Response Text: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

def check_system_config():
    print("\n--- Testing /system/config ---")
    try:
        r = requests.get(f"{BASE_URL}/system/config")
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}") # Truncate if long html
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_probe()
    test_register()
    check_system_config()
