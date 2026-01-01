from sqlalchemy import create_engine, text
from datetime import datetime

# Use the PUBLIC URL provided by the user previously
# postgresql://postgres:dRiFJcgoEwLvWXLLNjzFkJgsZCLZAKbE@nozomi.proxy.rlwy.net:47990/railway
url = "postgresql://postgres:dRiFJcgoEwLvWXLLNjzFkJgsZCLZAKbE@nozomi.proxy.rlwy.net:47990/railway"

def debug_pnl():
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print(f"--- 🔍 DEBUGGING PnL (Time: {datetime.now()}) ---")
            
            # 1. Fetch ALL evaluations with PnL != 0
            sql = """
            SELECT 
                s.id, 
                s.token, 
                s.source, 
                s.timestamp, 
                s.user_id, 
                e.result, 
                e.pnl_r,
                e.evaluated_at
            FROM signal_evaluations e
            JOIN signals s ON e.signal_id = s.id
            WHERE e.pnl_r != 0
            ORDER BY s.timestamp DESC
            """
            
            rows = conn.execute(text(sql)).fetchall()
            
            with open("backend/pnl_dump.txt", "w", encoding="utf-8") as f:
                f.write(f"{'ID':<6} | {'TOKEN':<6} | {'SOURCE':<20} | {'PnL':<10} | {'USER':<6} | {'TIMESTAMP'}\n")
                f.write("-" * 90 + "\n")
                
                total_pnl = 0.0
                found_suspect = False
                
                for r in rows:
                    s_id = r[0]
                    token = r[1]
                    source = r[2]
                    ts = r[3]
                    user_id = r[4]
                    pnl = float(r[6])
                    
                    # Highlight anything close to 0.29 or summing to it
                    marker = ""
                    if abs(pnl - 0.29) < 0.01:
                        marker = "!!! SUSPECT !!!"
                        found_suspect = True
                    
                    f.write(f"{s_id:<6} | {token:<6} | {source:<20} | {pnl:<10.4f} | {user_id!s:<6} | {ts} {marker}\n")
                    total_pnl += pnl
                    
                f.write("-" * 90 + "\n")
                f.write(f"TOTAL SUM IN DB: {total_pnl:.4f} R\n")
                
                if not found_suspect:
                     f.write("No single row with 0.29 found. Searching for combinations...\n")
                     
            print("Done writing to backend/pnl_dump.txt")

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    debug_pnl()
