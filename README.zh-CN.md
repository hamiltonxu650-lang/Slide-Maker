# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker 是一个本地优先的工具，用来把 PDF、截图、扫描页和拍照得到的幻灯片，重建成可编辑的 PowerPoint。

## v0.4.0

- Mac 桌面版已经做出来，并且这套 Mac 前端现在作为桌面端的视觉基准。
- Windows 桌面前端已经按 Mac 版重做，两端保持同一套产品界面。
- Windows 端保留自己的平台适配：Windows 标题栏按钮、Windows 字体回退、Windows 文件选择入口。
- 修复了左上角标题栏和侧栏图标发糊的问题，现在界面显示优先使用高清 PNG 图标。
- Mac 图形界面启动时现在会额外查找 App 内资源、`~/.local/bin`、Homebrew 和 NVM 里的 Node，避免因为 GUI 环境 `PATH` 太少而误切到兼容模式。
- PDF 转换现在会先做超大页面兼容性预检；不兼容时安全停止，不会降低 DPI 或缩小页面。
- 背景修复现在强制使用 LaMa，不再悄悄回退到 OpenCV。
- 打包版会更稳定地优先使用内置运行时。

## 它现在能做什么

- 把 PDF 转成可编辑的 `.pptx`
- 把单张图片转成 `.pptx`
- 把图片目录转成多页 `.pptx`
- 在 OCR 前先矫正拍照页面的透视
- 根据 OCR 结果重建文本框
- 用 LaMa 清理原图里的文字背景
- 在依赖和模型准备好后全程本地运行

## 最推荐的使用方式

### Windows 用户

