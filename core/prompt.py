"""Построение промпта из рубрики. Тексты критериев берутся только из JSON."""
from __future__ import annotations

from .code_checks import CodeCheck
from .rubrics import Rubric

SYSTEM = (
    "Ты помощник преподавателя по программированию. Проверяешь работу студента по критериям. "
    "Отвечай ТОЛЬКО JSON-объектом заданной структуры, без пояснений вне JSON. "
    "Объяснения пиши по-русски, одним коротким предложением. "
    "Не придумывай ошибок, которых нет в работе. "
    "Результаты автоматических проверок — факты: им нельзя противоречить."
)


def build_user_prompt(rubric: Rubric, code: str, check: CodeCheck) -> str:
    crit_lines = "\n".join(f"{c.id}. {c.text}" for c in rubric.criteria)
    facts = [f"- {check.summary}"]
    facts += [f"- Ошибка компилятора, {d}" for d in check.diagnostics]
    if check.performed and check.ok:
        facts.append("- Допускается считать, что код компилируется; верность вычислений проверь по тексту кода.")
    elif not check.performed:
        facts.append("- Не утверждай, что код успешно скомпилирован или запущен: такая проверка не выполнялась.")
    task = f"Задача: {rubric.task}\n\n" if rubric.task else ""
    return (
        f"Лабораторная работа: {rubric.title}. {rubric.description}\n"
        f"{task}"
        f"Критерии (оцени КАЖДЫЙ, id должны совпадать):\n{crit_lines}\n\n"
        f"Результаты автоматических проверок:\n" + "\n".join(facts) + "\n\n"
        'Верни JSON: {"criteria":[{"id":<число>,"status":"met"|"not_met","explanation":"<короткое предложение>"}],'
        '"recommendations":["<что исправить>", ...]}\n'
        "Рекомендации: 2–3 конкретных пункта только если есть невыполненные критерии, иначе пустой список.\n\n"
        f"Работа студента:\n```\n{code}\n```"
    )


def response_schema(rubric: Rubric) -> dict:
    """JSON-схема для структурированного вывода Ollama."""
    return {
        "type": "object",
        "properties": {
            "criteria": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "status": {"type": "string", "enum": ["met", "not_met"]},
                        "explanation": {"type": "string"},
                    },
                    "required": ["id", "status", "explanation"],
                },
            },
            "recommendations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["criteria", "recommendations"],
    }
