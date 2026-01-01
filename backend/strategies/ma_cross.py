# backend/strategies/ma_cross.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np

from .base import Strategy, StrategyMetadata
from core.schemas import Signal
from core.market_data_api import get_ohlcv_data


class MACrossStrategy(Strategy):
    """
    Estrategia de Cruce de Medias Móviles (MA Cross).

    Genera señales cuando una EMA rápida cruza una EMA lenta.
    - Golden Cross (Rápida cruza hacia arriba Lenta) -> LONG
    - Death Cross (Rápida cruza hacia abajo Lenta) -> SHORT
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fast_period = self.config.get("fast_period", 10)
        self.slow_period = self.config.get("slow_period", 50)
        self.tp_atr_mult = self.config.get("tp_atr_mult", 1.5)
        self.sl_atr_mult = self.config.get("sl_atr_mult", 1.0)
        self.bars_timeout = self.config.get("bars_timeout", 10)

    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            id="ma_cross_v1",
            name=f"MA Cross {self.fast_period}/{self.slow_period}",
            description="Estrategia de seguimiento de tendencia basada en cruce de EMAs.",
            version="1.0.0",
            default_timeframe="1h",
            universe=["*"],
            risk_profile="medium",
            mode="CUSTOM",
            source_type="ENGINE",
            enabled=True,
            config={
                "fast_period": self.fast_period,
                "slow_period": self.slow_period,
                "tp_atr_mult": self.tp_atr_mult,
                "sl_atr_mult": self.sl_atr_mult,
                "bars_timeout": self.bars_timeout,
            },
        )

    def analyze(self, df: pd.DataFrame, token: str, timeframe: str) -> List[Signal]:
        """
        Analiza un DataFrame histórico y devuelve señales.
        """
        if df.empty or len(df) < self.slow_period:
            return []

        d = df.copy()
        # Calcular indicadores
        d["ema_fast"] = d["close"].ewm(span=self.fast_period, adjust=False).mean()
        d["ema_slow"] = d["close"].ewm(span=self.slow_period, adjust=False).mean()

        # ATR para TP/SL
        d["tr"] = np.maximum(
            d["high"] - d["low"],
            np.maximum(
                abs(d["high"] - d["close"].shift(1)),
                abs(d["low"] - d["close"].shift(1)),
            ),
        )
        d["atr"] = d["tr"].rolling(window=14).mean()

        # Detectar cruces
        d["cross"] = 0
        d.loc[
            (d["ema_fast"] > d["ema_slow"])
            & (d["ema_fast"].shift(1) <= d["ema_slow"].shift(1)),
            "cross",
        ] = 1  # Golden
        d.loc[
            (d["ema_fast"] < d["ema_slow"])
            & (d["ema_fast"].shift(1) >= d["ema_slow"].shift(1)),
            "cross",
        ] = -1  # Death

        # Iterar sobre todos los cruces encontrados
        signals = []

        # Filtramos solo las filas donde hubo cruce para ser más eficientes
        cross_rows = d[d["cross"] != 0]

        for ts, row in cross_rows.iterrows():
            entry_price = float(row["close"])
            atr = float(row["atr"]) if not pd.isna(row["atr"]) else entry_price * 0.01
            cross_val = row["cross"]

            if cross_val == 1:
                direction = "long"
                tp = entry_price + self.tp_atr_mult * atr
                sl = entry_price - self.sl_atr_mult * atr
                rationale = (
                    f"Golden Cross: EMA{self.fast_period} > EMA{self.slow_period}"
                )
            else:
                direction = "short"
                tp = entry_price - self.tp_atr_mult * atr
                sl = entry_price + self.sl_atr_mult * atr
                rationale = (
                    f"Death Cross: EMA{self.fast_period} < EMA{self.slow_period}"
                )

            # Timestamp: Ensure strict adherence to candle timestamp for idempotency
            if isinstance(ts, (datetime, pd.Timestamp)):
                signal_ts = ts
            else:
                # Attempt to convert or fallback strictly to avoid 'repainting' timestamps
                try:
                    signal_ts = pd.to_datetime(ts).to_pydatetime()
                except:
                    # This should not happen if setup is correct, but if it does,
                    # we must not use utcnow() implies a new unique signal every ms.
                    # We will use the last known valid index if possible or skip.
                    print(f"⚠️ Warning: Invalid timestamp index in MA Cross: {ts}")
                    continue

            signal = Signal(
                timestamp=signal_ts,
                strategy_id=self.metadata().id,
                mode="CUSTOM",
                token=token.upper(),
                timeframe=timeframe,
                direction=direction,
                entry=round(entry_price, 2),
                tp=round(tp, 2),
                sl=round(sl, 2),
                confidence=0.8,
                rationale=rationale,
                source="ENGINE",
                extra={
                    "ema_fast": round(row["ema_fast"], 2),
                    "ema_slow": round(row["ema_slow"], 2),
                    "atr": round(atr, 2),
                },
            )
            signals.append(signal)

        return signals

    def generate_signals(
        self,
        tokens: List[str],
        timeframe: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Signal]:
        valid_tokens = self.validate_tokens(tokens)
        all_signals = []

        for token in valid_tokens:
            try:
                # 1. Obtener datos
                # Intentar sacar del context si existe (para backtesting inyectado)
                if context and "data" in context and token in context["data"]:
                    raw_data = context["data"][token]
                    # Asumimos que raw_data es lista de dicts o DataFrame
                    if isinstance(raw_data, list):
                        df = pd.DataFrame(raw_data)
                    else:
                        df = raw_data
                else:
                    # Fetch de API
                    ohlcv = get_ohlcv_data(token, timeframe, limit=200)
                    if not ohlcv:
                        continue
                    df = pd.DataFrame(ohlcv)

                # Normalizar columnas
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df.set_index("timestamp", inplace=True)

                # 2. Analizar
                signals = self.analyze(df, token, timeframe)
                all_signals.extend(signals)

            except Exception as e:
                print(f"Error generating signals for {token}: {e}")
                continue

        return all_signals
