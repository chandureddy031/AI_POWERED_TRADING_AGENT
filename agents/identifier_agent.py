"""
agents/identifier_agent.py
Validates the symbol, resolves full name, exchange, and fetches major
historical market events using LLM + NewsAPI.
"""
import requests
from utils.logger import get_logger
from utils.llm_client import llm_json
from config import NEWS_API_KEY

log = get_logger("identifier_agent")

_NEWS_EP = "https://newsapi.org/v2/everything"


def _search_news_events(symbol: str) -> list[str]:
    """Fetch top 5 historical headlines for the symbol."""
    log.info("Searching historical news for %s", symbol)
    params = {
        "q": f"{symbol} market crash OR rally OR major event",
        "sortBy": "relevancy",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY,
        "language": "en",
    }
    try:
        r = requests.get(_NEWS_EP, params=params, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        headlines = [a["title"] for a in articles if a.get("title")]
        log.debug("Found %d historical headlines", len(headlines))
        return headlines
    except Exception as exc:
        log.warning("Historical news fetch failed: %s", exc)
        return []


async def run(symbol: str, trade_type: str) -> dict:
    """
    Identify and validate the asset.
    Returns:
      {
        "symbol": str, "full_name": str, "asset_type": str,
        "exchange": str, "sector": str,
        "historical_events": [str, ...],
        "validation": "valid" | "invalid",
        "notes": str
      }
    """
    log.info("identifier_agent.run | symbol=%s trade_type=%s", symbol, trade_type)

    headlines = _search_news_events(symbol)
    headlines_text = "\n".join(headlines) if headlines else "No headlines found."

    system = (
        "You are a financial asset identification expert. "
        "Return ONLY valid JSON."
    )
    user = f"""
Symbol: {symbol}
Trade type: {trade_type}
Recent major headlines:
{headlines_text}

Identify this asset and return JSON:
{{
  "symbol": "{symbol}",
  "full_name": "<full company or coin name>",
  "asset_type": "crypto|stock|index|etf",
  "exchange": "<exchange name>",
  "sector": "<sector or category>",
  "historical_events": ["<event 1 with year>", "<event 2 with year>", "<event 3 with year>"],
  "validation": "valid",
  "notes": "<any important context for trader>"
}}
"""
    result = await llm_json(system, user)
    log.info("identifier_agent result: validation=%s", result.get("validation"))
    return result
