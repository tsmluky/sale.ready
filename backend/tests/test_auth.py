import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"
REGISTER_URL = f"{BASE_URL}/auth/register"

def test_registration():
    print("=== TEST START: Registration Flow ===")
    
    # Generate unique email
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_{unique_id}@example.com"
    
    payload = {
        "email": email,
        "password": "password123",
        "name": f"Test User {unique_id}"
    }
    
    # 1. Successful Registration
    print(f"\n[TEST 1] Testing Valid Registration: {email}")
    try:
        res = requests.post(REGISTER_URL, json=payload)
        print(f"Status: {res.status_code}")
        if res.status_code == 201:
            print("PASS: User created successfully.")
            print(json.dumps(res.json(), indent=2))
        else:
            print("FAIL: Expected 201")
            print(res.text)
    except Exception as e:
        print(f"CRASH: {e}")

    # 2. Duplicate Registration
    print(f"\n[TEST 2] Testing Duplicate Registration: {email}")
    try:
        res = requests.post(REGISTER_URL, json=payload)
        print(f"Status: {res.status_code}")
        if res.status_code == 409:
            print("PASS: Correctly rejected duplicate.")
        else:
            print(f"FAIL: Expected 409, got {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"CRASH: {e}")
        
    # 3. Invalid Email Format
    print(f"\n[TEST 3] Testing Invalid Email Format")
    bad_payload = {
        "email": "not-an-email",
        "password": "password123",
        "name": "Bad Email User"
    }
    try:
        res = requests.post(REGISTER_URL, json=bad_payload)
        print(f"Status: {res.status_code}")
        if res.status_code == 422:
            print("PASS: Correctly rejected invalid email.")
            print(json.dumps(res.json(), indent=2))
        else:
            print(f"FAIL: Expected 422, got {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"CRASH: {e}")

    print("\n=== TEST END ===")

if __name__ == "__main__":
    test_registration()
