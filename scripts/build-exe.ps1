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

$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonPath) {
    Write-Host "ERROR: Python not found in PATH" -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK: Python found at $($pythonPath.Source)" -ForegroundColor Green
Write-Host ""

# Step 2: Install PyInstaller
Write-Host "[2/4] Installing PyInstaller..." -ForegroundColor Blue
Write-Host "  Installing from pip..." -ForegroundColor Yellow

python -m pip install pyinstaller --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install PyInstaller" -ForegroundColor Red
    Write-Host ""
    Write-Host "IMPORTANT: You may be using Windows Store Python" -ForegroundColor Red
    Write-Host "This version has limitations and cannot run properly." -ForegroundColor Red
    Write-Host ""
    Write-Host "Solution: Install official Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Then uninstall Windows Store Python from Settings > Apps" -ForegroundColor Yellow
    exit 1
}
Write-Host "OK: PyInstaller installed" -ForegroundColor Green
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

    # Copy required files and folders to dist/
    Write-Host "[5/5] Copying project files..." -ForegroundColor Blue

    # Copy root-level files
    $filesToCopy = @(
        "docker-compose.yml",
        "Dockerfile",
        ".env.offline",
        "app.py",
        "main.py",
        "config.py",
        "database.py",
        "orchestrator.py",
        "requirements.txt"
    )

    $failedFiles = @()
    foreach ($file in $filesToCopy) {
        $fullPath = Join-Path $projectDir $file
        if (Test-Path $fullPath) {
            try {
                Copy-Item -Path $fullPath -Destination ".\dist\" -Force -ErrorAction Stop
                Write-Host "  ✓ $file" -ForegroundColor Gray
            } catch {
                $failedFiles += $file
                Write-Host "  ✗ $file (failed)" -ForegroundColor Red
            }
        } else {
            $failedFiles += $file
            Write-Host "  ✗ $file (not found)" -ForegroundColor Red
        }
    }

    # Copy all yml/yaml files
    Write-Host "  Searching for yml files in: $projectDir" -ForegroundColor Gray

    $ymlFiles = @()
    $ymlFiles += Get-ChildItem -Path "$projectDir\*.yml" -File -ErrorAction SilentlyContinue
    $ymlFiles += Get-ChildItem -Path "$projectDir\*.yaml" -File -ErrorAction SilentlyContinue

    if ($ymlFiles.Count -eq 0) {
        Write-Host "  (No yml files found)" -ForegroundColor Gray
    } else {
        foreach ($ymlFile in $ymlFiles) {
            try {
                $destPath = Join-Path ".\dist" $ymlFile.Name
                Copy-Item -Path $ymlFile.FullName -Destination $destPath -Force -ErrorAction Stop
                Write-Host "  ✓ $($ymlFile.Name)" -ForegroundColor Gray
            } catch {
                $failedFiles += $ymlFile.Name
                Write-Host "  ✗ $($ymlFile.Name) (failed: $_)" -ForegroundColor Red
            }
        }
    }

    # Copy folders
    $foldersToCopy = @("scripts", "agents", "utils", "static")
    foreach ($folder in $foldersToCopy) {
        $fullPath = Join-Path $projectDir $folder
        if (Test-Path $fullPath) {
            try {
                Copy-Item -Path $fullPath -Destination ".\dist\$folder" -Recurse -Force -ErrorAction Stop
                Write-Host "  ✓ $folder/" -ForegroundColor Gray
            } catch {
                $failedFiles += $folder
                Write-Host "  ✗ $folder/ (failed)" -ForegroundColor Red
            }
        } else {
            $failedFiles += $folder
            Write-Host "  ✗ $folder/ (not found)" -ForegroundColor Red
        }
    }

    if ($failedFiles.Count -gt 0) {
        Write-Host "WARNING: Failed to copy some files: $($failedFiles -join ', ')" -ForegroundColor Yellow
    }

    Write-Host "OK: Project files copied" -ForegroundColor Green
    Write-Host ""

    Write-Host ""
    Write-Host "=================================="
    Write-Host "BUILD SUCCESS!" -ForegroundColor Green
    Write-Host "=================================="
    Write-Host ""
    Write-Host "Generated deployment package:"
    Write-Host "  dist\ folder (complete standalone application)"
    Write-Host "  ├── AIAnalyzer.exe ($exeSize MB)"
    Write-Host "  ├── docker-compose.yml"
    Write-Host "  ├── Dockerfile"
    Write-Host "  ├── .env.offline"
    Write-Host "  ├── app.py, main.py, config.py, etc."
    Write-Host "  ├── agents\"
    Write-Host "  ├── utils\"
    Write-Host "  ├── static\"
    Write-Host "  └── scripts\"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  1. Copy entire dist\ folder to target location"
    Write-Host "  2. Double-click AIAnalyzer.exe to run"
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
