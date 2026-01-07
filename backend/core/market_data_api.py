# backend/market_data_api.py
"""
Módulo para obtener datos de mercado en tiempo real.
Refactorizado para usar CCXT (Binance) para consistencia con Trading Lab.
"""

import ccxt
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from core.cache import cache  # Importar Cache

print("[DEBUG] LOADING MARKET_DATA_API (Scale-Ready Fix)")


def get_ohlcv_data(
    symbol: str, timeframe: str = "30m", limit: int = 100, return_source: bool = False
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], str]]:
    """
    Obtiene datos OHLCV con Caching + Fallback.
    TTL: 60s para reducir latencia.
    """
    # 1. Intentar Cache
    cache_key = f"ohlcv:{symbol.upper()}:{timeframe}:{limit}"
    cached_data = cache.get(cache_key)
    if cached_data:
        # print(f"[MARKET] ⚡ Cache Hit for {cache_key}")
        if return_source:
            return cached_data, "cache"
        return cached_data

    # ... execution continues ...

    base_symbol = symbol.upper().replace("USDT", "").replace("-", "")
    ccxt_symbol = f"{base_symbol}/USDT"

    # 1. Fallback Order
    exchanges_config = [
        {"id": "binance", "class": ccxt.binance, "timeout": 5000},  # 5s timeout
        {"id": "kucoin", "class": ccxt.kucoin, "timeout": 5000},  # 5s timeout
        {"id": "bybit", "class": ccxt.bybit, "timeout": 5000},  # 5s timeout
    ]

    for cfg in exchanges_config:
        ex_id = cfg["id"]
        try:
            print(f"[MARKET DATA] Attempting fetch {ccxt_symbol} from {ex_id}...")
            exchange = cfg["class"](
                {"enableRateLimit": True, "timeout": cfg["timeout"]}
            )

            # [HARDENING] Retry with Exponential Backoff
            # Handles 429 Rate Limits gracefully prevents stampedes.
            max_retries = 3
            backoff = 1  # Start 1s
            
            for attempt in range(max_retries):
                try:
                    data = exchange.fetch_ohlcv(ccxt_symbol, timeframe, limit=limit)
                    break # Success
                except (ccxt.RateLimitExceeded, ccxt.NetworkError) as retry_err:
                     if attempt == max_retries - 1:
                         raise retry_err # Re-raise to trigger next exchange fallback
                     
                     sleep_time = backoff * (2 ** attempt)
                     print(f"[MARKET] ⚠️ 429/Network Error from {ex_id}. Retrying in {sleep_time}s...")
                     time.sleep(sleep_time)

            if data and len(data) > 0:
                print(f"[MARKET DATA] Success: {len(data)} candles from {ex_id}.")

                # Format
                ohlcv = []
                for candle in data:
                    ts = candle[0]
                    dt = datetime.fromtimestamp(ts / 1000)
                    ohlcv.append(
                        {
                            "timestamp": ts,
                            "time": dt.strftime("%Y-%m-%d %H:%M"),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5]),
                        }
                    )

                # Cache Valid Data: 20s TTL (Balance between load and freshness)
                cache.set(cache_key, ohlcv, ttl=20)
                if return_source:
                    return ohlcv, ex_id
                return ohlcv
        except BaseException as e:
            print(f"[MARKET DATA] ⚠️ Failed fetch from {ex_id}: {e}")
            continue  # Try next exchange

    # 2. Last Resort: Fail gracefully (No Mocks allowed per User Request)
    print("[MARKET DATA] 🚨 All exchanges failed. Returning EMPTY to avoid fake data.")
    if return_source:
        return [], "none"
    return []


def generate_mock_ohlcv(symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Generates synthetic OHLCV data for testing/fallback."""
    import random

    base_price = 50000.0 if "BTC" in symbol else 3000.0
    if "SOL" in symbol:
        base_price = 150.0

    data = []
    current_time = int(time.time() * 1000)
    # 1 hour intervals in ms
    interval_ms = 3600 * 1000

    for i in range(limit):
        ts = current_time - ((limit - i) * interval_ms)
        dt = datetime.fromtimestamp(ts / 1000)

        # Random walk
        change = random.uniform(-0.02, 0.02)
        close = base_price * (1 + change)
        open_p = base_price
        high = max(open_p, close) * 1.01
        low = min(open_p, close) * 0.99

        data.append(
            {
                "timestamp": ts,
                "time": dt.strftime("%Y-%m-%d %H:%M"),
                "open": round(open_p, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": round(random.uniform(100, 1000), 2),
            }
        )
        base_price = close

    return data


def get_market_summary(symbols: List[str]) -> List[Dict[str, Any]]:
    """
    Obtiene precio y cambio 24h para múltiples símbolos.
    """
    # 1. Cache Check (Strict)
    s_key = "-".join(sorted(symbols))
    cache_key = f"market:summary:{hash(s_key)}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 2. Try Fetch with Fallbacks
    exchanges_config = [
        {"id": "binance", "class": ccxt.binance},
        {"id": "kucoin", "class": ccxt.kucoin},
        {"id": "bybit", "class": ccxt.bybit},
        {"id": "kraken", "class": ccxt.kraken}, # Kraken often reliable in US/EU
    ]

    unique_syms = list(set([s.upper().replace("USDT", "").replace("-", "") for s in symbols]))
    # Pairs format might differ slightly per exchange, but "BTC/USDT" is fairly standard. 
    # Some exchanges need specific handling if strictly needed, but CCXT handles most "/"
    pairs = [f"{s}/USDT" for s in unique_syms]

    for cfg in exchanges_config:
        ex_id = cfg["id"]
        try:
            exchange = cfg["class"]({
                "enableRateLimit": True,
                "timeout": 4000
            })
            
            # Special handling for Kraken pairs if needed (often XBT/USD or similar), 
            # but let's stick to standard USDT pairs for crypto-to-crypto exchanges.
            # If Kraken fails on USDT pairs, loop continues.
            
            tickers = exchange.fetch_tickers(pairs)
            
            summary = []
            for p in pairs:
                t = tickers.get(p)
                # Some exchanges return different keys, but CCXT standardizes most.
                if t:
                    change = t.get("percentage")
                    if change is None and t.get("open") and t["open"] > 0:
                        change = ((t["last"] - t["open"]) / t["open"]) * 100
                    
                    summary.append({
                        "symbol": p.replace("/USDT", ""),
                        "price": t["last"],
                        "change_24h": change or 0.0
                    })
            
            if summary:
                # 3. Set Cache: 15s TTL
                cache.set(cache_key, summary, ttl=15)
                # print(f"[MARKET] Got summary from {ex_id}")
                return summary

        except Exception as e:
            print(f"[MARKET] Failed to fetch summary from {ex_id}: {e}")
            continue

    return []


def get_current_price(symbol: str) -> Optional[float]:
    """
    Obtiene el precio actual de un símbolo.
    """
    try:
        data = get_ohlcv_data(symbol, limit=1)
        if data:
            return data[-1]["close"]
    except Exception:
        pass
    return None
