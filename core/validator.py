"""Проверка ответа модели и расчёт итога. Вердикт считается программно."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .code_checks import CodeCheck
from .errors import InvalidModelResponse
from .rubrics import Rubric

STATUSES = {"met", "not_met"}


@dataclass
class CriterionResult:
    id: int
    text: str
    is_critical: bool
    status: str                 # "met" | "not_met"
    explanation: str
    source: str = "model"       # "model" | "auto" — кем принято решение


@dataclass
class CheckResult:
    criteria: list[CriterionResult]
    verdict: str                # "ready" | "needs_revision"
    recommendations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)   # заметки о методе проверки

    @property
    def met_count(self) -> int:
        return sum(c.status == "met" for c in self.criteria)

    @property
    def not_met_count(self) -> int:
        return len(self.criteria) - self.met_count


def _extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise InvalidModelResponse("невалидный JSON") from e
    if not isinstance(data, dict):
        raise InvalidModelResponse("корень ответа не объект")
    return data


def validate_response(raw: str, rubric: Rubric) -> tuple[dict[int, tuple[str, str]], list[str]]:
    """Возвращает ({id: (status, explanation)}, рекомендации) или бросает InvalidModelResponse."""
    data = _extract_json(raw)
    items = data.get("criteria")
    if not isinstance(items, list):
        raise InvalidModelResponse("нет списка criteria")

    expected = {c.id for c in rubric.criteria}
    parsed: dict[int, tuple[str, str]] = {}
    for it in items:
        if not isinstance(it, dict):
            raise InvalidModelResponse("элемент criteria не объект")
        cid, status, expl = it.get("id"), it.get("status"), it.get("explanation")
        if not isinstance(cid, int) or isinstance(cid, bool):
            raise InvalidModelResponse("id не целое число")
        if cid in parsed:
            raise InvalidModelResponse(f"повтор id {cid}")
        if cid not in expected:
            raise InvalidModelResponse(f"лишний id {cid}")
        if status not in STATUSES:
            raise InvalidModelResponse(f"недопустимый статус у {cid}")
        if not isinstance(expl, str) or not expl.strip():
            raise InvalidModelResponse(f"пустое объяснение у {cid}")
        parsed[cid] = (status, expl.strip())

    missing = expected - set(parsed)
    if missing:
        raise InvalidModelResponse(f"нет критериев: {sorted(missing)}")

    recs = data.get("recommendations", [])
    if not isinstance(recs, list) or not all(isinstance(r, str) for r in recs):
        raise InvalidModelResponse("recommendations не список строк")
    return parsed, [r.strip() for r in recs if r.strip()]


def compute_verdict(results: list[CriterionResult]) -> str:
    """ready — только если выполнены все обязательные критерии."""
    if any(r.is_critical and r.status == "not_met" for r in results):
        return "needs_revision"
    return "ready"


def build_result(parsed: dict[int, tuple[str, str]], recs: list[str],
                 rubric: Rubric, check: CodeCheck) -> CheckResult:
    """Накладывает объективные проверки на ответ модели и считает вердикт."""
    results: list[CriterionResult] = []
    notes: list[str] = []
    for c in rubric.criteria:
        status, expl = parsed[c.id]
        source = "model"
        if c.auto == "compiles" and check.performed:
            source = "auto"
            if check.ok:
                status, expl = "met", check.summary.replace(" Программа не запускалась.", "")
            else:
                status = "not_met"
                detail = f" ({check.diagnostics[0]})" if check.diagnostics else ""
                expl = f"{check.summary.rstrip('.')}{detail}."
        elif c.requires_compile and check.failed:
            source = "auto"
            status = "not_met"
            expl = "Верность не подтверждена: код не компилируется."
        results.append(CriterionResult(c.id, c.text, c.is_critical, status, expl, source))

    notes.append(check.summary)

    verdict = compute_verdict(results)
    if verdict == "ready":
        recs = []   # исправления не требуются
    else:
        recs = recs[:3]
        if not recs:
            failed = [r for r in results if r.status == "not_met"]
            recs = [f"Проверьте критерий «{r.text}»: {r.explanation}" for r in failed[:3]]
    return CheckResult(results, verdict, recs, notes)
