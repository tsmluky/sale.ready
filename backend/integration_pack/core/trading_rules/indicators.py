import pandas as pd

def ema(series: pd.Series, span: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=span, adjust=False).mean()

def rma(series: pd.Series, n: int) -> pd.Series:
    """Running Moving Average (used for ATR)"""
    return series.ewm(alpha=1/n, adjust=False).mean()

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range"""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return rma(tr, period)

def bollinger(series: pd.Series, period: int = 20, stds: float = 2.0):
    """Bollinger Bands: returns (mid, upper, lower)"""
    mid = series.rolling(period).mean()
    sd = series.rolling(period).std(ddof=0)
    upper = mid + stds * sd
    lower = mid - stds * sd
    return mid, upper, lower

def ensure_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the DataFrame has the minimal features required for standard strategies:
    - ATR (14)
    - EMA50
    - EMA200
    """
    df = df.copy()
    if "ATR" not in df.columns:
        df["ATR"] = atr(df, 14)
    if "EMA50" not in df.columns:
        df["EMA50"] = ema(df["close"], 50)
    if "EMA200" not in df.columns:
        df["EMA200"] = ema(df["close"], 200)
    return df
