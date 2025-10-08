import asyncio
import time
import httpx
import random

async def simple_http2_demo():
    """Простой тест, демонстрирующий преимущество HTTP/2"""
    print("🚀 ЗАПУСК ПРОСТОГО ТЕСТА HTTP/1.1 vs HTTP/2")
    print("=" * 50)
    # return
    # Тестируем оба протокола
    for use_http2 in [False, True]:
        protocol = "HTTP/2" if use_http2 else "HTTP/1.1"
        print(f"\n🔍 Тестируем {protocol}...")
        
        # Настройки клиента - КЛЮЧЕВОЙ МОМЕНТ!
        client_kwargs = {
            'http2': use_http2,
            'verify': False,
            'limits': httpx.Limits(
                max_connections=6 if not use_http2 else 1,  # Для HTTP/1.1 - только 1 соединение!
                max_keepalive_connections=6 if not use_http2 else 1,
            )
        }
        
        start_time = time.time()
        
        # print(client_kwargs)
        async with httpx.AsyncClient(**client_kwargs) as client:
            # Создаем 30 запросов ОДНОВРЕМЕННО
            tasks = []
            for i in range(300):
                if i % 2 == 0:
                    tasks.append(client.get("https://localhost/products"))
                else:
                    product_id = random.randint(1, 50)
                    tasks.append(client.get(f"https://localhost/products/{product_id}"))
            
            # Запускаем ВСЕ запросы параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # print(client.params)
        # print("HTTP VERSION")
        # for r in results:
        #     print(r)
        #     print(r.http_version)
        # Считаем успешные запросы
        success_count = sum(1 for r in results if isinstance(r, httpx.Response))
        rps = success_count / total_time
        
        print(f"✅ {protocol}:")
        print(f"   {success_count}/30 запросов за {total_time:.2f} сек")
        print(f"   {rps:.1f} запросов в секунду")
        
        # Для HTTP/1.1 показываем проблему
        if not use_http2:
            print(f"   ⚠️  HTTP/1.1 с 6 соединениями: запросы выполняются ПОСЛЕДОВАТЕЛЬНО!")
        else:
            print(f"   🚀 HTTP/2: все запросы выполняются ПАРАЛЛЕЛЬНО в одном соединении!")

async def advanced_demo():
    return
    """Более наглядная демонстрация с визуализацией"""
    print("\n" + "=" * 60)
    print("📊 РАСШИРЕННАЯ ДЕМОНСТРАЦИЯ")
    print("=" * 60)
    
    for use_http2 in [False, True]:
        protocol = "HTTP/2" if use_http2 else "HTTP/1.1"
        print(f"\n🎯 {protocol} - выполнение 20 запросов:")
        
        client_kwargs = {
            'http2': use_http2,
            'verify': False,
            'limits': httpx.Limits(max_connections=10 if not use_http2 else 10)
        }
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            start_times = []
            end_times = []
            
            async def make_request(i):
                start = time.time()
                start_times.append(start)
                res = None
                if i % 2 == 0:
                    res = await client.get("https://localhost/products")
                else:
                    res = await client.get(f"https://localhost/products/{i % 10 + 1}")
                
                end = time.time()
                end_times.append(end)
                print(f"   Запрос {i+1:2d} завершен за {(end-start):.3f}с")
                print(res)
            
            # Запускаем все запросы одновременно
            start_total = time.time()
            tasks = [make_request(i) for i in range(600)]
            await asyncio.gather(*tasks)
            total_time = time.time() - start_total
            
            # Анализируем временные характеристики
            if start_times and end_times:
                first_start = min(start_times)
                last_end = max(end_times)
                actual_duration = last_end - first_start
                
                print(f"\n   📈 Общее время: {total_time:.2f} сек")
                print(f"   ⏱️  Фактическая длительность: {actual_duration:.2f} сек")
                print(f"   💨 Эффективность: {20/actual_duration:.1f} запр/сек")

if __name__ == "__main__":
    # Простой тест
    asyncio.run(simple_http2_demo())
    
    # Расширенная демонстрация
    asyncio.run(advanced_demo())
    
    # print("\n" + "=" * 60)
    # print("💡 ВЫВОД:")
    # print("   HTTP/1.1 с 1 соединением: запросы в ОЧЕРЕДИ")
    # print("   HTTP/2 с 1 соединением: запросы ПАРАЛЛЕЛЬНО")
    # print("   Это главное преимущество HTTP/2!")
    # print("=" * 60)