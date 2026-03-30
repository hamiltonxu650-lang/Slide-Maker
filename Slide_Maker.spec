# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('models', 'models'), ('pptx-project\\layout_engine.js', 'pptx-project'), ('pptx-project\\node_modules', 'pptx-project\\node_modules'), ('pptx-project\\package.json', 'pptx-project'), ('pptx-project\\package-lock.json', 'pptx-project'), ('assets', 'assets')]
binaries = [('runtime\\node.exe', 'runtime'), ('C:\\Windows\\System32\\msvcp140.dll', '.'), ('C:\\Windows\\System32\\msvcp140_1.dll', '.'), ('C:\\Windows\\System32\\msvcp140_2.dll', '.'), ('C:\\Windows\\System32\\msvcp140_atomic_wait.dll', '.')]
hiddenimports = ['onnxruntime', 'onnxruntime.capi.onnxruntime_pybind11_state', 'pymupdf', 'fitz', 'wordninja', 'winrt_ocr_engine', 'winrt.windows.foundation', 'winrt.windows.foundation.collections', 'winrt.windows.media.ocr', 'winrt.windows.graphics.imaging', 'winrt.windows.storage', 'winrt.windows.storage.streams']
datas += collect_data_files('rapidocr_onnxruntime')
datas += collect_data_files('torch')
binaries += collect_dynamic_libs('onnxruntime')
binaries += collect_dynamic_libs('torch')
binaries += collect_dynamic_libs('winrt')
binaries += collect_dynamic_libs('pymupdf')
hiddenimports += collect_submodules('rapidocr_onnxruntime')
hiddenimports += collect_submodules('onnxruntime.capi')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('winrt')
hiddenimports += collect_submodules('pymupdf')
hiddenimports += collect_submodules('fitz')
tmp_ret = collect_all('simple_lama_inpainting')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['ui_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['altair', 'diffusers', 'gradio', 'matplotlib', 'pandas', 'paddle', 'paddleocr', 'scipy', 'tensorflow', 'torchaudio', 'timm', 'transformers', 'torchvision', 'uvicorn', 'onnxruntime.backend', 'onnxruntime.datasets', 'onnxruntime.quantization', 'onnxruntime.tools', 'onnxruntime.transformers'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Slide_Maker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\slide_maker_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Slide_Maker',
)
