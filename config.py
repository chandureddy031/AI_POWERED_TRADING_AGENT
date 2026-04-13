import os

# ─── API Keys ───────────────────────────────────────────────────────────────
GROQ_API_KEY       = os.getenv("GROQ_API_KEY","")
NEWS_API_KEY       = os.getenv("NEWS_API_KEY","")
TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN",   "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")   # set after /start on bot

# ─── LLM ────────────────────────────────────────────────────────────────────
GROQ_MODEL         = "llama-3.3-70b-versatile"          # best free Groq model
GROQ_BASE_URL      = "https://api.groq.com/openai/v1"

# ─── Data Sources ───────────────────────────────────────────────────────────
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
BINANCE_BASE       = "https://api.binance.com/api/v3"
MONEYCONTROL_BASE  = "https://www.moneycontrol.com"

# ─── Risk Defaults ──────────────────────────────────────────────────────────
MAX_RISK_PCT       = 0.02    # 2 % per trade
MAX_OPEN_TRADES    = 3
MIN_CONFIDENCE     = 0.60

# ─── Alert Thresholds ───────────────────────────────────────────────────────
ALERT_CONFIDENCE   = 0.65

# ─── DB ─────────────────────────────────────────────────────────────────────
DB_PATH            = "data/trading.db"

# ─── Logging ────────────────────────────────────────────────────────────────
LOG_LEVEL          = "INFO"
LOG_FILE           = "data/trading.log"
