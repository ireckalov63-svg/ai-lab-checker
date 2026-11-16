import os
import time
from pathlib import Path

import ollama

# ============================================================
# Настройки
# ============================================================
FOLDER       = "./works"
MODEL        = "qwen2.5:7b"
RESULTS_DIR  = "./results"
REQUEST_DELAY = 0.0

# Какие расширения берём. Для каждого — свой ридер (см. ниже).
EXTENSIONS = {
    ".txt", ".md",                         # plain text
    ".py", ".java", ".c", ".cpp", ".cs",   # исходники — тоже текст
    ".docx",                               # нужен python-docx
    ".pdf",                                # нужен pypdf
}

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
 
По каждому критерию напиши: номер, «выполнено» или «не выполнено» и одно
короткое предложение, почему. Потом напиши вердикт: «готово к сдаче» или «доработать».
В конце напиши, что студенту исправить (2-3 пункта).
Не придумывай ошибок, которых нет. Отвечай по-русски, просто.
 
Код студента:
{content}
"""

# ============================================================
# Чтение файлов
# ============================================================

# Расширения, которые читаются как обычный текст
_PLAIN_TEXT_EXT = {
    ".txt", ".md", ".rst",
    ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs",
    ".js", ".ts", ".go", ".rs", ".rb", ".php",
    ".json", ".yaml", ".yml", ".xml", ".html", ".css",
    ".sql", ".sh", ".bat", ".ps1",
}


def _read_plain(path: Path) -> str:
    """Читаем как текст, аккуратно перебирая кодировки."""
    # utf-8-sig — чтобы BOM не попал в начало строки (частая проблема с Windows)
    for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    # latin-1 не падает никогда — сюда дойдём только при странных файлах
    return path.read_text(encoding="latin-1", errors="replace")


def _read_docx(path: Path) -> str:
    """Текст из .docx (абзацы + таблицы)."""
    try:
        from docx import Document
    except ImportError as e:
        raise RuntimeError("Нужен python-docx: pip install python-docx") from e

    doc = Document(str(path))
    parts: list[str] = []

    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)

    # Таблицы часто содержат данные/результаты — их тоже вытаскиваем
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))

    return "\n".join(parts)


def _read_pdf(path: Path) -> str:
    """Текст из .pdf. Сканы без OCR слоя вернут пустоту — это нормально."""
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("Нужен pypdf: pip install pypdf") from e

    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n".join(pages)


def read_text_from_file(path: str | Path) -> str:
    """Единая точка входа: выбирает ридер по расширению."""
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
# Работа с моделью
# ============================================================
def ask_model(model: str, prompt: str) -> str:
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        # options={"temperature": 0, "num_predict": 1024},
    )
    return response["message"]["content"]


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
            print("  ⚠ текст не извлечён (пустой файл или PDF-скан без OCR), пропуск")
            continue

        prompt = PROMPT_TEMPLATE.replace("{content}", content)

        t0 = time.time()
        try:
            answer = ask_model(MODEL, prompt)
        except Exception as e:
            print(f"  ✗ ошибка модели: {e}")
            continue
        dt = time.time() - t0

        print(f"  ✓ ответ за {dt:.1f} с, {len(content)} симв. на входе, "
              f"{len(answer)} на выходе")

        out_path = Path(RESULTS_DIR) / f"{file_path.stem}.txt"
        out_path.write_text(answer, encoding="utf-8")

        if REQUEST_DELAY:
            time.sleep(REQUEST_DELAY)


if __name__ == "__main__":
    main()