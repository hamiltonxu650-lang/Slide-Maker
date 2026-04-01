# Slide Maker - Windows Build Pipeline
# ----------------------------------
# 1. Runs PyInstaller to create a standard 'onedir' bundle.
# 2. Runs Inno Setup to create a professional installer (setup.exe).

$python = ".\venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "[!] Virtual environment not found at .\venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "[*] Please create it first: python -m venv venv && .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

# 1. Clean previous builds
Write-Host "[*] Cleaning previous build artifacts..." -ForegroundColor Cyan
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "Output") { Remove-Item "Output" -Recurse -Force }

# 2. Run PyInstaller
Write-Host "[*] Phase 1: Building Application Bundle with PyInstaller..." -ForegroundColor Green
& $python -m PyInstaller --clean Slide_Maker.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] PyInstaller build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Compile Installer (Inno Setup)
Write-Host "[*] Phase 2: Compiling Windows Installer (Inno Setup)..." -ForegroundColor Green

# Try to find ISCC.exe in common locations
$iscc = "iscc.exe"
$programFiles = ${env:ProgramFiles(x86)}
if (-not (Get-Command $iscc -ErrorAction SilentlyContinue)) {
    $potentialPath = Join-Path $programFiles "Inno Setup 6\ISCC.exe"
    if (Test-Path $potentialPath) {
        $iscc = $potentialPath
    } else {
        Write-Host "[!] ISCC.exe not found. Please install Inno Setup 6 or add it to your PATH." -ForegroundColor Yellow
        Write-Host "[*] Skipping installer compilation. The portable app is available in dist\Slide-Maker."
        exit 0
    }
}

& $iscc Slide_Maker_Setup.iss

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Inno Setup compilation failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[+++] BUILD COMPLETE [+++]" -ForegroundColor White -BackgroundColor DarkGreen
Write-Host "[*] Installer generated: Output\Slide-Maker-Setup.exe" -ForegroundColor Cyan
Write-Host "[*] Portable version: dist\Slide-Maker\" -ForegroundColor Cyan

