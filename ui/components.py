"""HTML-фрагменты интерфейса. Весь пользовательский и модельный текст экранируется."""
from __future__ import annotations

from html import escape as e

from core.pipeline import STAGES

_P = {
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8.5 12.5 2.5 2.5 4.5-5"/>',
    "x": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>',
    "alert": '<path d="M12 4 3 19h18L12 4Z"/><path d="M12 10v4m0 3h.01"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"/><path d="M14 3v5h5"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5m0-8h.01"/>',
    "minus": '<path d="M6 12h12"/>',
}


def icon(name: str, size: int = 20) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_P[name]}</svg>')


LOGO = ('<svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><rect width="26" height="26" rx="7" fill="#2B5DD6"/>'
        '<path d="M7 9h8M7 13h5M7 17h4" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>'
        '<path d="m14 16.5 2.3 2.3L20 14" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>')

_STATUS = {
    "ready": ("ready", "Ассистент готов", "локальная модель"),
    "no_model": ("warn", "Модель не загружена", ""),
    "offline": ("off", "Сервер модели недоступен", ""),
}


def topbar(status: str, model: str) -> str:
    cls, text, _ = _STATUS[status]
    extra = f' <span class="long">· {e(model)}</span>' if status == "ready" else ""
    return (f'<div class="topbar"><div class="brand">{LOGO}<span>Проверка лабораторных</span></div>'
            f'<div class="status"><i class="dot {cls}"></i><span>{e(text)}{extra}</span></div></div>')


def human_size(n: int) -> str:
    if n < 1024:
        return f"{n} Б"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} КБ".replace(".", ",")
    return f"{n / 1024 / 1024:.1f} МБ".replace(".", ",")


FORMAT_NAMES = {".py": "Python", ".java": "Java", ".txt": "Текст", ".md": "Markdown",
                ".pdf": "PDF", ".docx": "Word", ".zip": "Архив ZIP"}


def file_card(name: str, ext: str, size: int) -> str:
    fmt = FORMAT_NAMES.get(ext, ext.lstrip(".").upper() or "файл")
    return (f'<div class="filecard"><div class="ico">{icon("file")}</div><div>'
            f'<div class="name">{e(name)}</div><div class="sub">{e(fmt)} · {human_size(size)}</div></div></div>')


def steps(stage: int, queue_pos: int | None, skip_syntax: str | None, elapsed: int) -> str:
    out = []
    for i, label in enumerate(STAGES):
        sub = ""
        if i == 2 and skip_syntax:
            state, sub = "skip", skip_syntax
        else:
            state = "done" if i < stage else ("active" if i == stage else "pending")
        if i == 3 and state == "active" and queue_pos:
            sub = "Ожидание в очереди"
        if i == 4 and state == "active":
            sub = f"Прошло {elapsed} с"
        mark = {"done": icon("check", 20), "active": '<i class="spin"></i>',
                "skip": icon("minus", 18), "pending": '<i class="pend"></i>'}[state]
        out.append(f'<div class="step {state}"><span class="mark">{mark}</span>'
                   f'<span>{e(label)}{f"<span class=sub>{e(sub)}</span>" if sub else ""}</span></div>')
    html = f'<div class="steps">{"".join(out)}</div>'
    if queue_pos:
        word = "запрос" if queue_pos == 1 else "запроса" if queue_pos < 5 else "запросов"
        html += (f'<div class="queue">{icon("info", 18)}<span>Модель занята. Перед вами в очереди: '
                 f'{queue_pos} {word}.</span></div>')
    return html


def verdict_block(result) -> str:
    ready = result.verdict == "ready"
    title = "Готово к сдаче" if ready else "Требуется доработка"
    sub = ("Все обязательные критерии выполнены." if ready
           else "Не выполнены обязательные критерии.")
    return (f'<div class="verdict {"ready" if ready else "fix"}">{icon("check" if ready else "alert", 28)}'
            f'<div><div class="t">{title}</div><div class="s">{sub}</div></div></div>'
            f'<div class="stats"><div class="stat"><b>{result.met_count}</b><span>Выполнено</span></div>'
            f'<div class="stat"><b>{result.not_met_count}</b><span>Не выполнено</span></div>'
            f'<div class="stat"><b>{len(result.criteria)}</b><span>Всего критериев</span></div></div>')


