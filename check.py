"""
batch_check.py — пакетная проверка лабораторных работ через локальную LLM.
Требует: pip install -U ollama pydantic
Опционально: pip install python-docx pypdf
"""

import os
import time
from pathlib import Path

import ollama
from pydantic import BaseModel, Field, field_validator


# ============================================================
# Настройки
# ============================================================
FOLDER        = "./works"
MODEL         = "qwen2.5:7b"
RESULTS_DIR   = "./results"
REQUEST_DELAY = 0.0
MAX_RETRIES   = 2

EXTENSIONS = {
    ".txt", ".md",
    ".py", ".java", ".c", ".cpp", ".cs",
    ".docx",
    ".pdf",
}


# ============================================================
# Схема ответа модели
# ============================================================
class Criterion(BaseModel):
    number: int = Field(ge=1, le=7, description="Номер критерия, 1..7")
    done: bool = Field(description="True если критерий выполнен, иначе False")
    comment: str = Field(description="Одно короткое предложение — почему так")


class WorkCheck(BaseModel):
    criteria: list[Criterion] = Field(
        min_length=7, max_length=7,
        description="Ровно 7 критериев — по одному на каждый пункт из задания",
    )
    recommendations: list[str] = Field(
        min_length=2, max_length=3,
        description="2-3 конкретных пункта, что студенту исправить",
    )

    @field_validator("criteria")
    @classmethod
    def _check_criteria_numbers(cls, v):
        numbers = sorted(c.number for c in v)
        if numbers != list(range(1, 8)):
            raise ValueError(f"Номера критериев должны покрывать 1..7, получено {numbers}")
        return v

    @property
    def verdict(self) -> str:
        return "готово" if all(c.done for c in self.criteria) else "доработать"


# ============================================================
# Промпт (без инструкций по формату — их задаёт схема)
# ============================================================
PROMPT_TEMPLATE = """Ты помощник преподавателя по программированию. Проверь работу студента.

Задача: найти в массиве [4, 8, 2, 6, 10] самое большое число и посчитать сумму всех чисел.
Верный ответ: сумма 30, максимум 10.

Критерии:
1. Программа запускается без ошибок.
2. Массив создан и заполнен.
3. Для обхода массива используется цикл.
4. Сумма посчитана верно.
5. Максимум найден верно.
6. Результат выводится на экран.
7. Названия переменных понятные.

Не придумывай ошибок, которых нет. Пиши по-русски, коротко.
Комментарии и рекомендации — на русском языке.

Код студента:
{content}
"""


# ============================================================
# Чтение файлов
# ============================================================
_PLAIN_TEXT_EXT = {
    ".txt", ".md", ".rst",
    ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs",
    ".js", ".ts", ".go", ".rs", ".rb", ".php",
    ".json", ".yaml", ".yml", ".xml", ".html", ".css",
    ".sql", ".sh", ".bat", ".ps1",
}


def _read_plain(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="latin-1", errors="replace")


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as e:
        raise RuntimeError("Нужен python-docx: pip install python-docx") from e
    doc = Document(str(path))
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("Нужен pypdf: pip install pypdf") from e
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n".join(pages)


def read_text_from_file(path: str | Path) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext in _PLAIN_TEXT_EXT:
        return _read_plain(p)
    if ext == ".docx":
        return _read_docx(p)
    if ext == ".pdf":
        return _read_pdf(p)
    raise ValueError(f"Неподдерживаемый формат: {ext}")


# ============================================================
# Модель
# ============================================================
def ask_model(model: str, prompt: str) -> WorkCheck:
    """Запрос к Ollama со структурированным ответом. Ретраит при невалидном JSON."""
    last_err: Exception | None = None
    current_prompt = prompt

    for attempt in range(MAX_RETRIES + 1):
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": current_prompt}],
            format=WorkCheck.model_json_schema(),   # ← гарантия формата
            options={"temperature": 0, "num_predict": 1024},
        )
        raw = response["message"]["content"]
        try:
            return WorkCheck.model_validate_json(raw)
        except Exception as e:
            last_err = e
            print(f"    ↻ попытка {attempt + 1}: невалидный ответ ({e})")
            current_prompt = (
                prompt
                + f"\n\nПредыдущий ответ не прошёл проверку схемы: {e}. "
                  "Верни строго по заданной схеме."
            )

    raise RuntimeError(
        f"Модель не вернула валидный ответ после {MAX_RETRIES + 1} попыток: {last_err}"
    )


# ============================================================
# Человекочитаемый отчёт
# ============================================================
def format_report(file_name: str, result: WorkCheck) -> str:
    lines = [f"Файл: {file_name}", ""]
    for c in result.criteria:
        mark = "✓" if c.done else "✗"
        lines.append(f"{mark} {c.number}. {c.comment}")
    lines.append("")
    lines.append(f"Вердикт: {result.verdict}")
    lines.append("Что исправить:")
    for r in result.recommendations:
        lines.append(f"  • {r}")
    return "\n".join(lines)


# ============================================================
# Основная логика
# ============================================================
def list_works(folder: str, extensions: set) -> list[Path]:
    p = Path(folder)
    if not p.is_dir():
        raise FileNotFoundError(f"Папка не найдена: {folder}")
    return sorted(
        f for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    )


def main() -> None:
    files = list_works(FOLDER, EXTENSIONS)
    total = len(files)
    print(f"Найдено файлов: {total} в папке {FOLDER!r}")
    if total == 0:
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)

    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{total}] {file_path.name}")

        try:
            content = read_text_from_file(file_path)
        except Exception as e:
            print(f"  ✗ ошибка чтения: {e}")
            continue

        if not content.strip():
            print("  ⚠ текст не извлечён, пропуск")
            continue

        prompt = PROMPT_TEMPLATE.replace("{content}", content)

        t0 = time.time()
        try:
            result = ask_model(MODEL, prompt)
        except Exception as e:
            print(f"  ✗ ошибка модели: {e}")
            continue
        dt = time.time() - t0

        done_count = sum(1 for c in result.criteria if c.done)
        print(f"  ✓ за {dt:.1f} с — критериев выполнено {done_count}/7, "
              f"вердикт: {result.verdict}")

        # JSON — машинно-читаемо (пригодится для сводных таблиц)
        json_path = Path(RESULTS_DIR) / f"{file_path.stem}.json"
        json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        # TXT — для чтения глазами
        txt_path = Path(RESULTS_DIR) / f"{file_path.stem}.txt"
        txt_path.write_text(format_report(file_path.name, result), encoding="utf-8")

        if REQUEST_DELAY:
            time.sleep(REQUEST_DELAY)


if __name__ == "__main__":
    main()