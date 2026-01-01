
import sys
import os
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import SessionLocal
from models_db import StrategyConfig

def seed_quant_configs():
    session = SessionLocal()
    try:
        print("🌱 Seeding Strategy Configurations...")

        # Definition of strategies to seed
        configs = [
            {
                "strategy_id": "ma_cross_v1",
                "name": "MA Cross Strategy",
                "description": "Trend following strategy using EMA crossovers (Fast/Slow).",
                "version": "1.0.0",
                "enabled": 1,
                "interval_seconds": 3600, # Run every 1 hour
                "tokens": json.dumps(["BTC", "ETH", "SOL"]),
                "timeframes": json.dumps(["1h", "4h"]),
                "risk_profile": "medium",
                "mode": "QUANT",
                "source_type": "ENGINE",
                "config_json": json.dumps({"fast_period": 9, "slow_period": 21})
            },
            {
                "strategy_id": "bb_mean_reversion_v1",
                "name": "Bollinger Mean Reversion",
                "description": "Counter-trend strategy exploiting Bollinger Band breakouts.",
                "version": "1.0.0",
                "enabled": 1,
                "interval_seconds": 3600, # Run every 1 hour
                "tokens": json.dumps(["BTC", "ETH", "SOL"]),
                "timeframes": json.dumps(["1h", "15m"]),
                "risk_profile": "high",
                "mode": "QUANT",
                "source_type": "ENGINE",
                "config_json": json.dumps({"period": 20, "std_dev": 2.0})
            }
        ]

        for cfg in configs:
            existing = session.query(StrategyConfig).filter_by(strategy_id=cfg["strategy_id"]).first()
            if existing:
                print(f"   Refreshed {cfg['name']}...")
                existing.name = cfg["name"]
                existing.description = cfg["description"]
                existing.enabled = cfg["enabled"]
                existing.interval_seconds = cfg["interval_seconds"]
                existing.tokens = cfg["tokens"]
                existing.timeframes = cfg["timeframes"]
                existing.updated_at = datetime.utcnow()
            else:
                print(f"   Created {cfg['name']}...")
                new_strat = StrategyConfig(**cfg)
                session.add(new_strat)
        
        session.commit()
        print("✅ Seeding Complete. Strategies are READY for Scheduler.")

    except Exception as e:
        print(f"❌ Error seeding strategies: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_quant_configs()
