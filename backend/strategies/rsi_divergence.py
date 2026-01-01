# backend/strategies/rsi_divergence.py
"""
RSI Divergence Strategy - Detección de agotamiento de tendencia

Esta estrategia identifica divergencias entre precio y RSI, que típicamente
indican agotamiento de tendencia y reversión inminente.

Divergencia Alcista (Bullish): Precio hace mínimos más bajos, RSI hace mínimos más altos → LONG
Divergencia Bajista (Bearish): Precio hace máximos más altos, RSI hace máximos más bajos → SHORT
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np

from .base import Strategy, StrategyMetadata
from core.schemas import Signal
from core.market_data_api import get_ohlcv_data


class RSIDivergenceStrategy(Strategy):
    """
    Estrategia de Divergencias RSI para detectar reversiones de tendencia.

    Identifica cuando el precio y el RSI están en desacuerdo (divergencia),
    lo cual es una señal muy fuerte de agotamiento de tendencia.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.rsi_period = self.config.get("rsi_period", 14)
        self.pivot_window = self.config.get(
            "pivot_window", 5
        )  # Ventana para detectar pivots
        self.min_pivot_distance = self.config.get(
            "min_pivot_distance", 10
        )  # Distancia mínima entre pivots
        self.divergence_lookback = self.config.get(
            "divergence_lookback", 50
        )  # Cuántas velas mirar atrás
        self.tp_atr_mult = self.config.get(
            "tp_atr_mult", 2.0
        )  # R:R más alto para divergencias
        self.sl_atr_mult = self.config.get("sl_atr_mult", 1.0)

    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            id="rsi_divergence_v1",
            name=f"RSI Divergence {self.rsi_period}",
            description="Detecta divergencias precio-RSI para anticipar reversiones de tendencia.",
            version="1.0.0",
            default_timeframe="1h",
            universe=["*"],
            risk_profile="medium",
            mode="CUSTOM",
            source_type="ENGINE",
            enabled=True,
            config={
                "rsi_period": self.rsi_period,
                "pivot_window": self.pivot_window,
                "min_pivot_distance": self.min_pivot_distance,
                "divergence_lookback": self.divergence_lookback,
                "tp_atr_mult": self.tp_atr_mult,
                "sl_atr_mult": self.sl_atr_mult,
            },
        )

    def _find_pivots(
        self, series: pd.Series, window: int = 5, pivot_type: str = "high"
    ) -> List[int]:
        """
        Encuentra pivots (máximos o mínimos locales) en una serie.

        Args:
            series: Serie de datos (precio o indicador)
            window: Ventana para determinar si es un pivot
            pivot_type: 'high' para máximos, 'low' para mínimos

        Returns:
            Lista de índices donde hay pivots
        """
        pivots = []

        for i in range(window, len(series) - window):
            if pivot_type == "high":
                # Es pivot high si es el máximo en la ventana
                if series.iloc[i] == series.iloc[i - window : i + window + 1].max():
                    # Verificar que no haya otro pivot muy cerca
                    if not pivots or (i - pivots[-1]) >= self.min_pivot_distance:
                        pivots.append(i)
            else:  # low
                # Es pivot low si es el mínimo en la ventana
                if series.iloc[i] == series.iloc[i - window : i + window + 1].min():
                    if not pivots or (i - pivots[-1]) >= self.min_pivot_distance:
                        pivots.append(i)

        return pivots

    def _detect_bullish_divergence(
        self, df: pd.DataFrame, price_lows: List[int], rsi_lows: List[int]
    ) -> Optional[Dict]:
        """
        Detecta divergencia alcista: precio hace mínimos más bajos, RSI hace mínimos más altos.
        """
        if len(price_lows) < 2 or len(rsi_lows) < 2:
            return None

        # Tomar los 2 últimos pivots
        for i in range(len(price_lows) - 1, 0, -1):
            idx_current = price_lows[i]
            idx_prev = price_lows[i - 1]

            # Verificar que el segundo mínimo esté dentro del lookback window
            if idx_current - idx_prev > self.divergence_lookback:
                continue

            price_current = df["low"].iloc[idx_current]
            price_prev = df["low"].iloc[idx_prev]

            # Buscar RSI lows correspondientes (dentro de ±2 velas del price low)
            rsi_current_idx = None
            rsi_prev_idx = None

            for rsi_idx in rsi_lows:
                if abs(rsi_idx - idx_current) <= 2:
                    rsi_current_idx = rsi_idx
                if abs(rsi_idx - idx_prev) <= 2:
                    rsi_prev_idx = rsi_idx

            if rsi_current_idx is None or rsi_prev_idx is None:
                continue

            rsi_current = df["rsi"].iloc[rsi_current_idx]
            rsi_prev = df["rsi"].iloc[rsi_prev_idx]

            # Divergencia alcista: precio baja, RSI sube
            if price_current < price_prev and rsi_current > rsi_prev:
                return {
                    "type": "bullish",
                    "price_idx": idx_current,
                    "price_diff": ((price_current / price_prev) - 1) * 100,
                    "rsi_diff": rsi_current - rsi_prev,
                    "rsi_current": rsi_current,
                }

        return None

    def _detect_bearish_divergence(
        self, df: pd.DataFrame, price_highs: List[int], rsi_highs: List[int]
    ) -> Optional[Dict]:
        """
        Detecta divergencia bajista: precio hace máximos más altos, RSI hace máximos más bajos.
        """
        if len(price_highs) < 2 or len(rsi_highs) < 2:
            return None

        for i in range(len(price_highs) - 1, 0, -1):
            idx_current = price_highs[i]
            idx_prev = price_highs[i - 1]

            if idx_current - idx_prev > self.divergence_lookback:
                continue

            price_current = df["high"].iloc[idx_current]
            price_prev = df["high"].iloc[idx_prev]

            # Buscar RSI highs correspondientes
            rsi_current_idx = None
            rsi_prev_idx = None

            for rsi_idx in rsi_highs:
                if abs(rsi_idx - idx_current) <= 2:
                    rsi_current_idx = rsi_idx
                if abs(rsi_idx - idx_prev) <= 2:
                    rsi_prev_idx = rsi_idx

            if rsi_current_idx is None or rsi_prev_idx is None:
                continue

            rsi_current = df["rsi"].iloc[rsi_current_idx]
            rsi_prev = df["rsi"].iloc[rsi_prev_idx]

            # Divergencia bajista: precio sube, RSI baja
            if price_current > price_prev and rsi_current < rsi_prev:
                return {
                    "type": "bearish",
                    "price_idx": idx_current,
                    "price_diff": ((price_current / price_prev) - 1) * 100,
                    "rsi_diff": rsi_prev - rsi_current,
                    "rsi_current": rsi_current,
                }

        return None

    def analyze(self, df: pd.DataFrame, token: str, timeframe: str) -> List[Signal]:
        if df.empty or len(df) < 100:
            return []

        d = df.copy()

        # Calcular RSI
        delta = d["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        d["rsi"] = 100 - (100 / (1 + rs))

        # ATR para gestión de riesgo
        d["tr"] = np.maximum(
            d["high"] - d["low"],
            np.maximum(
                abs(d["high"] - d["close"].shift(1)),
                abs(d["low"] - d["close"].shift(1)),
            ),
        )
        d["atr"] = d["tr"].rolling(window=14).mean()

        # Limpiar NaNs
        d = d.dropna()

        if len(d) < 50:
            return []

        # Encontrar pivots de precio
        price_highs = self._find_pivots(
            d["high"], window=self.pivot_window, pivot_type="high"
        )
        price_lows = self._find_pivots(
            d["low"], window=self.pivot_window, pivot_type="low"
        )

        # Encontrar pivots de RSI
        rsi_highs = self._find_pivots(
            d["rsi"], window=self.pivot_window, pivot_type="high"
        )
        rsi_lows = self._find_pivots(
            d["rsi"], window=self.pivot_window, pivot_type="low"
        )

        signals = []

        # Detectar divergencia alcista (LONG)
        bullish_div = self._detect_bullish_divergence(d, price_lows, rsi_lows)
        if bullish_div:
            close = float(d["close"].iloc[-1])
            atr = (
                float(d["atr"].iloc[-1])
                if not pd.isna(d["atr"].iloc[-1])
                else close * 0.02
            )

            entry = close
            tp = close + self.tp_atr_mult * atr
            sl = close - self.sl_atr_mult * atr

            confidence = min(
                0.85, 0.7 + (abs(bullish_div["rsi_diff"]) / 100)
            )  # Mayor diferencia RSI = mayor confidence

            rationale = (
                f"Bullish Divergence: Price -{bullish_div['price_diff']:.1f}%, "
                f"RSI +{bullish_div['rsi_diff']:.1f} (Exhaustion)"
            )

            # Timestamp: Strict candle timestamp
            ts_idx = d.index[-1]
            signal_ts = None

            if isinstance(ts_idx, (datetime, pd.Timestamp)):
                signal_ts = ts_idx
            else:
                try:
                    signal_ts = pd.to_datetime(ts_idx).to_pydatetime()
                except:
                    signal_ts = None

            if signal_ts:
                signal = Signal(
                    timestamp=signal_ts,
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token.upper(),
                    timeframe=timeframe,
                    direction="long",
                    entry=round(entry, 2),
                    tp=round(tp, 2),
                    sl=round(sl, 2),
                    confidence=round(confidence, 2),
                    rationale=rationale,
                    source="ENGINE",
                    extra={
                        "divergence_type": "bullish",
                        "rsi": round(bullish_div["rsi_current"], 1),
                        "rsi_diff": round(bullish_div["rsi_diff"], 1),
                        "price_diff": round(bullish_div["price_diff"], 2),
                    },
                )
                signals.append(signal)

        # Detectar divergencia bajista (SHORT)
        bearish_div = self._detect_bearish_divergence(d, price_highs, rsi_highs)
        if bearish_div:
            close = float(d["close"].iloc[-1])
            atr = (
                float(d["atr"].iloc[-1])
                if not pd.isna(d["atr"].iloc[-1])
                else close * 0.02
            )

            entry = close
            tp = close - self.tp_atr_mult * atr
            sl = close + self.sl_atr_mult * atr

            confidence = min(0.85, 0.7 + (abs(bearish_div["rsi_diff"]) / 100))

            rationale = (
                f"Bearish Divergence: Price +{bearish_div['price_diff']:.1f}%, "
                f"RSI -{bearish_div['rsi_diff']:.1f} (Exhaustion)"
            )

            # Timestamp: Strict candle timestamp
            ts_idx = d.index[-1]
            signal_ts = None

            if isinstance(ts_idx, (datetime, pd.Timestamp)):
                signal_ts = ts_idx
            else:
                try:
                    signal_ts = pd.to_datetime(ts_idx).to_pydatetime()
                except:
                    signal_ts = None

            if signal_ts:
                signal = Signal(
                    timestamp=signal_ts,
                    strategy_id=self.metadata().id,
                    mode="CUSTOM",
                    token=token.upper(),
                    timeframe=timeframe,
                    direction="short",
                    entry=round(entry, 2),
                    tp=round(tp, 2),
                    sl=round(sl, 2),
                    confidence=round(confidence, 2),
                    rationale=rationale,
                    source="ENGINE",
                    extra={
                        "divergence_type": "bearish",
                        "rsi": round(bearish_div["rsi_current"], 1),
                        "rsi_diff": round(bearish_div["rsi_diff"], 1),
                        "price_diff": round(bearish_div["price_diff"], 2),
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
                if context and "data" in context and token in context["data"]:
                    raw_data = context["data"][token]
                    df = (
                        pd.DataFrame(raw_data)
                        if isinstance(raw_data, list)
                        else raw_data
                    )
                else:
                    ohlcv = get_ohlcv_data(token, timeframe, limit=1000)
                    if not ohlcv:
                        continue
                    df = pd.DataFrame(ohlcv)

                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df.set_index("timestamp", inplace=True)

                all_signals.extend(self.analyze(df, token, timeframe))
            except Exception as e:
                print(f"Error in RSI Divergence for {token}: {e}")

        return all_signals
