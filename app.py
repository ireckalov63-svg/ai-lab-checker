import streamlit as st
import zipfile
import io
import time

st.title("ИИ-ассистент для проверки лабораторных")
st.write("Загрузите работы для проверки нейросетью.")

# Создаем виджет загрузки, разрешаем несколько файлов и ZIP
uploaded_files = st.file_uploader(
    "Выберите файлы с кодом, текстом или ZIP-архив", 
    type=["txt", "py", "java", "zip"],
    accept_multiple_files=True
)

# --- Работа с файлами ---
if uploaded_files:
    # Список для хранения (имя_файла, содержимое)
    files_to_check = [] 
    
    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.zip'):
            # Если это ZIP, распаковываем его прямо в памяти
            try:
                with zipfile.ZipFile(uploaded_file, 'r') as z:
                    for filename in z.namelist():
                        # Проверяем расширение внутри архива
                        if filename.endswith(('.py', '.java', '.txt')):
                            with z.open(filename) as f:
                                content = f.read().decode("utf-8", errors="ignore")
                                files_to_check.append((filename, content))
                st.success(f"Архив **{uploaded_file.name}** успешно распакован.")
            except Exception as e:
                st.error(f"Ошибка при чтении архива {uploaded_file.name}: {e}")
        else:
            # Если это обычный файл
            try:
                content = uploaded_file.read().decode("utf-8", errors="ignore")
                files_to_check.append((uploaded_file.name, content))
            except Exception as e:
                st.error(f"Ошибка при чтении файла {uploaded_file.name}: {e}")

    # Если после распаковки список пустой (не нашли ни py, ни java, ни txt)
    if not files_to_check:
        st.warning("В загруженных файлах или архивах не найдено ни одного файла с кодом (.py, .java, .txt). Пожалуйста, проверьте содержимое архива.")
    else:
        # Если файлы есть, показываем кнопку и всё остальное
        st.info(f"Подготовлено к проверке файлов: **{len(files_to_check)}**")
        
        if st.button("Отправить на проверку"):
            
            # --- ЗДЕСЬ БУДЕТ ВЫЗОВ КОДА НИКИТЫ ---
            

            
            # Пока используем заглушку(имитация работы ии)
            with st.spinner("Нейросеть проверяет работы... Это может занять время."):
                time.sleep(2) # Имитируем задержку сети
                
                # Имитируем ответ
                mock_results = [
                    {"filename": name, "status": "Проверено ИИ", "score": 5 if i % 2 == 0 else 3, "comment": "Отличный код!" if i % 2 == 0 else "Есть замечания по стилю."} 
                    for i, (name, content) in enumerate(files_to_check)
                ]
            # -------------------------------------

            # --- Вывод результатов ---
                st.divider()
                st.subheader("Результаты проверки:")
                
                # Проходимся по каждому результату
                for res in mock_results:
                    st.markdown(f"### 📄 {res['filename']}")
                    
                    # Выводим оценку 
                    if res['score'] >= 4:
                        st.success(f"**Оценка: {res['score']}/5** — {res['status']}\n\n{res['comment']}")
                    else:
                        st.error(f"**Оценка: {res['score']}/5** — {res['status']}\n\n{res['comment']}")
                    
                    # Выводим содержимое текущего файла
                    for name, content in files_to_check:
                        if name == res['filename']:
                            with st.expander(f"Посмотреть код файла {name}"):
                                lang = "python" if name.endswith('.py') else ("java" if name.endswith('.java') else None)
                                st.code(content, language=lang)
                            break