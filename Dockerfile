FROM python:3.9-slim

WORKDIR /app

# weasyprint 시스템 의존성 (PDF 내보내기용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    curl \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 필수 디렉토리 생성
RUN mkdir -p output temp_uploads logs projects data

# 포트 노출
EXPOSE 8000

# 앱 실행
CMD ["python", "app.py"]
