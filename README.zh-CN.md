# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker 是一个本地优先的工具，用来把 PDF、截图、扫描页和拍照得到的幻灯片，重建成可编辑的 PowerPoint。

## v0.4.0

- Windows 发布版现在提供经过测试的便携桌面包
- 背景修复现在强制使用 LaMa，不再悄悄回退到 OpenCV
- 打包版会更稳定地优先使用内置运行时
- README 重新整理过，更适合公开发布和新用户上手

## 它现在能做什么

- 把 PDF 转成可编辑的 `.pptx`
- 把单张图片转成 `.pptx`
- 把图片目录转成多页 `.pptx`
- 在 OCR 前先矫正拍照页面的透视
- 根据 OCR 结果重建文本框
- 用 LaMa 清理原图里的文字背景
- 在依赖和模型准备好后全程本地运行

## 最推荐的使用方式

### Windows 便携发布版

对大多数用户来说，最简单的方式就是直接下载 [Releases](https://github.com/hamiltonxu650-lang/Slide-Maker/releases) 页面里的最新 Windows 便携包。

1. 下载最新的便携 ZIP。
2. 解压到任意目录。
3. 把 `big-lama.pt` 放到 `%LOCALAPPDATA%\\SlideMaker\\models\\lama\\big-lama.pt`。
4. 运行 `SlideMaker.exe`。
5. 选择 PDF 或图片并导出 `.pptx`。

补充说明：

- Windows 打包版已经内置了高保真排版所需的 Node 运行时。
- 如果你想把 LaMa 模型放在别的位置，也可以设置 `SLIDE_MAKER_LAMA_MODEL`。

## 支持的使用方式

| 入口 | Windows | macOS | Linux | 说明 |
| --- | --- | --- | --- | --- |
| Terminal UI | 支持 | 支持 | 支持 | 适合第一次配置 |
| CLI | 支持 | 支持 | 支持 | 适合自动化 |
| 桌面 UI（源码运行） | 支持 | 支持 | 支持 | 需要 PyQt6 |
| 本地 Web 应用 | 支持 | 支持 | 支持 | 基于 FastAPI/Uvicorn |
| Docker 部署 Web | 支持 | 支持 | 支持 | 适合自托管 |
| 打包桌面版 | 支持 | 不支持 | 不支持 | 当前正式打包目标 |

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

## 打包说明

Windows 打包流程主要依赖：

- `build.ps1`
- `Slide_Maker.spec`
- `Slide_Maker_Setup.iss`

当前打包产物采用的是混合结构：

- 前台可见的是 PyInstaller 生成的桌面 GUI 外壳
- 真正负责转换的是 `portable_python`、`portable_site_packages`、`portable_app` 组成的便携 worker

这样设计是有意为之，因为它比“全部冻结成单一 worker”在 `torch` 和 `onnxruntime` 负载下更稳定。

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
- 现阶段重点在本地转换质量和 Windows 桌面可用性。
- Web 版本默认是本地部署入口，真正公网发布还需要你自己再做部署层处理。
