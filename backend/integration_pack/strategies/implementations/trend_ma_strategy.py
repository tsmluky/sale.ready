from typing import List
from datetime import datetime
from backend.core.schemas import Signal
from strategies.base import Strategy, StrategyConfigInRuntime
# Importamos las reglas puras (asegúrate de que core.trading_rules sea accesible)
from backend.core.trading_rules.indicators import ensure_features
from backend.core.trading_rules.side_generators import side_ma_cross
from backend.core.trading_rules.signal_builder import compute_entry_tp_sl

class TrendMaCrossStrategy(Strategy):
    """
    Estrategia de Cruce de Medias Móviles (MA Cross).
    Portado de trading_lab: engine.py -> ma_cross_series
    """
    id = "TREND_MA_CROSS_V1"
    name = "Trend MA Cross (Generic)"
    version = "1.0"
    default_timeframe = "60"
    
    # Parámetros por defecto (se pueden sobreescribir desde DB)
    default_params = {
        "fast": 20,
        "slow": 50,
        "tp_atr": 1.5,
        "sl_atr": 1.0
    }

    def run(self, config: StrategyConfigInRuntime, market_data_service) -> List[Signal]:
        signals = []
        params = config.params or self.default_params
        
        for token in config.tokens:
            # 1. Obtener datos (limit=300 es suficiente para EMA50/200)
            df = market_data_service.get_ohlcv(
                token=token, 
                timeframe=self.default_timeframe, 
                limit=300
            )
            
            if df.empty:
                continue

            # 2. Calcular indicadores
            df = ensure_features(df)

            # 3. Generar serie de señales (LONG/SHORT/None)
            side_series = side_ma_cross(
                df, 
                fast=params.get("fast", 20), 
                slow=params.get("slow", 50)
            )

            # 4. Calcular niveles de entrada para la ÚLTIMA vela
            sig_dict = compute_entry_tp_sl(
                df, 
                side_series, 
                tp_atr=params.get("tp_atr", 1.5), 
                sl_atr=params.get("sl_atr", 1.0)
            )

            # 5. Emitir señal si existe
            if sig_dict["side"] != "NO_TRADE":
                # Crear objeto Signal (Pydantic)
                new_signal = Signal(
                    strategy_id=self.id,
                    token=token,
                    timeframe=self.default_timeframe,
                    direction=sig_dict["side"],
                    entry_price=sig_dict["entry_price"],
                    tp_price=sig_dict["tp_price"],
                    sl_price=sig_dict["sl_price"],
                    confidence=100.0, # Lógica simple por ahora
                    rationale=f"MA Cross ({params['fast']}/{params['slow']})",
                    source="quant_lab",
                    created_at=datetime.utcnow()
                )
                signals.append(new_signal)

        return signals

