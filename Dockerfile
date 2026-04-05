# 오프라인 환경 지원 Dockerfile
FROM python:3.9-slim

# weasyprint 시스템 의존성 설치 (PDF 생성용)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements.txt 복사
COPY requirements.txt .

# pip install:
# 1. 온라인 모드: 인터넷에서 직접 설치
# 2. 오프라인 모드: packages/ 폴더가 있으면 로컬 wheel 사용
# packages 폴더가 없으면 자동으로 온라인 설치로 진행
RUN mkdir -p /tmp/packages/ && \
    pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 필수 디렉토리 생성
RUN mkdir -p output temp_uploads logs projects

# 포트 노출
EXPOSE 8000

# 앱 실행
CMD ["python", "app.py"]
