"""Конвейер проверки: чтение → проверка кода → модель → валидация → итог.
Работает в фоновом потоке; интерфейс только читает объект Progress."""
from __future__ import annotations

import itertools
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from . import config, llm
from .code_checks import CodeCheck, check_code
from .errors import CheckError, LLMFailure
from .prompt import build_user_prompt
from .readers import load_work
from .rubrics import Rubric
from .validator import CheckResult, build_result, validate_response

log = logging.getLogger("labcheck.pipeline")

STAGES = [
    "Файл получен",
    "Проверка формата и чтение содержимого",
    "Проверка синтаксиса",
    "Передача данных локальной нейросети",
    "Анализ по критериям",
    "Формирование обратной связи",
]


class LLMGate:
    """Модель обслуживает один запрос за раз; остальные ждут в очереди (FIFO)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cond = threading.Condition()
        self._queue: list[int] = []
        self._ids = itertools.count(1)

    def enter(self, on_position=None) -> int:
        ticket = next(self._ids)
        with self._cond:
            self._queue.append(ticket)
            while self._queue[0] != ticket or not self._lock.acquire(blocking=False):
                if on_position:
                    on_position(self._queue.index(ticket))  # сколько запросов впереди (включая выполняемый)
                self._cond.wait(timeout=0.5)
        if on_position:
            on_position(None)
        return ticket

    def leave(self, ticket: int) -> None:
        with self._cond:
            if ticket in self._queue:
                self._queue.remove(ticket)
            if self._lock.locked():
                self._lock.release()
            self._cond.notify_all()


GATE = LLMGate()


@dataclass
class Meta:
    filename: str
    rubric_title: str
    checked_at: str
    model: str
    code_check_method: str


@dataclass
class Progress:
    stage: int = 0                      # индекс активного этапа в STAGES
    queue_position: int | None = None   # None — не в очереди; N — запросов впереди
    finished: bool = False
    result: CheckResult | None = None
    meta: Meta | None = None
    error: CheckError | None = None
    started: float = field(default_factory=time.time)


def run_check(filename: str, data: bytes, rubric: Rubric, progress: Progress,
              client=None, gate: LLMGate = GATE) -> None:
    ticket = None
    try:
        progress.stage = 1
        work = load_work(filename, data, rubric.allowed_formats)

        progress.stage = 2
        code_info: CodeCheck = check_code(work.extension, work.text)

        progress.stage = 3
        prompt = build_user_prompt(rubric, work.text, code_info)

        def on_pos(pos):
            progress.queue_position = pos

        ticket = gate.enter(on_pos)
        progress.stage = 4
        parsed, recs = llm.ask_validated(
            prompt, rubric, lambda raw: validate_response(raw, rubric), client=client)
        gate.leave(ticket)
        ticket = None

        progress.stage = 5
        progress.result = build_result(parsed, recs, rubric, code_info)
        progress.meta = Meta(work.filename, rubric.title,
                             datetime.now().strftime("%d.%m.%Y, %H:%M"),
                             config.MODEL, code_info.method)
    except CheckError as e:
        log.warning("check failed: %s (%s)", e.kind, e.detail)
        progress.error = e
    except Exception as e:  # непредвиденное — без трассировки для пользователя
        log.exception("unexpected failure")
        progress.error = LLMFailure(type(e).__name__)
    finally:
        if ticket is not None:
            gate.leave(ticket)
        progress.queue_position = None
        progress.finished = True
