# Slide Maker - Windows Build Pipeline
# ----------------------------------
# 1. Builds a PyInstaller desktop shell for the GUI.
# 2. Adds a portable worker runtime (portable Python + site-packages + portable app).
# 3. Optionally wraps the result into an Inno Setup installer.

$python = ".\venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "[!] Virtual environment not found at .\venv\Scripts\python.exe" -ForegroundColor Red
    Write-Host "[*] Please create it first: python -m venv venv && .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

function Fail-Build {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Red
    exit 1
}

function Remove-PathIfExists {
    param([string]$PathText)
    if (Test-Path $PathText) {
        Remove-Item $PathText -Recurse -Force
    }
}

function Copy-DirectoryContents {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (-not (Test-Path $Source)) {
        Fail-Build "Missing source directory: $Source"
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    Get-ChildItem $Source -Force | ForEach-Object {
        Copy-Item $_.FullName -Destination $Destination -Recurse -Force
    }
}

function Remove-ChildDirectoriesByName {
    param(
        [string]$Root,
        [string[]]$Names
    )

    if (-not (Test-Path $Root)) {
        return
    }

    Get-ChildItem $Root -Recurse -Directory -Force -ErrorAction SilentlyContinue |
        Where-Object { $Names -contains $_.Name } |
        Sort-Object FullName -Descending |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force }
}

function Remove-ChildFilesByPattern {
    param(
        [string]$Root,
        [string[]]$Patterns
    )

    if (-not (Test-Path $Root)) {
        return
    }

    foreach ($pattern in $Patterns) {
        Get-ChildItem $Root -Recurse -File -Force -ErrorAction SilentlyContinue -Filter $pattern |
            ForEach-Object { Remove-Item $_.FullName -Force }
    }
}

function Prepare-PortableWorkerRuntime {
    param(
        [string]$PythonExe,
        [string]$DistRoot
    )

    $basePythonRoot = (& $PythonExe -c "import sys; print(sys.base_prefix)").Trim()
    if (-not $basePythonRoot) {
        Fail-Build "Unable to detect the base Python runtime."
    }
    $sitePackagesRoot = (& $PythonExe -c "import os, sys; print(os.path.join(sys.prefix, 'Lib', 'site-packages'))").Trim()
    if (-not (Test-Path $sitePackagesRoot)) {
        Fail-Build "Unable to find virtualenv site-packages at $sitePackagesRoot"
    }

    $portablePython = Join-Path $DistRoot "portable_python"
    $portableSitePackages = Join-Path $DistRoot "portable_site_packages"
    $portableApp = Join-Path $DistRoot "portable_app"

    Write-Host "[*] Phase 1.5: Preparing portable worker runtime..." -ForegroundColor Green
    foreach ($target in @($portablePython, $portableSitePackages, $portableApp)) {
        Remove-PathIfExists $target
        New-Item -ItemType Directory -Path $target -Force | Out-Null
    }

    Write-Host "[*] Copying base Python runtime..." -ForegroundColor Cyan
    Copy-DirectoryContents $basePythonRoot $portablePython
    foreach ($trimDir in @(
        "Doc",
        "Tools",
        "Scripts",
        "tcl",
        "Lib\site-packages",
        "Lib\test",
        "Lib\tkinter",
        "Lib\idlelib",
        "Lib\turtledemo",
        "Lib\ensurepip"
    )) {
        Remove-PathIfExists (Join-Path $portablePython $trimDir)
    }
    Remove-ChildDirectoriesByName $portablePython @("__pycache__")
    Remove-ChildFilesByPattern $portablePython @("*.pyc", "*.pyo")

    Write-Host "[*] Copying portable site-packages..." -ForegroundColor Cyan
    & $PythonExe .\scripts\build_portable_site_packages.py $sitePackagesRoot $portableSitePackages
    if ($LASTEXITCODE -ne 0) {
        Fail-Build "Failed to assemble portable_site_packages."
    }

    Write-Host "[*] Copying portable worker app..." -ForegroundColor Cyan
    $portableFiles = @(
        "extract_pdf.py",
        "gui_conversion_runner.py",
        "image_processor.py",
        "inpainting_engine.py",
        "main.py",
        "ocr_engine.py",
        "open_ppt_helper.py",
        "ppt_generator.py",
        "scanner_engine.py",
        "ui_app.py",
        "utils.py",
        "winrt_ocr_engine.py"
    )
    $portableDirs = @(
        "models",
        "pptx-project",
        "runtime",
        "services"
    )

    foreach ($fileName in $portableFiles) {
        if (-not (Test-Path $fileName)) {
            Fail-Build "Missing portable worker file: $fileName"
        }
        Copy-Item $fileName -Destination $portableApp -Force
    }
    foreach ($directoryName in $portableDirs) {
        Copy-DirectoryContents $directoryName (Join-Path $portableApp $directoryName)
    }
    Remove-ChildDirectoriesByName $portableApp @("__pycache__", "test", "tests")
    Remove-ChildFilesByPattern $portableApp @("*.pyc", "*.pyo")
}

