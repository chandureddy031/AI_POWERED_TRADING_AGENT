"""
agents/news_agent.py - Multi-source news: NewsAPI + 6 scrapers (BTC + stocks)
"""
import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger
from utils.llm_client import llm_json
from config import NEWS_API_KEY

log = get_logger("news_agent")
HDR = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36","Accept-Language":"en-US,en;q=0.9"}

def _get(url, timeout=10):
    try:
        r = requests.get(url, headers=HDR, timeout=timeout)
        return r if r.status_code==200 else None
    except Exception as e:
        log.warning("GET failed %s: %s", url, e)
        return None

def _newsapi(symbol, query=None):
    q = query or symbol
    log.info("NewsAPI | q=%s", q)
    try:
        r = requests.get("https://newsapi.org/v2/everything",
            params={"q":q,"sortBy":"publishedAt","pageSize":10,"language":"en","apiKey":NEWS_API_KEY},timeout=10)
        arts = r.json().get("articles",[])
        return [f"{a['title']} — {(a.get('description') or '')[:80]}" for a in arts if a.get("title")]
    except Exception as e:
        log.warning("NewsAPI failed: %s",e); return []

def _cryptopanic(symbol):
    """CryptoPanic free RSS endpoint for crypto news."""
    log.info("CryptoPanic RSS | %s", symbol)
    base = symbol.replace("USDT","").replace("USD","").upper()
    r = _get(f"https://cryptopanic.com/news/{base}/rss/")
    if not r: return []
    soup = BeautifulSoup(r.text,"lxml")
    return [item.title.text.strip() for item in soup.find_all("item")[:8]]

def _coindesk(symbol):
    log.info("CoinDesk scrape | %s", symbol)
    base = symbol.replace("USDT","").replace("USD","").lower()
    r = _get(f"https://www.coindesk.com/tag/{base}/")
    if not r: return []
    soup = BeautifulSoup(r.text,"lxml")
    tags = soup.select("h6 a, h4 a, .headline a")
    return [t.get_text(strip=True) for t in tags[:8]]

def _cointelegraph(symbol):
    log.info("CoinTelegraph scrape | %s", symbol)
    base = symbol.replace("USDT","").replace("USD","").lower()
    r = _get(f"https://cointelegraph.com/tags/{base}")
    if not r: return []
    soup = BeautifulSoup(r.text,"lxml")
    tags = soup.select("span.post-card-inline__title, h2.post-card__title")
    return [t.get_text(strip=True) for t in tags[:8]]

def _investing_com(symbol):
    log.info("Investing.com news | %s", symbol)
    r = _get(f"https://www.investing.com/search/?q={symbol}&tab=news")
    if not r: return []
    soup = BeautifulSoup(r.text,"lxml")
    tags = soup.select("article h3 a, .articleItem a")
    return [t.get_text(strip=True) for t in tags[:6]]

def _economic_times(symbol):
    log.info("Economic Times | %s", symbol)
    r = _get(f"https://economictimes.indiatimes.com/topic/{symbol.lower().replace('usdt','').replace('usd','')}")
    if not r: return []
    soup = BeautifulSoup(r.text,"lxml")
    tags = soup.select("div.eachStory h3 a, a.wrapLines")
    return [t.get_text(strip=True) for t in tags[:6]]

def _moneycontrol(symbol):
    log.info("MoneyControl | %s", symbol)
    base = symbol.lower().replace("usdt","").replace("usd","").replace(".ns","").replace(".bo","")
    r = _get(f"https://www.moneycontrol.com/news/tags/{base}.html")
    if not r: return []
    soup = BeautifulSoup(r.text,"lxml")
    tags = soup.select("li.clearfix h2 a, h2.article_title a, .article_box h2 a")
    return [t.get_text(strip=True) for t in tags[:6]]

def _is_crypto(symbol):
    return any(x in symbol.upper() for x in ["BTC","ETH","SOL","BNB","XRP","USDT","DOGE","ADA"])

async def run(symbol: str) -> dict:
    log.info("news_agent.run | symbol=%s", symbol)
    all_headlines = []
    all_headlines += _newsapi(symbol)

    if _is_crypto(symbol):
        all_headlines += _cryptopanic(symbol)
        all_headlines += _coindesk(symbol)
        all_headlines += _cointelegraph(symbol)
        all_headlines += _newsapi(symbol, query=symbol.replace("USDT","").replace("USD","")+" crypto news")
    else:
        all_headlines += _moneycontrol(symbol)
        all_headlines += _economic_times(symbol)
        all_headlines += _investing_com(symbol)

    # dedupe
    seen = set(); unique = []
    for h in all_headlines:
        if h and h not in seen: seen.add(h); unique.append(h)

    log.info("Total unique headlines: %d", len(unique))
    if not unique:
        return {"sentiment":"neutral","confidence":0.3,"key_events":[],
                "summary":"No news data found.","sources_used":0}

    text = "\n".join(f"- {h}" for h in unique[:25])
    system = "You are a financial news sentiment analyst. Return ONLY valid JSON."
    user = f"""Asset: {symbol}\nHeadlines:\n{text}\n
Return JSON:
{{
  "sentiment":"bullish|bearish|neutral",
  "confidence":<0.0-1.0>,
  "key_events":["<event1>","<event2>","<event3>"],
  "earnings_mention":true|false,
  "regulatory_mention":true|false,
  "macro_impact":"positive|negative|neutral",
  "fear_greed":"fear|greed|neutral",
  "summary":"<2-3 sentence synthesis>",
  "sources_used":{len(unique)}
}}"""
    result = await llm_json(system, user)
    result["sources_used"] = len(unique)
    log.info("news_agent done | sentiment=%s conf=%.2f sources=%d",
             result.get("sentiment"), result.get("confidence",0), len(unique))
    return result
