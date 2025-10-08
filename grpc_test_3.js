import grpc from 'k6/net/grpc';
import exec from 'k6/execution';
import { check } from 'k6';

// Загружаем прото-файл
const client = new grpc.Client();
client.load(['.'], 'catalog.proto');

export const options = {
  stages: [
    { duration: '30s', target: 100 },
    { duration: '1m', target: 100 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    grpc_req_duration: ['p(95)<300'],  // Более строгий порог для gRPC
  },
};

export default function () {
  if (exec.vu.iterationInScenario == 0) {
    client.connect('localhost:50051', {
      plaintext: true,  // Для незашифрованного соединения
    });
  }

  // Тест получения всех товаров
  const allResponse = client.invoke('CatalogService/GetAllProducts', {});
  check(allResponse, {
    'status OK (all products)': (r) => r && r.status === grpc.StatusOK,
    'has products': (r) => r.message.products.length > 0,
  });

  // Тест получения одного товара (рандомный ID)
  const randomId = Math.floor(Math.random() * 2) + 1;
  const singleResponse = client.invoke('CatalogService/GetProduct', {
    id: randomId,
  });
  check(singleResponse, {
    'status OK (single product)': (r) => r && r.status === grpc.StatusOK,
    'correct product ID': (r) => r.message.id === randomId,
  });

  // client.close();
}