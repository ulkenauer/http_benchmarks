import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 100 },   // Плавный рост до 100 пользователей
    { duration: '1m', target: 100 },    // Стабильная нагрузка
    { duration: '30s', target: 0 },     // Плавное снижение
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% запросов должны быть быстрее 500мс
    http_req_failed: ['rate<0.01'],     // Менее 1% ошибок
  },
};

export default function () {
  // Тест получения всех товаров
  const allProductsRes = http.get('https://localhost/products');
  check(allProductsRes, {
    'status 200 (all products)': (r) => r.status === 200,
    'has products': (r) => r.json().length > 0,
  });
  
  // Тест получения одного товара (рандомный ID)
  const randomId = Math.floor(Math.random() * 2) + 1;
  const singleProductRes = http.get(`https://localhost/products/${randomId}`);
  
  const requests = [];
  for (let i = 0; i < 15; i++) {
    const randomId = Math.floor(Math.random() * 2) + 1;
    
    requests.push({
      method: 'GET',
      url: 'https://localhost/products',
    });
    requests.push({
      method: 'GET',
      url: `https://localhost/products/${randomId}`,
    });
  }

  const responses = http.batch(requests)

  // Проверка, что все запросы успешны
  responses.forEach((r, i) => {
    check(r, {
      [`request ${i} status 200`]: (r) => r.status === 200,
    });
  });
  
  check(singleProductRes, {
    'status 200 (single product)': (r) => r.status === 200,
    'correct product ID': (r) => r.json().id === randomId,
  });
}