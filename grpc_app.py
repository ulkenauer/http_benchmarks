import grpc
from concurrent import futures
import catalog_pb2
import catalog_pb2_grpc
import json
import os

class CatalogService(catalog_pb2_grpc.CatalogServiceServicer):
    def __init__(self):
        self.products = self.load_products()
    
    def load_products(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(dir_path, 'products.json'), 'r') as f:
            return json.load(f)
    
    def GetAllProducts(self, request, context):
        response = catalog_pb2.ProductsResponse()
        for p in self.products:
            product = response.products.add()
            product.id = p["id"]
            product.name = p["name"]
            product.price = p["price"]
            product.category = p["category"]
        return response
    
    def GetProduct(self, request, context):
        product = next((p for p in self.products if p["id"] == request.id), None)
        if product:
            return catalog_pb2.Product(
                id=product["id"],
                name=product["name"],
                price=product["price"],
                category=product["category"]
            )
        return catalog_pb2.Product()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    catalog_pb2_grpc.add_CatalogServiceServicer_to_server(CatalogService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()