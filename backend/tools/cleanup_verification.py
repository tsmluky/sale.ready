
import sys
import os

# Setup Paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.dirname(current_dir)
sys.path.append(backend_root)

from database import SessionLocal
from models_db import User, Signal, SignalEvaluation

def cleanup():
    print("🧹 Cleaning up verification artifacts...")
    db = SessionLocal()
    try:
        # Find test user
        user = db.query(User).filter(User.email == "test@verify.com").first()
        if user:
            print(f"   - Found Test User (ID: {user.id}). Removing data...")
            
            # Delete Evaluations linked to user's signals
            # Subquery or join delete might be complex in pure ORM without cascade, so manual step:
            # First find signals
            signals = db.query(Signal).filter(Signal.user_id == user.id).all()
            sig_ids = [s.id for s in signals]
            
            if sig_ids:
                del_evals = db.query(SignalEvaluation).filter(SignalEvaluation.signal_id.in_(sig_ids)).delete(synchronize_session=False)
                print(f"     - Deleted {del_evals} evaluations.")
                
                del_sigs = db.query(Signal).filter(Signal.user_id == user.id).delete(synchronize_session=False)
                print(f"     - Deleted {del_sigs} signals.")
            
            # Delete User
            db.delete(user)
            db.commit()
            print("✅ Test User and linked data removed.")
        else:
            print("   - No Test User found. Already clean.")
            
    except Exception as e:
        print(f"❌ Cleanup Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
