import sqlite3
import os

# Helper to normalize DB URL for sqlite
# Assuming sqlite:///./trader.db format. 
# We look for dev_local.db in the current directory or backend/
DB_FILE = "dev_local.db"

def migrate():
    print("Checking for 'timezone' column in 'users' table...")
    
    if not os.path.exists(DB_FILE):
        print(f"Database file {DB_FILE} not found in current directory: {os.getcwd()}")
        # try backend/dev_local.db
        if os.path.exists(os.path.join("backend", DB_FILE)):
             DB_FILE = os.path.join("backend", DB_FILE)
        else:
             print("Could not find dev_local.db")
             # Create it? No, we need to migrate existing.
             return

    abs_db_path = os.path.abspath(DB_FILE)
    print(f"Migrating {abs_db_path}...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {tables}")

    try:
        # Check columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Columns in users: {columns}")
        
        if not columns:
            print("Table 'users' seems to be missing!")
            return
        
        if "timezone" not in columns:
            print("Adding 'timezone' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'UTC'")
            conn.commit()
            print("✅ Column 'timezone' added successfully.")
        else:
            print("✅ Column 'timezone' already exists.")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
