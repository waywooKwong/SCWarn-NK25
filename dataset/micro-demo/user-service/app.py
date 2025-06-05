from fastapi import FastAPI
import asyncio
import random
import requests

app = FastAPI()

PRODUCT_SERVICE_URL = "http://product-service:8000"
CART_SERVICE_URL = "http://cart-service:8000"


# 后台任务：定期检查用户并模拟用户行为
async def periodic_check():
    while True:
        try:
            # 随机检查几个用户
            for _ in range(2):
                user_id = random.randint(1, 10)
                user = get_user(user_id)
                print(f"User service checking user {user_id}: {user}")

                # 模拟用户浏览商品
                product_id = random.randint(1, 10)
                try:
                    product_response = requests.get(
                        f"{PRODUCT_SERVICE_URL}/products/{product_id}"
                    )
                    print(
                        f"User {user_id} browsing product {product_id}: {product_response.json()}"
                    )

                    # 50%的概率将商品加入购物车
                    if random.random() < 0.5:
                        cart_data = {"user_id": user_id, "product_id": product_id}
                        cart_response = requests.post(
                            f"{CART_SERVICE_URL}/carts", json=cart_data
                        )
                        print(
                            f"User {user_id} added product {product_id} to cart: {cart_response.json()}"
                        )
                except Exception as e:
                    print(f"Error in user browsing simulation: {str(e)}")

            # 模拟创建新用户
            if random.random() < 0.3:  # 30%的概率创建新用户
                new_user = {"name": f"NewUser{random.randint(100, 999)}"}
                result = create_user(new_user)
                print(f"Created new user: {result}")
        except Exception as e:
            print(f"Error during periodic check in user service: {str(e)}")

        # 等待10秒后再次检查
        await asyncio.sleep(10)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_check())


@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User{user_id}"}


@app.post("/users")
def create_user(user: dict):
    return {"msg": "User created", "user": user}
