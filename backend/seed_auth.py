import sys
import os
from database import SessionLocal
from models_db import User
from core.security import get_password_hash

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def seed_admin_user():
    print("--- [SEED AUTH] ensuring Admin User exists ---")
    db = SessionLocal()
    
    email = "admin@tradercopilot.com"
    # Basic password for MVP - in prod this should be changed immediately
    password_plain = "admin123" 
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Creating NEW Admin user: {email}")
            user = User(
                email=email,
                name="System Admin",
                hashed_password=get_password_hash(password_plain),
                role="admin",
                plan="OWNER",
                plan_status="active"
            )
            db.add(user)
            db.commit()
            print("✅ Admin created successfully.")
        else:
            print(f"ℹ️ Admin user already exists: {email}")
            # FORCE PASSWORD RESET (Verification Fix)
            print(f"  -> Resetting password to default: {password_plain}")
            user.hashed_password = get_password_hash(password_plain)
            
            # ENFORCE OWNER PLAN (Crucial for tests)
            if user.plan != "OWNER":
                print(f"  -> Upgrading plan from {user.plan} to OWNER")
                user.plan = "OWNER"
            
            db.commit()
            
    except Exception as e:
        print(f"❌ Error seeding admin: {e}")
        db.rollback()
    finally:
        db.close()

def seed_free_user():
    print("--- [SEED AUTH] ensuring Free User exists ---")
    db = SessionLocal()
    email = "test@tradercopilot.com"
    try:
        if not db.query(User).filter(User.email == email).first():
            print(f"Creating FREE user: {email}")
            u = User(
                email=email,
                name="Test Free",
                hashed_password=get_password_hash("test1234"),
                role="user",
                plan="FREE",
                plan_status="active"
            )
            db.add(u)
            db.commit()
            print("✅ Free user created.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_admin_user()
    seed_free_user()

