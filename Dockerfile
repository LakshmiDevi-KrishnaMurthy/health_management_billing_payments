# Dockerfile for Python-based Microservices
FROM python:3.9-slim
# Install curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# Install ping utility
RUN apt-get update && apt-get install -y iputils-ping
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "billing_app.py"]