def criteria_list(result) -> str:
    rows = []
    for c in result.criteria:
        ok = c.status == "met"
        pill = (f'<span class="pill ok">{icon("check", 14)}Выполнено</span>' if ok
                else f'<span class="pill no">{icon("x", 14)}Не выполнено</span>')
        tag = '<span class="tag">обязательный</span>' if c.is_critical else ""
        rows.append(f'<div class="row{"" if ok else " bad"}"><div class="num">{c.id}</div><div class="body">'
                    f'<div class="head"><div class="name">{e(c.text)}{tag}</div>{pill}</div>'
                    f'<div class="why">{e(c.explanation)}</div></div></div>')
    return f'<div class="crit">{"".join(rows)}</div>'


def recommendations(result) -> str:
    if result.verdict == "ready" or not result.recommendations:
        body = '<div class="rec"><span>Исправления не требуются.</span></div>'
    else:
        body = "".join(f'<div class="rec"><span class="n">{i}</span><span>{e(r)}</span></div>'
                       for i, r in enumerate(result.recommendations, 1))
    return f'<div class="recs">{body}</div>'


def meta_block(meta, result) -> str:
    rows = [("Файл", meta.filename), ("Лабораторная", meta.rubric_title),
            ("Дата проверки", meta.checked_at), ("Модель", meta.model)]
    dl = "".join(f"<div><dt>{k}</dt><dd>{e(v)}</dd></div>" for k, v in rows)
    note = "".join(f'<div class="note">{e(n)}</div>' for n in result.notes)
    return f'<dl class="meta" style="margin:0">{dl}</dl>{note}'


ERRORS = {
    "unsupported_format": ("Этот формат не подходит",
        "Для выбранной лабораторной такой файл принять нельзя.",
        "Загрузите файл в одном из форматов, указанных под областью загрузки.", False),
    "too_large": ("Файл слишком большой",
        "Работа превышает допустимый размер или объём текста для анализа.",
        "Уберите лишнее (например, скриншоты и вложения) и загрузите файл снова.", False),
    "empty_file": ("Файл пустой",
        "В файле нет текста, который можно проверить.",
        "Убедитесь, что сохранили работу, и загрузите файл снова.", False),
    "corrupted_file": ("Файл повреждён",
        "Не удалось открыть файл: он повреждён, защищён паролем или не является текстовым.",
        "Откройте файл у себя, пересохраните его и загрузите заново.", False),
    "read_failed": ("Не удалось прочитать файл",
        "Во время чтения произошёл сбой.",
        "Попробуйте ещё раз. Если ошибка повторяется, пересохраните файл.", True),
    "llm_unavailable": ("Нейросеть недоступна",
        "Сервер локальной модели не отвечает или нужная модель не загружена.",
        "Проверьте, что Ollama запущена и модель скачана, затем повторите проверку.", True),
    "llm_failed": ("Ошибка локальной модели",
        "Модель не смогла обработать запрос или не ответила вовремя.",
        "Повторите проверку. Если ошибка повторяется, перезапустите Ollama.", True),
    "bad_response": ("Не удалось обработать ответ модели",
        "Модель вернула ответ в неверном формате, результат не показан, чтобы не ввести вас в заблуждение.",
        "Повторите проверку.", True),
    "code_check_failed": ("Не удалось проверить код",
        "Автоматическая проверка кода завершилась сбоем или не уложилась во время.",
        "Повторите проверку. Если ошибка повторяется, упростите файл.", True),
    "rubric_problem": ("Проблема с описанием лабораторной",
        "Файл критериев выбранной работы содержит ошибку.",
        "Сообщите преподавателю.", False),
    "unknown": ("Что-то пошло не так",
        "Проверка не завершилась.", "Повторите попытку.", True),
}


def error_block(kind: str) -> tuple[str, bool]:
    title, text, todo, retry = ERRORS.get(kind, ERRORS["unknown"])
    html = (f'<div class="err"><div class="ic">{icon("alert", 24)}</div><h2>{e(title)}</h2>'
            f'<p>{e(text)}</p><p class="todo">{e(todo)}</p></div>')
    return html, retry


def lab_card(r) -> str:
    items = "".join(f'<li>{e(c.text)}{"<span class=tag>обязательный</span>" if c.is_critical else ""}</li>'
                    for c in r.criteria)
    fmts = ", ".join(r.allowed_formats)
    return (f'<div class="lab"><h3>{e(r.title)}</h3><div class="d">{e(r.description)} · форматы: {e(fmts)}</div>'
            f'<ol>{items}</ol></div>')
