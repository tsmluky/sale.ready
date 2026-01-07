import sys
import os

# Add parent dir to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models_db import User
from core.security import get_password_hash

def reset_password(email, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User not found: {email}")
            return

        print(f"found user: {user.email}")
        print(f"Old Hash (Potentially Broken): {user.hashed_password}")

        new_hash = get_password_hash(new_password)
        user.hashed_password = new_hash
        db.commit()
        
        print(f"✅ Password updated successfully for {email}")
        print(f"New Hash: {new_hash}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_admin_password.py <email> <new_password>")
        print("Example: python fix_admin_password.py admin@tradercopilot.app mysecurepassword")
    else:
        reset_password(sys.argv[1], sys.argv[2])
