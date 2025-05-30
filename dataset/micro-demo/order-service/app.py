from fastapi import FastAPI
import requests

app = FastAPI()

USER_SERVICE_URL = "http://user-service:8000"
PRODUCT_SERVICE_URL = "http://product-service:8000"


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    return {"order_id": order_id, "status": "created"}


@app.post("/orders")
def create_order(order: dict):
    user_id = order.get("user_id")
    product_id = order.get("product_id")
    user = requests.get(f"{USER_SERVICE_URL}/users/{user_id}").json()
    product = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}").json()
    return {"msg": "Order created", "order": order, "user": user, "product": product}
