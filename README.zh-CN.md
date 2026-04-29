# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker 是一个本地优先的桌面工具，用来把 PDF、截图、扫描页和拍照得到的幻灯片，转换成可编辑的 PowerPoint 文件。

## v0.4.0 本次刷新

这次更新继续沿用 `v0.4.0`，不新开版本号，而是把 Mac 和 Windows 两端近期修复都合回同一个版本线。

### 桌面 UI

- Mac 桌面版已经做出来，并作为当前桌面端视觉基准。
- Windows 桌面端同步 Mac 重做后的前端，同时保留 Windows 自己的标题栏、字体回退和文件选择逻辑。
- 左上角标题栏和侧栏图标已改用高清图标，解决发糊问题。
- 主转换按钮现在是状态按钮：
- 转换前显示“开始转换”。
- 任务运行时显示蓝色“暂停”，左侧是暂停图标。
- 点击暂停后，按钮会立刻变成灰色“继续”，左侧变成三角播放图标。
- 点击继续后，按钮会立刻回到蓝色“暂停”。
- 转换过程中，“取消转换”会直接显示在暂停/继续按钮下方。

### 转换流程

- 暂停、继续和取消已经接入 worker 控制通道。
- 取消转换会返回 `转换已取消。`，不会伪装成成功结果。
- Mac GUI 启动时会额外查找 App 内资源、`~/.local/bin`、Homebrew 和 NVM 中的 Node，减少误切兼容模式。
- 打包版会优先使用内置运行时。

### PDF 和图片质量

- PDF 转换会把真实页面 DPI 传给 Node 高保真排版引擎。
- 有文字层的 PDF 会优先读取 PDF 原生文字坐标和内容，只有扫描件才回退 OCR。
- 修复了高保真输出中文字框过大、文字跑出页面、OCR 拆词和 PDF 文字乱码的问题。
- PDF DPI 选项统一为 `100 / 150 / 200 / 300 DPI`。
- 用户选择的 DPI 不会被偷偷降低。
- 超大页面会在兼容性预检阶段被拒绝，不会自动降采样，也不会继续吃满内存。
- 背景修复现在强制使用 LaMa，不再悄悄回退到 OpenCV。
- PNG / 图片转换已经在接近 GUI 的受限环境里复测，仍然可以走 Node 高保真输出。

## 下载方式

Windows 和 Mac 是两个独立下载。

### Windows

Windows 用户请使用 Windows 便携包：

1. 下载 Windows ZIP。
2. 解压到任意目录。
3. 运行 `SlideMaker.exe`。

Windows 包包含前台 PyInstaller GUI 外壳，以及真正执行转换的便携 worker。worker 里包含便携 Python、OCR 依赖、Node、PPTX 排版引擎和 LaMa 模型。

重要打包说明：

- 完整更新 Windows 前台 GUI 外壳时，必须在 Windows 或 Windows 虚拟机里运行 `build.ps1` 重新生成 `SlideMaker.exe`。
- macOS 可以刷新 Windows ZIP 里的 `portable_app` worker 和源码文件，但不能原生重编 Windows `.exe`。
- 如果要发布正式 Windows 安装包或便携包，请在 Windows 环境中重新跑完整打包流程。

### Mac

Mac 用户请使用 Mac `.app` 包：

1. 下载 Mac app ZIP。
2. 解压。
3. 打开 `slides maker.app`。

Mac app 内置本地 Python 环境、LaMa 模型、Node 运行时和最新桌面前端。

## 系统要求

### Windows

- Windows 10 或 Windows 11，64 位
- Intel / AMD x64 处理器
- 正常使用建议 16 GB 内存
- 大型 PDF 建议 32 GB 内存
- 至少 4 GB 可用磁盘空间
- 不需要独立显卡
- 打包版不需要额外安装 Python 或 Node.js

### macOS

- 打包版支持 macOS 10.13 或更新版本
- 支持当前内置 Python 运行时覆盖的 Apple Silicon / Intel Mac
- 建议 16 GB 内存
- 至少 4 GB 可用磁盘空间

### 源码运行环境

- Python 3.9 或更高版本
- Node.js，用于高保真 PPTX 排版
- 在 `pptx-project` 中运行过 `npm install`
- 已准备 `big-lama.pt`
- 桌面 UI 需要 PyQt6

## 从源码启动

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python ui_app.py
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
python ui_app.py
```

## 其他入口

### 终端 UI

```bash
python terminal_ui.py
```

终端 UI 适合做首次配置检查、模型检查和引导式转换。

### CLI

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py ./slides --output Result_Presentation.pptx
python run_pipeline.py input.jpg --scan --output Result_Presentation.pptx
```

如果不想在完成后提示打开结果文件，可以加 `--no-open`。

### Web 应用

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
cd pptx-project && npm install && cd ..
uvicorn web_app:app --host 0.0.0.0 --port 7860
```

启动后访问 `http://127.0.0.1:7860`。

## 模型配置

### LaMa 背景修复

背景修复必须依赖 LaMa。

期望文件名：

- `big-lama.pt`

支持位置：

- `%LOCALAPPDATA%\SlideMaker\models\lama\big-lama.pt`，适合 Windows 打包版
- `.slide_maker_data/models/lama/big-lama.pt`，适合源码运行
- `SLIDE_MAKER_LAMA_MODEL`
- `LAMA_MODEL`

如果 LaMa 缺失，Slide Maker 会停止转换并提示你先配置模型。

官方上游模型：

- [big-lama.pt](https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt)

### OCR 模型

默认使用 RapidOCR。可选 OCR 模型目录：

- `.slide_maker_data/models/rapidocr/onnxruntime/`

辅助脚本：

```bash
python scripts/download_ocr_models.py
```

## 打包说明

### Windows 打包

请在 Windows 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Windows 打包依赖：

- `Slide_Maker.spec`
- `build.ps1`
- `Slide_Maker_Setup.iss`

当前 Windows 包采用拆分结构：

- `SlideMaker.exe` 是用户看到的 PyInstaller 桌面外壳。
- `portable_python`、`portable_site_packages` 和 `portable_app` 负责运行较重的转换 worker。

这样比把 `torch`、`onnxruntime`、LaMa 和 OCR 全部冻结进同一个 worker 更稳定。

### Mac 打包

Mac 版本是 `.app` 包，启动内置 backend 中的同一套桌面入口。本机当前 Mac app 已经从最新源码刷新，并验证过暂停/继续按钮状态。

## 验证摘要

- 桌面暂停 / 继续 / 取消按钮状态已通过 PyQt UI 验证。
- worker 暂停 / 继续 / 取消控制通道已验证。
- PNG / 图片转换已在受限 GUI 风格 `PATH` 下复测。
- PDF 转换已复测原生文字提取、真实 DPI 排版和 Node 高保真输出。
- `test/Istanbul.pdf` 第 1 页在 200 DPI 下生成了正确 `13.33 x 7.5 in` 的 PPTX。
- 300 DPI 超大 PDF 输入现在会在预检阶段拒绝，不会继续占满内存。
- Windows 便携包结构已在 macOS 上检查；完整 Windows GUI 重打包仍需 Windows 环境。

## 项目结构

```text
.
|-- ui_app.py
|-- ui/
|-- services/
|-- main.py
|-- extract_pdf.py
|-- image_processor.py
|-- ppt_generator.py
|-- pptx-project/
|-- scripts/
|-- assets/
|-- build.ps1
|-- Slide_Maker.spec
`-- Slide_Maker_Setup.iss
```

## 隐私

Slide Maker 设计为本地运行。依赖和模型准备好之后，文件会在你的电脑上处理。
