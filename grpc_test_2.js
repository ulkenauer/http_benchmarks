import grpc from 'k6/net/grpc';
import { check } from 'k6';

const client = new grpc.Client();
client.load(['.'], 'catalog.proto');

export const options = {
  vus: 100,
  duration: '1m',
};

export function setup() {
  // Соединение устанавливается один раз на VU
  client.connect('localhost:50051', {
    plaintext: true,
    timeout: '2s',
    // reuseConnection: true  // Критически важно!
  });
}

export default function () {
  const response = client.invoke('CatalogService/GetAllProducts', {});
  check(response, {
    'status is OK': (r) => r && r.status === grpc.StatusOK,
  });
}

export function teardown() {
  client.close();
}