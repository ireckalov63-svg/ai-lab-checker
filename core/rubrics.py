"""Загрузка рубрик из rubrics/*.json. Папка читается заново при каждом вызове,
поэтому новая или изменённая рубрика видна без перезапуска приложения."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

RUBRICS_DIR = Path(__file__).resolve().parent.parent / "rubrics"

# Допустимые значения поля "auto" у критерия (объективные проверки кода)
AUTO_CHECKS = {"compiles"}


@dataclass(frozen=True)
class Criterion:
    id: int
    text: str
    is_critical: bool = False
    auto: str | None = None          # "compiles": критерий решает результат проверки кода
    requires_compile: bool = False   # нельзя засчитать, если код не компилируется


@dataclass(frozen=True)
class Rubric:
    id: str
    title: str
    description: str
    allowed_formats: tuple[str, ...]
    criteria: tuple[Criterion, ...]
    task: str = ""
    path: str = ""


@dataclass
class LoadResult:
    rubrics: list[Rubric] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)  # «файл: что не так»


def _parse(data: dict, path: Path) -> Rubric:
    for key in ("id", "title", "criteria"):
        if key not in data:
            raise ValueError(f"нет поля «{key}»")
    if not isinstance(data["criteria"], list) or not data["criteria"]:
        raise ValueError("список критериев пуст")

    criteria, seen = [], set()
    for raw in data["criteria"]:
        cid, text = raw.get("id"), str(raw.get("text", "")).strip()
        if not isinstance(cid, int) or isinstance(cid, bool):
            raise ValueError("у критерия нет целочисленного id")
        if cid in seen:
            raise ValueError(f"повторяется id критерия {cid}")
        if not text:
            raise ValueError(f"у критерия {cid} пустой текст")
        auto = raw.get("auto")
        if auto is not None and auto not in AUTO_CHECKS:
            raise ValueError(f"неизвестная автопроверка «{auto}» у критерия {cid}")
        seen.add(cid)
        criteria.append(Criterion(
            id=cid, text=text,
            is_critical=bool(raw.get("is_critical", False)),
            auto=auto,
            requires_compile=bool(raw.get("requires_compile", False)),
        ))

    fmts = tuple(str(f).lower() for f in data.get("allowed_formats", [".txt", ".py", ".java"]))
    return Rubric(
        id=str(data["id"]), title=str(data["title"]),
        description=str(data.get("description", "")),
        allowed_formats=fmts, criteria=tuple(criteria),
        task=str(data.get("task", "")), path=str(path),
    )


def load_rubrics(directory: Path | str = RUBRICS_DIR) -> LoadResult:
    result = LoadResult()
    directory = Path(directory)
    if not directory.is_dir():
        result.problems.append(f"{directory.name}: папка не найдена")
        return result
    ids = set()
    for path in sorted(directory.glob("*.json")):
        try:
            rubric = _parse(json.loads(path.read_text(encoding="utf-8-sig")), path)
            if rubric.id in ids:
                raise ValueError(f"повторяется id рубрики «{rubric.id}»")
            ids.add(rubric.id)
            result.rubrics.append(rubric)
        except (OSError, json.JSONDecodeError) as e:
            result.problems.append(f"{path.name}: не читается как JSON ({type(e).__name__})")
        except (ValueError, AttributeError, TypeError) as e:
            result.problems.append(f"{path.name}: {e}")
    return result