$lamaModel = "models\big-lama.pt"
$nodeRuntime = "runtime\node.exe"
$pptxProjectDir = "pptx-project"
$pptxRuntimeModule = Join-Path $pptxProjectDir "node_modules\pptxgenjs"

if (-not (Test-Path $lamaModel)) {
    Fail-Build "Required LaMa model not found at $lamaModel"
}

$firstModelLine = Get-Content $lamaModel -TotalCount 1 -ErrorAction SilentlyContinue
if ($firstModelLine -like "version https://git-lfs.github.com/spec/v1*") {
    Fail-Build "models\\big-lama.pt is a Git LFS pointer, not the real model file."
}

if (-not (Test-Path $nodeRuntime)) {
    Fail-Build "Bundled Node runtime not found at $nodeRuntime"
}

if (-not (Test-Path $pptxRuntimeModule)) {
    Fail-Build "Missing PPTX runtime dependencies. Run npm install inside pptx-project first."
}

# Remove generated intermediates that are useful for testing but not for the packaged app.
Write-Host "[*] Cleaning generated layout-engine artifacts..." -ForegroundColor Cyan
Get-ChildItem $pptxProjectDir -Filter "clean_bg_*.png" -File -ErrorAction SilentlyContinue | Remove-Item -Force
Remove-Item (Join-Path $pptxProjectDir "ocr_data.json") -Force -ErrorAction SilentlyContinue
Get-ChildItem $pptxProjectDir -Filter "test_face_*.png" -File -ErrorAction SilentlyContinue | Remove-Item -Force

# Keep only production Node dependencies in the packaged runtime.
Write-Host "[*] Pruning PPTX runtime dependencies..." -ForegroundColor Cyan
Push-Location $pptxProjectDir
try {
    & npm.cmd prune --omit=dev
    if ($LASTEXITCODE -ne 0) {
        Fail-Build "npm prune failed for pptx-project."
    }
}
finally {
    Pop-Location
}

$nodeRuntimeTrimTargets = @(
    (Join-Path $pptxProjectDir "node_modules\.bin"),
    (Join-Path $pptxProjectDir "node_modules\@types"),
    (Join-Path $pptxProjectDir "node_modules\undici-types"),
    (Join-Path $pptxProjectDir "node_modules\.package-lock.json")
)
foreach ($trimTarget in $nodeRuntimeTrimTargets) {
    if (Test-Path $trimTarget) {
        Remove-Item $trimTarget -Recurse -Force
    }
}
$emptyScopedDir = Join-Path $pptxProjectDir "node_modules\@img"
if ((Test-Path $emptyScopedDir) -and -not (Get-ChildItem $emptyScopedDir -Force -ErrorAction SilentlyContinue)) {
    Remove-Item $emptyScopedDir -Force
}

# 1. Clean previous builds
Write-Host "[*] Cleaning previous build artifacts..." -ForegroundColor Cyan
Remove-PathIfExists "dist"
Remove-PathIfExists "build"
Remove-PathIfExists "Output"

# 2. Run PyInstaller for the desktop shell
Write-Host "[*] Phase 1: Building desktop shell with PyInstaller..." -ForegroundColor Green
& $python -m PyInstaller --clean Slide_Maker.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] PyInstaller build failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

$distRoot = Join-Path (Get-Location) "dist\Slide-Maker"
Prepare-PortableWorkerRuntime -PythonExe $python -DistRoot $distRoot

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
Write-Host "[*] Installer generated: Output\Slide-Maker-Setup-v0.3.0.exe" -ForegroundColor Cyan
Write-Host "[*] Portable version: dist\Slide-Maker\" -ForegroundColor Cyan

