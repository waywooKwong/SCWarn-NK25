from fastapi import FastAPI
import requests

app = FastAPI()

PRODUCT_SERVICE_URL = "http://product-service:8000"


@app.get("/carts/{cart_id}")
def get_cart(cart_id: int):
    return {"cart_id": cart_id, "items": []}


@app.post("/carts")
def create_cart(cart: dict):
    product_id = cart.get("product_id")
    product = requests.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}").json()
    return {"msg": "Cart created", "cart": cart, "product": product}
