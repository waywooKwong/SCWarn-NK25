FROM python:3.10-slim

WORKDIR /app

RUN pip install fastapi==0.104.1 \
    uvicorn==0.24.0 \
    aiofiles==23.2.1 \
    python-multipart==0.0.6 \
    httpx==0.25.0

# 确保目录存在
RUN mkdir -p /app/static

# 分别复制文件
COPY static/index.html /app/static/
COPY app.py k8s.yaml /app/

# 设置权限
RUN chmod -R 755 /app/static

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"] 