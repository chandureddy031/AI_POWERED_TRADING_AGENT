"""
agents/strategy_agent.py
Depends on: technical_agent output (structure + volume already embedded).
Validates concrete trade setups based on rule-based + LLM logic.
"""
from utils.logger import get_logger
from utils.llm_client import llm_json

log = get_logger("strategy_agent")


# ─── Rule-based helpers ──────────────────────────────────────────────────────

def _breakout_retest(tech: dict) -> dict | None:
    """Breakout + retest setup."""
    ind   = tech.get("raw_indicators", {})
    price = ind.get("current_price")
    res   = ind.get("resistance")
    vol_r = ind.get("vol_ratio", 1.0)
    if not (price and res):
        return None
    broke_out = price > res * 0.998
    high_volume = vol_r >= 1.5
    if broke_out and high_volume:
        entry_low  = round(res * 0.99, 4)
        entry_high = round(res * 1.01, 4)
        sl = round(res * 0.97, 4)
        tp = round(price + (price - sl) * 2, 4)
        log.debug("Breakout-retest setup detected")
        return {
            "setup": "breakout_retest",
            "valid": True,
            "entry_zone": [entry_low, entry_high],
            "stop_loss": sl,
            "target": tp,
            "rr": round((tp - entry_high) / (entry_high - sl), 2),
        }
    return None


def _ob_bounce(tech: dict) -> dict | None:
    """Order block bounce setup."""
    ob = tech.get("raw_order_blocks", {}).get("bullish_ob")
    if not ob:
        return None
    ind   = tech.get("raw_indicators", {})
    price = ind.get("current_price")
    if price and ob["low"] <= price <= ob["high"] * 1.005:
        sl = round(ob["low"] * 0.995, 4)
        tp = round(price + (price - sl) * 2.5, 4)
        log.debug("OB bounce setup detected")
        return {
            "setup": "ob_bounce",
            "valid": True,
            "entry_zone": [ob["low"], ob["high"]],
            "stop_loss": sl,
            "target": tp,
            "rr": round((tp - price) / (price - sl), 2),
        }
    return None


def _fvg_fill(tech: dict) -> dict | None:
    """FVG fill setup."""
    fvgs = tech.get("raw_fvgs", [])
    ind   = tech.get("raw_indicators", {})
    price = ind.get("current_price")
    if not fvgs or not price:
        return None
    for fvg in fvgs:
        if fvg["type"] == "bullish_fvg" and fvg["bottom"] <= price <= fvg["top"]:
            sl = round(fvg["bottom"] * 0.997, 4)
            tp = round(price + (price - sl) * 2, 4)
            log.debug("FVG fill setup detected")
            return {
                "setup": "fvg_fill",
                "valid": True,
                "entry_zone": [fvg["bottom"], fvg["top"]],
                "stop_loss": sl,
                "target": tp,
                "rr": round((tp - price) / (price - sl), 2),
            }
    return None


async def run(technical: dict, symbol: str, timeframe: str, trade_type: str) -> dict:
    """
    Validate and score all setups, then use LLM for final synthesis.
    Returns top setup with entry / SL / TP.
    """
    log.info("strategy_agent.run | symbol=%s tf=%s type=%s", symbol, timeframe, trade_type)

    rule_setups = []
    br = _breakout_retest(technical)
    ob = _ob_bounce(technical)
    fv = _fvg_fill(technical)
    for s in [br, ob, fv]:
        if s:
            rule_setups.append(s)

    log.info("Rule-based setups found: %d", len(rule_setups))

    system = "You are a professional trade setup validator. Return ONLY valid JSON."
    user = f"""
Symbol: {symbol}  Timeframe: {timeframe}  Trade type: {trade_type}

Technical summary:
- Trend: {technical.get('trend')}
- Signal: {technical.get('technical_signal')}
- Confidence: {technical.get('confidence')}
- SMC: {technical.get('smc_analysis')}
- Top strategies from tech agent: {technical.get('strategies', [])[:3]}

Rule-based setups detected:
{rule_setups}

Select the BEST single trade setup based on confluence and return JSON:
{{
  "setup": "<setup name>",
  "valid": true|false,
  "trade_bias": "BUY|SELL|HOLD",
  "entry_zone": [<low>, <high>],
  "stop_loss": <float>,
  "target_1": <float>,
  "target_2": <float>,
  "rr_ratio": <float>,
  "timeframe_alignment": "<is TF aligned with higher TF trend?>",
  "confluence_score": <1-10>,
  "setup_confidence": <0.0-1.0>,
  "invalidation": "<what would invalidate this setup>",
  "notes": "<execution tips>"
}}
"""
    result = await llm_json(system, user)
    result["rule_setups"] = rule_setups
    log.info("strategy_agent result: setup=%s conf=%.2f",
             result.get("setup"), result.get("setup_confidence", 0))
    return result
