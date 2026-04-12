# ⚡ AI Multi-Agent Trading Assistant

🚀 Live AI Trading Agent: https://trading-agent-production-feab.up.railway.app

💡 Built with FastAPI + Docker, delivering real-time AI-powered trading insights and automation.

Docker image : chandu013/trading-agent:latest

Multi-agent trading decision support system using Groq LLM, Yahoo Finance, Binance, and NewsAPI.

---

## 📁 Project Structure

```
trading_agent/
├── agents/
│   ├── data_agent.py          # OHLCV from Binance / Yahoo Finance
│   ├── identifier_agent.py    # Validates symbol + historical events
│   ├── fundamental_agent.py   # PE, market cap, ROE, etc.
│   ├── news_agent.py          # NewsAPI + MoneyControl + Economic Times scraper
│   ├── technical_agent.py     # Full SMC/ICT + EMA/RSI/MACD/BB + 10 strategies
│   ├── strategy_agent.py      # Setup selection: OB bounce, FVG, breakout
│   ├── risk_agent.py          # Position sizing & hard rules
│   └── decision_agent.py      # Weighted scoring + final trade card
├── orchestrator.py            # Dependency-aware async pipeline
├── main.py                    # FastAPI backend
├── config.py                  # All API keys & settings
├── requirements.txt
├── ui/
│   └── index.html             # Beautiful dark trading dashboard
└── utils/
    ├── logger.py              # Central logging (file + console)
    ├── llm_client.py          # Groq async wrapper
    ├── alerts.py              # Telegram alerts
    └── db.py                  # SQLite persistence
```

---

## 🚀 How to Run

### 1. Install dependencies
```bash
cd trading_agent
pip install -r requirements.txt
```

### 2. (Optional) Set environment variables
API keys are already hardcoded in `config.py`.  
To override, set env vars:
```bash
export GROQ_API_KEY=your_key
export NEWS_API_KEY=your_key
export TELEGRAM_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id   # send /start to @magnuskarlbot first
```

### 3. Start the backend
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open the UI
Visit: **http://localhost:8000**

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze` | Run full analysis |
| GET  | `/api/history` | Past analyses |
| GET  | `/api/health`  | Health check |

### Example POST body
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "trade_type": "swing",
  "account_size": 10000,
  "open_trades": 0
}
```

---

## 🤖 Agent Pipeline

```
Phase 1:  OHLCV data fetch (Binance or Yahoo)
Phase 2:  Identifier + News (parallel)
Phase 3:  Fundamental + Technical (parallel)
Phase 4:  Strategy (depends on Technical)
Phase 5:  Risk (depends on Strategy + Fundamental)
Phase 6:  Decision (aggregates all)
```

---

## 📊 Symbols Guide

| Type   | Example Symbols |
|--------|----------------|
| Crypto | BTCUSDT, ETHUSDT, SOLUSDT |
| US Stocks | AAPL, TSLA, NVDA |
| Indian Stocks | RELIANCE.NS, TCS.NS, INFY.NS |
| Indices | ^NSEI (Nifty), ^BSESN (Sensex) |

---

## ⚠️ Disclaimer
This is a **decision support tool**. Not financial advice. Always do your own research.
docker build -t chandu013/trading-agent:latest .
docker push chandu013/trading-agent:latest

docker build -t chandu013/trading-agent:latest . && docker push chandu013/trading-agent:latest

docker run -d -p 8000:8000 --name trading chandu013/trading-agent:latest

docker rm -f trading
docker run -d -p 8000:8000 --name trading chandu013/trading-agent:latest

http://localhost:8000/docs
