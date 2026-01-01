import requests
import json
import traceback

BASE_URL = "http://localhost:8000"

def verify_backtest():
    print("[-] Running Backtest Simulation...")
    
    payload = {
        "strategy_id": "rsi_divergence", # Assuming this exists from previous listing
        "token": "SOL",
        "timeframe": "1h",
        "days": 7,
        "initial_capital": 1000
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/backtest/run", json=payload)
        
        if resp.status_code != 200:
            print(f"[!] Backtest Failed: {resp.status_code} - {resp.text}")
            return False
            
        data = resp.json()
        metrics = data.get("metrics", {})
        
        print("\n[+] Backtest Results:")
        print(json.dumps(metrics, indent=4))
        
        # Check specific fields
        if "max_drawdown" not in metrics:
            print("\n[FAILED] 'max_drawdown' missing from metrics")
            return False
            
        if "roi_pct" not in metrics:
            print("\n[FAILED] 'roi_pct' missing from metrics")
            return False
            
        print(f"\n[PASS] max_drawdown: {metrics['max_drawdown']}%")
        print(f"[PASS] roi_pct: {metrics['roi_pct']}%")
        
        return True
        
    except Exception as e:
        print(f"[!] Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if verify_backtest():
        print("\nSUCCESS: Backtest metrics verified.")
        exit(0)
    else:
        print("\nFAILURE: Backtest metrics verification failed.")
        exit(1)
