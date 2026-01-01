import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import DATABASE_URL
except ImportError:
    from dotenv import load_dotenv

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")


def fix_data():
    if not DATABASE_URL:
        return

    sync_url = DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with engine.connect() as conn:
        print("🔧 Repairing Strategy IDs...")

        # 1. Update Strategy IDs to match main.py registry
        # The scheduler reads 'strategy_id' from DB and tries to find it in registry.
        # DB has 'rsi_divergence_v1' -> Registry calls it 'rsi_macd_divergence_v1' or similar?
        # Actually, let's verify what main.py has.
        # Assuming main.py registers: rsi_macd_divergence_v1

        try:
            conn.execute(
                text(
                    "UPDATE strategy_configs SET strategy_id='rsi_macd_divergence_v1' "
                    "WHERE strategy_id='rsi_divergence_v1'"
                )
            )
            conn.commit()
            print("   ✅ Updated 'rsi_divergence_v1' -> 'rsi_macd_divergence_v1'")
        except Exception as e:
            print(f"   ⚠️ Could not update strategy ID: {e}")

        # 2. Clear corrupted subscriptions
        conn.execute(text("DELETE FROM push_subscriptions"))
        conn.commit()
        print("   ✅ Cleared push_subscriptions table (forcing fresh sub).")

    print("✨ Repairs Done.")


if __name__ == "__main__":
    fix_data()
