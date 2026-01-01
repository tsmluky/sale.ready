# backend/strategies/TrendFollowingNative.py
"""
Trend Following Native Strategy
Ported from Jesse Framework to Native TraderCopilot format.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd

from .base import Strategy, StrategyMetadata
from core.schemas import Signal
from core.market_data_api import get_ohlcv_data

class TrendFollowingNative(Strategy):
    """
    Native implementation of TrendFollowingMasterV1.
    Logic:
    - Entry Long: EMA_Fast crosses over EMA_Slow AND ADX > Threshold
    - Entry Short: EMA_Fast crosses under EMA_Slow AND ADX > Threshold
    - Exit: ATR-based dynamic SL/TP
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Hyperparameters (Defaults matching original)
        self.ema_fast_len = self.config.get("ema_fast", 20)
        self.ema_slow_len = self.config.get("ema_slow", 100)
        self.adx_period = self.config.get("adx_period", 14)
        self.adx_threshold = self.config.get("adx_threshold", 25)
        self.atr_period = self.config.get("atr_period", 14)
        self.risk_reward = self.config.get("risk_reward", 2.0) # TP = 2 * Risk (Standard 2:1)
        # Note: Original code had TP=4*ATR, SL=2*ATR => 2:1 Ratio

    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            id="trend_following_native_v1",
            name=f"Trend Master Native (EMA{self.ema_fast_len}/{self.ema_slow_len})",
            description="Trend Following with EMA Cross + ADX Filter + ATR Stops",
            version="1.0.0",
            default_timeframe="4h",
            universe=["*"],
            risk_profile="medium",
            mode="CUSTOM",
            source_type="ENGINE",
            enabled=True,
            config={
                "ema_fast": self.ema_fast_len,
                "ema_slow": self.ema_slow_len,
                "adx_period": self.adx_period,
                "adx_threshold": self.adx_threshold,
                "atr_period": self.atr_period
            }
        )

    def analyze(self, df: pd.DataFrame, token: str, timeframe: str) -> List[Signal]:
        if df.empty or len(df) < self.ema_slow_len + 5:
            return []
        
        d = df.copy()
        
        # 1. Calculate Indicators
        d.ta.ema(length=self.ema_fast_len, append=True) # EMA_20
        d.ta.ema(length=self.ema_slow_len, append=True) # EMA_100
        d.ta.adx(length=self.adx_period, append=True)   # ADX_14_...
        d.ta.atr(length=self.atr_period, append=True)   # ATR_14
        
        # Rename for easier access
        fast_col = f"EMA_{self.ema_fast_len}"
        slow_col = f"EMA_{self.ema_slow_len}"
        adx_col = f"ADX_{self.adx_period}" # pandas_ta usually outputs ADX_14, DMP_14, DMN_14
        atr_col = f"ATRr_{self.atr_period}"
        
        # Handle potential column name mismatches if needed, but standard logic applies
        if adx_col not in d.columns:
             # Fallback check for exact column name needed by pandas_ta
             # Sometimes it's just ADX_14
             cols = [c for c in d.columns if c.startswith("ADX")]
             if cols: adx_col = cols[0]
        
        d = d.dropna()
        if len(d) < 2: return []
        
        signals = []
        
        # 2. Check logic on the LAST closed candle (trigger)
        # Using -1 as current closed candle, -2 as previous
        curr = d.iloc[-1]
        prev = d.iloc[-2]
        
        # Values
        curr_fast = curr[fast_col]
        curr_slow = curr[slow_col]
        prev_fast = prev[fast_col]
        prev_slow = prev[slow_col]
        
        adx = curr[adx_col]
        atr = curr[atr_col]
        close = curr["close"]
        
        # Logic: Crossover
        
        # LONG: Fast crosses ABOVE Slow
        if (prev_fast <= prev_slow) and (curr_fast > curr_slow):
            # ADX Filter
            if adx > self.adx_threshold:
                # Signal Generation
                sl = close - (2 * atr)
                tp = close + (4 * atr) # 2:1 Reward ratio
                
                # Confidence based on ADX strength (25-50 scale mapped to 0.6-0.9)
                confidence = min(0.95, 0.6 + ((adx - 25) / 100))
                
                signal = Signal(
                    timestamp=curr.name if isinstance(curr.name, datetime) else datetime.utcnow(),
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token.upper(),
                    timeframe=timeframe,
                    direction="long",
                    entry=round(close, 2),
                    tp=round(tp, 2),
                    sl=round(sl, 2),
                    confidence=round(confidence, 2),
                    rationale=f"Golden Cross (EMA {self.ema_fast_len} > {self.ema_slow_len}) with ADX {adx:.1f}",
                    source="ENGINE",
                    extra={"adx": round(adx, 2), "atr": round(atr, 2)}
                )
                signals.append(signal)

        # SHORT: Fast crosses BELOW Slow
        elif (prev_fast >= prev_slow) and (curr_fast < curr_slow):
             # ADX Filter
            if adx > self.adx_threshold:
                sl = close + (2 * atr)
                tp = close - (4 * atr)
                
                confidence = min(0.95, 0.6 + ((adx - 25) / 100))
                
                signal = Signal(
                    timestamp=curr.name if isinstance(curr.name, datetime) else datetime.utcnow(),
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token.upper(),
                    timeframe=timeframe,
                    direction="short",
                    entry=round(close, 2),
                    tp=round(tp, 2),
                    sl=round(sl, 2),
                    confidence=round(confidence, 2),
                    rationale=f"Death Cross (EMA {self.ema_fast_len} < {self.ema_slow_len}) with ADX {adx:.1f}",
                    source="ENGINE",
                    extra={"adx": round(adx, 2), "atr": round(atr, 2)}
                )
                signals.append(signal)
                
        return signals

    def generate_signals(self, tokens: List[str], timeframe: str, context: Optional[Dict[str, Any]] = None) -> List[Signal]:
        # Boilerplate generator
        valid_tokens = self.validate_tokens(tokens)
        all_signals = []
        for token in valid_tokens:
            try:
                if context and "data" in context and token in context["data"]:
                    raw = context["data"][token]
                    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
                else:
                    raw = get_ohlcv_data(token, timeframe, limit=300)
                    if not raw: continue
                    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
                
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df.set_index("timestamp", inplace=True)
                
                all_signals.extend(self.analyze(df, token, timeframe))
            except Exception as e:
                print(f"[TrendMaster] Error analyzing {token}: {e}")
        return all_signals

