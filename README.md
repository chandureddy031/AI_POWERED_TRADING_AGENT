# ⚡ AI Trading Assistant — Multi-Agent System

<<<<<<< HEAD
🚀 Live AI Trading Agent: https://trading-agent-production-feab.up.railway.app

💡 Built with FastAPI + Docker, delivering real-time AI-powered trading insights and automation.

Docker image : chandu013/trading-agent:latest

Multi-agent trading decision support system using Groq LLM, Yahoo Finance, Binance, and NewsAPI.
=======
A real-world agentic AI system that analyses stocks and crypto using 8 specialized AI agents working together — and tells you whether to BUY, SELL, or HOLD.

## 📸 Screenshots We are 
<p align="center">
  <img src="./ings/Screenshot 2026-04-13 183829.png" width="45%" />
  <img src="./ings/Screenshot 2026-04-13 185049.png" width="45%" />
</p>

<p align="center">
  <img src="./ings/Screenshot 2026-04-13 185110.png" width="45%" />
  <img src="./ings/Screenshot 2026-04-13 185117.png" width="45%" />
</p>

<p align="center">
  <img src="./ings/Screenshot 2026-04-13 185131.png" width="45%" />
  <img src="./ings/Screenshot 2026-04-13 185137.png" width="45%" />
</p>

## 🧠 What Is This?

Most trading tools give you one signal from one algorithm. This system uses **8 AI agents**, each doing one specific job, and then combines their findings to make a final decision — just like a team of analysts working together.

You type in a symbol like `BTCUSDT` or `RELIANCE.NS`, pick a timeframe, and the system:

1. Fetches live price data
2. Reads recent news from 6 sources
3. Checks fundamentals (PE ratio, market cap, etc.)
4. Detects 40+ technical patterns (SMC, ICT, Head & Shoulders, FVGs, Order Blocks...)
5. Validates a trade setup
6. Checks your risk
7. Makes a final decision with confidence score
8. Sends you a Telegram alert if confidence is high enough

---

## 🤖 What Is Agentic AI? (Simple Explanation)

Think of regular AI like asking one person a question. They answer from what they know.

**Agentic AI** is different. It's like hiring a whole team:

```
You ask: "Should I buy Bitcoin right now?"

Normal AI:  One response based on training data.

Agentic AI: 
  → News Analyst reads today's headlines
  → Technical Analyst checks charts and patterns
  → Fundamentals Analyst checks market cap and volume
  → Risk Manager checks your account size
  → Decision Maker combines everything and answers
```

Each "agent" is a focused AI with a specific job. They pass their findings to the next agent. The final answer comes from all of them together — not just one.

---

## 🔄 Why No AgentScope Framework?

AgentScope is a framework for managing agents. But frameworks add complexity, extra dependencies, and can be hard to debug.

This project uses **raw Python + asyncio** instead. Here's why that's actually better for learning:

| Thing | AgentScope Framework | This Project (Raw Python) |
|-------|---------------------|--------------------------|
| Code you can read | Hidden inside framework | You see every line |
| Dependencies | Heavy | Minimal |
| Debugging | Hard | Just check the logs |
| Learning value | Low (framework does it) | High (you built it) |
| Performance | Framework overhead | Direct async calls |

The agents here communicate by **passing Python dictionaries** to each other. Simple, fast, transparent.

> 💡 **The agentic pattern is in the design, not the framework.** Each agent has one job, agents depend on each other, and results are combined. That's what makes it agentic.

---

## 🗂️ Project Structure — Every File Explained

