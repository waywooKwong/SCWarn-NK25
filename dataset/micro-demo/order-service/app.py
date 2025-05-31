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
    return {"order_id": order_id, "status": "created"}


@app.post("/orders")
def create_order(order: dict):
    user_id = order.get("user_id")
    product_id = order.get("product_id")
    user = requests.get(f"{USER_SERVICE_URL}/users/{user_id}").json()
    product = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}").json()

    # 创建订单后自动创建支付
    try:
        payment_data = {
            "order_id": random.randint(1000, 9999),  # 模拟订单ID
            "amount": random.randint(100, 1000),  # 模拟订单金额
            "user_id": user_id,
        }
        payment_response = requests.post(
            f"{PAYMENT_SERVICE_URL}/payments", json=payment_data
        )
        print(f"Created payment for order: {payment_response.json()}")
    except Exception as e:
        print(f"Error creating payment: {str(e)}")

    return {"msg": "Order created", "order": order, "user": user, "product": product}
