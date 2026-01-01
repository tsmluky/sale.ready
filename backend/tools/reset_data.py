
import sys
import os
from pathlib import Path
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import SessionLocal

def reset_system():
    print("🧹 Starting System Reset / Clean Slate...")

    # 1. Clear Logs (CSV)
    logs_dir = Path(__file__).resolve().parent.parent / "logs"
    subdirs = ["LITE", "PRO", "ADVISOR", "EVALUATED", "CUSTOM"]
    
    for subdir in subdirs:
        dir_path = logs_dir / subdir
        if dir_path.exists():
            print(f"   Cleaning {dir_path}...")
            # Remove all files but keep directory
            for item in dir_path.iterdir():
                if item.is_file():
                    item.unlink()
    print("✅ Logs cleared.")

    # 2. Add Database Reset
    # We want to delete rows from 'signals' and 'signal_evaluations'
    # And reset stats in 'strategy_configs', but KEEP the configs themselves (so we don't need to re-seed)
    
    session = SessionLocal()
    try:
        print("   Truncating Signals & Evaluations...")
        # SQLite doesn't support TRUNCATE with CASCADE usually, so we use DELETE
        # Order matters due to FK
        session.execute(text("DELETE FROM signal_evaluations"))
        session.execute(text("DELETE FROM signals"))
        
        print("   Resetting Strategy Stats...")
        session.execute(text("UPDATE strategy_configs SET total_signals=0, win_rate=0.0, avg_confidence=0.0, last_execution=NULL"))
        
        session.commit()
        print("✅ Database tables cleared and stats reset.")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        session.rollback()
    finally:
        session.close()

    print("\n✨ System is clean and ready for fresh testing.")

if __name__ == "__main__":
    confirmation = input("⚠️  This will DELETE ALL SIGNALS and HISTORY. Are you sure? (y/n): ")
    if confirmation.lower() == 'y':
        reset_system()
    else:
        print("Aborted.")
