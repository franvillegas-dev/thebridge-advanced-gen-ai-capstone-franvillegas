import logging
import os
import time
import random
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("agile_agent.llm")

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_FALLBACK_MODEL = "gemini-1.5-flash"
_MAX_RETRIES = 3
_BASE_DELAY = 1.0


def get_model_name() -> str:
    return os.getenv("GOOGLE_MODEL", DEFAULT_MODEL)


def get_fallback_model_name() -> str | None:
    val = os.getenv("GOOGLE_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)
    return val if val else None


def create_llm(temperature: float = 0, **kwargs) -> ChatGoogleGenerativeAI:
    model = kwargs.pop("model", None) or get_model_name()
    return ChatGoogleGenerativeAI(model=model, temperature=temperature, **kwargs)


def is_rate_limited(error: Exception) -> bool:
    error_str = str(error)
    return "429" in error_str or "RESOURCE_EXHAUSTED" in error_str


def invoke_with_retry(runnable, *args, max_retries=_MAX_RETRIES, **kwargs):
    model_name = get_model_name()
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return runnable.invoke(*args, **kwargs)
        except Exception as e:
            last_error = e
            if not is_rate_limited(e):
                raise
            if attempt < max_retries:
                delay = _BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(
                    "Rate limited on %s, retrying in %.1fs (attempt %d/%d)...",
                    model_name, delay, attempt + 1, max_retries
                )
                time.sleep(delay)
    raise last_error
