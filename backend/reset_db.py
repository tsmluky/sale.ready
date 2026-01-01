import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine_sync, Base

def reset_db():
    print("--- [RESET DB] Dropping all tables to enforce new Schema/Constraints ---")
    
    # 1. Drop Tables (Cascade manual if needed, but Base.metadata.drop_all roughly works)
    # Using raw SQL for SQLite safety or just metadata
    Base.metadata.drop_all(bind=engine_sync)
    print("tables dropped.")

    # 2. Create Tables (with new UniqueConstraint / idempotency_key)
    Base.metadata.create_all(bind=engine_sync)
    print("tables recreated.")

    print("--- [RESET DB] Schema Update Complete ---")

if __name__ == "__main__":
    reset_db()
