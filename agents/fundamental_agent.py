"""
agents/fundamental_agent.py
Fetches fundamental data (PE ratio, market cap, volume, 52-week range, etc.)
via yfinance, then asks LLM to summarise implications.
"""
import yfinance as yf
from utils.logger import get_logger
from utils.llm_client import llm_json

log = get_logger("fundamental_agent")


def _fetch_fundamentals(symbol: str) -> dict:
    """Pull key fundamental fields from yfinance."""
    log.info("Fetching fundamentals for %s", symbol)
    try:
        t = yf.Ticker(symbol)
        info = t.info
        keys = [
            "shortName","sector","industry","marketCap","trailingPE","forwardPE",
            "priceToBook","debtToEquity","returnOnEquity","revenueGrowth",
            "earningsGrowth","dividendYield","fiftyTwoWeekLow","fiftyTwoWeekHigh",
            "averageVolume","volume","currentPrice","beta",
        ]
        data = {k: info.get(k) for k in keys}
        log.debug("Fundamentals fetched: %s", list(data.keys()))
        return data
    except Exception as exc:
        log.warning("yfinance fundamentals failed (%s): %s", symbol, exc)
        return {}


async def run(symbol: str, asset_type: str) -> dict:
    """
    Return fundamental analysis dict with LLM interpretation.
    For crypto (no PE etc.) falls back to on-chain/market metrics via LLM.
    """
    log.info("fundamental_agent.run | symbol=%s asset_type=%s", symbol, asset_type)

    raw = _fetch_fundamentals(symbol)

    system = "You are a fundamental analysis expert. Return ONLY valid JSON."
    user = f"""
Asset: {symbol} ({asset_type})
Raw fundamental data:
{raw}

Analyse and return JSON:
{{
  "pe_ratio": <float or null>,
  "market_cap_b": <billion USD float or null>,
  "52w_low": <float>,
  "52w_high": <float>,
  "current_price": <float>,
  "volume_vs_avg": "<above/below/at average>",
  "debt_equity": <float or null>,
  "roe": <float or null>,
  "revenue_growth": <float or null>,
  "dividend_yield": <float or null>,
  "beta": <float or null>,
  "fundamental_signal": "bullish|bearish|neutral",
  "confidence": <0.0-1.0>,
  "summary": "<2-3 sentence interpretation for a trader>",
  "key_risks": ["<risk1>", "<risk2>"],
  "key_strengths": ["<strength1>", "<strength2>"]
}}
"""
    result = await llm_json(system, user)
    log.info("fundamental_agent result: signal=%s conf=%.2f",
             result.get("fundamental_signal"), result.get("confidence", 0))
    return result
