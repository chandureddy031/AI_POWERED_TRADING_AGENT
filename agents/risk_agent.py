"""
agents/risk_agent.py
Calculates position size, validates risk parameters, enforces hard rules.
"""
from utils.logger import get_logger
from utils.llm_client import llm_json
from config import MAX_RISK_PCT, MAX_OPEN_TRADES, MIN_CONFIDENCE

log = get_logger("risk_agent")


async def run(strategy: dict, fundamental: dict, symbol: str,
              account_size: float = 10000.0, open_trades: int = 0) -> dict:
    """
    Evaluate risk and return position sizing + go/no-go verdict.
    """
    log.info("risk_agent.run | symbol=%s open_trades=%d account=%.2f",
             symbol, open_trades, account_size)

    entry   = strategy.get("entry_zone", [0, 0])
    sl      = strategy.get("stop_loss", 0)
    conf    = strategy.get("setup_confidence", 0)
    bias    = strategy.get("trade_bias", "HOLD")

    entry_price = sum(entry) / 2 if entry else 0
    risk_per_unit = abs(entry_price - sl) if sl and entry_price else 1
    risk_amount   = account_size * MAX_RISK_PCT
    qty           = round(risk_amount / risk_per_unit, 4) if risk_per_unit else 0

    hard_rules = {
        "max_risk_ok":     True,
        "max_trades_ok":   open_trades < MAX_OPEN_TRADES,
        "min_confidence_ok": conf >= MIN_CONFIDENCE,
        "no_hold_bias":    bias != "HOLD",
    }
    go = all(hard_rules.values())
    log.info("Risk hard rules: %s → go=%s", hard_rules, go)

    system = "You are a risk management specialist. Return ONLY valid JSON."
    user = f"""
Symbol: {symbol}
Entry: {entry}  SL: {sl}  Bias: {bias}
Account size: ${account_size}  Open trades: {open_trades}
Setup confidence: {conf}
Hard rule checks: {hard_rules}
Fundamental signal: {fundamental.get('fundamental_signal')}

Return JSON:
{{
  "go": {str(go).lower()},
  "position_size": {qty},
  "risk_amount_usd": {round(risk_amount, 2)},
  "risk_reward": {strategy.get('rr_ratio', 0)},
  "max_loss_usd": {round(qty * risk_per_unit, 2)},
  "hard_rules": {hard_rules},
  "risk_level": "low|medium|high",
  "recommendation": "<one sentence>",
  "warnings": ["<warning if any>"]
}}
"""
    result = await llm_json(system, user)
    result["go"]            = go
    result["position_size"] = qty
    result["risk_amount_usd"] = round(risk_amount, 2)
    log.info("risk_agent result: go=%s size=%.4f", go, qty)
    return result
