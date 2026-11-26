"""Объективные проверки кода. Пользовательский код НЕ запускается:
Python проверяется синтаксически (ast), Java — только компилируется javac
во временной папке с таймаутом. Результат передаётся модели как факт."""
from __future__ import annotations

import ast
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .errors import CodeCheckFailure

JAVAC_TIMEOUT = 20
MAX_DIAG_LINES = 5


@dataclass
class CodeCheck:
    performed: bool          # проверка действительно выполнялась
    ok: bool | None          # True / False; None, если не выполнялась
    summary: str             # короткая фраза-факт для модели и интерфейса
    diagnostics: list[str]   # безопасные строки ошибок (без путей и трассировок)
    method: str = "none"     # "javac" | "ast" | "none"

    @property
    def failed(self) -> bool:
        return self.performed and self.ok is False


def java_available() -> bool:
    return shutil.which("javac") is not None


def _check_python(text: str) -> CodeCheck:
    try:
        ast.parse(text)
        return CodeCheck(True, True, "Синтаксис Python корректен. Код не запускался (статическая проверка).", [], "ast")
    except SyntaxError as e:
        line = f"строка {e.lineno}: {e.msg}"
        return CodeCheck(True, False, "Найдена синтаксическая ошибка Python.", [line], "ast")


_CLASS_RE = re.compile(r"public\s+(?:final\s+|abstract\s+)*(?:class|interface|enum|record)\s+([A-Za-z_]\w*)")


def _check_java(text: str) -> CodeCheck:
    if not java_available():
        return CodeCheck(False, None,
                         "Компиляция Java не выполнялась: JDK (javac) не найден. Выполнена только оценка текста кода.",
                         [], "none")
    m = _CLASS_RE.search(text)
    class_name = m.group(1) if m else "Main"
    try:
        with tempfile.TemporaryDirectory(prefix="labcheck_") as tmp:
            src = Path(tmp) / f"{class_name}.java"
            src.write_text(text, encoding="utf-8")
            proc = subprocess.run(
                ["javac", "-proc:none", "-encoding", "UTF-8", "-Xmaxerrs", "5", "-d", tmp, src.name],
                cwd=tmp, capture_output=True, text=True, timeout=JAVAC_TIMEOUT,
                env={"PATH": "/usr/bin:/bin:/usr/local/bin", "LANG": "C.UTF-8"},
            )
            raw = (proc.stderr or "") + (proc.stdout or "")
    except subprocess.TimeoutExpired as e:
        raise CodeCheckFailure("javac timeout") from e
    except OSError as e:
        raise CodeCheckFailure(f"javac: {type(e).__name__}") from e

    if proc.returncode == 0:
        return CodeCheck(True, True, "Java-код успешно скомпилирован. Программа не запускалась.", [], "javac")

    diags = []
    for line in raw.splitlines():
        # Формат javac: «Main.java:12: error: текст» — оставляем только это
        mm = re.match(r"^[\w$]+\.java:(\d+):\s*error:\s*(.+)$", line.strip())
        if mm:
            diags.append(f"строка {mm.group(1)}: {mm.group(2)}")
    return CodeCheck(True, False, "Java-код не компилируется.", diags[:MAX_DIAG_LINES], "javac")


def check_code(extension: str, text: str) -> CodeCheck:
    if extension == ".py":
        return _check_python(text)
    if extension == ".java":
        return _check_java(text)
    return CodeCheck(False, None, "Автоматическая проверка запуска не применялась: это не файл с кодом.", [], "none")
