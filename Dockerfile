# 간단한 Python 기반 Dockerfile
FROM python:3.9-slim

WORKDIR /app

# requirements.txt 복사
COPY requirements.txt .

# Python 패키지 설치 (pip로 모든 의존성 처리)
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# 필수 디렉토리 생성
RUN mkdir -p output temp_uploads logs projects data

# 포트 노출
EXPOSE 8000

# 앱 실행
CMD ["python", "app.py"]
