from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import httpx

app = FastAPI()

# 确保静态文件目录存在
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 服务映射配置
SERVICE_MAP = {
    "users": "http://user-service:8080",
    "products": "http://product-service:8080",
    "carts": "http://cart-service:8080",
    "orders": "http://order-service:8080",
}


@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(request: Request, service: str, path: str):
    if service not in SERVICE_MAP:
        return {"error": "Service not found"}, 404

    target_url = f"{SERVICE_MAP[service]}/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=request.headers,
            content=await request.body(),
        )
        return response.json()
