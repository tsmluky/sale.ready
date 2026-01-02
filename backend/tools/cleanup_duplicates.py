
import sys
import os
from datetime import datetime, timedelta

# Ensure we can import from backend root (where 'database.py' and 'core/' exist)
# Script: backend/tools/cleanup_duplicates.py
# Needed Path: backend/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from database import SessionLocal, engine
from models_db import Signal # ORM Model

def clean_duplicates():
    session = SessionLocal()
    try:
        print("Starting duplicate cleanup...")
        
        # 1. Fetch identifying fields only (avoid 'extra' column error if schema drift)
        # Order by timestamp desc
        all_signals = session.query(
            Signal.id,
            Signal.timestamp,
            Signal.strategy_id,
            Signal.token,
            Signal.timeframe,
            Signal.direction
        ).order_by(Signal.timestamp.desc()).all()
        
        seen = set()
        to_delete = []
        
        for sig in all_signals:
            # Key for duplication: Strategy + Token + Timeframe + Direction + Timestamp (rounded to minute)
            # Rounding to minute catches slightly offset executions of exact same candle
            ts_key = sig.timestamp.strftime("%Y-%m-%d %H:%M")
            
            key = (sig.strategy_id, sig.token, sig.timeframe, sig.direction, ts_key)
            
            if key in seen:
                to_delete.append(sig.id)
            else:
                seen.add(key)
        
        print(f"Found {len(to_delete)} duplicates out of {len(all_signals)} total signals.")
        
        if to_delete:
            # Batch delete
            session.query(Signal).filter(Signal.id.in_(to_delete)).delete(synchronize_session=False)
            session.commit()
            print("Successfully deleted duplicates.")
        else:
            print("No duplicates found.")
            
    except Exception as e:
        session.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    clean_duplicates()
