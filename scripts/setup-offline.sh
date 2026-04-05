#!/bin/bash

# ========================================
# 오프라인 배포 설정 스크립트 (macOS/Linux)
# ========================================
# 이 스크립트는 온라인 환경에서 1회 실행하여
# 필요한 모든 파일을 다운로드 및 준비합니다.

set -e

echo "======================================"
echo "오프라인 배포 설정 (macOS/Linux)"
echo "======================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 필수 도구 확인 함수
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}[오류] $1 이(가) 설치되어 있지 않습니다.${NC}"
        echo "설치 방법: brew install $1"
        exit 1
    fi
}

# 진행 상황 출력 함수
progress_step() {
    echo -e "${BLUE}[$(printf '%d/%d' "$1" "$2")] $3${NC}"
}

# 완료 메시지 함수
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 경고 메시지 함수
warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 1단계: 필수 도구 확인
progress_step 1 6 "필수 도구 확인..."
check_command docker
check_command curl
success "Docker 및 curl 설치 확인"
echo ""

# 2단계: vendor 디렉토리 생성 및 CDN 라이브러리 다운로드
progress_step 2 6 "CDN 라이브러리 다운로드..."
mkdir -p static/vendor/fontawesome/css
mkdir -p static/vendor/fontawesome/webfonts
success "vendor 디렉토리 생성"

# Tailwind CSS 다운로드
if [ ! -f "static/vendor/tailwind.min.css" ]; then
    echo "  → Tailwind CSS 다운로드 중..."
    curl -fsSL "https://unpkg.com/tailwindcss@3/dist/tailwind.min.css" \
         -o "static/vendor/tailwind.min.css"
    success "Tailwind CSS 다운로드 완료"
else
    warn "Tailwind CSS 이미 존재, 건너뜀"
fi

# Font Awesome CSS 다운로드
if [ ! -f "static/vendor/fontawesome/css/all.min.css" ]; then
    echo "  → Font Awesome CSS 다운로드 중..."
    curl -fsSL "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" \
         -o "static/vendor/fontawesome/css/all.min.css"
    success "Font Awesome CSS 다운로드 완료"
else
    warn "Font Awesome CSS 이미 존재, 건너뜀"
fi

# Font Awesome 웹폰트 다운로드
for font in fa-solid-900 fa-regular-400 fa-brands-400; do
    if [ ! -f "static/vendor/fontawesome/webfonts/${font}.woff2" ]; then
        echo "  → ${font}.woff2 다운로드 중..."
        curl -fsSL "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/${font}.woff2" \
             -o "static/vendor/fontawesome/webfonts/${font}.woff2"
        success "${font}.woff2 다운로드 완료"
    else
        warn "${font}.woff2 이미 존재, 건너뜀"
    fi
done

# marked.js 다운로드
if [ ! -f "static/vendor/marked.min.js" ]; then
    echo "  → marked.min.js 다운로드 중..."
    curl -fsSL "https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js" \
         -o "static/vendor/marked.min.js"
    success "marked.min.js 다운로드 완료"
else
    warn "marked.min.js 이미 존재, 건너뜀"
fi

echo ""

# 3단계: pip 패키지 다운로드
progress_step 3 6 "pip 패키지 다운로드..."
mkdir -p packages

echo "  → 패키지 캐시 생성 중 (1-2분 소요)..."
pip download -r requirements.txt \
    --dest packages/ \
    --quiet 2>&1 | tail -5

success "pip 패키지 다운로드 완료 ($(ls packages/*.whl 2>/dev/null | wc -l)개 파일)"
echo ""

# 4단계: 환경 설정 파일
progress_step 4 6 "환경 설정..."

if [ ! -f ".env" ]; then
    cp .env.offline .env
    success ".env 파일 생성 완료"
else
    warn ".env 이미 존재, 기존 설정 유지"
fi

echo ""

# 5단계: Docker 이미지 빌드
progress_step 5 6 "Docker 이미지 빌드..."
echo "  → (3-5분 소요)..."

if docker-compose build > /tmp/docker-build.log 2>&1; then
    success "Docker 이미지 빌드 완료"
else
    echo -e "${RED}[오류] Docker 빌드 실패${NC}"
    cat /tmp/docker-build.log
    exit 1
fi

echo ""

# 6단계: Ollama 모델 다운로드
progress_step 6 6 "Ollama 모델 다운로드..."

# .env에서 LLM_MODEL 읽기
if [ -f ".env" ]; then
    OLLAMA_MODEL=$(grep "^LLM_MODEL=" .env | cut -d'=' -f2 | tr -d ' ')
else
    OLLAMA_MODEL="qwen2.5:7b"
fi

echo "  → 모델: ${OLLAMA_MODEL} (처음 실행 시 다운로드, 5-20분 소요)"
echo "  → Ollama 서비스 시작 중..."

if docker-compose run --rm ollama ollama pull "${OLLAMA_MODEL}" > /tmp/ollama-pull.log 2>&1; then
    success "Ollama 모델 다운로드 완료"
else
    warn "Ollama 모델 다운로드 실패 (네트워크 확인 필요)"
fi

echo ""
echo "======================================"
echo -e "${GREEN}✓ 설정 완료!${NC}"
echo "======================================"
echo ""
echo "다음 단계:"
echo ""
echo "1. Docker Compose 시작:"
echo "   docker-compose up -d"
echo ""
echo "2. 상태 확인:"
echo "   docker-compose ps"
echo ""
echo "3. 웹 브라우저에서 접속:"
echo "   http://localhost:8000"
echo ""
echo "4. 로그 확인:"
echo "   docker-compose logs -f app"
echo ""
echo "5. 종료:"
echo "   docker-compose down"
echo ""
echo "======================================"
echo ""
