import asyncio
import ssl
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.h3.connection import H3Connection
from aioquic.h3.events import HeadersReceived, DataReceived

class Http3Client:
    def __init__(self):
        self.configuration = QuicConfiguration(
            alpn_protocols=["h3"],
            is_client=True,
        )
        self.configuration.verify_mode = ssl.CERT_NONE  # Игнорировать самоподписанные сертификаты

    async def test_connection(self):
        try:
            async with connect('localhost', 4433, configuration=self.configuration) as connection:
                print("✅ QUIC соединение установлено")
                
                http = H3Connection(connection)
                
                # Отправляем GET запрос
                stream_id = http.send_headers([
                    (b":method", b"GET"),
                    (b":scheme", b"https"),
                    (b":authority", b"localhost:4433"),
                    (b":path", b"/products"),
                ])
                # http.send_data(stream_id, b"", end_stream=True)
                
                # Получаем ответ
                response_received = False
                while not response_received:
                    event = await http.receive_event()
                    if isinstance(event, HeadersReceived):
                        print(f"📨 Получены заголовки: {event.headers}")
                    elif isinstance(event, DataReceived):
                        print(f"📦 Получены данные: {event.data.decode()}")
                        response_received = True
                
                print("✅ HTTP/3 запрос выполнен успешно")
                return True
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

async def main():
    client = Http3Client()
    success = await client.test_connection()
    if success:
        print("\n🎉 Сервер работает корректно!")
    else:
        print("\n💥 Проблемы с сервером!")

if __name__ == "__main__":
    asyncio.run(main())