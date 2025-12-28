from sqlalchemy import create_engine, text

# User provided public URL
url = "postgresql://postgres:dRiFJcgoEwLvWXLLNjzFkJgsZCLZAKbE@nozomi.proxy.rlwy.net:47990/railway"

def run():
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print("--- Connecting to Railway DB ---")
            
            # Explicit Delete of Rogue ID 9 (PnL +0.29)
            print("Deleting Rogue Signal ID 9...")
            conn.execute(text("DELETE FROM signal_evaluations WHERE signal_id = 9"))
            res = conn.execute(text("DELETE FROM signals WHERE id = 9"))
            conn.commit()
            print(f"✅ SUCCESS: Deleted {res.rowcount} rogue signals.")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    run()
