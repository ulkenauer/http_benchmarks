#!/bin/bash

# Функция для настройки сетевых ограничений
setup_network() {
    local interface=eth0
    
    echo "Setting up network limitations..."
    
    # Очистка предыдущих правил
    tc qdisc del dev $interface root 2>/dev/null || true
    
    # Добавление задержки, потери пакетов и ограничения带宽
    # Формат: delay LATENCY JITTER CORRELATION distribution DISTRIBUTION
    tc qdisc add dev $interface root netem \
        delay 50ms
        # delay 300ms 20ms 25%
        # delay 100ms 20ms 25% \
        # loss 1% \
        # rate 10mbit \
        # duplicate 0.5%
    
    echo "Network limitations applied:"
    echo "  - Latency: 50ms"
    # echo "  - Latency: 300ms ± 20ms"
    # echo "  - Latency: 100ms ± 20ms"
    # echo "  - Packet loss: 1%"
    # echo "  - Bandwidth: 10 mbit"
    # echo "  - Duplicate packets: 0.5%"
}

# Настройка сети
setup_network

# Запуск FastAPI приложения через hypercorn
echo "Starting FastAPI application..."
uv run hypercorn http_app:app --config hypercorn.toml --debug --bind "0.0.0.0:443" --keyfile key.pem --certfile cert.pem