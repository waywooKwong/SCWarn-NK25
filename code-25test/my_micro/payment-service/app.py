from fastapi import FastAPI
import requests

app = FastAPI()

ORDER_SERVICE_URL = "http://order-service:8000"


@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    return {"payment_id": payment_id, "status": "paid"}


@app.post("/payments")
def create_payment(payment: dict):
    order_id = payment.get("order_id")
    order = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}").json()
    return {"msg": "Payment processed", "payment": payment, "order": order}
