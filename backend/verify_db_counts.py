import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "dev_local.db"

def verify_counts():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=== Database Verification ===")
        
        # 1. Total Signals
        cursor.execute("SELECT COUNT(*) FROM signals")
        total = cursor.fetchone()[0]
        print(f"Total Signals: {total}")
        
        # 2. Signals by is_saved
        cursor.execute("SELECT is_saved, COUNT(*) FROM signals GROUP BY is_saved")
        print("Signals by is_saved status:")
        for row in cursor.fetchall():
            print(f"  is_saved={row[0]}: {row[1]}")
            
        # 3. Signals in last 24h (LITE)
        day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        cursor.execute(f"SELECT COUNT(*) FROM signals WHERE timestamp >= '{day_ago}' AND mode='LITE'")
        lite_24h_total = cursor.fetchone()[0]
        print(f"LITE Signals (Last 24h, Total): {lite_24h_total}")
        
        cursor.execute(f"SELECT COUNT(*) FROM signals WHERE timestamp >= '{day_ago}' AND mode='LITE' AND is_saved=1")
        lite_24h_saved = cursor.fetchone()[0]
        print(f"LITE Signals (Last 24h, Saved=1): {lite_24h_saved}")
        
        # 4. Filtered Query Simulation (apply_filters logic)
        # Assuming user_id is either specific or NULL
        # Let's inspect user_id distribution
        cursor.execute("SELECT user_id, COUNT(*) FROM signals GROUP BY user_id")
        print("Signals by user_id:")
        rows = cursor.fetchall()
        for row in rows:
             print(f"  user_id={row[0]}: {row[1]}")

        # Check a sample of recent signals
        cursor.execute("SELECT id, token, mode, is_saved, user_id FROM signals ORDER BY timestamp DESC LIMIT 5")
        print("\nRecent 5 Signals:")
        for row in cursor.fetchall():
            print(f"  {row}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_counts()
