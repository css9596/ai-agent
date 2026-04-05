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
if [ -f "dist/AI분석서생성" ] || [ -f "dist/AI분석서생성.exe" ]; then
    EXE_FILE=$(ls dist/AI분석서생성* 2>/dev/null | head -1)
    EXE_SIZE=$(du -h "$EXE_FILE" | cut -f1)
    echo "✓ exe 파일 생성 완료"
    echo ""

    # 필요한 파일 복사
    echo "[5/5] 프로젝트 파일 복사 중..."

    FILES_TO_COPY=(
        "docker-compose.yml"
        "Dockerfile"
        ".env.offline"
        "app.py"
        "main.py"
        "config.py"
        "database.py"
        "orchestrator.py"
        "requirements.txt"
    )

    FAILED_FILES=()
    for file in "${FILES_TO_COPY[@]}"; do
        if [ -f "$file" ]; then
            if cp "$file" dist/ 2>/dev/null; then
                echo "  ✓ $file"
            else
                FAILED_FILES+=("$file")
                echo "  ✗ $file (복사 실패)"
            fi
        else
            FAILED_FILES+=("$file")
            echo "  ✗ $file (파일 없음)"
        fi
    done

    # Copy all yml/yaml files
    for ymlFile in *.yml *.yaml; do
        if [ -f "$ymlFile" ]; then
            if cp "$ymlFile" dist/ 2>/dev/null; then
                echo "  ✓ $ymlFile"
            else
                FAILED_FILES+=("$ymlFile")
                echo "  ✗ $ymlFile (복사 실패)"
            fi
        fi
    done

    FOLDERS_TO_COPY=("scripts" "agents" "utils" "static")
    for folder in "${FOLDERS_TO_COPY[@]}"; do
        if [ -d "$folder" ]; then
            if cp -r "$folder" dist/ 2>/dev/null; then
                echo "  ✓ $folder/"
            else
                FAILED_FILES+=("$folder")
                echo "  ✗ $folder/ (복사 실패)"
            fi
        else
            FAILED_FILES+=("$folder")
            echo "  ✗ $folder/ (폴더 없음)"
        fi
    done

    if [ ${#FAILED_FILES[@]} -gt 0 ]; then
        echo "⚠ 경고: 일부 파일 복사 실패 - ${FAILED_FILES[*]}" >&2
    fi

    echo "✓ 파일 복사 완료"
    echo ""

    echo "✓ 빌드 성공!"
    echo ""
    echo "생성된 배포 패키지:"
    echo "  dist/ 폴더 (완전한 독립 실행형 애플리케이션)"
    echo "  ├── AI분석서생성 ($EXE_SIZE)"
    echo "  ├── docker-compose.yml"
    echo "  ├── Dockerfile"
    echo "  ├── .env.offline"
    echo "  ├── app.py, main.py, config.py, etc."
    echo "  ├── agents/"
    echo "  ├── utils/"
    echo "  ├── static/"
    echo "  └── scripts/"
    echo ""
    echo "사용 방법:"
    echo "  1. 전체 dist/ 폴더를 다른 위치로 복사"
    echo "  2. AI분석서생성을 더블클릭해서 실행"
    echo ""
else
    echo "[오류] exe 파일 생성 실패"
    exit 1
fi

echo ""
echo "======================================"
echo "✓ 빌드 완료!"
echo "======================================"
echo ""
