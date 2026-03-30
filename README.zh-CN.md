# Slide Maker

[English](README.md) | [简体中文](README.zh-CN.md)

Slide Maker 是一个离线桌面工具，用来把 PDF、截图和幻灯片图片还原成可编辑的 PowerPoint。它更强调本地处理、隐私安全、排版还原和背景修复，而不是依赖云端服务。

当前版本把 OCR、去字修复、背景重建和 PPTX 生成整合在一起，主形态是面向 Windows 的桌面应用，同时保留了命令行入口。

## 核心能力

- 将 PDF 页面转换为可编辑的 `.pptx`
- 将截图或图片文件夹转换为可编辑演示文稿
- 基于 OCR 结果重建文本框位置、颜色和字号
- 擦除原图文字后再重建页面，尽量保留背景观感
- 优先使用更轻量的 OCR 方案，方便本地打包
- 安装完依赖后可完全离线运行
- 同时提供桌面 UI 和命令行工作流

## 工作流程

Slide Maker 当前采用一条本地多阶段处理链路：

1. 从 PDF 中拆出页面，或者收集输入图片
2. 运行 OCR，识别文字、边框和阅读顺序
3. 估算字号，并从原图中提取文字颜色
4. 通过图像修复去掉原图中的文字
5. 重新生成可编辑的 `.pptx` 幻灯片

当前仓库主要使用：

- `RapidOCR` 作为首选 OCR 后端
- Windows OCR 作为兼容回退
- `simple-lama-inpainting`，必要时回退到 OpenCV 去字修复
- `python-pptx` 负责生成 PowerPoint
- `PyQt6` 负责桌面界面

## 环境要求

- 建议 Python 3.10 及以上
- 桌面版主要面向 Windows
- 打包流程依赖 PowerShell
- 需要先安装 `requirements.txt` 中的依赖

## 安装

创建虚拟环境并安装依赖：

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

如果你只是想直接运行项目，不做打包，这一步通常就够了。

## 快速开始

### 桌面版

启动 PyQt 应用：

```bash
python ui_app.py
```

当前界面已经接入两条真实流程：

- PDF 转 PPTX
- 图片转 PPTX

### 命令行

使用更高层的转换入口：

```bash
python run_pipeline.py input.pdf --output Result_Presentation.pptx
```

处理单张图片或图片目录：

```bash
python run_pipeline.py input.png --output Result_Presentation.pptx
python run_pipeline.py path\to\image_folder --output Result_Presentation.pptx
```

### 底层脚本

原始的底层图像转 PPT 流程仍然保留：

```bash
python main.py --input path\to\images --output output.pptx
```

## 打包

仓库内置了基于 PyInstaller 的 Windows 打包脚本：

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

这个脚本会一起打包：

- PyQt 桌面应用
- OCR 运行时依赖
- 去字修复相关资源
- `pptx-project` 里的 Node 布局资源
- 图标和运行时辅助文件

## 项目结构

```text
.
├── ui_app.py                    # 桌面应用入口
├── run_pipeline.py              # 命令行转换入口
├── main.py                      # 核心图像转 PPT 流程
├── ocr_engine.py                # OCR 后端适配层
├── image_processor.py           # 文字遮罩和背景修复
├── ppt_generator.py             # PPTX 重建
├── extract_pdf.py               # PDF 拆页
├── services/                    # 转换调度和应用模型
├── ui/                          # PyQt UI 组件
├── assets/                      # 图标和资源
├── pptx-project/                # 补充布局引擎资源
├── build.ps1                    # Windows 打包脚本
└── requirements.txt
```

## 输出结果

最终产物是可编辑的 `.pptx`。根据 OCR 和背景修复运行情况，输出可能是：

- 完整重建的可编辑文本幻灯片
- 更偏兼顾排版的可编辑输出
- 在 OCR 不可用时，退化为兼容优先的图片型页面输出

## 当前状态

这个仓库现在更像一个持续迭代中的本地产品工作台，而不是已经完全打磨完的公开 SDK。仓库里还保留了开发日志和架构记录，它们适合深入了解背景，但不是日常使用的必读材料。

## 许可证

这个仓库此前没有面向首页的许可证说明。若要做公开分发或商业使用，请先检查仓库后续是否补充正式 license 文件，再决定使用方式。
