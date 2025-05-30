from fastapi import FastAPI

app = FastAPI()


@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User{user_id}"}


@app.post("/users")
def create_user(user: dict):
    return {"msg": "User created", "user": user}
