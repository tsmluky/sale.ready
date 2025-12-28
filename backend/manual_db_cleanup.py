import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure we load from the right place
current_dir = os.path.dirname(os.path.abspath(__file__))
# Check local backend .env
load_dotenv(os.path.join(current_dir, ".env"))

def run_analysis():
    print("==========================================")
    print("      TRADERCOPILOT DB INSPECTOR          ")
    print("==========================================")

    # Priority: 1. Arg, 2. Env
    if len(sys.argv) > 1:
        db_url = sys.argv[1]
    
    if not db_url or "localhost" in db_url:
        print(f"⚠️  Current DB URL points to implies LOCALHOST: {db_url}")
        print("To fix the Production/Railway issue, we need the REMOTE URL.")
        print("Paste your Railway 'DATABASE_URL' below (or press Enter to try local):")
        inp = input("> ").strip()
        if inp:
            if "railway.internal" in inp:
                print("\n⚠️  WARNING: You pasted an INTERNAL Railway URL.")
                print("   Your local computer cannot reach this address.")
                print("   Please go to Railway -> Postgres -> Variables and copy 'DATABASE_PUBLIC_URL'.")
                print("   It should look like: postgresql://postgres:...@roundhouse.proxy.rlwy.net:...\n")
                retry = input("Try again? Paste PUBLIC URL > ").strip()
                if retry:
                    db_url = retry
                else:
                    db_url = inp # Fallback to trying anyway if they insist
            else:
                db_url = inp

    if not db_url:
        print("❌ Error: No DATABASE_URL provided.")
        return

    # Fix potential postgres:// deprecation in SQLAlchemy
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print(f"🔌 Connecting to: {db_url.split('@')[-1] if '@' in db_url else 'LOCAL'}")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # 1. ANALYZE
            print("\n🔍 Scanning for suspicious DOGE signals (Price > $1.0)...")
            query = text("SELECT id, token, entry, direction, timestamp FROM signals WHERE token = 'DOGE' AND entry > 1.0 ORDER BY entry DESC")
            result = conn.execute(query)
            rows = result.fetchall()

            if not rows:
                print("✅ CLEAN: No suspicious DOGE signals found.")
            else:
                print(f"⚠️ FOUND {len(rows)} CORRUPTED RECORDS:")
                print(f"{'ID':<10} | {'TOKEN':<6} | {'PRICE':<10} | {'TIME'}")
                print("-" * 50)
                for r in rows:
                    print(f"{r.id:<10} | {r.token:<6} | {r.entry:<10} | {r.timestamp}")

                # 2. ACTION
                print(f"\n⚠️ These values (e.g. {rows[0].entry}) are impossible for DOGE.")
                confirm = input(f"💥 DELETE these {len(rows)} records permanently? (y/n): ")
                
                if confirm.lower().strip() == 'y':
                    delete_query = text("DELETE FROM signals WHERE token = 'DOGE' AND entry > 1.0")
                    res = conn.execute(delete_query)
                    conn.commit()
                    print(f"\n✅ SUCCESS: Deleted {res.rowcount} records.")
                    print("👉 Please refresh your Dashboard now.")
                else:
                    print("\n🚫 Operation cancelled.")
    
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        print("Tip: Ensure you are connected to the internet and the DATABASE_URL is correct.")

if __name__ == "__main__":
    run_analysis()
