from fastapi import FastAPI
import requests
import asyncio
from fastapi.background import BackgroundTasks
import random

app = FastAPI()

USER_SERVICE_URL = "http://user-service:8000"
PRODUCT_SERVICE_URL = "http://product-service:8000"
PAYMENT_SERVICE_URL = "http://payment-service:8000"


# 后台任务：定期检查用户和商品服务
async def periodic_check():
    while True:
        try:
            # 随机检查一个用户
            user_id = random.randint(1, 10)
            user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
            print(f"Checking user {user_id}: {user_response.json()}")

            # 随机检查一个商品
            product_id = random.randint(1, 10)
            product_response = requests.get(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}"
            )
            print(f"Checking product {product_id}: {product_response.json()}")

            # 随机检查一个订单
            order_id = random.randint(1, 10)
            order = get_order(order_id)
            print(f"Checking order {order_id}: {order}")

        except Exception as e:
            print(f"Error during periodic check in order service: {str(e)}")

        # 等待30秒后再次检查
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_check())


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    return {"message": "This is a fixed response from order-service for get_order."}


@app.post("/orders")
def create_order(order: dict):
    return {"message": "This is a fixed response from order-service for create_order."}
