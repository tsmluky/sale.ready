from datetime import datetime
try:
    from pydantic import BaseModel, Field
    
    print("Pydantic imported.")
    import pydantic
    print(f"Pydantic Version: {pydantic.VERSION}")

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
