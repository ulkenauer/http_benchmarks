import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import json
import os

app = FastAPI()

# Загрузка данных
def load_products():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'products.json'), 'r') as f:
        return json.load(f)

products = load_products()

# Эндпоинты
@app.get("/products", response_class=JSONResponse)
async def get_products():
    await asyncio.sleep(0.3)
    return products

@app.get("/products/{product_id}", response_class=JSONResponse)
async def get_product(product_id: int):
    await asyncio.sleep(0.2)
    return next((p for p in products if p["id"] == product_id), None)

if __name__ == "__main__":
    import uvicorn
    # Для HTTP/1.1
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    
    # Для HTTP/2 (нужен сертификат)
    # uvicorn.run(app, host="0.0.0.0", port=8001, ssl_keyfile="./key.pem", ssl_certfile="./cert.pem", http2=True)