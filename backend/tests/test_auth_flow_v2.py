import sys
import os
import random
import string

sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ["DATABASE_URL"] = "sqlite:///./dev_local.db"
os.environ["AI_PROVIDER"] = "deepseek" # Force DeepSeek or dummy to avoid Gemini failing in test if key missing
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_auth_flow_complete():
    # 1. Register (Randomize to avoid conflict)
    rand_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    email = f"test_auth_{rand_suffix}@example.com"
    password = "password123"
    
    print(f"Registering {email}...")
    reg_payload = {
        "email": email,
        "password": password,
        "name": "Auth Tester"
    }
    response = client.post("/auth/register", json=reg_payload)
    assert response.status_code == 201, f"Register failed: {response.text}"

    # 2. Login
    login_data = {
        "username": email,
        "password": password
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    assert token is not None

    # 3. Verify Advisor Access (Protected)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/advisor/profile", headers=headers)
    assert response.status_code == 200, f"Profile access failed: {response.text}"
    
    # 4. Verify Context Endpoint (Requires Auth)
    response = client.get("/auth/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == email
