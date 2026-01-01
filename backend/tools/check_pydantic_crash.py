from datetime import datetime
from fastapi.testclient import TestClient
from main import app
from core.security import create_access_token
from datetime import timedelta
try:
    from pydantic import BaseModel
    
    print("Pydantic imported.")
    import pydantic
    print(f"Pydantic Version: {pydantic.VERSION}")

    client = TestClient(app)

    def trigger_crash():
        # 1. Generate a valid token for the user we know exists
        token = create_access_token(
            data={"sub": "tsmluky@gmail.com"}, 
            expires_delta=timedelta(minutes=5)
        )
        print(f"Generated Token: {token[:20]}...")
        
        # 2. Hit the endpoint
        print("Sending Request to /auth/users/me ...")
        try:
            response = client.get(
                "/auth/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print("CRASH CAUGHT IN CLIENT:")
            import traceback
            traceback.print_exc()
            with open("manual_crash.txt", "w") as f:
                f.write(str(e) + "\n")
                f.write(traceback.format_exc())

    if __name__ == "__main__":
        trigger_crash()

    class UserResponse(BaseModel):
        id: int
        email: str
        created_at: datetime
        
        class Config:
            from_attributes = True

    print("UserResponse class defined successfully.")
    
    # Test if it actually works or ignores it
    print(f"Config from_attributes: {getattr(UserResponse.Config, 'from_attributes', 'Not Found')}")
    print(f"Config orm_mode: {getattr(UserResponse.Config, 'orm_mode', 'Not Found')}")

except Exception as e:
    print(f"CRASH: {e}")
