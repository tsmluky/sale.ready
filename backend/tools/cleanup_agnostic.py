
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import text

# Setup paths
import dotenv
# Setup paths - Add 'backend' folder to sys.path so 'database.py' is found as top-level module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# LOAD ENV manually since database.py doesn't do it
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../.env'))
dotenv.load_dotenv(env_path)

from database import SessionLocal, engine
from models_db import Signal

def clean_agnostic():
    print(f"📦 Database URL: {engine.url}")
    session = SessionLocal()
    try:
        # Fetch all signals sorted primarily by timestamp
        # attributes: id, strategy_id, token, direction, timestamp
        query = text("""
            SELECT id, strategy_id, token, direction, timestamp 
            FROM signals 
            ORDER BY timestamp ASC
        """)
        
        result = session.execute(query)
        rows = result.fetchall()
        
        print(f"🔍 Scanned {len(rows)} signals.")
        
        to_delete = []
        last_seen = {} # (strategy_id, token, direction) -> timestamp
        
        count_dupes = 0
        
        for row in rows:
            # row is tuple-like
            s_id = row[0]
            strat = row[1]
            tok = row[2]
            direction = row[3]
            ts = row[4]
            
            # Ensure ts is datetime
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", ""))
                except:
                    continue
            
            key = (strat, tok, direction)
            
            if key in last_seen:
                prev_ts = last_seen[key]
                # If within 2 hours of previous signal
                if ts - prev_ts < timedelta(hours=2):
                    to_delete.append(s_id)
                    count_dupes += 1
                    continue
            
            # Update last seen
            last_seen[key] = ts
            
        print(f"🗑️ Found {len(to_delete)} duplicates (Aggressive 2h window).")
        
        if to_delete:
            # Delete in chunks
            chunk_size = 500
            for i in range(0, len(to_delete), chunk_size):
                chunk = to_delete[i:i+chunk_size]
                # Convert list to string for SQL IN clause
                # safe usage since we know they are IDs
                ids_str = ",".join(str(x) for x in chunk)
                del_sql = text(f"DELETE FROM signals WHERE id IN ({ids_str})")
                session.execute(del_sql)
                session.commit()
                print(f"   Deleted chunk {i}")
            
            print("✅ Cleanup Complete.")
        else:
            print("✨ Clean.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    clean_agnostic()
