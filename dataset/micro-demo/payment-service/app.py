from fastapi import FastAPI
import requests
import asyncio
import random

app = FastAPI()

ORDER_SERVICE_URL = "http://order-service:8000"
USER_SERVICE_URL = "http://user-service:8000"


# 后台任务：定期检查订单和支付状态
async def periodic_check():
    while True:
        try:
            # 随机检查一个订单
            order_id = random.randint(1, 10)
            order_response = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}")
            print(f"Payment service checking order {order_id}: {order_response.json()}")

            # 模拟支付操作
            payment_id = random.randint(1, 5)
            payment = get_payment(payment_id)
            print(f"Checking payment {payment_id}: {payment}")

            # 随机检查用户账户
            user_id = random.randint(1, 10)
            try:
                user_response = requests.get(f"{USER_SERVICE_URL}/users/{user_id}")
                print(f"Checking user account {user_id}: {user_response.json()}")
            except Exception as e:
                print(f"Error checking user account: {str(e)}")

        except Exception as e:
            print(f"Error during periodic check in payment service: {str(e)}")

        # 等待20秒后再次检查
        await asyncio.sleep(20)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_check())


@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    return {
        "payment_id": payment_id,
        "status": random.choice(["pending", "processing", "completed"]),
        "amount": random.randint(100, 1000),
    }


@app.post("/payments")
def create_payment(payment: dict):
    order_id = payment.get("order_id")
    user_id = payment.get("user_id")

    # 获取订单信息
    order = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}").json()

    # 获取用户信息
    user = requests.get(f"{USER_SERVICE_URL}/users/{user_id}").json()

    # 模拟支付处理
    payment_status = random.choice(["success", "pending", "failed"])

    return {
        "msg": f"Payment {payment_status}",
        "payment": payment,
        "order": order,
        "user": user,
        "status": payment_status,
    }
