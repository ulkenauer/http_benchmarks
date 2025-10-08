import subprocess
import asyncio
import time

def check_port():
    """Проверяет, занят ли порт"""
    try:
        result = subprocess.run(['lsof', '-i', ':4433'], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

async def test_http3_request():
    """Тестирует HTTP/3 запрос"""
    try:
        from test_client import Http3Client
        client = Http3Client()
        return await client.test_connection()
    except Exception as e:
        print(f"Ошибка при тестировании запроса: {e}")
        return False

async def main():
    print("🔍 Проверка работоспособности HTTP/3 сервера...")
    
    # Проверка порта
    if check_port():
        print("✅ Порт 4433 занят (сервер запущен)")
    else:
        print("❌ Порт 4433 свободен (сервер не запущен)")
        return
    
    # Проверка HTTP/3 запроса
    print("\n🔄 Тестирование HTTP/3 запроса...")
    start_time = time.time()
    success = await test_http3_request()
    elapsed = time.time() - start_time
    
    if success:
        print(f"✅ HTTP/3 запрос выполнен за {elapsed:.2f} секунд")
    else:
        print("❌ HTTP/3 запрос не удался")

if __name__ == "__main__":
    asyncio.run(main())