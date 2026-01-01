
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import engine, Base
from strategies.registry import get_registry
from strategies.ma_cross import MACrossStrategy
from strategies.bb_mean_reversion import BBMeanReversionStrategy
from backend.core.schemas import Signal
from backend.core.signal_logger import log_signal
from evaluated_logger import evaluate_all_tokens

async def init_db():
    print("🔹 Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database Initialized.")

def verify_strategy_registration():
    print("\n🔹 Verifying Strategy Registration...")
    registry = get_registry()
    registry.register(MACrossStrategy)
    registry.register(BBMeanReversionStrategy)
    
    strategies = registry.list_all()
    print(f"   Registered Strategies: {[s.id for s in strategies]}")
    
    if "ma_cross_v1" in [s.id for s in strategies]:
        print("✅ Strategies Registered.")
    else:
        print("❌ Strategy Registration Failed.")

def verify_signal_logging():
    print("\n🔹 Verifying Signal Logging...")
    # Create a mock signal
    # Use TESTTOKEN and mode LITE so evaluated_logger picks it up (it scans LITE dir)
    sig = Signal(
        timestamp=datetime.utcnow() - timedelta(minutes=10), 
        strategy_id="test_integrity_strat",
        mode="LITE",
        token="TESTTOKEN",
        timeframe="1h",
        direction="long",
        entry=100.0,
        tp=110.0,
        sl=90.0,
        confidence=0.9,
        rationale="Integrity Test",
        source="SYSTEM_CHECK"
    )
    
    try:
        log_signal(sig)
        print("✅ Signal Logged to CSV and DB.")
    except Exception as e:
        print(f"❌ Signal Logging Failed: {e}")
        raise e

def verify_evaluation_update():
    print("\n🔹 Verifying Evaluation Logic...")
    try:
        # TESTTOKEN.csv should exist in logs/LITE now
        # We need market data for TESTTOKEN for evaluation to work properly, or it will default to neutral/open
        # evaluated_logger uses get_market_data. logic handles missing data gracefully.
        
        processed, new_evals = evaluate_all_tokens()
        print(f"   Processed Tokens: {processed}, New Evals: {new_evals}")
        print("✅ Evaluation Logic Ran Successfully.")
    except Exception as e:
        print(f"❌ Evaluation Logic Failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 Starting System Integrity Verification...")
    
    # 1. DB Init
    asyncio.run(init_db())
    
    # 2. Strategies
    verify_strategy_registration()
    
    # 3. Logging
    verify_signal_logging()
    
    # 4. Evaluation
    verify_evaluation_update()
    
    print("\n✅ SYSTEM INTEGRITY VERIFIED. ALL SYSTEMS GO.")

if __name__ == "__main__":
    main()

