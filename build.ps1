# Build Script for Slide Maker
# Directory mode remains the default so OCR models and Node runtime stay readable.

$python = ".\venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "Python not found in D:\maker\venv. Please create the local virtual environment first."
}

$arguments = @(
    '-y'
    '--name=Slide_Maker'
    '--add-data=pptx-project\layout_engine.js;pptx-project'
    '--add-data=pptx-project\node_modules;pptx-project\node_modules'
    '--add-data=pptx-project\package.json;pptx-project'
    '--add-data=pptx-project\package-lock.json;pptx-project'
    '--add-data=assets;assets'
    '--icon=assets\slide_maker_icon.ico'
    '--collect-all=simple_lama_inpainting'
    '--collect-submodules=rapidocr_onnxruntime'
    '--collect-data=rapidocr_onnxruntime'
    '--collect-binaries=onnxruntime'
    '--collect-submodules=onnxruntime.capi'
    '--collect-submodules=torch'
    '--collect-data=torch'
    '--collect-binaries=torch'
    '--collect-submodules=winrt'
    '--collect-binaries=winrt'
    '--collect-submodules=pymupdf'
    '--collect-binaries=pymupdf'
    '--collect-submodules=fitz'
    '--hidden-import=onnxruntime'
    '--hidden-import=onnxruntime.capi.onnxruntime_pybind11_state'
    '--hidden-import=pymupdf'
    '--hidden-import=fitz'
    '--hidden-import=wordninja'
    '--hidden-import=winrt_ocr_engine'
    '--hidden-import=winrt.windows.foundation'
    '--hidden-import=winrt.windows.foundation.collections'
    '--hidden-import=winrt.windows.media.ocr'
    '--hidden-import=winrt.windows.graphics.imaging'
    '--hidden-import=winrt.windows.storage'
    '--hidden-import=winrt.windows.storage.streams'
    '--exclude-module=altair'
    '--exclude-module=diffusers'
    '--exclude-module=gradio'
    '--exclude-module=matplotlib'
    '--exclude-module=pandas'
    '--exclude-module=paddle'
    '--exclude-module=paddleocr'
    '--exclude-module=scipy'
    '--exclude-module=tensorflow'
    '--exclude-module=torchaudio'
    '--exclude-module=timm'
    '--exclude-module=transformers'
    '--exclude-module=torchvision'
    '--exclude-module=uvicorn'
    '--exclude-module=onnxruntime.backend'
    '--exclude-module=onnxruntime.datasets'
    '--exclude-module=onnxruntime.quantization'
    '--exclude-module=onnxruntime.tools'
    '--exclude-module=onnxruntime.transformers'
    '--windowed'
)

if (Test-Path ".\runtime\node.exe") {
    $arguments += '--add-binary=runtime\node.exe;runtime'
}

foreach ($vcRuntime in @(
    'C:\Windows\System32\msvcp140.dll',
    'C:\Windows\System32\msvcp140_1.dll',
    'C:\Windows\System32\msvcp140_2.dll',
    'C:\Windows\System32\msvcp140_atomic_wait.dll'
)) {
    if (Test-Path $vcRuntime) {
        $arguments += "--add-binary=$vcRuntime;."
    }
}

$arguments += 'ui_app.py'

$allArgs = $arguments | ConvertTo-Json -Compress
$script = @"
import json
import sys
from PyInstaller.__main__ import run

sys.setrecursionlimit(sys.getrecursionlimit() * 5)
run(json.loads(r'''$allArgs'''))
"@

$script | & $python -
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$basePython = (& $python -c "import sys; print(sys.base_prefix)").Trim()
$distRoot = Join-Path (Get-Location) "dist\Slide_Maker"
$portablePythonRoot = Join-Path $distRoot "portable_python"
$portableSitePackages = Join-Path $distRoot "portable_site_packages"
$portableAppRoot = Join-Path $distRoot "portable_app"
$venvRoot = Split-Path (Split-Path $python -Parent) -Parent

foreach ($path in @($portablePythonRoot, $portableSitePackages, $portableAppRoot)) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
    }
}

New-Item -ItemType Directory -Force -Path $portablePythonRoot | Out-Null
New-Item -ItemType Directory -Force -Path $portableSitePackages | Out-Null
New-Item -ItemType Directory -Force -Path $portableAppRoot | Out-Null

foreach ($item in @('python.exe', 'pythonw.exe', 'python310.dll', 'python3.dll', 'python310.zip', 'DLLs', 'Lib')) {
    $source = Join-Path $basePython $item
    if (Test-Path $source) {
        Copy-Item $source -Destination $portablePythonRoot -Recurse -Force
    }
}

$sitePackagesSource = Join-Path $venvRoot 'Lib\site-packages'
Copy-Item $sitePackagesSource\* -Destination $portableSitePackages -Recurse -Force

foreach ($item in @(
    'ui_app.py',
    'gui_conversion_runner.py',
    'main.py',
    'extract_pdf.py',
    'image_processor.py',
    'inpainting_engine.py',
    'ocr_engine.py',
    'winrt_ocr_engine.py',
    'ppt_generator.py',
    'utils.py',
    'open_ppt_helper.py',
    'services',
    'ui',
    'assets',
    'runtime',
    'pptx-project'
)) {
    $source = Join-Path (Get-Location) $item
    if (Test-Path $source) {
        Copy-Item $source -Destination $portableAppRoot -Recurse -Force
    }
}
