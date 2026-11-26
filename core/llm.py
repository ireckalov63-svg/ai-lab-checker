"""Единственное место, где происходит обращение к локальной модели (Ollama)."""
from __future__ import annotations

import logging

from . import config
from .errors import InvalidModelResponse, LLMFailure, LLMUnavailable
from .prompt import SYSTEM, response_schema

log = logging.getLogger("labcheck.llm")


def _client():
    import ollama
    return ollama.Client(host=config.OLLAMA_HOST, timeout=config.LLM_TIMEOUT_S)


def server_status() -> str:
    """'ready' | 'no_model' | 'offline' — для индикатора в интерфейсе."""
    try:
        listed = _client().list()
        names = {getattr(m, "model", None) or m.get("model", "") for m in listed["models"]}
    except Exception:
        return "offline"
    wanted = config.MODEL
    ok = wanted in names or any(n.split(":")[0] == wanted and wanted.endswith(":latest") for n in names)
    return "ready" if ok else "no_model"


def ask(user_prompt: str, rubric, client=None) -> str:
    """Один запрос к модели. Возвращает сырой текст ответа."""
    import ollama
    client = client or _client()
    try:
        resp = client.chat(
            model=config.MODEL,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": user_prompt}],
            format=response_schema(rubric),
            options={"temperature": 0, "num_ctx": config.NUM_CTX, "num_predict": 1500},
        )
        return resp["message"]["content"]
    except ollama.ResponseError as e:
        log.warning("ollama response error: %s", e)
        if getattr(e, "status_code", None) == 404:
            raise LLMUnavailable(f"модель {config.MODEL} не найдена") from e
        raise LLMFailure(str(e)) from e
    except (ConnectionError, OSError) as e:
        raise LLMUnavailable(type(e).__name__) from e
    except Exception as e:
        name = type(e).__name__
        log.warning("llm error: %s", name)
        if "Connect" in name or "Timeout" in name:
            raise LLMUnavailable(name) from e
        raise LLMFailure(name) from e


def ask_validated(user_prompt: str, rubric, validate, client=None, attempts: int | None = None):
    """Запрос с ограниченным числом повторов при невалидном ответе."""
    attempts = attempts or config.LLM_ATTEMPTS
    last: Exception | None = None
    for i in range(attempts):
        raw = ask(user_prompt, rubric, client)
        try:
            return validate(raw)
        except InvalidModelResponse as e:
            log.info("invalid model response (attempt %d): %s", i + 1, e.detail)
            last = e
    raise InvalidModelResponse(getattr(last, "detail", "")) from last
