from fastapi import FastAPI
import asyncio
import random

app = FastAPI()


# 后台任务：定期检查商品
async def periodic_check():
    while True:
        try:
            # 随机检查几个商品
            for _ in range(3):
                product_id = random.randint(1, 10)
                product = get_product(product_id)
                print(f"Product service checking product {product_id}: {product}")
        except Exception as e:
            print(f"Error during periodic check in product service: {str(e)}")

        # 等待15秒后再次检查
        await asyncio.sleep(15)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_check())


@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {"message": "This is a fixed response from product-service for get_product."}


@app.post("/products")
def create_product(product: dict):
    return {
        "message": "This is a fixed response from product-service for create_product."
    }
