
import sqlite3
import os
from datetime import datetime

# Path to database. 
# backend/database.py typically uses "dev_local.db" in the root or backend folder.
# We will check both.

# Prioritize backend/dev_local.db as it is the most likely active one based on file listings
DB_NAMES = ["backend/dev_local.db", "dev_local.db", "backend/dev.db", "dev.db"]

def get_db_path():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    for name in DB_NAMES:
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return None

def clean_duplicates_sql():
    db_path = get_db_path()
    if not db_path:
        print("❌ Could not find database file.")
        return

    print(f"📦 Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all signals
        # We assume columns: id, strategy_id, token, timeframe, direction, timestamp
        cursor.execute("SELECT id, strategy_id, token, timeframe, direction, timestamp FROM signals ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        print(f"🔍 Scanned {len(rows)} signals.")
        
        seen = set()
        ids_to_delete = []
        
        for row in rows:
            sig_id = row[0]
            strategy_id = row[1]
            token = row[2]
            timeframe = row[3]
            direction = row[4]
            timestamp_str = row[5]
            
            # Timestamp might be string in SQLite
            # Simplistic 1-minute dedup key
            try:
                # Truncate to minute
                # Format usually: YYYY-MM-DD HH:MM:SS.ssssss
                if timestamp_str:
                    ts_key = timestamp_str[:16] # "2023-01-01 12:00"
                else:
                    ts_key = "none"
            except:
                ts_key = str(timestamp_str)
                
            key = (strategy_id, token, timeframe, direction, ts_key)
            
            if key in seen:
                ids_to_delete.append(sig_id)
            else:
                seen.add(key)

        print(f"🗑️ Found {len(ids_to_delete)} duplicates.")
        
        if ids_to_delete:
            # Delete in batches
            batch_size = 900
            for i in range(0, len(ids_to_delete), batch_size):
                batch = ids_to_delete[i:i+batch_size]
                placeholders = ',' .join('?' * len(batch))
                cursor.execute(f"DELETE FROM signals WHERE id IN ({placeholders})", batch)
                print(f"   Deleted batch {i}-{i+len(batch)}")
            
            conn.commit()
            print("✅ Deduplication complete.")
        else:
            print("✨ Clean.")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clean_duplicates_sql()
