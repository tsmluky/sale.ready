# backend/strategies/HyperScalpStrategy.py
"""
Hyper Scalp Strategy - Optimized for High Frequency / Demo Engagement
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd

from .base import Strategy, StrategyMetadata
from core.schemas import Signal
from core.market_data_api import get_ohlcv_data


class HyperScalpStrategy(Strategy):
    """
    Hyper-Aggressive Scalping Strategy.
    Designed to generate frequent activity (WOW factor).

    Logic:
    - Timeframe: 5m (Very fast)
    - RSI(7): Fast reaction.
    - Bollinger Bands (20, 1.5): Tighter bands to catch more breakouts/reversions.
    - Entry: Price touches Band + RSI confirms.
    - Exit: Mean Reversion (Mid Band) or Fixed TP 0.8%
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Hyperparameters (Tuned for Activity)
        self.rsi_period = 7  # Standard is 14. 7 is faster.
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.bb_length = 20
        self.bb_std = 1.5  # Standard is 2.0. 1.5 creates MORE signals.
        self.tp_pct = 0.008  # 0.8% TP
        self.sl_pct = 0.012  # 1.2% SL (Wide enough to breathe)

    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            id="hyper_scalp_v1",
            name="Hyper Scalp AI (5m)",
            description="High-frequency scalper seeking rapid micro-profits on 5m charts.",
            version="1.0.0",
            default_timeframe="5m",
            universe=["*"],
            risk_profile="high",
            mode="CUSTOM",
            source_type="ENGINE",
            enabled=True,
            config={
                "rsi_period": self.rsi_period,
                "bb_std": self.bb_std,
                "tp_pct": self.tp_pct,
            },
        )

    def analyze(self, df: pd.DataFrame, token: str, timeframe: str) -> List[Signal]:
        if df.empty or len(df) < 30:
            return []

        d = df.copy()

        # 1. Indicators
        # RSI
        d.ta.rsi(length=self.rsi_period, append=True)  # RSI_7

        # Bollinger Bands
        # format: BBL_20_1.5, BBM_20_1.5, BBU_20_1.5
        d.ta.bbands(length=self.bb_length, std=self.bb_std, append=True)

        rsi_col = f"RSI_{self.rsi_period}"
        lower_col = f"BBL_{self.bb_length}_{self.bb_std}"
        upper_col = f"BBU_{self.bb_length}_{self.bb_std}"
        mid_col = f"BBM_{self.bb_length}_{self.bb_std}"

        # Cleanup
        d = d.dropna()
        if len(d) < 2:
            return []

        signals = []

        # 2. Logic on LAST Candle
        curr = d.iloc[-1]

        rsi = curr.get(rsi_col)
        lower = curr.get(lower_col)
        upper = curr.get(upper_col)
        mid = curr.get(mid_col)
        close = curr["close"]
        low = curr["low"]
        high = curr["high"]

        if rsi is None or lower is None:
            return []

        # Trend Filter (EMA 200)
        d.ta.ema(length=200, append=True)
        ema_col = "EMA_200"

        # Vectorized Signal Search
        # LONG: Low < BB_Lower AND RSI < 30 AND Close > EMA200 (Trend is Up)
        long_cond = (
            (d["low"] < d[lower_col])
            & (d[rsi_col] <= self.rsi_oversold)
            & (d["close"] > d.get(ema_col, 0))
        )

        # SHORT: High > BB_Upper AND RSI > 70 AND Close < EMA200 (Trend is Down)
        short_cond = (
            (d["high"] > d[upper_col])
            & (d[rsi_col] >= self.rsi_overbought)
            & (d["close"] < d.get(ema_col, 1000000))
        )

        # Get indices where conditions are met
        long_idx = d.index[long_cond]
        short_idx = d.index[short_cond]

        # Combine and sort
        all_indices = sorted(long_idx.union(short_idx))

        for idx in all_indices:
            row = d.loc[idx]
            curr_rsi = row[rsi_col]

            if idx in long_idx:
                entry = row["close"]
                tp = entry * (1 + 0.015)  # Boost TP to 1.5%
                sl = entry * (1 - 0.007)  # Tight SL 0.7% (2:1 Ratio attempt)
                confidence = min(0.95, 0.6 + ((30 - curr_rsi) / 100))

                signal = Signal(
                    timestamp=idx if isinstance(idx, datetime) else datetime.utcnow(),
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token.upper(),
                    timeframe=timeframe,
                    direction="long",
                    entry=round(entry, 4),
                    tp=round(tp, 4),
                    sl=round(sl, 4),
                    confidence=round(confidence, 2),
                    rationale=f"Scalp Long: Oversold RSI({curr_rsi:.1f}) + BB + TrendUp",
                    source="ENGINE",
                    extra={"rsi": round(curr_rsi, 1)},
                )
                signals.append(signal)

            elif idx in short_idx:
                entry = row["close"]
                tp = entry * (1 - 0.015)
                sl = entry * (1 + 0.007)
                confidence = min(0.95, 0.6 + ((curr_rsi - 70) / 100))

                signal = Signal(
                    timestamp=idx if isinstance(idx, datetime) else datetime.utcnow(),
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token.upper(),
                    timeframe=timeframe,
                    direction="short",
                    entry=round(entry, 4),
                    tp=round(tp, 4),
                    sl=round(sl, 4),
                    confidence=round(confidence, 2),
                    rationale=f"Scalp Short: Overbought RSI({curr_rsi:.1f}) + BB + TrendDown",
                    source="ENGINE",
                    extra={"rsi": round(curr_rsi, 1)},
                )
                signals.append(signal)

        return signals

    def generate_signals(
        self,
        tokens: List[str],
        timeframe: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Signal]:
        # Generator logic
        valid_tokens = self.validate_tokens(tokens)
        all_signals = []
        for token in valid_tokens:
            try:
                if context and "data" in context and token in context["data"]:
                    raw = context["data"][token]
                    df = pd.DataFrame(
                        raw,
                        columns=["timestamp", "open", "high", "low", "close", "volume"],
                    )
                else:
                    raw = get_ohlcv_data(token, timeframe, limit=100)
                    if not raw:
                        continue
                    df = pd.DataFrame(
                        raw,
                        columns=["timestamp", "open", "high", "low", "close", "volume"],
                    )

                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df.set_index("timestamp", inplace=True)

                all_signals.extend(self.analyze(df, token, timeframe))
            except Exception as e:
                print(f"[HyperScalp] Error {token}: {e}")
        return all_signals
