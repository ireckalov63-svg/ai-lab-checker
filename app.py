import streamlit as st

st.title("ИИ-ассистент для проверки лабораторных")
st.write("Интерфейс находится в разработке. Скоро здесь все появится.")

# Создаем виджет загрузки файла с нужными расширениями
uploaded_file = st.file_uploader(
    "Выберите файл с кодом или текстом", 
    type=["txt", "py", "java"]
)

# Если файл был загружен
if uploaded_file is not None:
    st.success(f"Файл **{uploaded_file.name}** успешно загружен!")
    
    # Читаем содержимое файла. 
    file_contents = uploaded_file.read().decode("utf-8")
    
    st.subheader("Содержимое файла:")
    
    # Выводим содержимое
    st.code(file_contents, language=None)