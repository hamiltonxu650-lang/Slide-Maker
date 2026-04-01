# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker 是一个本地优先的工具链，用来把 PDF、截图、扫描照片和幻灯片图片还原成可编辑的 PowerPoint。

`v0.3.0` 是第一版把项目扩展到更完整可部署形态的版本，核心包括：

- 一个跨平台的引导式终端界面
- 一个适合日常使用的桌面 UI
- 一个适合脚本化调用的 CLI
- 一个可本地部署的 Web 入口
- 扫描风格的透视裁正能力
- 用户自管的 LaMa / OCR 模型槽位
- 一个可选的 Node 高保真排版阶段，以及兼容模式回退
- 一条可继续封装成安装器的 Windows 打包链路

## v0.3.0 重点更新

- 新增扫描裁正能力，适合斜拍幻灯片和拍照文档
- Terminal UI、桌面 UI、CLI、Web 版共用同一条转换服务层
- 新增 FastAPI 本地网页入口，并支持 Docker 部署
- 优化了非 Windows 环境的原生 Node.js 检测
- 在仓库只保留 Git LFS 指针文件时，LaMa 模型加载更稳
- Windows 打包链路继续完善，并补上了 Inno Setup 安装器脚本

## 这个版本能做什么

Slide Maker 现在可以：

- 把 PDF 转成可编辑的 `.pptx`
- 把单张图片转成 `.pptx`
- 把图片目录转成多页 `.pptx`
- 先把斜拍文档或斜拍幻灯片裁正，再继续转换
- 根据 OCR 结果重建文字框
- 先去掉原图文字，再重建页面内容
- 在依赖和可选模型准备好之后完全本地运行

当前处理链路大致是：

1. 拆分 PDF 页面，或者收集输入图片
2. 可选地先对斜拍图片做扫描裁正
3. 运行 OCR，识别文字框
4. 估算字号，并从原图采样文字颜色
5. 用 LaMa 或 OpenCV 回退方案清理背景文字
6. 生成可编辑的 `.pptx`
7. 可选地再走一遍基于 Node 的高保真排版

## 平台支持

| 工作流 | Windows | macOS | Linux | 说明 |
| --- | --- | --- | --- | --- |
| Terminal UI | 支持 | 支持 | 支持 | 推荐从这里开始 |
| CLI | 支持 | 支持 | 支持 | 适合自动化 |
| 源码运行桌面 UI | 支持 | 支持 | 支持 | 需要安装 PyQt6 依赖 |
| 本地 Web 版 | 支持 | 支持 | 支持 | 基于 FastAPI/Uvicorn |
| Docker Web 部署 | 支持 | 支持 | 支持 | 需要 Docker |
| 打包后的桌面版 | 支持 | 不支持 | 不支持 | 当前打包脚本只面向 Windows |
| Windows 安装器产物 | 支持 | 不支持 | 不支持 | 基于已打包桌面版继续封装 |

## 环境要求

- 仍然建议使用 Python 3.10 或更高版本
- 如果你想使用高保真排版，需要 Node.js 在 `PATH` 中
- 安装 `requirements.txt` 里的 Python 依赖
- 在 `pptx-project` 目录执行 `npm install`
- 只有在打包 Windows 桌面版时才需要 PowerShell
- 只有在生成 Windows 安装器时才需要 Inno Setup

如果没有 Node.js，Slide Maker 仍然可以运行，只是会自动回退到兼容渲染模式。

## 本版本的主要入口

`v0.3.0` 的几条主要入口都共用同一套转换服务：

- `terminal_ui.py`：引导式配置与交互运行
- `ui_app.py`：PyQt 桌面界面
- `run_pipeline.py`：CLI 自动化入口
- `web_app.py`：本地浏览器入口

这意味着偏好映射、OCR、背景修复、排版渲染和输出处理在不同入口之间是一致的。

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
python run_pipeline.py input.jpg --scan --output Result_Presentation.pptx
```

如果你不希望程序提示打开结果文件，可以加上 `--no-open`。

### Web 版

如果你想把它作为网页使用，可以启动 FastAPI Web 入口：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-web.txt
cd pptx-project && npm install && cd ..
uvicorn web_app:app --host 0.0.0.0 --port 7860
```

启动后访问：

```text
http://127.0.0.1:7860
```

网页当前支持：

- 上传 PDF
- 上传 PNG / JPG / JPEG
- 选择转换重点
- 直接下载生成的 `.pptx`

### 更底层的流程入口

```bash
python main.py --input ./slides --output output.pptx
```

## 扫描裁正

`v0.3.0` 增加了一条扫描风格的预处理路径，适合处理拍照得到的页面。

这部分能力包括：

- 自动检测文档四角
- 基于四点透视变换做裁正
- 提供彩色增强、灰度锐化、黑白净化等增强模式
- 在桌面端提供手动拖点校正对话框，方便自动识别失败时人工修边

这条扫描路径尤其适合：

- 手机拍的幻灯片照片
- 拍下来的纸质讲义
- 本身带明显透视畸变、需要先拉正再做 OCR 的图片

## 模型管理

### LaMa 背景修复模型

Slide Maker 已经不再把 LaMa 权重视作仓库里稳定内置的源码资产。

期望文件名：

- `big-lama.pt`

支持的放置方式：

- 预留槽位：`.slide_maker_data/models/lama/big-lama.pt`
- 自定义环境变量：`SLIDE_MAKER_LAMA_MODEL`
- 兼容别名：`LAMA_MODEL`

如果没有配置 LaMa，Slide Maker 会自动回退到 OpenCV Telea。

如果仓库里只有 Git LFS 指针占位文件，程序会优先尝试模型槽位配置，必要时再下载官方上游权重。

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

Windows 打包目前由这几个文件驱动：

- `build.ps1`
- `Slide_Maker.spec`
- `Slide_Maker_Setup.iss`

当前 Windows 发布链路大致是：

1. 先用 PyInstaller 构建桌面分发目录
2. 再把 OCR、排版、扫描、UI 所需运行时资源一起带上
3. 最后可选地用 Inno Setup 再封装成安装器

## Docker 部署

仓库现在也提供了 Web 版的 Dockerfile，可直接部署到支持 Docker 的平台，例如 Railway、Render、Fly.io 或自建服务器：

```bash
docker build -t slide-maker-web .
docker run --rm -p 7860:7860 slide-maker-web
```

## 项目结构

```text
.
├── terminal_ui.py               # 跨平台引导式终端工作流
├── ui_app.py                    # 桌面 UI 入口
├── run_pipeline.py              # 高层 CLI 入口
├── web_app.py                   # FastAPI Web 入口
├── scanner_engine.py            # 透视裁正与增强处理
├── main.py                      # 核心 image-to-ppt 流程
├── services/                    # 设置、运行时检测、转换调度
├── ui/                          # PyQt UI 组件
├── scripts/                     # 安装脚本和 OCR 下载脚本
├── web/                         # 本地网页的 HTML/CSS
├── pptx-project/                # Node 布局引擎资源
├── assets/                      # 图标和界面资源
└── build.ps1                    # Windows 打包脚本
```

## 说明

- 这个仓库目前更像一个持续迭代中的产品工作台，而不是完全打磨完成的公开 SDK。
- 仓库里还保留了一些历史开发记录，方便追溯上下文。
- 仓库根目录目前还没有明确的 license 文件，公开分发前请先确认使用权限。
- 当前 Web 版默认是“本地部署入口”，如果要变成公网可访问服务，还需要额外做正式上线部署。
