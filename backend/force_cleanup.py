from sqlalchemy import create_engine, text

# User provided public URL
url = "postgresql://postgres:dRiFJcgoEwLvWXLLNjzFkJgsZCLZAKbE@nozomi.proxy.rlwy.net:47990/railway"

def run():
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print("--- Connecting to Railway DB ---")
            
            # Check 1: Count bad records
            check_sql = "SELECT count(*) FROM signals WHERE token = 'DOGE' AND entry > 50"
            count = conn.execute(text(check_sql)).scalar()
            
            print(f"Found {count} corrupted DOGE records (Price > $50).")
            
            if count > 0:
                print("Deleting dependent rows in signal_evaluations...")
                # 1. Delete children
                child_sql = "DELETE FROM signal_evaluations WHERE signal_id IN (SELECT id FROM signals WHERE token = 'DOGE' AND entry > 50)"
                conn.execute(text(child_sql))
                
                print("Deleting signals...")
                # 2. Delete parent
                del_sql = "DELETE FROM signals WHERE token = 'DOGE' AND entry > 50"
                res = conn.execute(text(del_sql))
                conn.commit()
                print(f"✅ SUCCESS: Deleted {res.rowcount} records.")
            else:
                print("✅ CLEAN: No garbage data found.")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    run()
