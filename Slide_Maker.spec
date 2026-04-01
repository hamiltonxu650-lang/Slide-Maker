# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules, collect_all

# Slide Maker Deployment Spec
# Target: Windows (PyInstaller onedir)

block_cipher = None

# 1. Prepare Data and Binaries
datas = [
    ('pptx-project/layout_engine.js', 'pptx-project'),
    ('pptx-project/node_modules', 'pptx-project/node_modules'),
    ('pptx-project/package.json', 'pptx-project'),
    ('pptx-project/package-lock.json', 'pptx-project'),
    ('assets', 'assets')
]

binaries = []

# Include Node runtime if present locally
if os.path.exists('runtime/node.exe'):
    binaries.append(('runtime/node.exe', 'runtime'))

# Optional: Bundle VC Runtime DLLs if found in common System32 locations 
# (This helps on barebones Windows systems that lack redistributables)
vc_dlls = ['msvcp140.dll', 'msvcp140_1.dll', 'msvcp140_2.dll', 'msvcp140_atomic_wait.dll']
sys32 = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
for dll in vc_dlls:
    dll_path = os.path.join(sys32, dll)
    if os.path.exists(dll_path):
        binaries.append((dll_path, '.'))

# 2. Collect dependencies from packages
# RapidOCR & ONNX
datas += collect_data_files('rapidocr_onnxruntime')
binaries += collect_dynamic_libs('onnxruntime')

# PyMuPDF
datas += collect_data_files('pymupdf')
binaries += collect_dynamic_libs('pymupdf')

# Torch (heavy)
datas += collect_data_files('torch')
binaries += collect_dynamic_libs('torch')

# WinRT & Others
hiddenimports = [
    'onnxruntime', 'onnxruntime.capi.onnxruntime_pybind11_state',
    'fitz', 'pymupdf', 'wordninja', 'winrt_ocr_engine',
    'winrt.windows.foundation', 'winrt.windows.foundation.collections',
    'winrt.windows.media.ocr', 'winrt.windows.graphics.imaging',
    'winrt.windows.storage', 'winrt.windows.storage.streams'
]
hiddenimports += collect_submodules('rapidocr_onnxruntime')
hiddenimports += collect_submodules('onnxruntime.capi')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('winrt')
hiddenimports += collect_submodules('fitz')

# Simple-Lama
tmp_ret = collect_all('simple_lama_inpainting')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 3. Analysis
a = Analysis(
    ['ui_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'altair', 'diffusers', 'gradio', 'matplotlib', 'pandas', 'paddle',
        'paddleocr', 'scipy', 'tensorflow', 'torchaudio', 'timm', 'transformers',
        'torchvision', 'uvicorn', 'onnxruntime.backend', 'onnxruntime.datasets',
        'onnxruntime.quantization', 'onnxruntime.tools', 'onnxruntime.transformers'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SlideMaker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Set to False for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/slide_maker_icon.ico'] if os.path.exists('assets/slide_maker_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Slide-Maker',
)
