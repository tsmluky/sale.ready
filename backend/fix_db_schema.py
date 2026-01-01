import sqlite3
import os

DB_PATH = "dev_local.db"

def fix_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check columns in signals table
        cursor.execute("PRAGMA table_info(signals)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        if "is_saved" not in columns:
            print("Column 'is_saved' missing. Adding it...")
            cursor.execute("ALTER TABLE signals ADD COLUMN is_saved INTEGER DEFAULT 0")
            print("Column 'is_saved' added successfully.")
        else:
            print("Column 'is_saved' already exists.")

        if "extra" not in columns:
            print("Column 'extra' missing. Adding it...")
            cursor.execute("ALTER TABLE signals ADD COLUMN extra TEXT")
            print("Column 'extra' added successfully.")
        else:
             print("Column 'extra' already exists.")
            
        conn.commit()
            
    except Exception as e:
        print(f"Error checking/fixing schema: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_schema()
