import sqlite3
import os

DB_PATH = "dev_local.db"

def clean_signals():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Wiping ALL signals and evaluations for a Clean Start...")
        
        # Clear evaluations first
        cursor.execute("DELETE FROM signal_evaluations")
        
        # Clear signals
        cursor.execute("DELETE FROM signals")
        
        conn.commit()
        print("Deleted ALL signals and evaluations.")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM signals")
        remain = cursor.fetchone()[0]
        print(f"Remaining signals: {remain}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_signals()
