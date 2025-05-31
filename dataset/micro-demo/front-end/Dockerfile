FROM python:3.10-slim

WORKDIR /app

RUN pip install fastapi==0.104.1 \
    uvicorn==0.24.0 \
    aiofiles==23.2.1 \
    python-multipart==0.0.6

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"] 