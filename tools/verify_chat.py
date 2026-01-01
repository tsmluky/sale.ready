import requests
import json
import sys

BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@tradercopilot.com"
ADMIN_PASSWORD = "admin123"

def verify_chat():
    print("[-] Logging in...")
    resp = requests.post(f"{BASE_URL}/auth/token", data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if resp.status_code != 200:
        print(f"[!] Login failed: {resp.text}")
        sys.exit(1)
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("[-] Sending Chat Message...")
    chat_payload = {
        "messages": [{"role": "user", "content": "Analyze BTC status"}],
        "context": {"token": "BTC", "timeframe": "1h"}
    }
    
    # Endpoint is /advisor/chat
    chat_resp = requests.post(f"{BASE_URL}/advisor/chat", json=chat_payload, headers=headers)
    
    if chat_resp.status_code == 200:
        print(f"[+] Chat Response: {chat_resp.json()}")
    elif chat_resp.status_code == 404:
        # Try alternate path if refactored
        print("[-] /advisor/chat not found, trying /copilot/chat...")
        chat_resp = requests.post(f"{BASE_URL}/copilot/chat", json=chat_payload, headers=headers)
        print(f"[{'+' if chat_resp.status_code == 200 else '!'}] Alternate Response: {chat_resp.status_code} - {chat_resp.text}")
    else:
        print(f"[!] Chat Failed: {chat_resp.status_code} - {chat_resp.text}")

if __name__ == "__main__":
    verify_chat()
