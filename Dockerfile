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

# 오프라인 설치를 위해 packages/ 폴더의 wheel 파일들을 먼저 복사
COPY packages/ /tmp/packages/
COPY requirements.txt .

# pip install: 먼저 로컬 wheel로 시도, 실패 시 인터넷에서 설치
# (오프라인 환경에서는 packages/ 폴더가 필수)
RUN pip install --no-cache-dir --no-index --find-links=/tmp/packages/ -r requirements.txt \
    || pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 필수 디렉토리 생성
RUN mkdir -p output temp_uploads logs projects

# 포트 노출
EXPOSE 8000

# 앱 실행
CMD ["python", "app.py"]
