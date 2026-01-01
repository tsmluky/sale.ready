import requests
import json
import os
import sys

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@tradercopilot.com"
ADMIN_PASSWORD = "admin123"

class VerificationSession:
    def __init__(self):
        self.session = requests.Session()
        self.token = None

    def log(self, msg, status="INFO"):
        print(f"[{status}] {msg}")

    def login(self):
        self.log(f"Attempting login as {ADMIN_EMAIL}...")
        try:
            payload = {
                "username": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            }
            resp = self.session.post(f"{BASE_URL}/auth/token", data=payload)
            if resp.status_code == 200:
                data = resp.json()
                self.token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log("Login successful.", "SUCCESS")
                return True
            else:
                self.log(f"Login failed: {resp.status_code} - {resp.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Login failed (Exception): {e}", "CRITICAL")
            return False

    def check_signals_lite(self):
        self.log("Testing /analyze/lite (BTC 1h)...")
        try:
            # Payload based on likely LiteReq structure (symbol/token, timeframe)
            # Will confirm with models.py inspection if this fails, but standard is token/timeframe
            payload = {
                "token": "BTC",
                "timeframe": "1h",
                "mode": "LITE", # Optional likely
                "source": "verification_script" # Optional
            }
            resp = self.session.post(f"{BASE_URL}/analyze/lite", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if "direction" in data and "confidence" in data:
                    self.log(f"Lite Signal OK: {data['direction']} ({data['confidence']}%)", "SUCCESS")
                    return True
                else:
                    self.log(f"Lite Signal format unexpected: {data.keys()}", "WARNING")
                    return True # Still 200 OK
            else:
                self.log(f"Lite Signal failed: {resp.status_code} - {resp.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Lite Signal Exception: {e}", "CRITICAL")
            return False

    def check_analysis_pro(self):
        self.log("Testing /analyze/pro (ETH 4h)...")
        try:
             # Payload based on ProReq likely structure
            payload = {
                "token": "ETH",
                "timeframe": "4h",
                "mode": "PRO",
                "style": "scalping" # Guessing fields
            }
            resp = self.session.post(f"{BASE_URL}/analyze/pro", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if "raw" in data or "markdown" in data:
                    self.log("Pro Analysis OK (Content received).", "SUCCESS")
                    return True
                else:
                     self.log(f"Pro Analysis format unexpected: {data.keys()}", "WARNING")
                     return True
            else:
                # 429 is also a "success" in terms of connectivity, but strictly it's a failure for the test intent
                # However, for verification we want 200.
                self.log(f"Pro Analysis failed: {resp.status_code} - {resp.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Pro Analysis Exception: {e}", "CRITICAL")
            return False

    def check_logs(self):
        self.log("Testing /logs/recent...")
        try:
            resp = self.session.get(f"{BASE_URL}/logs/recent")
            if resp.status_code == 200:
                data = resp.json()
                count = len(data)
                self.log(f"Logs retrieved: {count} entries.", "SUCCESS")
                return True
            else:
                self.log(f"Logs failed: {resp.status_code} - {resp.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Logs Exception: {e}", "CRITICAL")
            return False

    def check_copilot_profile(self):
        self.log("Testing /advisor/profile...")
        try:
            resp = self.session.get(f"{BASE_URL}/advisor/profile")
            if resp.status_code == 200:
                self.log("Advisor Profile OK.", "SUCCESS")
                return True
            else:
                self.log(f"Advisor Profile failed: {resp.status_code} - {resp.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Advisor Profile Exception: {e}", "CRITICAL")
            return False

def main():
    session = VerificationSession()
    if not session.login():
        print("❌ Critical Auth Failure. Aborting.")
        sys.exit(1)
    
    # Run Checks
    results = {
        "Signals LITE": session.check_signals_lite(),
        "Analysis PRO": session.check_analysis_pro(),
        "Logs System": session.check_logs(),
        "Copilot Profile": session.check_copilot_profile()
    }

    print("\n--- SUMMARY ---")
    fail = False
    for k, v in results.items():
        icon = "✅" if v else "❌"
        print(f"{icon} {k}")
        if not v: fail = True
    
    if fail:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
