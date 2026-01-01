
import sys
import os
import json

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import _build_lite_from_market, _inject_rag_into_lite_rationale, _build_pro_markdown, _load_brain_context
from models import ProReq

# Mock Data
mock_market = {
    "price": 3000.0,
    "rsi": 25.0,  # Oversold -> should trigger LONG recall
    "ema21": 3100.0,
    "ema50": 3200.0,
    "macd": -10.0,
    "macd_hist": -2.0,
    "atr": 50.0,
    "trend": "BEARISH",
    "price_change_24h": -6.0 
}

token = "eth"
timeframe = "1h"

print(f"--- MOCK MARKET DATA ({token} {timeframe}) ---")
print(json.dumps(mock_market, indent=2))
print("-" * 50)

# 1. Test LITE Construction
print("\n>>> TESTING LITE CONSTRUCTION...")
lite_signal, indicators = _build_lite_from_market(token, timeframe, mock_market)
print(f"Direction: {lite_signal.direction}")
print(f"Base Rationale: {lite_signal.rationale}")

# 2. Test RAG Injection
print("\n>>> TESTING RAG INJECTION...")
# Mock loading brain context to avoid file dependency if files were missing (but we checked they exist)
# actually we will use the real implementation to test file reading too.
brain = _load_brain_context(token)
print(f"Loaded brain keys: {list(brain.keys())}")

enriched_rationale = _inject_rag_into_lite_rationale(token, timeframe, lite_signal, mock_market)
print(f"Enriched Rationale: {enriched_rationale}")

# 3. Test PRO Markdown Construction
print("\n>>> TESTING PRO MARKDOWN...")
req = ProReq(token=token, timeframe=timeframe, user_message="Check resistance levels")
markdown = _build_pro_markdown(req, lite_signal, indicators, brain)

print(f"Markdown length: {len(markdown)} chars")
print("First 5 lines:")
print("\n".join(markdown.splitlines()[:5]))
print("...")
print("Last 5 lines:")
print("\n".join(markdown.splitlines()[-5:]))

if "#ANALYSIS_START" in markdown and "#ANALYSIS_END" in markdown:
    print("\n✅ PRO Markdown Structure VALID")
else:
    print("\n❌ PRO Markdown Structure INVALID")
