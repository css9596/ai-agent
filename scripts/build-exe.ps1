# ========================================
# PyInstaller를 사용해 Windows exe 빌드
# ========================================
# PowerShell 실행 정책 허용:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# 실행 방법:
# powershell -ExecutionPolicy Bypass -File build-exe.ps1

param(
    [switch]$SkipCleanup = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Windows exe 빌드 스크립트" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Python 확인
Write-Host "[1/4] Python 확인..." -ForegroundColor Blue
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python 확인: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python이 설치되지 않았습니다." -ForegroundColor Red
    Write-Host "설치: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# PyInstaller 확인
Write-Host "[2/4] PyInstaller 설치..." -ForegroundColor Blue
try {
    python -c "import PyInstaller" 2>$null
    Write-Host "✓ PyInstaller 이미 설치됨" -ForegroundColor Green
} catch {
    Write-Host "  → PyInstaller 설치 중..." -ForegroundColor Yellow
    python -m pip install pyinstaller --quiet
    Write-Host "✓ PyInstaller 설치 완료" -ForegroundColor Green
}
Write-Host ""

# 현재 폴더 설정
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

Write-Host "작업 폴더: $projectDir" -ForegroundColor Gray
Write-Host ""

# 이전 빌드 정리
if (-not $SkipCleanup) {
    Write-Host "[3/4] 이전 빌드 정리..." -ForegroundColor Blue
    Remove-Item -Path ".\build" -Recurse -ErrorAction SilentlyContinue | Out-Null
    Remove-Item -Path ".\dist" -Recurse -ErrorAction SilentlyContinue | Out-Null
    Remove-Item -Path ".\run_app.spec" -ErrorAction SilentlyContinue | Out-Null
    Write-Host "✓ 정리 완료" -ForegroundColor Green
} else {
    Write-Host "[3/4] 정리 건너뜀" -ForegroundColor Yellow
}
Write-Host ""

# exe 빌드
Write-Host "[4/4] exe 파일 생성 중..." -ForegroundColor Blue
Write-Host "  (2-5분 소요)" -ForegroundColor Gray
Write-Host ""

# 아이콘 파일 확인
$iconPath = ".\scripts\app_icon.ico"
if (Test-Path $iconPath) {
    $iconArg = @("--icon=$iconPath")
} else {
    Write-Host "  경고: app_icon.ico를 찾을 수 없습니다 (생략)" -ForegroundColor Yellow
    $iconArg = @()
}

# PyInstaller 실행 (Invoke-Expression 대신 직접 배열로 전달)
$pyInstallerArgs = @(
    "--onefile",
    "--name=AI분석서생성",
    '--distpath=.\dist',
    '--specpath=.\build',
    '--workpath=.\build',
    "--console"
) + $iconArg + @(".\scripts\run-app.py")

& python -m PyInstaller $pyInstallerArgs

Write-Host ""

# 결과 확인
if (Test-Path ".\dist\AI분석서생성.exe") {
    $exeSize = (Get-Item ".\dist\AI분석서생성.exe").Length / 1MB
    Write-Host "✓ 빌드 성공!" -ForegroundColor Green
    Write-Host ""
    Write-Host "생성된 파일:" -ForegroundColor Green
    Write-Host "  dist\AI분석서생성.exe ($([Math]::Round($exeSize, 1)) MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "사용 방법:" -ForegroundColor Cyan
    Write-Host "  1. dist\AI분석서생성.exe를 원하는 폴더로 복사" -ForegroundColor Cyan
    Write-Host "  2. multi-agent\ 폴더와 같은 위치에 배치" -ForegroundColor Cyan
    Write-Host "  3. exe를 더블클릭해서 실행" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "폴더 구조 예시:" -ForegroundColor Cyan
    Write-Host "  C:\User\App" -ForegroundColor Gray
    Write-Host "  ├── AI분석서생성.exe" -ForegroundColor Gray
    Write-Host "  └── multi-agent\" -ForegroundColor Gray
    Write-Host "      ├── docker-compose.yml" -ForegroundColor Gray
    Write-Host "      ├── .env.offline" -ForegroundColor Gray
    Write-Host "      └── ..." -ForegroundColor Gray
    Write-Host ""
    Write-Host "실행:" -ForegroundColor Yellow
    Write-Host "  & '.\dist\AI분석서생성.exe'" -ForegroundColor Yellow
} else {
    Write-Host "✗ exe 파일 생성 실패" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✓ 빌드 완료!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# exe 실행할지 묻기
$response = Read-Host "지금 exe를 테스트하시겠습니까? (Y/n)"
if ($response -eq "Y" -or $response -eq "y" -or $response -eq "") {
    Write-Host ""
    & ".\dist\AI분석서생성.exe"
}
