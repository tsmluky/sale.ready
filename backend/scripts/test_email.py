import os
import sys
import requests
from dotenv import load_dotenv

# Add parent directory to path to find .env if run from scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env explicitly
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

API_KEY = os.getenv("MAILGUN_API_KEY")
DOMAIN = os.getenv("MAILGUN_DOMAIN")
TO_EMAIL = "tsmluky@gmail.com" # Hardcoded for test based on screenshot

print("--- Mailgun Configuration Test ---")
print(f"API Key Found: {'YES' if API_KEY else 'NO'} ({API_KEY[:5]}...)")
print(f"Domain Found:  {'YES' if DOMAIN else 'NO'} ({DOMAIN})")
print(f"Target Email:  {TO_EMAIL}")

if not API_KEY or not DOMAIN:
    print("❌ Critical: Missing Credentials in .env")
    sys.exit(1)

print("\n🚀 Attempting to send test email via Mailgun API...")

try:
    # DETECTED EU REGION in Screenshot -> Switch to EU Endpoint
    endpoint = "https://api.eu.mailgun.net/v3" 
    print(f"🌍 Sending to EU Endpoint: {endpoint}")

    res = requests.post(
        f"{endpoint}/{DOMAIN}/messages",
        auth=("api", API_KEY),
        data={
            "from": f"TraderCopilot Test <postmaster@{DOMAIN}>",
            "to": TO_EMAIL,
            "subject": "TraderCopilot Config Test",
            "text": "If you are reading this, your Mailgun API configuration is CORRECT!"
        },
        timeout=15
    )
    
    print(f"\nResponse Status: {res.status_code}")
    print(f"Response Body:   {res.text}")

    if res.status_code == 200:
        print("\n✅ SUCCESS! The email was accepted by Mailgun.")
        print("Check your inbox (and spam folder).")
    elif res.status_code == 401:
        print("\n❌ ERROR: Unauthorized. Your API Key is likely incorrect.")
    elif res.status_code == 404:
        print("\n❌ ERROR: Not Found. Your Domain might be incorrect or verified on a different region (EU vs US).")
    else:
        print("\n⚠️ ERROR: Mailgun rejected the request.")

except Exception as e:
    print(f"\n❌ EXCEPTION: Could not connect to Mailgun: {e}")
