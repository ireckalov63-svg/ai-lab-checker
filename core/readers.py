"""Чтение загруженных файлов. Формат считается поддерживаемым только если его
ридер реально работает (для .pdf и .docx проверяется наличие библиотеки)."""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from .errors import (CorruptedFile, EmptyFile, FileTooLarge, ReadFailure,
                     UnsupportedFormat)

MAX_FILE_BYTES = 5 * 1024 * 1024      # размер загружаемого файла
MAX_ZIP_UNPACKED = 5 * 1024 * 1024    # защита от zip-бомб
MAX_CHARS = 20_000                    # больше в модель не отправляем

PLAIN = {".txt", ".md", ".py", ".java"}
_ENCODINGS = ("utf-8-sig", "utf-8", "cp1251")


@dataclass
class LoadedWork:
    filename: str      # имя работы (внутри архива — имя файла из архива)
    extension: str
    text: str
    size_bytes: int    # размер исходного загруженного файла


def _module_ok(name: str) -> bool:
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def supported_extensions() -> list[str]:
    exts = sorted(PLAIN)
    if _module_ok("pypdf"):
        exts.append(".pdf")
    if _module_ok("docx"):
        exts.append(".docx")
    return exts + [".zip"]


def _decode(data: bytes) -> str:
    for enc in _ENCODINGS:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise CorruptedFile("не удалось определить кодировку")


def _read_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise CorruptedFile("pdf зашифрован")
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except CorruptedFile:
        raise
    except Exception as e:
        raise CorruptedFile(f"pdf: {type(e).__name__}") from e


def _read_docx(data: bytes) -> str:
    from docx import Document
    try:
        doc = Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception as e:
        raise CorruptedFile(f"docx: {type(e).__name__}") from e


def _extract_from_zip(data: bytes, allowed: set[str]) -> tuple[str, bytes]:
    """Достаёт из архива ровно одну работу. Пути из архива не используются."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            candidates = [
                i for i in z.infolist()
                if not i.is_dir()
                and "__MACOSX" not in i.filename
                and not PurePosixPath(i.filename).name.startswith(".")
                and PurePosixPath(i.filename).suffix.lower() in allowed
            ]
            if not candidates:
                raise UnsupportedFormat("в архиве нет подходящих файлов")
            if len(candidates) > 1:
                raise UnsupportedFormat("в архиве несколько файлов")
            info = candidates[0]
            if info.file_size > MAX_ZIP_UNPACKED:
                raise FileTooLarge("файл в архиве слишком большой")
            return PurePosixPath(info.filename).name, z.read(info)
    except zipfile.BadZipFile as e:
        raise CorruptedFile("повреждённый zip") from e


def load_work(filename: str, data: bytes, allowed_formats: tuple[str, ...] | None = None) -> LoadedWork:
    """Читает файл и возвращает текст. Бросает типизированные ошибки."""
    size = len(data)
    if size > MAX_FILE_BYTES:
        raise FileTooLarge(f"{size} байт")
    ext = PurePosixPath(filename).suffix.lower()
    supported = set(supported_extensions())
    if ext not in supported:
        raise UnsupportedFormat(ext)

    if ext == ".zip":
        inner_allowed = {e for e in supported if e != ".zip"}
        if allowed_formats:
            inner_allowed &= set(allowed_formats)
        filename, data = _extract_from_zip(data, inner_allowed)
        ext = PurePosixPath(filename).suffix.lower()
    elif allowed_formats and ext not in allowed_formats:
        raise UnsupportedFormat(f"{ext} не разрешён рубрикой")

    if not data.strip():
        raise EmptyFile("файл пуст")
    try:
        if ext == ".pdf":
            text = _read_pdf(data)
        elif ext == ".docx":
            text = _read_docx(data)
        else:
            text = _decode(data)
    except (CorruptedFile, UnsupportedFormat):
        raise
    except Exception as e:
        raise ReadFailure(type(e).__name__) from e

    if "\x00" in text:
        raise CorruptedFile("в тексте нулевые байты (бинарный файл)")
    if not text.strip():
        raise EmptyFile("текст не извлечён")
    if len(text) > MAX_CHARS:
        raise FileTooLarge(f"{len(text)} символов")
    return LoadedWork(filename=filename, extension=ext, text=text, size_bytes=size)
