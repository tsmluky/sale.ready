
import sqlite3
import os
from datetime import datetime, timedelta

# Find DB
DB_NAMES = ["backend/dev_local.db", "dev_local.db", "backend/dev.db"]
def get_db_path():
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    for name in DB_NAMES:
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return None

def clean_aggressive():
    db_path = get_db_path()
    if not db_path:
        print("❌ DB not found.")
        return

    print(f"📦 DB: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all signals sorted by time
        cursor.execute("SELECT id, strategy_id, token, direction, timestamp FROM signals ORDER BY timestamp ASC")
        rows = cursor.fetchall()
        
        to_delete = []
        # Check against recent history
        # Key: (strategy, token, direction) -> last_timestamp
        last_seen = {}
        
        for row in rows:
            sid, strat, token, direction, ts_str = row
            
            # Parse TS
            try:
                # Handle ISO format or space separated
                if "T" in ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", ""))
                else:
                    ts = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
            except:
                # Fallback
                continue
                
            key = (strat, token, direction)
            
            if key in last_seen:
                last_ts = last_seen[key]
                # If within 2 hours, it's a dupe/spam
                if ts - last_ts < timedelta(hours=2):
                    to_delete.append(sid)
                    continue # Don't update last_ts, keep the first one as anchor
            
            # Update anchor
            last_seen[key] = ts

        print(f"🗑️ Found {len(to_delete)} signals to assume as duplicates (within 2h window).")
        
        if to_delete:
            batch_size = 900
            for i in range(0, len(to_delete), batch_size):
                batch = to_delete[i:i+batch_size]
                placeholders = ',' .join('?' * len(batch))
                cursor.execute(f"DELETE FROM signals WHERE id IN ({placeholders})", batch)
            conn.commit()
            print("✅ Deleted.")
        else:
            print("✨ Clean.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_aggressive()
