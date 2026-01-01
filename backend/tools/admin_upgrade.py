import sys
import os
import argparse
from database import SessionLocal
from models_db import User

# Setup path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def upgrade_user(email: str, plan: str):
    print(f"--- [ADMIN] Upgrading {email} to {plan} ---")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return
        
        user.plan = plan.upper()
        if user.plan == "FREE":
            user.subscription_status = "inactive" # or active-free
        else:
            user.subscription_status = "active"
            
        db.commit()
        print(f"✅ User {user.email} upgraded to {user.plan}.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upgrade User Plan")
    parser.add_argument("email", type=str, help="User Email")
    parser.add_argument("plan", type=str, choices=["FREE", "PRO", "OWNER"], help="New Plan")
    
    args = parser.parse_args()
    upgrade_user(args.email, args.plan)
