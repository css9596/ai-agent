#!/bin/bash

# ========================================
# PyInstaller를 사용해 Windows exe 빌드
# ========================================
# 이 스크립트를 온라인 환경의 Windows 또는 WSL에서 실행하면
# 실행 가능한 exe 파일을 생성합니다.

set -e

echo "======================================"
echo "Windows exe 빌드 스크립트"
echo "======================================"
echo ""

# Python 버전 확인
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[오류] Python이 설치되어 있지 않습니다."
    echo "설치: https://www.python.org/downloads/"
    exit 1
fi

PYTHON=${PYTHON:-python3}
echo "✓ Python 확인: $($PYTHON --version)"
echo ""

# PyInstaller 설치 확인
echo "[1/4] PyInstaller 확인..."
if ! $PYTHON -c "import PyInstaller" 2>/dev/null; then
    echo "  → PyInstaller 설치 중..."
    $PYTHON -m pip install pyinstaller --quiet
fi
echo "✓ PyInstaller 설치 완료"
echo ""

# 현재 스크립트 디렉토리 기준
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 이전 빌드 정리
echo "[2/4] 이전 빌드 정리..."
rm -rf build/ dist/ run_app.spec 2>/dev/null || true
echo "✓ 정리 완료"
echo ""

# PyInstaller 빌드
echo "[3/4] exe 파일 생성 중..."
echo "  (2-5분 소요)"

$PYTHON -m PyInstaller \
    --onefile \
    --name "AI분석서생성" \
    --distpath "./dist" \
    --specpath "./build" \
    --workpath "./build" \
    --console \
    --icon=scripts/app_icon.ico 2>/dev/null || \
$PYTHON -m PyInstaller \
    --onefile \
    --name "AI분석서생성" \
    --distpath "./dist" \
    --specpath "./build" \
    --workpath "./build" \
    --console \
    scripts/run-app.py

echo "✓ exe 파일 생성 완료"
echo ""

# 결과 확인
echo "[4/4] 빌드 결과 확인..."
if [ -f "dist/AI분석서생성.exe" ]; then
    EXE_SIZE=$(du -h "dist/AI분석서생성.exe" | cut -f1)
    echo "✓ 빌드 성공!"
    echo ""
    echo "생성된 파일:"
    echo "  dist/AI분석서생성.exe ($EXE_SIZE)"
    echo ""
    echo "사용 방법:"
    echo "  1. dist/AI분석서생성.exe를 다른 폴더로 복사"
    echo "  2. multi-agent/ 폴더와 같은 위치에 배치"
    echo "  3. exe를 더블클릭해서 실행"
    echo ""
    echo "폴더 구조 예시:"
    echo "  C:/User/App/"
    echo "  ├── AI분석서생성.exe"
    echo "  └── multi-agent/"
    echo "      ├── docker-compose.yml"
    echo "      ├── .env.offline"
    echo "      ├── static/"
    echo "      └── ..."
else
    echo "[오류] exe 파일 생성 실패"
    exit 1
fi

echo ""
echo "======================================"
echo "✓ 빌드 완료!"
echo "======================================"
echo ""
