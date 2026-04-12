"""
agents/decision_agent.py
Aggregates ALL agent outputs using weighted scoring to produce a final
trade decision and a beautiful trade card summary.
"""
from utils.logger import get_logger
from utils.llm_client import llm_json

log = get_logger("decision_agent")

# Weights must sum to 1.0
WEIGHTS = {
    "news":       0.15,
    "fundamental":0.15,
    "technical":  0.30,
    "strategy":   0.25,
    "risk":       0.15,
}


def _sentiment_to_score(sentiment: str) -> float:
    return {"bullish": 1.0, "neutral": 0.5, "bearish": 0.0}.get(sentiment, 0.5)


def _weighted_score(
    news: dict, fundamental: dict, technical: dict,
    strategy: dict, risk: dict
) -> float:
    scores = {
        "news":        news.get("confidence", 0.5) * _sentiment_to_score(news.get("sentiment","neutral")),
        "fundamental": fundamental.get("confidence", 0.5) * _sentiment_to_score(fundamental.get("fundamental_signal","neutral")),
        "technical":   technical.get("confidence", 0.5) * _sentiment_to_score(technical.get("technical_signal","neutral")),
        "strategy":    strategy.get("setup_confidence", 0.5),
        "risk":        1.0 if risk.get("go") else 0.0,
    }
    score = sum(scores[k] * WEIGHTS[k] for k in scores)
    log.debug("Weighted scores: %s → final=%.4f", scores, score)
    return round(score, 4)


async def run(
    symbol: str, timeframe: str, trade_type: str,
    identifier: dict, fundamental: dict, news: dict,
    technical: dict, strategy: dict, risk: dict,
) -> dict:
    """
    Final decision and trade card generation.
    """
    log.info("decision_agent.run | symbol=%s tf=%s type=%s", symbol, timeframe, trade_type)

    conf = _weighted_score(news, fundamental, technical, strategy, risk)
    bias = strategy.get("trade_bias", "HOLD")
    action = bias if risk.get("go") and conf >= 0.60 else "HOLD"

    log.info("Decision: action=%s confidence=%.4f", action, conf)

    system = "You are a senior trading decision analyst. Return ONLY valid JSON."
    user = f"""
Symbol: {symbol}  Timeframe: {timeframe}  Trade type: {trade_type}

Agent outputs:
- Identifier: {identifier.get('full_name')} | {identifier.get('asset_type')} | {identifier.get('sector')}
- News sentiment: {news.get('sentiment')} (conf={news.get('confidence'):.2f}) | {news.get('summary')}
- Fundamental: {fundamental.get('fundamental_signal')} | PE={fundamental.get('pe_ratio')} | {fundamental.get('summary')}
- Technical: {technical.get('technical_signal')} (conf={technical.get('confidence'):.2f}) | {technical.get('summary')}
- Strategy setup: {strategy.get('setup')} | Entry={strategy.get('entry_zone')} | SL={strategy.get('stop_loss')} | TP1={strategy.get('target_1')} | TP2={strategy.get('target_2')}
- Risk: go={risk.get('go')} | size={risk.get('position_size')} | RR={risk.get('risk_reward')}

Weighted confidence: {conf:.2f}
Proposed action: {action}

Generate the FINAL TRADE CARD as JSON:
{{
  "action": "{action}",
  "symbol": "{symbol}",
  "timeframe": "{timeframe}",
  "trade_type": "{trade_type}",
  "confidence": {conf},
  "entry_zone": {strategy.get('entry_zone', [])},
  "stop_loss": {strategy.get('stop_loss', 0)},
  "target_1": {strategy.get('target_1', 0)},
  "target_2": {strategy.get('target_2', 0)},
  "position_size": {risk.get('position_size', 0)},
  "risk_reward": {risk.get('risk_reward', 0)},
  "setup_name": "{strategy.get('setup', '')}",
  "reason": "<comprehensive 2-3 sentence reason combining all agents>",
  "trade_plan": {{
    "before_entry": "<what to watch before entering>",
    "entry_trigger": "<exact trigger candle/level>",
    "management": "<how to manage the trade>",
    "exit_plan": "<when to exit with profit or loss>"
  }},
  "signal_components": {{
    "news_weight": {WEIGHTS['news']},
    "news_score": {news.get('confidence', 0):.2f},
    "fundamental_weight": {WEIGHTS['fundamental']},
    "fundamental_score": {fundamental.get('confidence', 0):.2f},
    "technical_weight": {WEIGHTS['technical']},
    "technical_score": {technical.get('confidence', 0):.2f},
    "strategy_weight": {WEIGHTS['strategy']},
    "strategy_score": {strategy.get('setup_confidence', 0):.2f},
    "risk_weight": {WEIGHTS['risk']},
    "risk_score": {1.0 if risk.get('go') else 0.0}
  }},
  "warnings": {risk.get('warnings', [])},
  "key_levels": {{
    "resistance": {technical.get('raw_indicators', {}).get('resistance', 0)},
    "support": {technical.get('raw_indicators', {}).get('support', 0)},
    "order_block": "{technical.get('raw_order_blocks', {})}",
    "fvg": "{technical.get('raw_fvgs', [{}])[0] if technical.get('raw_fvgs') else None}"
  }}
}}
"""
    result = await llm_json(system, user)
    result["action"]     = action
    result["confidence"] = conf
    result["symbol"]     = symbol
    result["timeframe"]  = timeframe
    log.info("decision_agent FINAL: action=%s confidence=%.4f", action, conf)
    return result
