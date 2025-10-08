import asyncio
import time
import statistics
import argparse
from collections import defaultdict
from urllib.parse import urlparse
import ssl
import sys

try:
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.connection import QuicConnection
    from aioquic.h3.connection import H3Connection, H3_ALPN
    from aioquic.h3.events import HeadersReceived, DataReceived, H3Event
    from aioquic.quic.events import QuicEvent, StreamDataReceived
except ImportError:
    print("Ошибка: требуется установить aioquic")
    print("pip install aioquic")
    sys.exit(1)


class HTTP3LoadTester:
    def __init__(self, url, concurrency=10, total_requests=100, timeout=10.0):
        self.url = url
        self.parsed_url = urlparse(url)
        self.concurrency = concurrency
        self.total_requests = total_requests
        self.timeout = timeout
        
        # Результаты тестирования
        self.results = {
            'response_times': [],
            'status_codes': defaultdict(int),
            'errors': 0,
            'timeouts': 0
        }
        
        # Семафор для ограничения параллельных запросов
        self.semaphore = asyncio.Semaphore(concurrency)
        
    async def create_quic_connection(self):
        """Создает QUIC соединение"""
        configuration = QuicConfiguration(
            alpn_protocols=H3_ALPN,
            verify_mode=ssl.CERT_NONE,
        )
        
        # Создаем QUIC соединение
        connection = QuicConnection(
            configuration=configuration,
            destination_addr=(self.parsed_url.hostname, self.parsed_url.port or 443)
        )
        
        return connection
    
    async def send_single_request(self, request_id):
        """Отправляет один HTTP/3 запрос"""
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # Создаем QUIC соединение для каждого запроса
                connection = await self.create_quic_connection()
                http = H3Connection(connection)
                
                # Создаем транспорт
                loop = asyncio.get_event_loop()
                transport, protocol = await loop.create_datagram_endpoint(
                    lambda: QuicProtocol(connection),
                    remote_addr=(self.parsed_url.hostname, self.parsed_url.port or 443)
                )
                
                try:
                    # Открываем поток
                    stream_id = connection.get_next_available_stream_id()
                    
                    # Отправляем заголовки
                    headers = [
                        (b":method", b"GET"),
                        (b":scheme", self.parsed_url.scheme.encode()),
                        (b":authority", self.parsed_url.netloc.encode()),
                        (b":path", self.parsed_url.path.encode() or b"/"),
                        (b"user-agent", b"load-tester/1.0"),
                    ]
                    http.send_headers(stream_id=stream_id, headers=headers)
                    http.send_data(stream_id=stream_id, data=b"", end_stream=True)
                    
                    # Отправляем данные
                    connection.transmit()
                    
                    # Ждем ответ
                    response_received = False
                    status_code = None
                    data_received = b""
                    
                    end_time = start_time + self.timeout
                    
                    while time.time() < end_time and not response_received:
                        # Получаем события
                        event = connection.next_event()
                        
                        if event is None:
                            # Нет событий, передаем данные и ждем
                            connection.transmit()
                            await asyncio.sleep(0.01)
                            continue
                            
                        if isinstance(event, StreamDataReceived):
                            if event.stream_id == stream_id:
                                data_received += event.data
                                
                        if isinstance(event, HeadersReceived):
                            if event.stream_id == stream_id:
                                # Ищем статус код
                                for header, value in event.headers:
                                    if header == b":status":
                                        status_code = int(value.decode())
                                        self.results['status_codes'][status_code] += 1
                                        break
                                response_received = True
                                break
                    
                    response_time = (time.time() - start_time) * 1000
                    self.results['response_times'].append(response_time)
                    
                    if not response_received:
                        self.results['timeouts'] += 1
                        print(f"Request {request_id}: TIMEOUT")
                    else:
                        print(f"Request {request_id}: {status_code} - {response_time:.2f}ms")
                        
                except Exception as e:
                    self.results['errors'] += 1
                    print(f"Request {request_id}: ERROR - {str(e)}")
                    
                finally:
                    transport.close()
                    
            except Exception as e:
                self.results['errors'] += 1
                print(f"Request {request_id}: CONNECTION ERROR - {str(e)}")
    
    async def run_test(self):
        """Запускает нагрузочное тестирование"""
        print(f"Starting HTTP/3 load test for {self.url}")
        print(f"Concurrency: {self.concurrency}, Total requests: {self.total_requests}")
        print("-" * 50)
        
        start_time = time.time()
        
        # Создаем задачи для всех запросов
        tasks = []
        for i in range(self.total_requests):
            task = asyncio.create_task(self.send_single_request(i + 1))
            tasks.append(task)
        
        # Ждем завершения всех задач
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Выводим результаты
        self.print_results(total_time)
        
        return self.results
    
    def print_results(self, total_time):
        """Выводит результаты тестирования"""
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ HTTP/3")
        print("=" * 50)
        
        total_requests = len(self.results['response_times'])
        successful_requests = total_requests - self.results['errors'] - self.results['timeouts']
        
        print(f"URL: {self.url}")
        print(f"Общее время: {total_time:.2f} сек")
        print(f"Всего запросов: {self.total_requests}")
        print(f"Успешных запросов: {successful_requests}")
        print(f"Ошибок: {self.results['errors']}")
        print(f"Таймаутов: {self.results['timeouts']}")
        print(f"Запросов в секунду: {total_requests / total_time:.2f}")
        
        if self.results['response_times']:
            times = self.results['response_times']
            print(f"\nВРЕМЯ ОТВЕТА (мс):")
            print(f"  Среднее: {statistics.mean(times):.2f}")
            print(f"  Медиана: {statistics.median(times):.2f}")
            print(f"  Максимальное: {max(times):.2f}")
            print(f"  Минимальное: {min(times):.2f}")
            
            # Вычисляем перцентили
            sorted_times = sorted(times)
            n = len(sorted_times)
            p95 = sorted_times[int(0.95 * n)] if n > 0 else 0
            p99 = sorted_times[int(0.99 * n)] if n > 0 else 0
            
            print(f"  95-й перцентиль: {p95:.2f}")
            print(f"  99-й перцентиль: {p99:.2f}")
        
        print(f"\nСТАТУС КОДЫ:")
        for code, count in self.results['status_codes'].items():
            print(f"  {code}: {count} запросов")


