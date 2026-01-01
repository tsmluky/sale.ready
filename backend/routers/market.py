from fastapi import APIRouter, Query
from typing import List, Optional
from core.market_data_api import get_market_summary, get_ohlcv_data

router = APIRouter()

@router.get("/summary")
def market_summary_endpoint(symbols: Optional[List[str]] = Query(None)):
    """
    Returns price and 24h change for the default watchlist.
    """
    if not symbols:
        # Default watchlist (Prioritize Major Caps for Free Tier)
        symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX"]

    
    return {"current_prices": get_market_summary(symbols)}


@router.get("/ohlcv/{token}")
def get_market_ohlcv(
    token: str, 
    timeframe: str = "30m", 
    limit: int = 100
):
    """
    Obtiene datos OHLCV (candlestick) para un token específico.
    
    Args:
        token: Símbolo del token (btc, eth, sol)
        timeframe: Intervalo de tiempo (1m, 5m, 15m, 30m, 1h, 4h, 1d)
        limit: Número de velas a retornar (máx 1000)
    
    Returns:
        Lista de datos OHLCV
    """
    # Validate timeframe?
    # Logic inside library handles it via CCXT
    
    data = get_ohlcv_data(token, timeframe, limit=limit)
    if not data:
        # 404? Or just empty list? Front needs list.
        return []
    return data

