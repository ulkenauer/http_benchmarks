FROM python:3.13-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копирование приложения
COPY . .

RUN uv sync --frozen

# Установка утилит для сетевого управления
RUN apt-get update && apt-get install -y \
    iproute2 \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Скрипт для настройки сети
COPY setup_network.sh /setup_network.sh
RUN chmod +x /setup_network.sh

EXPOSE 8000

CMD ["/setup_network.sh"]