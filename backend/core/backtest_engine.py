
import pandas as pd
import importlib
import inspect
import sys
import os
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add root to path to find 'strategies'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.market_data_api import get_ohlcv_data

class BacktestEngine:
    """
    Motor de simulación histórica para validar estrategias.
    """
    
    def __init__(self, initial_capital: float = 1000.0):
        self.initial_capital = initial_capital
        self.strategies = {}
        
    def load_strategy(self, strategy_id: str):
        """
        Carga una estrategia por su ID.
        Prioridad: 
        1. Registry (Memoria/Oficial)
        2. Import dinámico por nombre de archivo (Legacy)
        """
        try:
            # 1. Try Registry First
            from strategies.registry import get_registry
            registry = get_registry()
            strategy_instance = registry.get(strategy_id)
            
            if strategy_instance:
                self.strategies[strategy_id] = strategy_instance
                print(f"[Backtest] Estrategia cargada desde Registry: {strategy_id}")
                return

            # 2. Fallback: Dynamic Import (Legacy filename match)
            print(f"[Backtest] Strategy '{strategy_id}' not in registry. Trying file import...")
            module_name = f"strategies.{strategy_id}"
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
                
            found_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and obj.__module__ == module_name:
                    if hasattr(obj, 'generate_signals') and hasattr(obj, 'metadata'):
                        found_class = obj
                        break
            
            if found_class:
                self.strategies[strategy_id] = found_class()
                print(f"[Backtest] Estrategia cargada desde archivo: {strategy_id}")
            else:
                raise Exception(f"No se encontró clase compatible en {strategy_id}")
            
        except Exception as e:
            print(f"[Backtest] Error cargando estrategia {strategy_id}: {e}")
            raise e

        except Exception as e:
            print("[Backtest Critical Error]:")
            traceback.print_exc()
            raise e

    def _safe_float(self, val):
        import math
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f):
                return 0.0
            return f
        except:
            return 0.0

    def run(self, strategy_id: str, symbol: str, timeframe: str = "1h", days: int = 30) -> Dict[str, Any]:
        """
        Ejecuta el backtest Walk-Forward.
        Recorre vela a vela simulando que "hoy es t".
        """
        try:
            self.load_strategy(strategy_id)
            strategy = self.strategies.get(strategy_id)
            if not strategy:
                raise Exception("Estrategia no cargada")
    
            # Determine limit based on candles per day
            candles_per_day = 24  # default 1h
            if timeframe == '30m': candles_per_day = 48
            if timeframe == '4h': candles_per_day = 6
            if timeframe == '15m': candles_per_day = 96
            
            limit = days * candles_per_day
            
            limit += 50 
            # Removed arbitrary 1000 cap to support long backtests with pagination
            # limit = min(limit, 1000)
    
            print(f"[Backtest] Descargando {limit} velas para {symbol}...")
            try:
                ohlcv = get_ohlcv_data(symbol, timeframe, limit=limit)
            except Exception as e:
                raise Exception(f"Error descargando datos: {str(e)}")
            
            if not ohlcv or len(ohlcv) < 60:
                raise Exception("Datos históricos insuficientes para backtest")
    
            df = pd.DataFrame(ohlcv)
            if "timestamp" in df.columns:
                df["timestamp_dt"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            trades = []
            equity_curve = [] # List of {time, strategy_equity, buy_hold_equity, price}
            
            current_capital = self.initial_capital
            initial_price = df.iloc[50]['open'] # Start price after warmup
            buy_hold_amount = self.initial_capital / initial_price
            
            active_position = None
            warmup = 50
            
            print(f"[Backtest] Running loop from {warmup} to {len(df)}")
            
            for i in range(warmup, len(df)):
                current_candle = df.iloc[i]
                current_time = current_candle['time']
                current_ts_val = current_candle['timestamp']
                
                # --- A. GESTIÓN DE SALIDAS (TP/SL) ---
                if active_position:
                    exit_price = None
                    exit_reason = None
                    
                    is_long = active_position['type'].lower() == 'long'
                    entry_price = active_position['entry']
                    sl_price = active_position['sl']
                    tp_price = active_position['tp']
                    
                    low = current_candle['low']
                    high = current_candle['high']
                    
                    sl_hit = False
                    if is_long and low <= sl_price:
                        sl_hit = True
                        exit_price = sl_price 
                    elif not is_long and high >= sl_price:
                        sl_hit = True
                        exit_price = sl_price
                    
                    if sl_hit:
                        exit_reason = "STOP_LOSS"
                    elif is_long and high >= tp_price:
                        exit_price = tp_price
                        exit_reason = "TAKE_PROFIT"
                    elif not is_long and low <= tp_price:
                        exit_price = tp_price
                        exit_reason = "TAKE_PROFIT"
                    
                    if exit_price:
                        quantity = active_position['quantity']
                        
                        if is_long:
                            pnl_raw = (exit_price - entry_price) * quantity
                        else:
                            pnl_raw = (entry_price - exit_price) * quantity
                            
                        # ZERO FEES for Marketing/MVP Presentation
                        fees = 0.0 
                        net_pnl = pnl_raw - fees
                        
                        current_capital += net_pnl
                        
                        trades.append({
                            "id": len(trades) + 1,
                            "entry_time": active_position["time_str"],
                            "exit_time": current_time,
                            "exit_ts": self._safe_float(current_ts_val), # Add for chart markers
                            "symbol": symbol.upper(),
                            "type": active_position["type"].upper(),
                            "entry": entry_price,
                            "exit": exit_price,
                            "pnl": round(self._safe_float(net_pnl), 2),
                            "result": "WIN" if net_pnl > 0 else "LOSS",
                            "reason": exit_reason
                        })
                        
                        active_position = None 
                
                # --- B. GESTIÓN DE ENTRADAS ---
                if not active_position:
                    df_slice = df.iloc[:i+1].copy()
                    try:
                        signals = strategy.generate_signals(
                            tokens=[symbol], 
                            timeframe=timeframe, 
                            context={"data": {symbol: df_slice}}
                        )
                        
                        valid_signal = None
                        if signals:
                            last_sig = signals[-1]
                            sig_ts = pd.to_datetime(last_sig.timestamp)
                            current_ts = df_slice["timestamp_dt"].iloc[-1]
                            
                            if sig_ts == current_ts:
                                valid_signal = last_sig
                                
                        if valid_signal:
                            entry_price = valid_signal.entry
                            sl_price = valid_signal.sl
                            tp_price = valid_signal.tp
                            quantity = current_capital / entry_price
                            
                            active_position = {
                                "type": valid_signal.direction,
                                "entry": entry_price,
                                "sl": sl_price,
                                "tp": tp_price,
                                "quantity": quantity,
                                "time_str": current_time,
                                "timestamp": current_ts_val
                            }
                            
                    except Exception as e:
                        pass
    
                # --- C. UPDATE EQUITY CURVE (Each Candle) ---
                # Calculate floating equity
                floating_equity = current_capital
                if active_position:
                    curr_p = float(current_candle['close'])
                    qty = active_position['quantity']
                    # Floating PnL
                    if active_position['type'] == 'long':
                        floating_pnl = (curr_p - active_position['entry']) * qty
                    else:
                        floating_pnl = (active_position['entry'] - curr_p) * qty
                    floating_equity += floating_pnl
                
                try:
                    close_price = float(current_candle['close'])
                    buy_hold_equity = buy_hold_amount * close_price
                    
                    equity_curve.append({
                        "time": str(current_time),
                        "timestamp": self._safe_float(current_ts_val),
                        "strategy_equity": round(self._safe_float(floating_equity), 2),
                        "buy_hold_equity": round(self._safe_float(buy_hold_equity), 2),
                        "price": round(self._safe_float(close_price), 2)
                    })
                except Exception as e:
                    print(f"[Backtest Warning] Error adding curve point at {i}: {e}")
    
            wins = [t for t in trades if t['pnl'] > 0]
            win_rate = (len(wins) / len(trades) * 100) if trades else 0
            
            final_buy_hold = equity_curve[-1]['buy_hold_equity'] if equity_curve else self.initial_capital
            
            # --- D. METRICS CALCULATION ---
            # Max Drawdown
            max_equity = self.initial_capital
            max_drawdown = 0.0
            
            for point in equity_curve:
                eq = point['strategy_equity']
                if eq > max_equity:
                    max_equity = eq
                
                dd = (eq - max_equity) / max_equity
                if dd < max_drawdown:
                    max_drawdown = dd
            
            roi_pct = ((current_capital - self.initial_capital) / self.initial_capital) * 100

            return {
                "metrics": {
                    "initial_capital": round(self._safe_float(self.initial_capital), 2),
                    "final_capital": round(self._safe_float(current_capital), 2),
                    "total_pnl": round(self._safe_float(current_capital - self.initial_capital), 2),
                    "roi_pct": round(self._safe_float(roi_pct), 2),
                    "buy_hold_pnl": round(self._safe_float(final_buy_hold - self.initial_capital), 2),
                    "max_drawdown": round(self._safe_float(max_drawdown * 100), 2),
                    "total_trades": int(len(trades)),
                    "win_rate": round(self._safe_float(win_rate), 1),
                    "best_trade": round(self._safe_float(max([t['pnl'] for t in trades]) if trades else 0), 2),
                    "worst_trade": round(self._safe_float(min([t['pnl'] for t in trades]) if trades else 0), 2),
                },
                "trades": trades[-50:],
                "curve": equity_curve 
            }
        except Exception as e:
            print("[Backtest Critical Error]:")
            traceback.print_exc()
            raise e

