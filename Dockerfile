FROM python:3.11-slim

# 보안 및 권한 문제를 위해 비루트(non-root) 사용자 생성을 고려할 수 있으나, 
# Render와 같은 PaaS 환경에서는 기본 설정을 따르는 것이 안정적입니다.
# 경고를 숨기기 위해 환경변수를 설정하거나 권한을 조정합니다.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render 환경에 맞게 포트 설정
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
