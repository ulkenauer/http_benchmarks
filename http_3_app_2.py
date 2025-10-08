import asyncio
import ssl
from aioquic.asyncio import serve
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import (
    DataReceived,
    HeadersReceived,
    H3Event,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import stream_is_unidirectional
from aioquic.asyncio.protocol import QuicConnectionProtocol


class HTTP3ConnectionHandler:
    def __init__(self, quic, protocol):
        self.quic = quic
        self.protocol = protocol
        self._http = H3Connection(quic)

    def http_event_received(self, event: H3Event):
        if isinstance(event, HeadersReceived):
            self.handle_headers(event)
        elif isinstance(event, DataReceived):
            self.handle_data(event)

    def handle_headers(self, event: HeadersReceived):
        stream_id = event.stream_id
        headers = {}
        method = ""
        path = ""
        
        for header, value in event.headers:
            header_name = header.decode().lower()
            headers[header_name] = value.decode()
            if header == b":method":
                method = value.decode()
            elif header == b":path":
                path = value.decode()

        print(f"Received {method} request for {path} on stream {stream_id}")

        # Формируем ответ
        response_body = f"Hello HTTP/3!\nMethod: {method}\nPath: {path}\nStream ID: {stream_id}".encode('utf-8')

        # Отправляем заголовки ответа
        self._http.send_headers(
            stream_id=stream_id,
            headers=[
                (b":status", b"200"),
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(response_body)).encode()),
                (b"server", b"python-http3-server"),
            ],
        )

        # Отправляем тело ответа
        self._http.send_data(stream_id=stream_id, data=response_body, end_stream=True)

    def handle_data(self, event: DataReceived):
        # Обрабатываем данные тела запроса (если есть)
        if event.data:
            print(f"Received data on stream {event.stream_id}: {event.data.decode('utf-8', errors='ignore')}")


class HTTP3ServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http = None

    def quic_event_received(self, event):
        if self._http is None:
            self._http = HTTP3ConnectionHandler(self._quic, self)
        
        # Обрабатываем события HTTP/3
        for http_event in self._http._http.handle_event(event):
            self._http.http_event_received(http_event)


async def main():
    # Конфигурация QUIC
    configuration = QuicConfiguration(
        is_client=False,
        max_datagram_frame_size=65536,
    )

    # Загружаем SSL сертификаты
    try:
        configuration.load_cert_chain("cert.pem", "key.pem")
    except Exception as e:
        print(f"Error loading certificates: {e}")
        print("Please generate certificates first:")
        print("openssl req -new -x509 -days 365 -nodes -out certificate.pem -keyout private.key -subj \"/CN=localhost\"")
        return

    # Настройки для HTTP/3
    configuration.alpn_protocols = ["h3"]

    # Запускаем сервер
    server_address = "0.0.0.0"  # Слушаем на всех интерфейсах
    server_port = 4433

    print(f"Starting HTTP/3 server on {server_address}:{server_port}")
    print("Make sure you have generated certificate.pem and private.key")
    print("You can test with: curl --http3 https://localhost:4433/ --insecure")
    print("Press Ctrl+C to stop the server")

    try:
        await serve(
            host=server_address,
            port=server_port,
            configuration=configuration,
            create_protocol=HTTP3ServerProtocol,
        )
        # Бесконечно ждем
        await asyncio.Future()
    except Exception as e:
        print(f"Server error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped gracefully")