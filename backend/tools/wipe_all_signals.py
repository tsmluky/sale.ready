
import sys
import os
import dotenv
from sqlalchemy import text

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# LOAD ENV manually
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
dotenv.load_dotenv(env_path)

from database import SessionLocal, engine

def wipe_signals():
    print(f"⚠️  DANGER ZONE: Wiping ALL signals from {engine.url}...")
    confirm = input("Are you sure? Type 'yes' to proceed: ")
    if confirm.lower() != "yes":
        print("Aborted.")
        return

    session = SessionLocal()
    try:
        # Cascade delete (Evaluations first)
        print("   Running: DELETE FROM signal_evaluations;")
        session.execute(text("DELETE FROM signal_evaluations;"))
        
        print("   Running: DELETE FROM signals;")
        session.execute(text("DELETE FROM signals;"))
        
        session.commit()
        print("✅ Signals (and evaluations) table wiped successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    wipe_signals()