请下载 [Releases](https://github.com/hamiltonxu650-lang/Slide-Maker/releases) 页面里的 Windows 版本，或者使用交付目录里的 Windows 便携 ZIP。

1. 下载最新的便携 ZIP。
2. 解压到任意目录。
3. 运行 `SlideMaker.exe`。
4. 选择 PDF 或图片并导出 `.pptx`。

补充说明：

- Windows 打包版已经内置了高保真排版所需的 Node 运行时。
- Windows 打包版也已经内置了便携 Python、OCR 运行时和 LaMa 模型。
- 如果你想把 LaMa 模型放在别的位置，也可以设置 `SLIDE_MAKER_LAMA_MODEL`。

### Mac 用户

请使用 Mac 版本。Mac 桌面前端已经完成，并且 Windows 版前端现在就是从这套 Mac 设计同步过去的。

如果从源码启动 Mac 桌面端，可以运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python ui_app.py
```

## 系统要求

### Windows 最低建议配置

- Windows 10 或 Windows 11，64 位
- Intel / AMD x64 处理器
- 16 GB 内存，适合正常使用
- 至少 4 GB 可用磁盘空间
- 不需要独立显卡
- 不需要额外安装 Python 或 Node.js

### Windows 推荐配置

- Windows 11，64 位
- 16 GB 到 32 GB 内存
- SSD，并预留 8 GB 以上可用空间
- 现代 4 核或更高性能 CPU

### macOS 源码运行环境

- macOS，Python 3.9 或更高版本
- Node.js 在 `PATH`、`~/.local/bin`、Homebrew 或 NVM 中，用于高保真排版
- LaMa 模型和 OCR 模型已经放入 `.slide_maker_data/`
- 桌面 UI 需要 PyQt6

### 已测试的运行情况

`v0.4.0` 的 Windows 便携版此前已经按“自带运行时”的方式做过实测：

- ZIP 下载包大小约 `753 MB`
- 解压后大小约 `1.85 GB`
- 内含 `Python 3.10.10`、`Node v24.14.0`、`torch 2.10.0+cpu`、`onnxruntime 1.23.2` 和 `big-lama.pt`
- 单张图片转换时，本地测试峰值工作集约 `1.5 GB`
- 3 页 PDF 转换时，本地测试峰值工作集约 `5.8 GB`

如果用户只有 `8 GB` 内存，处理轻量单图任务也许还能运行，但不建议把多页 PDF 转换作为稳定使用目标。

这次同步前端后，Mac 端转换流程也重新跑过：

- 使用 `test/download.jpg` 转换图片，成功输出 1 页 `.pptx`。
- 使用 `test/Quiz 1.pdf` 转换 PDF，成功输出 3 页 `.pptx`。
- 使用 `ui_app.py --worker` 跑桌面端实际调用的 worker 流程，成功输出 `.pptx`。
- Mac 端测试完整走通了 RapidOCR、LaMa AI 背景修复和 Node 高保真排版。

这次 `v0.4.0` 稳定性修复又专门复测了你截图里的两个问题：

- PNG / 图片转换在接近 Mac GUI 的受限环境里重新跑过，`PATH=/usr/bin:/bin` 时仍然成功走 Node 高保真输出。
- 在不降质模式下，超过约 `6 MP` 或最长边超过 `3200 px` 的页面会被判定为不兼容，需要先裁掉超大画布或拆分异常页面。
- `test/Quiz 1.pdf` 在 200 DPI 下已经全质量跑通：不降 PDF DPI、不缩 OCR 输入，使用 LaMa 全尺寸修复和 Node 高保真输出。
- `test/Barcelona_Redefined_page1.pdf` 在 200 DPI 下约为 `8.15 MP`，已经被识别为不适合全尺寸 OCR / LaMa 链路的输入。
- 额外构造了一个超大页面 PDF，现在会在兼容性预检阶段明确拒绝并提示原因，不会降低 DPI，也不会继续无限吃内存。

Windows 便携包在 macOS 上检查了包结构，包括 `SlideMaker.exe`、便携 Python、内置 Node、OCR 模型和 `big-lama.pt`。因为 macOS 不能直接执行 Windows `.exe`，最终 Windows 输出测试仍需要在 Windows 机器或 Windows 虚拟机里跑一次。

## 支持的使用方式

| 入口 | Windows | macOS | Linux | 说明 |
| --- | --- | --- | --- | --- |
| Terminal UI | 支持 | 支持 | 支持 | 适合第一次配置 |
| CLI | 支持 | 支持 | 支持 | 适合自动化 |
| 桌面 UI（源码运行） | 支持 | 支持 | 支持 | 使用新的 Mac/Windows 共享前端 |
| 本地 Web 应用 | 支持 | 支持 | 支持 | 基于 FastAPI/Uvicorn |
| Docker 部署 Web | 支持 | 支持 | 支持 | 适合自托管 |
| 打包桌面版 | 支持 | 支持 | 不支持 | Windows 用户下载 Windows 版，Mac 用户下载 Mac 版 |

## 从源码启动

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
python terminal_ui.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
python terminal_ui.py
```

如果你是从源码运行，最推荐先用 `terminal_ui.py`，因为它可以帮你检查运行环境、引导模型配置，并直接执行转换。

## 其他入口

### 桌面 UI

```bash
python ui_app.py
```

只看界面预览：

```bash
python ui_app.py --demo
```

这次更新之后，桌面 UI 是最主要的用户界面。Mac 和 Windows 使用同一套重做后的前端，只在窗口外壳和平台文件支持上做差异适配。

### CLI

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py ./slides --output Result_Presentation.pptx
python run_pipeline.py input.jpg --scan --output Result_Presentation.pptx
```

如果你不想在完成后提示打开结果文件，可以加 `--no-open`。

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

### LaMa 背景修复模型

`v0.4.0` 中，背景修复必须依赖 LaMa。

期望文件名：

- `big-lama.pt`

支持的位置：

- `%LOCALAPPDATA%\\SlideMaker\\models\\lama\\big-lama.pt`，适合 Windows 打包版
- `.slide_maker_data/models/lama/big-lama.pt`，适合源码运行
- `SLIDE_MAKER_LAMA_MODEL`
- `LAMA_MODEL`

如果 LaMa 没配置好，Slide Maker 会直接停止转换并提示你先补齐模型。

依赖库使用的上游模型地址：

- [big-lama.pt](https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt)

### OCR 模型

项目支持直接使用 RapidOCR，也支持你自己管理 OCR 模型。

预留目录：

- `.slide_maker_data/models/rapidocr/onnxruntime/`

辅助下载脚本：

```bash
python scripts/download_ocr_models.py
```

## 渲染模式

Slide Maker 最终有两种输出路径：

- 高保真模式：使用 Node.js 和 `pptx-project/layout_engine.js` 做更好的排版还原
- 兼容模式：当 Node.js 不可用，或者你主动选择兼容模式时，保留 Python 生成的 `.pptx`

Windows 打包版会自动优先使用内置 Node 运行时。

Mac 源码版或 App 启动时，也会额外检查 `~/.local/bin/node`、Homebrew 和 NVM 等 GUI 环境里经常缺失的 Node 位置，然后才会切换到兼容模式。

## 打包说明

Windows 打包流程主要依赖：

- `build.ps1`
- `Slide_Maker.spec`
- `Slide_Maker_Setup.iss`

当前打包产物采用的是混合结构：

- 前台可见的是 PyInstaller 生成的桌面 GUI 外壳
- 真正负责转换的是 `portable_python`、`portable_site_packages`、`portable_app` 组成的便携 worker

这样设计是有意为之，因为它比“全部冻结成单一 worker”在 `torch` 和 `onnxruntime` 负载下更稳定。

Mac 版本现在也是项目的一条正式桌面路线。Mac 端重做出来的前端已经作为当前共享桌面 UI 的来源，Windows 端在不改转换流程的前提下完成了适配。

## 项目结构

```text
.
├── terminal_ui.py
├── ui_app.py
├── run_pipeline.py
├── web_app.py
├── services/
├── ui/
├── scripts/
├── web/
├── pptx-project/
├── runtime/
├── assets/
└── build.ps1
```

## 当前状态

- 这个仓库目前更像一个持续迭代中的产品工作台，而不是一个已经完全稳定的 SDK。
- 现阶段重点在本地转换质量，以及 Windows / Mac 两端桌面体验保持一致。
- Web 版本默认是本地部署入口，真正公网发布还需要你自己再做部署层处理。
