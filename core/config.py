"""Настройки. Переопределяются переменными окружения."""
import os

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("LAB_MODEL", "qwen2.5:7b")
LLM_TIMEOUT_S = float(os.getenv("LAB_LLM_TIMEOUT", "180"))   # ожидание ответа модели
LLM_ATTEMPTS = int(os.getenv("LAB_LLM_ATTEMPTS", "2"))       # 1 основная + повторы при невалидном JSON
NUM_CTX = int(os.getenv("LAB_NUM_CTX", "8192"))
