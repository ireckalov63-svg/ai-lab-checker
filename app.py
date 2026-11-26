"""Интерфейс ИИ-ассистента проверки лабораторных работ (Streamlit).
Вся логика проверки — в пакете core/; здесь только экраны."""
import threading
import time
from pathlib import PurePosixPath

import streamlit as st

from core import config, llm
from core.code_checks import java_available
from core.pipeline import Progress, run_check
from core.readers import supported_extensions
from core.rubrics import load_rubrics
from ui import components as ui
from ui.styles import CSS

st.set_page_config(page_title="Проверка лабораторных", page_icon="✅", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

S = st.session_state
S.setdefault("page", "check")        # check | labs
S.setdefault("screen", "upload")     # upload | processing | result | error
S.setdefault("upload_key", 0)
S.setdefault("rubric_id", None)


@st.cache_data(ttl=8, show_spinner=False)
def _status() -> str:
    return llm.server_status()


def go(screen: str):
    S.screen = screen


def reset():
    S.screen = "upload"
    S.upload_key += 1
    S.pop("job", None)
    S.pop("payload", None)


# ---------- шапка ----------
st.markdown(ui.topbar(_status(), config.MODEL), unsafe_allow_html=True)
with st.container(key="nav"):
    c1, c2, _ = st.columns([1, 1, 4])
    for col, page, label in ((c1, "check", "Проверка"), (c2, "labs", "Лабораторные")):
        with col:
            key = f"nav_on_{page}" if S.page == page else f"nav_{page}"
            if st.button(label, key=key, type="tertiary"):
                S.page = page
                st.rerun()

loaded = load_rubrics()   # перечитывается при каждом обновлении страницы
rubrics = {r.id: r for r in loaded.rubrics}


# ---------- страница «Лабораторные» ----------
if S.page == "labs":
    st.markdown('<div class="hero"><h1>Лабораторные</h1><p>Критерии, по которым ассистент проверяет работу. '
                'Они берутся из файлов в папке rubrics.</p></div>', unsafe_allow_html=True)
    if not rubrics:
        st.markdown('<div class="hint">Лабораторные не найдены. Добавьте JSON-файл в папку rubrics.</div>', unsafe_allow_html=True)
    for r in rubrics.values():
        st.markdown(ui.lab_card(r), unsafe_allow_html=True)
    for p in loaded.problems:
        st.markdown(f'<div class="hint">Пропущено: {ui.e(p)}</div>', unsafe_allow_html=True)
    st.stop()


# ---------- экран 1: загрузка ----------
def screen_upload():
    st.markdown('<div class="hero"><h1>Проверьте свою лабораторную работу</h1>'
                '<p>Загрузите выполненную работу и получите подробную обратную связь по критериям преподавателя.</p></div>',
                unsafe_allow_html=True)
    if not rubrics:
        st.markdown(ui.error_block("rubric_problem")[0], unsafe_allow_html=True)
        for p in loaded.problems:
            st.caption(p)
        return

    st.markdown('<div class="label">Лабораторная работа</div>', unsafe_allow_html=True)
    ids = list(rubrics)
    if S.rubric_id not in ids:
        S.rubric_id = ids[0]
    chosen = st.selectbox("Лабораторная работа", ids, key="rubric_id",
                          format_func=lambda i: rubrics[i].title, label_visibility="collapsed")
    r = rubrics[chosen]
    st.markdown(f'<div class="rubric-meta">{ui.e(r.description)} · критериев: {len(r.criteria)}</div>', unsafe_allow_html=True)

    st.markdown('<div class="label">Файл с работой</div>', unsafe_allow_html=True)
    exts = supported_extensions()
    up = st.file_uploader("Файл с работой", type=[x.lstrip(".") for x in exts],
                          key=f"up_{S.upload_key}", label_visibility="collapsed")
    allowed = [x for x in r.allowed_formats if x in exts]
    hint = "Для этой работы: " + ", ".join(allowed) + (". Один файл или ZIP с одним файлом. До 5 МБ." if ".zip" in exts else ". До 5 МБ.")
    st.markdown(f'<div class="hint">{ui.e(hint)}</div>', unsafe_allow_html=True)

    if up is not None:
        ext = PurePosixPath(up.name).suffix.lower()
        with st.container(key="file_row"):
            a, b = st.columns([6, 1.3])
            a.markdown(ui.file_card(up.name, ext, up.size), unsafe_allow_html=True)
            if b.button("Удалить", key="rm"):
                S.upload_key += 1
                st.rerun()

    with st.container(key="go"):
        if st.button("Проверить работу", type="primary", disabled=up is None, key="start"):
            S.payload = {"name": up.name, "data": up.getvalue(), "rubric_id": chosen}
            go("processing")
            st.rerun()
    if up is None:
        st.markdown('<div class="hint">Кнопка станет доступна после выбора файла.</div>', unsafe_allow_html=True)
    if loaded.problems:
        st.markdown(f'<div class="hint">Не загружено лабораторных: {len(loaded.problems)}. См. вкладку «Лабораторные».</div>', unsafe_allow_html=True)


# ---------- экран 2: процесс ----------
def screen_processing():
    p = S.get("payload")
    if not p or p["rubric_id"] not in rubrics:
        reset(); st.rerun()
    rubric = rubrics[p["rubric_id"]]
    ext = PurePosixPath(p["name"]).suffix.lower()
    st.markdown(f'<div class="hero"><h1>Идёт проверка</h1><p>{ui.e(p["name"])} · {ui.e(rubric.title)}</p></div>',
                unsafe_allow_html=True)

    skip = None
    if ext not in (".py", ".java", ".zip"):
        skip = "Не применяется к этому формату"
    elif ext == ".java" and not java_available():
        skip = "Компиляция недоступна: JDK не найден"

    progress = Progress()
    threading.Thread(target=run_check, args=(p["name"], p["data"], rubric, progress), daemon=True).start()
    slot = st.empty()
    while not progress.finished:
        slot.markdown(ui.steps(progress.stage, progress.queue_position, skip, int(time.time() - progress.started)),
                      unsafe_allow_html=True)
        time.sleep(0.4)
    S.job = progress
    go("error" if progress.error else "result")
    st.rerun()


# ---------- экран 3: результат ----------
def screen_result():
    job = S.job
    res, meta = job.result, job.meta
    st.markdown('<div class="result">', unsafe_allow_html=True)
    st.markdown(ui.verdict_block(res), unsafe_allow_html=True)
    st.markdown('<div class="section-title">Критерии</div>', unsafe_allow_html=True)
    st.markdown(ui.criteria_list(res), unsafe_allow_html=True)
    st.markdown('<div class="section-title">Что нужно исправить</div>', unsafe_allow_html=True)
    st.markdown(ui.recommendations(res), unsafe_allow_html=True)
    st.markdown('<div class="section-title">О проверке</div>', unsafe_allow_html=True)
    st.markdown(ui.meta_block(meta, res), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    with st.container(key="actions"):
        a, b, _ = st.columns([2, 2, 3])
        if a.button("Проверить другую работу", type="primary", key="again"):
            reset(); st.rerun()
        if b.button("Проверить ещё раз", key="redo"):
            go("processing"); st.rerun()


# ---------- экран 4: ошибки ----------
def screen_error():
    err = S.job.error
    html, retry = ui.error_block(err.kind)
    st.markdown(f'<div class="hero"><h1>Проверка не выполнена</h1></div>', unsafe_allow_html=True)
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    with st.container(key="actions"):
        a, b, _ = st.columns([2, 2, 3])
        if retry and a.button("Повторить попытку", type="primary", key="retry"):
            go("processing"); st.rerun()
        if b.button("Загрузить другой файл", key="other", type="secondary" if retry else "primary"):
            reset(); st.rerun()


{"upload": screen_upload, "processing": screen_processing,
 "result": screen_result, "error": screen_error}[S.screen]()