```
trading_agent/
│
├── 📄 config.py               ← All your API keys and settings live here
├── 📄 requirements.txt        ← Python packages to install
├── 📄 main.py                 ← The web server (FastAPI). Starts the app, handles requests
├── 📄 orchestrator.py         ← The conductor. Runs all 8 agents in the right order
│
├── 🤖 agents/
│   ├── data_agent.py          ← Agent 1: Fetches live price data (Binance for crypto, Yahoo for stocks)
│   ├── identifier_agent.py    ← Agent 2: Identifies the asset, validates it, finds historical events
│   ├── news_agent.py          ← Agent 3: Scrapes news from 6 sources, classifies sentiment
│   ├── fundamental_agent.py   ← Agent 4: Gets PE ratio, market cap, ROE, beta, 52-week range
│   ├── technical_agent.py     ← Agent 5: Detects 40+ patterns — SMC, ICT, candlesticks, chart patterns
│   ├── strategy_agent.py      ← Agent 6: Picks the best trade setup from all the data
│   ├── risk_agent.py          ← Agent 7: Calculates position size, checks risk rules
│   └── decision_agent.py      ← Agent 8: Combines everything, gives BUY/SELL/HOLD + confidence
│
├── 🛠️ utils/
│   ├── logger.py              ← Logging setup used by every single agent and function
│   ├── llm_client.py          ← Connects to Groq (the free AI brain) — used by all agents
│   ├── alerts.py              ← Sends Telegram messages when confidence is high enough
│   └── db.py                  ← Saves every analysis to SQLite so you can see history
│
├── 🌐 ui/
│   └── index.html             ← The full trading dashboard (HTML + CSS + JS, no framework needed)
│
└── 📁 data/
    └── trading.db             ← Auto-created SQLite database (your analysis history)
```

---

## 🔄 How The Agents Work Together

This is the agent pipeline. Each box is one agent doing its job:

```
┌─────────────────────────────────────────────────────┐
│                    YOU (The User)                    │
│         "Analyse BTCUSDT on 1h timeframe"           │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │  🗂️  DATA AGENT         │
          │  Fetches 300 candles    │
          │  from Binance / Yahoo   │
          └────────────┬───────────┘
                       │
          ┌────────────┴────────────┐
          │      RUNS IN PARALLEL   │
          ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐
│ 🔍 IDENTIFIER    │    │ 📰 NEWS AGENT         │
│ Validates symbol │    │ Scrapes 6 news sites  │
│ Finds asset type │    │ Classifies sentiment  │
│ Historical events│    │ Bullish/Bearish/Neutral│
└──────────────────┘    └──────────────────────┘
          │                         │
          └────────────┬────────────┘
                       │
          ┌────────────┴────────────┐
          │      RUNS IN PARALLEL   │
          ▼                         ▼
┌──────────────────┐    ┌──────────────────────────┐
│ 📋 FUNDAMENTAL   │    │ 📈 TECHNICAL AGENT        │
│ PE ratio         │    │ 40+ patterns detected:    │
│ Market cap       │    │ • SMC: BOS, CHoCH, OBs    │
│ Revenue growth   │    │ • ICT: FVGs, Liquidity    │
│ Beta, ROE        │    │ • Chart: H&S, Flags       │
│ 52-week range    │    │ • Candles: Engulfing etc  │
└──────────────────┘    │ • Fibonacci levels        │
                        │ • RSI, MACD, BB, ATR      │
                        └──────────────────────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  🎯 STRATEGY AGENT      │
                       │  Depends on Technical   │
                       │  Picks best setup:      │
                       │  • Breakout + Retest    │
                       │  • Order Block Bounce   │
                       │  • FVG Fill             │
                       │  Gives Entry / SL / TP  │
                       └────────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  ⚖️  RISK AGENT          │
                       │  Depends on Strategy    │
                       │  Checks hard rules:     │
                       │  • Max 2% risk per trade│
                       │  • Max 3 open trades    │
                       │  • Min 60% confidence   │
                       │  Calculates position    │
                       └────────────┬───────────┘
                                    │
                                    ▼
                       ┌────────────────────────┐
                       │  🧠 DECISION AGENT      │
                       │  Depends on ALL agents  │
                       │  Weighted scoring:      │
                       │  News      → 15%        │
                       │  Fundam.   → 15%        │
                       │  Technical → 30%        │
                       │  Strategy  → 25%        │
                       │  Risk      → 15%        │
                       └────────────┬───────────┘
                                    │
               ┌────────────────────┼─────────────────────┐
               ▼                    ▼                      ▼
     ┌──────────────┐    ┌──────────────────┐   ┌──────────────────┐
     │  📊 Dashboard │    │  💾 Save to DB    │   │  📱 Telegram Bot │
     │  BUY/SELL/   │    │  SQLite history  │   │  Alert if conf   │
     │  HOLD card   │    │  for all trades  │   │  > 65%           │
     └──────────────┘    └──────────────────┘   └──────────────────┘
```

