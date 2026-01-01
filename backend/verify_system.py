import requests

BASE_URL = "http://localhost:8000"

def check(name, url):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            print(f"[PASS] {name}: 200 OK")
            return True
        else:
            print(f"[FAIL] {name}: {res.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False

def check_json(name, url, key=None):
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if key and key not in str(data):
                print(f"[WARN] {name}: Key '{key}' not found in response")
            print(f"[PASS] {name}: Valid JSON")
            return True
        else:
            print(f"[FAIL] {name}: {res.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] {name}: {e}")
        return False

print("=== TraderCopilot System Verification ===")
check("Backend Health", f"{BASE_URL}/health")
check_json("Marketplace Strategies", f"{BASE_URL}/strategies/marketplace")
check_json("System Config", f"{BASE_URL}/system/config")

# Check if public endpoints are up
check("Logs Endpoint (Auth Required - Expect 401)", f"{BASE_URL}/logs/recent") 

# Wait, logs might be protected.
try:
    res = requests.get(f"{BASE_URL}/logs/recent", timeout=5)
    if res.status_code in [200, 401, 403]:
        print(f"[PASS] Logs Endpoint: Reachable ({res.status_code})")
    else:
        print(f"[FAIL] Logs Endpoint: {res.status_code}")
except Exception:
    print("[FAIL] Logs Endpoint: Connection Error")

print("=== Verification Complete ===")
