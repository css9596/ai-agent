# Windows exe build script using PyInstaller
# Usage: powershell -ExecutionPolicy Bypass -File scripts\build-exe.ps1

param(
    [switch]$SkipCleanup = $false
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=================================="
Write-Host "Windows exe Build Script"
Write-Host "=================================="
Write-Host ""

# Step 1: Check Python
Write-Host "[1/4] Checking Python..." -ForegroundColor Blue

$pythonCheck = & python --version 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not installed" -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

if ($pythonCheck) {
    Write-Host "OK: $pythonCheck" -ForegroundColor Green
} else {
    Write-Host "ERROR: Python version not detected" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Check PyInstaller
Write-Host "[2/4] Installing PyInstaller..." -ForegroundColor Blue

$pyinstCheck = & python -c "import PyInstaller" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: PyInstaller already installed" -ForegroundColor Green
} else {
    Write-Host "  Installing PyInstaller..." -ForegroundColor Yellow
    & python -m pip install pyinstaller --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: PyInstaller installed" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 3: Set working directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

Write-Host "Working directory: $projectDir" -ForegroundColor Gray
Write-Host ""

# Step 4: Clean previous builds
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

# Step 5: Build exe
Write-Host "[4/4] Building exe..." -ForegroundColor Blue
Write-Host "  (This may take 2-5 minutes)" -ForegroundColor Gray
Write-Host ""

# Prepare PyInstaller arguments
$pyArgs = @(
    "--onefile",
    "--name=AIAnalyzer",
    "--distpath=.\dist",
    "--specpath=.\build",
    "--workpath=.\build",
    "--console",
    ".\scripts\run-app.py"
)

# Run PyInstaller
& python -m PyInstaller $pyArgs

Write-Host ""

# Check result
$exePath = ".\dist\AIAnalyzer.exe"
if (Test-Path $exePath) {
    $exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "=================================="
    Write-Host "BUILD SUCCESS!" -ForegroundColor Green
    Write-Host "=================================="
    Write-Host ""
    Write-Host "Generated file:"
    Write-Host "  dist\AIAnalyzer.exe ($exeSize MB)"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  1. Copy dist\AIAnalyzer.exe to deployment folder"
    Write-Host "  2. Keep all project files in same location"
    Write-Host "  3. Double-click exe to run"
    Write-Host ""
    Write-Host "Required folder structure:"
    Write-Host "  C:\MyApp\"
    Write-Host "  ├── AIAnalyzer.exe"
    Write-Host "  ├── docker-compose.yml"
    Write-Host "  ├── .env.offline"
    Write-Host "  ├── Dockerfile"
    Write-Host "  ├── requirements.txt"
    Write-Host "  ├── app.py"
    Write-Host "  ├── main.py"
    Write-Host "  ├── config.py"
    Write-Host "  ├── database.py"
    Write-Host "  ├── orchestrator.py"
    Write-Host "  ├── scripts\"
    Write-Host "  ├── agents\"
    Write-Host "  ├── utils\"
    Write-Host "  └── static\"
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

# Ask to test exe
Write-Host ""
$response = Read-Host "Test exe now? (Y/n)"
if ($response -eq "Y" -or $response -eq "y" -or $response -eq "") {
    Write-Host ""
    Write-Host "Running exe..." -ForegroundColor Blue
    Write-Host ""
    & ".\dist\AIAnalyzer.exe"
}