---

## 🧩 Agent Dependency Map

Some agents run alone. Some agents need other agents to finish first.

```
Data Agent      ──────────────────────────────► runs first (everyone needs price data)

Identifier      ──────────────────────────────► runs independently (parallel)
News Agent      ──────────────────────────────► runs independently (parallel)

Fundamental     ──── needs: identifier result ► runs after phase 2
Technical       ──── needs: price data        ► runs after phase 2 (parallel with fundamental)

Strategy        ──── needs: technical result  ► runs after technical
Risk            ──── needs: strategy result   ► runs after strategy

Decision        ──── needs: ALL results       ► runs last, combines everything
```

This is the core idea of **agentic systems**: agents are not all equal. Some are independent workers, some are synthesizers that depend on others.

---

## 📈 What Patterns Does It Detect?

### SMC / ICT Concepts
- **BOS** (Break of Structure) — price breaks a previous swing high/low
- **CHoCH** (Change of Character) — trend is reversing
- **Order Blocks** — the last opposing candle before a strong move (bullish and bearish)
- **Breaker Blocks** — order blocks that got mitigated and flipped
- **FVG** (Fair Value Gap) — price imbalance between candles (bullish and bearish)
- **Liquidity Pools** — equal highs/lows where stop losses cluster
- **Inducement** — fake move to grab liquidity before the real move
- **OTE Zone** (Optimal Trade Entry) — 62–79% Fibonacci retracement

### Chart Patterns
Head & Shoulders · Inverse H&S · Double Top · Double Bottom · Bull Flag · Bear Flag · Ascending Triangle · Descending Triangle · Rising Wedge · Falling Wedge

### Candlestick Patterns
Doji · Hammer · Shooting Star · Marubozu · Bullish Engulfing · Bearish Engulfing · Piercing Line · Dark Cloud Cover · Morning Star · Evening Star · Three White Soldiers · Three Black Crows

### Classic Indicators
EMA 9/21/50/200 · SMA 10/20/50 · RSI 7/14 (with divergence) · MACD · Bollinger Bands · ATR · Stochastic · CCI · ADX · MFI · Williams %R · VWAP

---

## 🗞️ News Sources

For **crypto**: NewsAPI + CryptoPanic RSS + CoinDesk + CoinTelegraph
For **stocks**: NewsAPI + MoneyControl + Economic Times + Investing.com

---

## 🚀 How To Run

### Local
```bash
git clone https://github.com/yourusername/trading-agent
cd trading-agent
pip install -r requirements.txt
# Add your API keys to config.py
uvicorn main:app --reload --port 8000
# Open http://localhost:8000
```

### Docker
```bash
docker run -d -p 8000:8000 chandu013/trading-agent:latest
# Open http://localhost:8000
```

---

## 🔑 API Keys Needed (All Free)

| Key | Where to get | Cost |
|-----|-------------|------|
| Groq API | console.groq.com | Free |
| NewsAPI | newsapi.org | Free (100 req/day) |
| Telegram Bot | @BotFather on Telegram | Free |
| Binance | No key needed (public API) | Free |
| Yahoo Finance | No key needed | Free |

**Total cost: $0**

---

## 📊 Supported Symbols

| Type | Examples |
|------|---------|
| Crypto | `BTCUSDT` `ETHUSDT` `SOLUSDT` `BNBUSDT` |
| US Stocks | `AAPL` `TSLA` `NVDA` `MSFT` |
| Indian Stocks | `RELIANCE.NS` `TCS.NS` `INFY.NS` |
| Indices | `^NSEI` `^BSESN` `^GSPC` |

---

## ⚠️ Disclaimer

This is a **decision support tool** — not financial advice. The system gives structured analysis to help you think through a trade. It will not guarantee profit. Always do your own research and never risk money you cannot afford to lose.

---

## 🤝 Contributing

<<<<<<< HEAD
http://localhost:8000/docs
=======
Pull requests welcome. Open an issue first to discuss what you'd like to change.

---

*Built with Python · FastAPI · Groq Llama3 · Binance API · Yahoo Finance · BeautifulSoup*
>>>>>>> 0c9e452 (Readme)
