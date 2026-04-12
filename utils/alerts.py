"""
utils/alerts.py
Telegram alert dispatcher.
"""
import httpx
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, ALERT_CONFIDENCE
from utils.logger import get_logger

log = get_logger("alerts")

_TG_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


async def send_telegram(message: str, chat_id: str = TELEGRAM_CHAT_ID) -> bool:
    """Send a plain-text Telegram message. Returns True on success."""
    if not chat_id:
        log.warning("TELEGRAM_CHAT_ID not set – skipping alert")
        return False
    log.info("Sending Telegram alert (len=%d)", len(message))
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(_TG_URL, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            })
        if r.status_code == 200:
            log.info("Telegram alert sent OK")
            return True
        log.warning("Telegram returned %d: %s", r.status_code, r.text)
        return False
    except Exception as exc:
        log.error("Telegram send failed: %s", exc, exc_info=True)
        return False


def format_signal_alert(decision: dict) -> str:
    """Build a formatted Telegram message from a decision dict."""
    action     = decision.get("action", "HOLD")
    symbol     = decision.get("symbol", "?")
    tf         = decision.get("timeframe", "?")
    conf       = decision.get("confidence", 0)
    entry      = decision.get("entry_zone", ["-", "-"])
    sl         = decision.get("stop_loss", "-")
    tp         = decision.get("target", "-")
    reason     = decision.get("reason", "")

    emoji = "🟢" if action == "BUY" else ("🔴" if action == "SELL" else "⚪")
    msg = (
        f"{emoji} *{action} SIGNAL — {symbol}* ({tf})\n"
        f"Confidence : `{conf*100:.1f}%`\n"
        f"Entry zone : `{entry}`\n"
        f"Stop loss  : `{sl}`\n"
        f"Target     : `{tp}`\n"
        f"Reason     : {reason}"
    )
    log.debug("Formatted alert: %s", msg[:80])
    return msg


async def maybe_alert(decision: dict) -> None:
    """Send alert only if confidence exceeds threshold."""
    conf = decision.get("confidence", 0)
    log.info("maybe_alert | confidence=%.2f threshold=%.2f", conf, ALERT_CONFIDENCE)
    if conf >= ALERT_CONFIDENCE:
        msg = format_signal_alert(decision)
        await send_telegram(msg)
    else:
        log.info("Confidence below threshold – no alert sent")
