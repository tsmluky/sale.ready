import os
import requests
from dotenv import load_dotenv

# Load env from .env file explicitly
load_dotenv(".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")
API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

print("--- DeepSeek Verification ---")
print(f"API URL: {API_URL}")
print(f"Model: {MODEL}")
if API_KEY:
    masked_key = f"{API_KEY[:4]}...{API_KEY[-4:]}"
    print(f"API Key: Present ({masked_key})")
else:
    print("API Key: MISSING ❌")
    exit(1)

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "Say 'DeepSeek Online' in Spanish."}
    ],
    "max_tokens": 10
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

try:
    print("Sending request...")
    resp = requests.post(API_URL, json=payload, headers=headers, timeout=10)
    print(f"Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        content = data['choices'][0]['message']['content']
        print(f"Response: {content}")
        print("✅ SUCCESS: DeepSeek API is working.")
    else:
        print(f"❌ FAILED: {resp.text}")

except Exception as e:
    print(f"❌ EXCEPTION: {e}")
