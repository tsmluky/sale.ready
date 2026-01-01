from datetime import datetime
# Asumimos imports de tu backend
# from db.session import get_db
# from models_db import SignalModel
# from services.market_data import MarketDataService

class SignalEvaluatorWorker:
    """
    Worker que corre en segundo plano para evaluar señales PENDING.
    Replica la lógica de 'evaluated_logger.py' pero contra DB y API de datos.
    """
    
    def __init__(self, market_data_service):
        self.mds = market_data_service

    async def run_once(self):
        print("[Evaluator] Buscando señales pendientes...")
        # signals = db.query(SignalModel).filter(SignalModel.status == "PENDING").all()
        # MOCK:
        signals = [] 
        
        for sig in signals:
            await self.evaluate_signal(sig)

    async def evaluate_signal(self, sig):
        # 1. Determinar ventana de tiempo a revisar
        # Desde que se creó hasta ahora
        start_time = sig.created_at
        end_time = datetime.utcnow()
        
        # Si ha pasado poco tiempo, ignorar
        if (end_time - start_time).total_seconds() < 300: # 5 min mínimo
            return

        # 2. Pedir velas de 1m o 5m para alta precisión en la evaluación
        # Nota: Usamos velas de timeframe bajo para ver si tocó TP/SL intra-vela
        candles = await self.mds.get_ohlcv(
            token=sig.token, 
            timeframe="5m", 
            start=start_time, 
            end=end_time
        )
        
        if candles.empty:
            return

        # 3. Simular recorrido (Lógica de evaluated_logger.py)
        outcome = "PENDING"
        exit_price = None
        
        tp = sig.tp_price
        sl = sig.sl_price
        
        for _, row in candles.iterrows():
            high, low = row["high"], row["low"]
            
            if sig.direction == "LONG":
                if low <= sl:
                    outcome = "LOSS"
                    exit_price = sl
                    break
                if high >= tp:
                    outcome = "WIN"
                    exit_price = tp
                    break
            else: # SHORT
                if high >= sl:
                    outcome = "LOSS"
                    exit_price = sl
                    break
                if low <= tp:
                    outcome = "WIN"
                    exit_price = tp
                    break
        
        # 4. Actualizar DB si hubo desenlace
        if outcome != "PENDING":
            sig.status = "EVALUATED"
            sig.result = outcome # WIN / LOSS
            sig.exit_price = exit_price
            sig.closed_at = datetime.utcnow()
            
            # Calcular PnL
            if sig.direction == "LONG":
                pnl = (exit_price - sig.entry_price) / sig.entry_price
            else:
                pnl = (sig.entry_price - exit_price) / sig.entry_price
            
            sig.pnl_pct = pnl * 100.0
            
            print(f"[Evaluator] Señal {sig.id} -> {outcome} ({sig.pnl_pct:.2f}%)")
            # db.commit()
