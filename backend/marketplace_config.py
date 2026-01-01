from typing import List, Dict, Any

# Define the "Personas" for the Strategy Marketplace
# This maps the "Marketing View" to the "Technical Implementation"

import json
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
USER_STRATEGIES_FILE = DATA_DIR / "user_strategies.json"

# ensures data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

SYSTEM_PERSONAS = [
    {
        "id": "trend_king_sol",
        "name": "The Trend King",
        "symbol": "SOL",
        "timeframe": "1d",
        "strategy_id": "donchian_v2",
        "description": "Aggressive trend hunter. Catches the massive waves in Solana. High volatility, massive reward.",
        "risk_level": "High",
        "expected_roi": "290%",
        "win_rate": "46%",
        "frequency": "Low (1 trade / 3 days)",
        "color": "amber",
        "is_active": True,
        "is_custom": False
    },

    {
        "id": "titan_btc",
        "name": "Titan Fortress",
        "symbol": "BTC",
        "timeframe": "1d",
        "strategy_id": "donchian_v2",
        "description": "The immovable object. Slow, steady accumulation of Bitcoin. Your safety net.",
        "risk_level": "Low",
        "expected_roi": "20%",
        "win_rate": "52%",
        "frequency": "Very Low",
        "color": "slate",
        "is_active": True,
        "is_custom": False
    },
    {
        "id": "eth_breaker",
        "name": "Ether Breaker",
        "symbol": "ETH",
        "timeframe": "4h",
        "strategy_id": "donchian_v2",
        "description": "Exploits volatility breakouts in Ethereum. Captures 4-hour moves.",
        "risk_level": "Medium",
        "expected_roi": "45%",
        "win_rate": "48%",
        "frequency": "Medium (3 trades/week)",
        "color": "indigo",
        "is_active": True,
        "is_custom": False
    },
    {
        "id": "doge_runner",
        "name": "Doge Runner",
        "symbol": "DOGE",
        "timeframe": "4h",
        "strategy_id": "donchian_v2",
        "description": "Meme-coin momentum hunter. Rides the Doge waves when they break key levels.",
        "risk_level": "High",
        "expected_roi": "120%",
        "win_rate": "40%",
        "frequency": "Low (1 trade/week)",
        "color": "amber",
        "is_active": True,
        "is_custom": False
    },
    {
        "id": "flow_avax",
        "name": "Flow Master",
        "symbol": "AVAX",
        "timeframe": "1d",
        "strategy_id": "trend_following_native_v1",
        "description": "Smooth operator using Golden Cross logic. Validated technical momentum.",
        "risk_level": "Medium",
        "expected_roi": "28%",
        "win_rate": "55%",
        "frequency": "Medium",
        "color": "indigo",
        "is_active": True,
        "is_custom": False
    },
    {
        "id": "system_scanner",
        "name": "Global Market Scanner",
        "symbol": "SCANNER",
        "timeframe": "4h",
        "strategy_id": "trend_following_native_v1",
        "description": "System-wide scanner evaluating 150+ assets for breakout opportunities.",
        "risk_level": "Medium",
        "expected_roi": "Variable",
        "win_rate": "N/A",
        "frequency": "High",
        "color": "cyan",
        "is_active": True,
        "is_custom": False
    }
]


SYSTEM_OVERRIDES_FILE = DATA_DIR / "system_overrides.json"

def load_user_strategies():
    """Load strategies from JSON file."""
    if not USER_STRATEGIES_FILE.exists():
        return []
    try:
        with open(USER_STRATEGIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print(f"Error loading user strategies: {e}")
        return []

def save_user_strategies(strategies: List[Dict[str, Any]]):
    """Save user strategies to JSON file."""
    try:
        with open(USER_STRATEGIES_FILE, "w", encoding="utf-8") as f:
            json.dump(strategies, f, indent=4)
        print(f"[MARKETPLACE] Saved {len(strategies)} user strategies.")
    except Exception as e:
        print(f"Error saving user strategies: {e}")


def load_system_overrides():
    """Load system persona overrides (e.g. is_active state)."""
    if not SYSTEM_OVERRIDES_FILE.exists():
        return {}
    try:
        with open(SYSTEM_OVERRIDES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading system overrides: {e}")
        return {}

def save_system_overrides(overrides: Dict[str, Any]):
    """Save system persona overrides."""
    try:
        with open(SYSTEM_OVERRIDES_FILE, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=4)
    except Exception as e:
        print(f"Error saving system overrides: {e}")

MARKETPLACE_PERSONAS = []

def refresh_personas():
    """Reloads MARKETPLACE_PERSONAS to include latest file changes and overrides"""
    global MARKETPLACE_PERSONAS
    
    # 1. Load Overrides
    overrides = load_system_overrides()
    
    # 2. Apply Overrides to System Personas
    current_system = []
    for p in SYSTEM_PERSONAS:
        p_copy = p.copy()
        if p["id"] in overrides:
            p_copy.update(overrides[p["id"]])
        current_system.append(p_copy)
        
    # 3. Load User Strategies
    user_strategies = load_user_strategies()
    
    MARKETPLACE_PERSONAS = current_system + user_strategies
    return MARKETPLACE_PERSONAS

def get_active_strategies():
    """Returns list of strategies to run in the scheduler"""
    refresh_personas() # Ensure latest
    return [p for p in MARKETPLACE_PERSONAS if p.get("is_active", True)]

