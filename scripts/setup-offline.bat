@echo off
setlocal enabledelayedexpansion
REM Windows 인코딩을 UTF-8로 설정
chcp 65001 > nul 2>&1

REM ========================================
REM 오프라인 배포 설정 스크립트 (Windows)
REM ========================================
REM 이 스크립트는 온라인 환경에서 1회 실행하여
REM 필요한 모든 파일을 다운로드 및 준비합니다.

setlocal
cd /d "%~dp0\.."

echo.
echo ======================================
echo 오프라인 배포 설정 (Windows)
echo ======================================
echo.

REM 1단계: Docker 확인
echo [1/6] Docker 설치 확인 중...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Docker Desktop이 설치되어 있지 않습니다.
    echo 다운로드: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✓ Docker 설치 확인 완료
echo.

REM 2단계: vendor 디렉토리 생성 및 CDN 라이브러리 다운로드
echo [2/6] CDN 라이브러리 다운로드 중...
mkdir static\vendor\fontawesome\css 2>nul
mkdir static\vendor\fontawesome\webfonts 2>nul
echo ✓ vendor 디렉토리 생성

REM Tailwind CSS
if not exist "static\vendor\tailwind.min.css" (
    echo   ^→ Tailwind CSS 다운로드 중...
    curl -fsSL "https://unpkg.com/tailwindcss@3/dist/tailwind.min.css" ^
         -o "static\vendor\tailwind.min.css"
    echo ✓ Tailwind CSS 다운로드 완료
) else (
    echo ⚠ Tailwind CSS 이미 존재, 건너뜀
)

REM Font Awesome CSS
if not exist "static\vendor\fontawesome\css\all.min.css" (
    echo   ^→ Font Awesome CSS 다운로드 중...
    curl -fsSL "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" ^
         -o "static\vendor\fontawesome\css\all.min.css"
    echo ✓ Font Awesome CSS 다운로드 완료
) else (
    echo ⚠ Font Awesome CSS 이미 존재, 건너뜀
)

REM Font Awesome 웹폰트
for %%f in (fa-solid-900 fa-regular-400 fa-brands-400) do (
    if not exist "static\vendor\fontawesome\webfonts\%%f.woff2" (
        echo   ^→ %%f.woff2 다운로드 중...
        curl -fsSL "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/webfonts/%%f.woff2" ^
             -o "static\vendor\fontawesome\webfonts\%%f.woff2"
        echo ✓ %%f.woff2 다운로드 완료
    ) else (
        echo ⚠ %%f.woff2 이미 존재, 건너뜀
    )
)

REM marked.js
if not exist "static\vendor\marked.min.js" (
    echo   ^→ marked.min.js 다운로드 중...
    curl -fsSL "https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js" ^
         -o "static\vendor\marked.min.js"
    echo ✓ marked.min.js 다운로드 완료
) else (
    echo ⚠ marked.min.js 이미 존재, 건너뜀
)

echo.

REM 3단계: pip 패키지
echo [3/6] pip 패키지 다운로드 중...
mkdir packages 2>nul
echo   ^→ 패키지 캐시 생성 중 (1-2분 소요)...
pip download -r requirements.txt ^
    --dest packages\ ^
    --quiet 2>nul
echo ✓ pip 패키지 다운로드 완료
echo.

REM 4단계: 환경 설정
echo [4/6] 환경 설정 중...
if not exist ".env" (
    copy .env.offline .env >nul 2>&1
    echo ✓ .env 파일 생성 완료
) else (
    echo ⚠ .env 이미 존재, 기존 설정 유지
)
echo.

REM 5단계: Docker 빌드
echo [5/6] Docker 이미지 빌드 중...
echo   ^→ (3-5분 소요)...
docker-compose build >nul 2>&1
if errorlevel 1 (
    echo [오류] Docker 빌드 실패
    docker-compose build
    pause
    exit /b 1
)
echo ✓ Docker 이미지 빌드 완료
echo.

REM 6단계: Ollama 모델 다운로드
echo [6/6] Ollama 모델 다운로드 중...

REM .env에서 LLM_MODEL 읽기
for /f "tokens=2 delims==" %%a in ('findstr "^LLM_MODEL=" .env') do set OLLAMA_MODEL=%%a
if "!OLLAMA_MODEL!"=="" set OLLAMA_MODEL=qwen2.5:7b

echo   ^→ 모델: !OLLAMA_MODEL! (처음 실행 시 다운로드, 5-20분 소요)
echo   ^→ Ollama 서비스 시작 중...
docker-compose run --rm ollama ollama pull !OLLAMA_MODEL! >nul 2>&1
if errorlevel 1 (
    echo ⚠ Ollama 모델 다운로드 실패 (네트워크 확인 필요)
) else (
    echo ✓ Ollama 모델 다운로드 완료
)

echo.
echo ======================================
echo ✓ 설정 완료!
echo ======================================
echo.
echo 다음 단계:
echo.
echo 1. Docker Compose 시작:
echo    docker-compose up -d
echo.
echo 2. 상태 확인:
echo    docker-compose ps
echo.
echo 3. 웹 브라우저에서 접속:
echo    http://localhost:8000
echo.
echo 4. 로그 확인:
echo    docker-compose logs -f app
echo.
echo 5. 종료:
echo    docker-compose down
echo.
echo ======================================
echo.
pause
