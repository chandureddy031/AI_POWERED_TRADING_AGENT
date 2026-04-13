
import json
from openai import AsyncOpenAI
from config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL
from utils.logger import get_logger

log = get_logger("llm_client")


_client = AsyncOpenAI(api_key="", base_url=GROQ_BASE_URL)


async def llm_chat(system: str, user: str, json_mode: bool = False) -> str:
    """
    Send a chat completion request to Groq.
    Returns the text content of the first choice.
    """
    log.debug("llm_chat called | system_len=%d user_len=%d json=%s",
              len(system), len(user), json_mode)
    kwargs: dict = dict(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=0.2,
        max_tokens=1800,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = await _client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        log.debug("llm_chat response len=%d", len(text))
        return text
    except Exception as exc:
        log.error("llm_chat error: %s", exc, exc_info=True)
        raise


async def llm_json(system: str, user: str) -> dict:
    """Convenience: returns parsed JSON dict from LLM."""
    raw = await llm_chat(system, user, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        log.warning("JSON decode failed, returning raw in 'text' key")
        return {"text": raw}
