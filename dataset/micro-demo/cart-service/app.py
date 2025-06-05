from fastapi import FastAPI
import requests
import asyncio
import random

app = FastAPI()

PRODUCT_SERVICE_URL = "http://product-service:8000"
ORDER_SERVICE_URL = "http://order-service:8000"


# 后台任务：定期检查商品服务和模拟购物车操作
async def periodic_check():
    while True:
        try:
            # 随机检查一个商品
            product_id = random.randint(1, 10)
            product_response = requests.get(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}"
            )
            print(
                f"Cart service checking product {product_id}: {product_response.json()}"
            )

            # 模拟购物车操作
            cart_id = random.randint(1, 5)
            cart = get_cart(cart_id)
            print(f"Checking cart {cart_id}: {cart}")

            # 40%的概率从购物车创建订单
            if random.random() < 0.4:
                user_id = random.randint(1, 10)
                order_data = {
                    "user_id": user_id,
                    "product_id": product_id,
                    "cart_id": cart_id,
                }
                try:
                    order_response = requests.post(
                        f"{ORDER_SERVICE_URL}/orders", json=order_data
                    )
                    print(f"Created order from cart {cart_id}: {order_response.json()}")
                except Exception as e:
                    print(f"Error creating order: {str(e)}")

        except Exception as e:
            print(f"Error during periodic check in cart service: {str(e)}")

        # 等待25秒后再次检查
        await asyncio.sleep(25)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_check())


@app.get("/carts/{cart_id}")
def get_cart(cart_id: int):
    return {"cart_id": cart_id, "items": []}


@app.post("/carts")
def create_cart(cart: dict):
    product_id = cart.get("product_id")
    user_id = cart.get("user_id")
    product = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}").json()
    return {"msg": "Cart created", "cart": cart, "product": product, "user_id": user_id}
