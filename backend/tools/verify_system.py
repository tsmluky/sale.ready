
import sys
import os

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.append(backend_root)

from database import SessionLocal
from models_db import User, Signal
from routers.analysis import _analyze_lite_unsafe
from models import LiteReq

def verify_system():
    print("🚀 Verifying System Integrity...")
    
    db = SessionLocal()
    try:
        # 1. Get or Create Test User
        user = db.query(User).filter(User.email == "test@verify.com").first()
        if not user:
            print("[INFO] Creating test user...")
            user = User(email="test@verify.com", name="Test User", role="user", plan="PRO")
            db.add(user)
            db.commit()
            db.refresh(user)
        
        print(f"✅ User ID: {user.id}")
        
        # 2. Simulate Lite Analysis
        print("[INFO] Running Lite Analysis (BTC 30m)...")
        req = LiteReq(token="BTC", timeframe="30m")
        
        try:
            result = _analyze_lite_unsafe(req, user)
            print(f"✅ Analysis Success. Direction: {result['direction']}")
        except Exception as e:
            print(f"❌ Analysis Failed: {e}")
            return
            
        # 3. Verify DB Persistence with User ID
        # Wait a bit or query immediately (sync)
        sig = db.query(Signal).filter(Signal.token == "BTC", Signal.user_id == user.id).order_by(Signal.id.desc()).first()
        
        if sig:
            print(f"✅ Signal Saved to DB! ID: {sig.id}")
            print(f"   - User ID: {sig.user_id}")
            print(f"   - Timestamp: {sig.timestamp}")
            print(f"   - Strategy: {sig.strategy_id}")
        else:
            print("❌ Signal NOT found in DB. Logic Error.")
            
        # 4. Verify CSV
        csv_path = os.path.join(backend_root, "logs", "LITE", "btc.csv")
        if os.path.exists(csv_path):
             print(f"✅ CSV Log found: {csv_path}")
        else:
             print("⚠️ CSV Log not found (might differ based on mode).")

    except Exception as e:
        print(f"❌ Verification Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_system()
