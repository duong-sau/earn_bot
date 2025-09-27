# Base image
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    TZ=Asia/Ho_Chi_Minh

# Cài đặt gói hệ thống tối thiểu (tzdata, build deps nhẹ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements trước để cache
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY . .

# Tạo thư mục logs (sẽ mount ra ngoài ở compose)
RUN mkdir -p logs _settings

# Entrypoint dùng chung: set SERVICE env để chọn microservice
ENTRYPOINT ["python", "run_microservice.py"]

