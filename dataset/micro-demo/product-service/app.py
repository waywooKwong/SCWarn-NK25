from fastapi import FastAPI

app = FastAPI()


@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {"product_id": product_id, "name": f"Product{product_id}"}


@app.post("/products")
def create_product(product: dict):
    return {"msg": "Product created", "product": product}
