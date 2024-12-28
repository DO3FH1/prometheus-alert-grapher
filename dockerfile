FROM python:3.8-slim

# Установка необходимых пакетов и зависимостей Python
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

# Копирование приложения
WORKDIR /app
COPY app.py .

# Запуск приложения
CMD ["python", "app.py"]
