import os
import sys
import json
from sqlalchemy import text
from pathlib import Path

# Fix import paths
current_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(current_dir))

from database import engine, SessionLocal
from marketplace_config import SYSTEM_PERSONAS
from models_db import StrategyConfig, User

def apply_db_patches():
    print("🔧 [DB PATCH] Starting Manual DB Patching & Seeding...")
    
    with engine.begin() as conn:
         # 1. Rationale Text Fix
        if "postgresql" in str(engine.url):
            try:
                conn.execute(text("ALTER TABLE signals ALTER COLUMN rationale TYPE TEXT;"))
                print("   ✅ Altered rationale to TEXT")
            except Exception:
                pass
                
        # 2. Add Telegram Chat ID
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR;"))
        except Exception:
            pass

        # 3. Add is_saved
        try:
             conn.execute(text("ALTER TABLE signals ADD COLUMN is_saved INTEGER DEFAULT 0;"))
        except Exception:
            pass
            
        # 4. Drop Bad Constraint
        # (This logic was complex in main.py, simplified here)
        # We assume users run this offline.
        
    db = SessionLocal()
    try:
        # 5. Fix Schema Constraints (Logic from main.py)
        # Simplified: We trust Alembic or this script.
        pass 
        
        # 6. Seed System Personas
        print("🌱 [SEED] Verify System Personas...")
        for sp in SYSTEM_PERSONAS:
            db_p = db.query(StrategyConfig).filter(StrategyConfig.persona_id == sp["id"]).first()
            if not db_p:
                print(f"   Creating {sp['name']}...")
                db_p = StrategyConfig(
                    persona_id=sp["id"],
                    strategy_id=sp["strategy_id"],
                    name=sp["name"],
                    description=sp["description"],
                    timeframes=json.dumps([sp["timeframe"]]),
                    tokens=json.dumps([sp["symbol"]]),
                    risk_profile=sp["risk_level"],
                    expected_roi=sp["expected_roi"],
                    color=sp["color"],
                    is_public=1,
                    user_id=None,
                    enabled=1,
                )
                db.add(db_p)
            else:
                # Update
                db_p.name = sp["name"]
                db_p.description = sp["description"]
                db_p.is_public = 1
                db_p.user_id = None
        db.commit()
        print("✅ [SEED] System Personas Synced.")
    except Exception as e:
        db.rollback()
        print(f"❌ [SEED] Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    apply_db_patches()
