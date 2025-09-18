# ---------- build stage ----------
FROM python:3.13-slim AS builder

WORKDIR /app

# Устанавливаем системные зависимости для сборки пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и ставим зависимости в отдельный слой
COPY requirements.txt .

RUN pip install --prefix=/install -r requirements.txt


# ---------- runtime stage ----------
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Копируем только установленные пакеты из builder stage
COPY --from=builder /install /usr/local

# Копируем исходники
COPY src ./src

# Запуск
CMD ["python", "src/main.py"]
