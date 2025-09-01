# Используем Python 3.11 slim
FROM python:3.11-slim-bookworm

# Устанавливаем рабочую директорию
WORKDIR /usr/src/app/src

# Устанавливаем зависимости системы
RUN apt-get update && \
    apt-get install -y gcc netcat-openbsd && \
    apt-get clean

# Копируем requirements.txt
COPY requirements.txt ../

# Обновляем pip и ставим зависимости
RUN pip install --upgrade pip
RUN pip install -r ../requirements.txt

# Копируем весь код проекта в контейнер
COPY ./src .

# Указываем переменную окружения PYTHONPATH, чтобы Python видел модуль app
ENV PYTHONPATH=/usr/src/app/src

# Запуск FastAPI через uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
