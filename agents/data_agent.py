"""
agents/data_agent.py
Fetches OHLCV price data from Yahoo Finance (stocks) or Binance (crypto).
"""
import pandas as pd
import yfinance as yf
import requests
from utils.logger import get_logger
from config import BINANCE_BASE

log = get_logger("data_agent")

# timeframe → (yfinance interval, Binance interval, yfinance period)
TF_MAP = {
    "1m":  ("1m",  "1m",  "1d"),
    "5m":  ("5m",  "5m",  "5d"),
    "15m": ("15m", "15m", "5d"),
    "1h":  ("1h",  "1h",  "30d"),
    "4h":  ("4h",  "4h",  "60d"),
    "1d":  ("1d",  "1d",  "180d"),
    "1w":  ("1wk", "1w",  "365d"),
}

CRYPTO_SYMBOLS = {"BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "AVAX", "MATIC"}


def _is_crypto(symbol: str) -> bool:
    base = symbol.upper().replace("USDT", "").replace("USD", "")
    return base in CRYPTO_SYMBOLS or symbol.upper().endswith("USDT")


def _fetch_binance(symbol: str, tf: str, limit: int = 300) -> pd.DataFrame:
    log.info("Fetching Binance OHLCV | symbol=%s tf=%s limit=%d", symbol, tf, limit)
    sym = symbol.upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    _, b_tf, _ = TF_MAP.get(tf, ("1h", "1h", "30d"))
    url = f"{BINANCE_BASE}/klines"
    params = {"symbol": sym, "interval": b_tf, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","qav","num_trades","tbbav","tbqav","ignore"
        ])
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df = df.set_index("open_time")
        for col in ["open","high","low","close","volume"]:
            df[col] = df[col].astype(float)
        log.info("Binance fetch OK | rows=%d", len(df))
        return df[["open","high","low","close","volume"]]
    except Exception as exc:
        log.error("Binance fetch failed: %s", exc, exc_info=True)
        raise


def _fetch_yahoo(symbol: str, tf: str) -> pd.DataFrame:
    log.info("Fetching Yahoo Finance OHLCV | symbol=%s tf=%s", symbol, tf)
    yf_tf, _, period = TF_MAP.get(tf, ("1h", "1h", "30d"))
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=yf_tf)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open","high","low","close","volume"]].dropna()
        log.info("Yahoo fetch OK | rows=%d", len(df))
        return df
    except Exception as exc:
        log.error("Yahoo fetch failed: %s", exc, exc_info=True)
        raise


def fetch_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Public entry point.
    Auto-detects crypto vs stock and routes to the correct data source.
    Returns DataFrame with columns: open, high, low, close, volume.
    """
    log.info("fetch_ohlcv | symbol=%s timeframe=%s", symbol, timeframe)
    if _is_crypto(symbol):
        return _fetch_binance(symbol, timeframe)
    else:
        return _fetch_yahoo(symbol, timeframe)


def get_current_price(symbol: str) -> float:
    """Return latest close price."""
    log.info("get_current_price | symbol=%s", symbol)
    df = fetch_ohlcv(symbol, "1m")
    price = float(df["close"].iloc[-1])
    log.info("Current price for %s = %.4f", symbol, price)
    return price
