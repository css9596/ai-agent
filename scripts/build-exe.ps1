# Windows exe 빌드 스크립트 (PyInstaller)
# 사용: powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1

param(
    [switch]$SkipCleanup = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=================================="
Write-Host "Windows exe Build Script"
Write-Host "=================================="
Write-Host ""

# Step 1: Python 확인
Write-Host "[1/4] Checking Python..." -ForegroundColor Blue
try {
    $pythonVersion = python --version 2>&1
    Write-Host "OK: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not installed" -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 2: PyInstaller 확인
Write-Host "[2/4] Installing PyInstaller..." -ForegroundColor Blue
try {
    python -c "import PyInstaller" 2>$null
    Write-Host "OK: PyInstaller already installed" -ForegroundColor Green
} catch {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    python -m pip install pyinstaller --quiet
    Write-Host "OK: PyInstaller installed" -ForegroundColor Green
}
Write-Host ""

# Step 3: 현재 폴더 설정
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

Write-Host "Working directory: $projectDir" -ForegroundColor Gray
Write-Host ""

# Step 4: 이전 빌드 정리
if (-not $SkipCleanup) {
    Write-Host "[3/4] Cleaning previous builds..." -ForegroundColor Blue
    Remove-Item -Path ".\build" -Recurse -ErrorAction SilentlyContinue | Out-Null
    Remove-Item -Path ".\dist" -Recurse -ErrorAction SilentlyContinue | Out-Null
    Remove-Item -Path ".\run_app.spec" -ErrorAction SilentlyContinue | Out-Null
    Write-Host "OK: Cleanup complete" -ForegroundColor Green
} else {
    Write-Host "[3/4] Skipping cleanup" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: exe 빌드
Write-Host "[4/4] Building exe file..." -ForegroundColor Blue
Write-Host "  (This may take 2-5 minutes)" -ForegroundColor Gray
Write-Host ""

# PyInstaller args 준비
$pyArgs = @(
    "--onefile",
    "--name=AI분석서생성",
    "--distpath=.\dist",
    "--specpath=.\build",
    "--workpath=.\build",
    "--console",
    ".\scripts\run-app.py"
)

# PyInstaller 실행
& python -m PyInstaller $pyArgs

Write-Host ""

# 결과 확인
$exePath = ".\dist\AI분석서생성.exe"
if (Test-Path $exePath) {
    $exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "=================================="
    Write-Host "BUILD SUCCESS!" -ForegroundColor Green
    Write-Host "=================================="
    Write-Host ""
    Write-Host "Generated file:"
    Write-Host "  dist\AI분석서생성.exe ($exeSize MB)"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  1. Copy dist\AI분석서생성.exe to deployment folder"
    Write-Host "  2. Keep multi-agent\ folder in same location"
    Write-Host "  3. Double-click exe to run"
    Write-Host ""
    Write-Host "Folder structure:"
    Write-Host "  C:\MyApp\"
    Write-Host "  ├── AI분석서생성.exe"
    Write-Host "  └── multi-agent\"
    Write-Host "      ├── docker-compose.yml"
    Write-Host "      ├── .env.offline"
    Write-Host "      └── ..."
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=================================="
    Write-Host "BUILD FAILED!" -ForegroundColor Red
    Write-Host "=================================="
    Write-Host ""
    Write-Host "ERROR: exe file not created"
    Write-Host "Check error messages above"
    Write-Host ""
    exit 1
}

# exe 테스트 여부 묻기
Write-Host ""
$response = Read-Host "Test exe now? (Y/n)"
if ($response -eq "Y" -or $response -eq "y" -or $response -eq "") {
    Write-Host ""
    Write-Host "Running exe..." -ForegroundColor Blue
    Write-Host ""
    & ".\dist\AI분석서생성.exe"
}