class QuicProtocol:
    """Протокол для обработки QUIC соединения"""
    def __init__(self, connection):
        self.connection = connection
    
    def datagram_received(self, data, addr):
        self.connection.receive_datagram(data, addr, time.time())
    
    def connection_lost(self, exc):
        pass


async def main():
    parser = argparse.ArgumentParser(description='HTTP/3 Load Tester')
    parser.add_argument('--url', required=True, help='URL для тестирования (например, https://http3-test.litespeedtech.com:4433/)')
    parser.add_argument('--concurrency', '-c', type=int, default=10, help='Количество параллельных соединений')
    parser.add_argument('--requests', '-r', type=int, default=100, help='Общее количество запросов')
    parser.add_argument('--timeout', '-t', type=float, default=10.0, help='Таймаут для запросов в секундах')
    
    args = parser.parse_args()
    
    # Проверяем URL
    if not args.url.startswith('https://'):
        print("Ошибка: URL должен использовать HTTPS")
        return
    
    # Создаем и запускаем тестер
    tester = HTTP3LoadTester(
        url=args.url,
        concurrency=args.concurrency,
        total_requests=args.requests,
        timeout=args.timeout
    )
    
    await tester.run_test()


if __name__ == "__main__":
    # Проверяем версию Python
    if sys.version_info < (3, 7):
        print("Требуется Python 3.7 или выше")
        sys.exit(1)
    
    asyncio.run(main())