from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3_ALPN
from aioquic.h3.exceptions import H3Error
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived
import asyncio

class Http3Server:
    def __init__(self):
        self.configuration = QuicConfiguration(
            alpn_protocols=H3_ALPN,
            is_client=False,
            max_datagram_frame_size=65536,
        )
        self.configuration.load_cert_chain('cert.pem', 'key.pem')

    async def handle_request(self, stream_id, headers, data):
        method = ""
        path = ""
        for header, value in headers:
            if header == b":method":
                method = value.decode()
            elif header == b":path":
                path = value.decode()

        if method == "GET" and path == "/":
            response_headers = [
                (b":status", b"200"),
                (b"content-type", b"text/plain"),
            ]
            response_data = b"Hello, HTTP/3!"
            
            self.http.send_headers(stream_id, response_headers)
            self.http.send_data(stream_id, response_data, end_stream=True)

    def http_event_received(self, event):
        if isinstance(event, HeadersReceived):
            asyncio.create_task(self.handle_request(
                stream_id=event.stream_id,
                headers=event.headers,
                data=b""
            ))
        elif isinstance(event, DataReceived):
            # Обработка POST данных при необходимости
            pass

    async def handle_connection(self, reader, writer):
        self.http = H3Connection(reader, writer)
        try:
            while True:
                event = await self.http.receive_event()
                if event is None:
                    break
                self.http_event_received(event)
        except H3Error as e:
            print(f"H3Error: {e}")
        finally:
            writer.close()

    async def run(self, host: str = 'localhost', port: int = 4433):
        await serve(host, port, 
                   configuration=self.configuration,
                   create_protocol=self.handle_connection)
        print(f"HTTP/3 server running on https://{host}:{port}")

        await asyncio.Future()  # Бесконечное ожидание

if __name__ == "__main__":
    server = Http3Server()
    asyncio.run(server.run())