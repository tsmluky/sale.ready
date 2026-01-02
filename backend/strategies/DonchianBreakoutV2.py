import pandas as pd
import pandas_ta as ta
from datetime import datetime
from typing import List, Dict, Any, Optional
from .base import Strategy, StrategyMetadata
from core.schemas import Signal
from indicators.market import get_market_data


class DonchianBreakoutV2(Strategy):
    """
    Donchian Breakout V2 (Refined)

    Logic:
    - LONG: Close > Upper Band (20) AND ATR > SMA(ATR, 20) AND Close > EMA(200)
    - SHORT: Close < Lower Band (20) AND ATR > SMA(ATR, 20) AND Close < EMA(200)

    Exit:
    - Trailing Stop at Donchian Middle Band
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Parameters
        self.period = self.config.get("period", 20)
        self.atr_period = self.config.get("atr_period", 14)
        self.atr_ma_period = self.config.get("atr_ma_period", 20)
        self.ema_trend_period = self.config.get("ema_trend_period", 200)

    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            id="donchian_v2",
            name="Donchian Breakout V2",
            description="Trend following breakout with volatility and trend filters",
            version="2.0.0",
            default_timeframe="1h",
            universe=["ETH", "BTC", "SOL"],
            risk_profile="medium",
            mode="PRO",
            source_type="ENGINE",
            enabled=True,
            config={
                "period": self.period,
                "atr_period": self.atr_period,
                "atr_ma_period": self.atr_ma_period,
                "ema_trend_period": self.ema_trend_period,
            },
        )

    def generate_signals(
        self,
        tokens: List[str],
        timeframe: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Signal]:
        signals = []

        for token in tokens:
            try:
                # 1. Get Data (need enough for EMA200 + buffer)
                required_candles = self.ema_trend_period + 50
                df, market = get_market_data(
                    token.lower(), timeframe, limit=required_candles
                )

                # [FIX] Ensure Timestamp Index
                if df is not None and not df.empty and "timestamp" in df.columns:
                     df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                     df.set_index("timestamp", inplace=True)

                if df is None or df.empty:
                    print(f"[DonchianV2] No data returned for {token}")
                    continue

                if len(df) < self.ema_trend_period:
                    print(
                        f"[DonchianV2] Insufficient data for {token}: got {len(df)}, need {self.ema_trend_period}"
                    )
                    continue

                # 2. Calculate Indicators
                high = df["high"]
                low = df["low"]
                close = df["close"]

                # Donchian Channels (manual calculation for clarity)
                dc_upper = high.rolling(window=self.period).max().shift(1)
                dc_lower = low.rolling(window=self.period).min().shift(1)
                dc_mid = (dc_upper + dc_lower) / 2

                # ATR & ATR MA
                atr_series = ta.atr(high, low, close, length=self.atr_period)
                atr_ma = atr_series.rolling(window=self.atr_ma_period).mean()

                # EMA 200 Trend Filter
                ema_trend = ta.ema(close, length=self.ema_trend_period)

                # 3. Logic (on the last COMPLETED candle to avoid repainting)
                curr_idx = -2
                curr_close = close.iloc[curr_idx]
                # curr_high = high.iloc[curr_idx]
                # curr_low = low.iloc[curr_idx]
                curr_dc_upper = dc_upper.iloc[curr_idx]
                curr_dc_lower = dc_lower.iloc[curr_idx]
                curr_dc_mid = dc_mid.iloc[curr_idx]
                curr_atr = atr_series.iloc[curr_idx]
                curr_atr_ma = atr_ma.iloc[curr_idx]
                curr_ema = ema_trend.iloc[curr_idx]

                # Skip if NaN
                if pd.isna(curr_dc_upper) or pd.isna(curr_atr) or pd.isna(curr_ema):
                    continue

                # Volatility Filter
                vol_ok = curr_atr > curr_atr_ma

                # Trend Filter
                trend_up = curr_close > curr_ema
                trend_dn = curr_close < curr_ema

                signal_dir = None
                rationale = []
                stop_loss = None
                take_profit = None

                # LONG
                if curr_close > curr_dc_upper and vol_ok and trend_up:
                    signal_dir = "long"
                    rationale.append(f"Breakout Upper Donchian ({curr_dc_upper:.2f})")
                    rationale.append("High Volatility (ATR > Avg)")
                    rationale.append(
                        f"Bullish Trend (Price {curr_close:.2f} > EMA200 {curr_ema:.2f})"
                    )

                    stop_loss = curr_dc_mid
                    risk = curr_close - stop_loss
                    take_profit = curr_close + (risk * 2.0)

                # SHORT
                elif curr_close < curr_dc_lower and vol_ok and trend_dn:
                    signal_dir = "short"
                    rationale.append(f"Breakout Lower Donchian ({curr_dc_lower:.2f})")
                    rationale.append("High Volatility (ATR > Avg)")
                    rationale.append(
                        f"Bearish Trend (Price {curr_close:.2f} < EMA200 {curr_ema:.2f})"
                    )

                    stop_loss = curr_dc_mid
                    risk = stop_loss - curr_close
                    take_profit = curr_close - (risk * 2.0)

                # [FIX] Use candle timestamp for stability (prevents dupes)
                ts_candle = df.index[curr_idx]
                if isinstance(ts_candle, (int, float)):
                    ts_candle = datetime.utcfromtimestamp(ts_candle / 1000.0)
                elif not isinstance(ts_candle, datetime):
                    ts_candle = datetime.utcnow()

                if signal_dir:
                    sig = Signal(
                        timestamp=ts_candle,
                        strategy_id=self.metadata().id,
                        mode="PRO",
                        token=token.upper(),
                        timeframe=timeframe,
                        direction=signal_dir,
                        entry=float(curr_close),
                        tp=float(take_profit),
                        sl=float(stop_loss),
                        confidence=0.85,
                        rationale=" | ".join(rationale),
                        source="donchian_v2",
                    )
                    signals.append(sig)
                    print(
                        f"[DonchianV2] ✅ Signal generated: {token} {signal_dir.upper()} @ {curr_close:.2f}"
                    )

            except Exception as e:
                print(f"[DonchianV2] Error for {token}: {e}")
                import traceback

                traceback.print_exc()
                continue

        return signals
