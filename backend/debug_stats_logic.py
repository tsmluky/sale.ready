from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker, declarative_base
from models_db import Signal, SignalEvaluation, User
from datetime import datetime, timedelta

# Mock Database
import os
DB_PATH = "dev_local.db"
DATABASE_URL = f"sqlite:///./{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Mock User
class MockUser:
    id = 9
    created_at = datetime.utcnow() - timedelta(days=30) 

def test_query():
    user = MockUser()
    test_sources = ['audit_script', 'verification']
    day_ago = datetime.utcnow() - timedelta(hours=24)
    
    # Replicate apply_filters exactly as in main.py (visually checked)
    # I will try to replicate the indentation structure I assume exists
    
    # Query Base
    q_lite = db.query(func.count(Signal.id))
    
    # Apply Filters Logic
    q_lite = q_lite.filter(Signal.source.notin_(test_sources))
    q_lite = q_lite.filter(Signal.source.notlike('lite-rule%'))
    
    if user:
        if user.created_at:
             q_lite = q_lite.filter(Signal.timestamp >= user.created_at)
        
        q_lite = q_lite.filter(or_(Signal.user_id == user.id, Signal.user_id == None))
    
    # Hypothetically this is where indentation matters.
    # If I put it here (inside if user, effectively)
    q_lite_filtered = q_lite.filter(Signal.is_saved == 1)
    
    print("--- Query with is_saved=1 ---")
    print(str(q_lite_filtered))
    count = q_lite_filtered.filter(Signal.timestamp >= day_ago, Signal.mode == 'LITE').scalar()
    print(f"Result Count: {count}")
    
    # Query WITHOUT is_saved=1 (just to verify the 24 number)
    print("\n--- Query WITHOUT is_saved filter ---")
    active_q = q_lite.filter(Signal.timestamp >= day_ago, Signal.mode == 'LITE')
    count_raw = active_q.scalar()
    print(f"Result Count (Raw): {count_raw}")

if __name__ == "__main__":
    try:
        test_query()
    except Exception as e:
        print(e)
    finally:
        db.close()
