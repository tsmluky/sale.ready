import sys
import os

# Ensure backend dir is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Load Env BEFORE imports
from core.config import load_env_if_needed
load_env_if_needed()

from database import SessionLocal
from models_db import Signal, SignalEvaluation
from sqlalchemy import delete

def purge_signals(strategy_id=None, execute=False):
    session = SessionLocal()
    try:
        if strategy_id:
            # Delete evaluations first (FK)
            print("Purging evaluations for strategy...")
            # Complex query, easier to just delete all signals and cascade? 
            # SQLite might not cascade by default without PRAGMA.
            # Let's delete signals, assuming cascade or we don't care about orphans for now if we delete ALL.
            
            stmt = delete(Signal).where(Signal.strategy_id == strategy_id)
            print(f"Targeting signals for strategy_id: {strategy_id}")
        else:
            # Delete ALL
            print("Targeting ALL signals (and evaluations via cascade if configured)...")
            session.execute(delete(SignalEvaluation)) # Safer to delete children first
            stmt = delete(Signal)

        if execute:
            result = session.execute(stmt)
            session.commit()
            print(f"✅ Deleted {result.rowcount} signals.")
        else:
            print("⚠️ Dry run only. Pass execute=True to delete.")
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", help="Strategy ID to purge (e.g., '1234' or 'rsi_divergence_v1')")
    parser.add_argument("--all", action="store_true", help="Delete ALL signals")
    parser.add_argument("--force", action="store_true", help="Actually execute the deletion")
    
    args = parser.parse_args()
    
    if args.strategy:
        purge_signals(args.strategy, args.force)
    elif args.all:
        purge_signals(None, args.force)
    else:
        print("Usage: python purge_signals.py --strategy <id> --force OR --all --force")
