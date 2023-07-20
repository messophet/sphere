# Dockerfile
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt