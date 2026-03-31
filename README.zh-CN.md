# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker 是一个本地优先的工具链，用来把 PDF、截图和幻灯片图片还原成可编辑的 PowerPoint。

`v0.2.0` 是当前产品形态第一次比较完整的一版，核心包括：

- 一个跨平台的引导式 `terminal_ui.py`
- 一个适合日常使用的桌面 UI
- 一个适合脚本化调用的 CLI
- 用户自管的 LaMa / OCR 模型槽位
- 一个可选的 Node 高保真排版阶段，以及兼容模式回退

## 这个版本能做什么

Slide Maker 现在可以：

- 把 PDF 转成可编辑的 `.pptx`
- 把单张图片转成 `.pptx`
- 把图片目录转成多页 `.pptx`
- 根据 OCR 结果重建文字框
- 先去掉原图文字，再重建页面内容
- 在依赖和可选模型准备好之后完全本地运行

当前处理链路大致是：

1. 拆分 PDF 页面，或者收集输入图片
2. 运行 OCR，识别文字框
3. 估算字号，并从原图采样文字颜色
4. 用 LaMa 或 OpenCV 回退方案清理背景文字
5. 生成可编辑的 `.pptx`
6. 可选地再走一遍基于 Node 的高保真排版

## 平台支持

| 工作流 | Windows | macOS | Linux | 说明 |
| --- | --- | --- | --- | --- |
| Terminal UI | 支持 | 支持 | 支持 | 推荐从这里开始 |
| CLI | 支持 | 支持 | 支持 | 适合自动化 |
| 源码运行桌面 UI | 支持 | 支持 | 支持 | 需要安装 PyQt6 依赖 |
| 打包后的桌面版 | 支持 | 不支持 | 不支持 | 当前打包脚本只面向 Windows |

## 环境要求

- Python 3.10 或更高版本
- 如果你想使用高保真排版，需要 Node.js 在 `PATH` 中
- 安装 `requirements.txt` 里的 Python 依赖
- 在 `pptx-project` 目录执行 `npm install`
- 只有在打包 Windows 桌面版时才需要 PowerShell

如果没有 Node.js，Slide Maker 仍然可以运行，只是会自动回退到兼容渲染模式。

## 安装

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

### macOS

```bash
bash ./scripts/setup_macos.sh
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
cd pptx-project && npm install && cd ..
```

## 推荐入口：Terminal UI

如果你想从 0 开始配置并直接使用这个版本，最简单的方式是：

```bash
python terminal_ui.py
```

这个终端界面支持 Windows、macOS、Linux，并且可以：

- 检查运行环境
- 引导你从零开始配置 LaMa 和 OCR 模型
- 把官方 OCR ONNX 模型下载到预留槽位
- 帮你打开模型目录
- 保存默认转换参数
- 交互式执行 PDF、单图、图片目录转换

## 其他入口

### 桌面 UI

```bash
python ui_app.py
```

常用附加参数：

```bash
python ui_app.py --demo
```

### CLI

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py ./slides --output Result_Presentation.pptx
```

如果你不希望程序提示打开结果文件，可以加上 `--no-open`。

### 更底层的流程入口

```bash
python main.py --input ./slides --output output.pptx
```

## 模型管理

### LaMa 背景修复模型

当前仓库已经不再把 LaMa 权重当成仓库内置资产。

期望文件名：

- `big-lama.pt`

支持的放置方式：

- 预留槽位：`.slide_maker_data/models/lama/big-lama.pt`
- 自定义环境变量：`SLIDE_MAKER_LAMA_MODEL`
- 兼容别名：`LAMA_MODEL`

如果没有配置 LaMa，Slide Maker 会自动回退到 OpenCV Telea。

原始依赖使用的上游模型地址：

- [big-lama.pt](https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt)

### OCR 模型

默认情况下，Slide Maker 可以直接使用打包在 RapidOCR 里的默认模型。这个版本也支持用户自己管理 OCR 模型。

预留槽位目录：

- `.slide_maker_data/models/rapidocr/onnxruntime/`

期望文件名：

- `ch_PP-OCRv4_det_infer.onnx`
- `ch_ppocr_mobile_v2.0_cls_infer.onnx`
- `ch_PP-OCRv4_rec_infer.onnx`

自定义环境变量：

- `SLIDE_MAKER_OCR_DET_MODEL`
- `SLIDE_MAKER_OCR_CLS_MODEL`
- `SLIDE_MAKER_OCR_REC_MODEL`

快速下载到预留槽位：

```bash
python scripts/download_ocr_models.py
```

## 渲染模式

Slide Maker 最终有两种生成方式：

- 高保真模式：使用 Node.js 和 `pptx-project/layout_engine.js` 做更好的排版还原
- 兼容模式：当没有 Node.js，或者你主动选择兼容模式时，保留 Python 生成的 `.pptx`

也就是说，即使环境不完整，工具仍然可以继续工作。

## 运行时数据目录

运行过程中，Slide Maker 会把日志、临时文件和模型槽位写入应用数据目录：

- macOS / Linux 源码运行：`.slide_maker_data/`
- Windows 应用数据模式：`%LOCALAPPDATA%\SlideMaker\`

常见子目录包括：

- `logs/`
- `runtime/`
- `models/lama/`
- `models/rapidocr/onnxruntime/`
- `config/`

## 打包

Windows 打包目前由这两个文件驱动：

- `build.ps1`
- `Slide_Maker.spec`

当前版本已经不再把 LaMa 模型作为仓库内跟踪的源码资产打包进去。

## 项目结构

```text
.
├── terminal_ui.py               # 跨平台引导式终端工作流
├── ui_app.py                    # 桌面 UI 入口
├── run_pipeline.py              # 高层 CLI 入口
├── main.py                      # 核心 image-to-ppt 流程
├── services/                    # 设置、运行时检测、转换调度
├── ui/                          # PyQt UI 组件
├── scripts/                     # 安装脚本和 OCR 下载脚本
├── pptx-project/                # Node 布局引擎资源
├── assets/                      # 图标和界面资源
└── build.ps1                    # Windows 打包脚本
```

## 说明

- 这个仓库目前更像一个持续迭代中的产品工作台，而不是完全打磨完成的公开 SDK。
- 仓库里还保留了一些历史开发记录，方便追溯上下文。
- 仓库根目录目前还没有明确的 license 文件，公开分发前请先确认使用权限。
