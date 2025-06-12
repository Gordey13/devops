# Этап сборки
FROM python:3.9-slim as builder

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y gcc libpq-dev

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Финальный образ
FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Копирование кода
COPY . .

# Настройка среды
ENV PYTHONPATH=/app
ENV PROMETHEUS_MULTIPROC_DIR=/tmp

# Запуск приложения
CMD ["sh", "-c", "uvicorn app.api.base_api:app --host 0.0.0.0 --port 8000 & python app/consumers/kafka_consumer.py"] 