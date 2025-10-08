import asyncio
import time
import httpx
import random
from collections import defaultdict
import statistics

class SimpleBrowserAPITest:
    def __init__(self, base_url):
        self.base_url = base_url
        self.results = defaultdict(list)
    
    async def test_protocol(self, use_http2=False, test_name="Test"):
        """Тестирует один протокол с браузероподобным поведением"""
        protocol = "HTTP/2" if use_http2 else "HTTP/1.1"
        print(f"🌐 {test_name} с {protocol}")
        
        # Конфигурация клиента как в браузере
        client_kwargs = {
            'http2': use_http2,
            'verify': False,  # Игнорируем SSL для localhost
            'timeout': 30.0,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, */*',
                'Accept-Encoding': 'gzip, deflate, br',
            },
            'limits': httpx.Limits(
                max_connections=100 if use_http2 else 6,  # Ключевое различие!
                max_keepalive_connections=20 if use_http2 else 6,
            )
        }
        
        if not use_http2:
            client_kwargs['http1'] = True
        
        all_response_times = []
        successful_requests = 0
        total_requests = 0
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            # Фаза 1: Имитация загрузки страницы - несколько параллельных запросов
            print("  📊 Фаза 1: Параллельные запросы (имитация загрузки страницы)")
            
            # Создаем 15-20 параллельных запросов разных типов
            phase1_tasks = []
            for i in range(18):
                if i % 2 == 0:  # 50% на список продуктов
                    phase1_tasks.append(self._make_simple_request(client, "/products"))
                else:  # 50% на детали продукта
                    product_id = random.randint(1, 100)
                    phase1_tasks.append(self._make_simple_request(client, f"/products/{product_id}"))
            
            # Запускаем все параллельно
            phase1_start = time.time()
            phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)
            phase1_duration = time.time() - phase1_start
            
            # Обрабатываем результаты
            for result in phase1_results:
                total_requests += 1
                if isinstance(result, dict) and result['success']:
                    successful_requests += 1
                    all_response_times.append(result['duration'])
            
            print(f"    ✅ {len(phase1_tasks)} запросов за {phase1_duration:.3f}с")
            
            # Короткая пауза (как в браузере между действиями)
            await asyncio.sleep(0.2)
            
            # Фаза 2: Имитация пользовательских действий - несколько волн запросов
            print("  📊 Фаза 2: Волны запросов (имитация действий пользователя)")
            
            # Создаем 30 запросов, но выполняем волнами
            all_phase2_tasks = []
            for i in range(30):
                if i % 3 == 0:  # 33% на список
                    all_phase2_tasks.append(self._make_simple_request(client, "/products"))
                else:  # 67% на детали
                    product_id = random.randint(1, 100)
                    all_phase2_tasks.append(self._make_simple_request(client, f"/products/{product_id}"))
            
            # Выполняем волнами разного размера (как в браузере)
            wave_sizes = [6, 8, 4, 7, 5]  # Разный параллелизм
            phase2_start = time.time()
            
            task_index = 0
            wave_num = 0
            
            while task_index < len(all_phase2_tasks):
                wave_size = wave_sizes[wave_num % len(wave_sizes)]
                current_wave = all_phase2_tasks[task_index:task_index + wave_size]
                
                # Небольшая случайная задержка между волнами
                if wave_num > 0:
                    await asyncio.sleep(random.uniform(0.05, 0.1))
                
                wave_results = await asyncio.gather(*current_wave, return_exceptions=True)
                
                for result in wave_results:
                    total_requests += 1
                    if isinstance(result, dict) and result['success']:
                        successful_requests += 1
                        all_response_times.append(result['duration'])
                
                task_index += wave_size
                wave_num += 1
            
            phase2_duration = time.time() - phase2_start
            print(f"    ✅ {len(all_phase2_tasks)} запросов за {phase2_duration:.3f}с")
            
            # Фаза 3: Фоновые запросы (имитация lazy loading)
            print("  📊 Фаза 3: Фоновые запросы")
            
            phase3_tasks = []
            for i in range(12):
                if random.random() > 0.3:
                    phase3_tasks.append(self._make_simple_request(client, "/products"))
                else:
                    product_id = random.randint(1, 100)
                    phase3_tasks.append(self._make_simple_request(client, f"/products/{product_id}"))
            
            phase3_start = time.time()
            phase3_results = await asyncio.gather(*phase3_tasks, return_exceptions=True)
            phase3_duration = time.time() - phase3_start
            
            for result in phase3_results:
                total_requests += 1
                if isinstance(result, dict) and result['success']:
                    successful_requests += 1
                    all_response_times.append(result['duration'])
            
            print(f"    ✅ {len(phase3_tasks)} запросов за {phase3_duration:.3f}с")
        
        # Статистика
        total_duration = phase1_duration + phase2_duration + phase3_duration
        
        stats = {
            'protocol': protocol,
            'total_duration': total_duration,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
            'avg_response_time': statistics.mean(all_response_times) if all_response_times else 0,
            'p95_response_time': statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else 0,
            'requests_per_second': successful_requests / total_duration if total_duration > 0 else 0,
        }
        
        self.results[protocol].append(stats)
        return stats
    
    async def _make_simple_request(self, client, endpoint):
        """Простой запрос к API"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            response = await client.get(url)
            duration = time.time() - start_time
            
            return {
                'success': response.status_code == 200,
                'duration': duration,
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            }
    
    def run_comparison(self, iterations=3):
        """Запускает сравнение HTTP/1.1 и HTTP/2"""
        print("🚀 ЗАПУСК ТЕСТА ЭМУЛЯЦИИ БРАУЗЕРА")
        print("="*50)
        print("Эндпоинты:")
        print(f"  - {self.base_url}/products")
        print(f"  - {self.base_url}/products/{{id}}")
        print("="*50)
        
        async def run_tests():
            for i in range(iterations):
                print(f"\n🎯 Итерация {i+1}/{iterations}")
                print("-" * 40)
                
                # Тестируем HTTP/1.1
                http1_stats = await self.test_protocol(use_http2=False, test_name=f"Итерация {i+1}")
                
                # Пауза между тестами
                await asyncio.sleep(2)
                
                # Тестируем HTTP/2
                http2_stats = await self.test_protocol(use_http2=True, test_name=f"Итерация {i+1}")
                
                # Быстрое сравнение для этой итерации
                rps_diff = ((http2_stats['requests_per_second'] - http1_stats['requests_per_second']) / 
                           http1_stats['requests_per_second'] * 100)
                print(f"    🔄 RPS разница: {rps_diff:+.1f}%")
                
                # Пауза между итерациями
                if i < iterations - 1:
                    await asyncio.sleep(3)
        
        asyncio.run(run_tests())
        self._print_final_results()
    
    def _print_final_results(self):
        """Выводит финальные результаты сравнения"""
        print("\n" + "="*70)
        print("📊 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ")
        print("="*70)
        
        if not self.results:
            print("Нет данных для анализа")
            return
        
        # Агрегируем результаты
        http1_all = self.results['HTTP/1.1']
        http2_all = self.results['HTTP/2']
        
        def aggregate_stats(stats_list):
            return {
                'avg_rps': statistics.mean([s['requests_per_second'] for s in stats_list]),
                'avg_response_time': statistics.mean([s['avg_response_time'] for s in stats_list]),
                'avg_p95': statistics.mean([s['p95_response_time'] for s in stats_list]),
                'avg_success_rate': statistics.mean([s['success_rate'] for s in stats_list]),
                'total_requests': sum([s['total_requests'] for s in stats_list]),
                'total_duration': statistics.mean([s['total_duration'] for s in stats_list]),
            }
        
        http1_agg = aggregate_stats(http1_all)
        http2_agg = aggregate_stats(http2_all)
        
        # Расчет улучшения
        rps_improvement = ((http2_agg['avg_rps'] - http1_agg['avg_rps']) / http1_agg['avg_rps']) * 100
        response_improvement = ((http1_agg['avg_response_time'] - http2_agg['avg_response_time']) / 
                               http1_agg['avg_response_time']) * 100
        
        print(f"\n🔵 HTTP/1.1 (среднее по {len(http1_all)} тестам):")
        print(f"   📈 Запросов в секунду: {http1_agg['avg_rps']:.1f}")
        print(f"   ⏱️  Среднее время ответа: {http1_agg['avg_response_time']*1000:.1f} мс")
        print(f"   📊 P95 время ответа: {http1_agg['avg_p95']*1000:.1f} мс")
        print(f"   ✅ Успешность: {http1_agg['avg_success_rate']:.1f}%")
        
        print(f"\n🟢 HTTP/2 (среднее по {len(http2_all)} тестам):")
        print(f"   📈 Запросов в секунду: {http2_agg['avg_rps']:.1f}")
        print(f"   ⏱️  Среднее время ответа: {http2_agg['avg_response_time']*1000:.1f} мс")
        print(f"   📊 P95 время ответа: {http2_agg['avg_p95']*1000:.1f} мс")
        print(f"   ✅ Успешность: {http2_agg['avg_success_rate']:.1f}%")
        
        print(f"\n🎯 СРАВНЕНИЕ:")
        print(f"   🚀 Ускорение RPS: {rps_improvement:+.1f}%")
        print(f"   ⚡ Ускорение ответа: {response_improvement:+.1f}%")
        
        if rps_improvement > 5:
            print(f"\n✅ HTTP/2 ЗНАЧИТЕЛЬНО БЫСТРЕЕ на {rps_improvement:.1f}%!")
        elif rps_improvement > 0:
            print(f"\n✅ HTTP/2 быстрее на {rps_improvement:.1f}%")
        elif rps_improvement > -5:
            print(f"\n⚠️  Производительность примерно одинакова")
        else:
            print(f"\n❌ HTTP/2 медленнее на {abs(rps_improvement):.1f}%")
        
        print(f"\n💡 Общее количество запросов:")
        print(f"   HTTP/1.1: {http1_agg['total_requests']}")
        print(f"   HTTP/2:   {http2_agg['total_requests']}")

# Запуск теста
if __name__ == "__main__":
    base_url = "https://localhost"  # Ваш URL
    
    # print("🔍 ПРОВЕРКА ПОДКЛЮЧЕНИЯ...")
    # try:
    #     import requests
    #     requests.get(f"{base_url}/products", verify=False, timeout=5)
    #     print("✅ Сервер доступен")
    # except Exception as e:
    #     print(e)
    #     print("❌ Сервер недоступен! Проверьте что сервер запущен.")
    #     exit(1)
    
    # Запускаем тест
    tester = SimpleBrowserAPITest(base_url)
    tester.run_comparison(iterations=3)  # 3 итерации для статистики