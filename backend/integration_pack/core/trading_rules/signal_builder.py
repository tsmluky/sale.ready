import pandas as pd
from typing import Dict, Any

def compute_entry_tp_sl(
    df: pd.DataFrame, 
    side_series: pd.Series, 
    tp_atr: float, 
    sl_atr: float,
    commission_pct: float = 0.0004,
    slippage_pct: float = 0.0002
) -> Dict[str, Any]:
    """
    Computes the Entry, TP, and SL prices based on the LAST signal in the series.
    Assumes entry at the OPEN of the NEXT candle (which is 'now' in a live context if the candle just closed).
    
    Returns a dictionary with:
    - side: LONG, SHORT, or NO_TRADE
    - entry_price
    - tp_price
    - sl_price
    - ts_signal: Timestamp of the signal candle
    """
    if side_series.empty:
        return {"side": "NO_TRADE"}

    # Get the last signal
    last_idx = side_series.index[-1]
    side = side_series.iloc[-1]
    
    if side not in ["LONG", "SHORT"]:
        return {"side": "NO_TRADE"}

    # In a live context, we assume the 'last' row in df is the candle that just closed and generated the signal.
    # The entry price is theoretically the Open of the *next* candle.
    # If we are running this right after close, we might not have the next candle row yet.
    # We use the Close of the signal candle as a proxy for the next Open, 
    # OR if the caller provides a specific current price, we could use that.
    # Here we stick to the logic: Entry = Close of Signal Candle (approx for Next Open) 
    # adjusted by slippage/commissions for conservative estimation.
    
    # NOTE: The original lab code looked for 'pos+1' in the dataframe. 
    # In production, we might only have the dataframe up to 'now'.
    # We will use the CLOSE of the last candle as the base for entry calculation.
    
    raw_entry = float(df["close"].iloc[-1])
    
    # Apply estimated costs to the entry price to model realistic execution
    if side == "LONG":
        entry = raw_entry * (1 + slippage_pct) * (1 + commission_pct)
        atr = float(df["ATR"].iloc[-1])
        tp = entry + tp_atr * atr
        sl = entry - sl_atr * atr
    else:
        entry = raw_entry * (1 - slippage_pct) * (1 - commission_pct)
        atr = float(df["ATR"].iloc[-1])
        tp = entry - tp_atr * atr
        sl = entry + sl_atr * atr

    return {
        "ts_signal": str(last_idx),
        "side": side,
        "entry_price": entry,
        "tp_price": tp,
        "sl_price": sl,
        "atr_used": atr
    }
