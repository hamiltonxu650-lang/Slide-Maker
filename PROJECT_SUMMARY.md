# NotebookLM PPT Converter - 完整项目开发日志

> **项目启动时间**：2026-03-23  
> **工作空间**：`D:\maker`  
> **备份位置**：`D:\maker_main_backup`（含完整 AI 版本代码）

---

## 一、项目起源与目标

### 1.1 产品定位
一款主打 **"零云端成本、绝对隐私安全、离线可用"** 的 PC 端本地幻灯片逆向工程与重构软件。

### 1.2 核心功能
将带有复杂排版和高光渐变背景的各类演示截图（如 NotebookLM 生成界面、在线课程、PDF 截屏等）自动转换为**文本完全可编辑**、且**原图背景无痕保留**的 `.pptx` 格式演示文稿。

### 1.3 核心业务价值
解决市面上轻量级转换工具 "排版串行识别错位" 和 "擦除原字后背景糊化" 的业务痛点。

---

## 二、原型阶段（由之前对话完成）

### 2.1 第一代技术栈探索
- 采用 `pytesseract`（Tesseract）跑通中英文双语文本坐标定位
- 结合 `OpenCV`，利用 `cv2.inpaint` 传统数学算法完成 "定位 -> 遮罩生成 -> 擦除 -> 填补" 链路
- 基于 `python-pptx` 构建 PPT 生成器

### 2.2 探明的技术天花板
- **排版天花板**：Tesseract 天然缺乏 "版面分析（Layout Analysis）" 能力，面对多栏并列排版时导致排版碎片化
- **视觉天花板**：OpenCV 算法本质是单纯的数学涂抹，在处理带有高光裂缝等复杂背景时产生明显的涂抹痕迹
- **生态排障**：发现了超前 Python 版本导致的底层环境断层，明确了将基础设施降级至 Python 3.11 的必要性

### 2.3 第一代核心架构升级
- **OCR 引擎**：全面替换为 **PaddleOCR**，具备商业级版面感知与文字对齐能力
- **AI 图像修复引擎**：引入深度学习修复模型 **LaMa（Large Mask Inpainting）**
- **幻灯片装配**：基于 `python-pptx` 构建，含自动吸取颜色和估算字号的算法
- **主控调度**：`main.py` 统筹协调文件 I/O、PaddleOCR 分析、Mask 生成、LaMa 推理和 PPTX 封装

---

## 三、本次会话工作全记录

### 3.1 项目迁移与环境初始化

#### 3.1.1 文件迁移
- 将之前对话中存放在 `C:\Users\lewis\.gemini\antigravity\scratch\notebook_ppt_converter\` 的全部项目文件（含虚拟环境 `venv`）复制到了当前活跃工作空间 `D:\maker`
- 将架构设计文档 `notebook_ppt_converter_architecture.md` 从之前对话的 brain 目录移动到 `D:\maker`

#### 3.1.2 迁移后的文件结构
```
D:\maker
├── build.ps1                 # PyInstaller 打包脚本雏形
├── inpainting_engine.py      # LaMa AI 图像修复引擎
├── main.py                   # 主控调度脚本
├── ocr_engine.py             # OCR 文字提取引擎
├── ppt_generator.py          # PPT 生成器（python-pptx）
├── requirements.txt          # Python 依赖列表
├── utils.py                  # 工具函数（遮罩生成、颜色提取、字号估算）
├── notebook_ppt_converter_architecture.md  # 架构文档
└── venv/                     # Python 虚拟环境
```

---

### 3.2 PaddleOCR 引擎适配与修复

#### 3.2.1 问题发现
当前安装的 PaddleOCR 版本（v3.4.0，基于 PaddleX 后端）的 API 与之前编写的代码不兼容。具体表现为：

1. **`show_log=False` 参数不再被支持**  
   `PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)` 抛出 `ValueError: Unknown argument: show_log`

2. **`cls=True` 参数不再被支持**  
   `ocr.ocr(image_path, cls=True)` 抛出 `PaddleOCR.predict() got an unexpected keyword argument 'cls'`

3. **MKLDNN 兼容性问题**  
   在 Windows CPU 环境下，PaddlePaddle 的 OneDNN（MKLDNN）指令集触发了 `ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute]` 错误。通过添加 `enable_mkldnn=False` 参数解决。

4. **返回值格式变化**  
   PaddleOCR v5（PaddleX 后端）的输出从之前的嵌套列表格式：
   ```python
   # 旧格式：[ [([[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, score)), ...] ]
   ```
   变为了字典格式：
   ```python
   # 新格式：[{'dt_polys': [...], 'rec_texts': [...], 'rec_scores': [...], ...}]
   ```

#### 3.2.2 修复措施
- 移除 `show_log=False` 和 `cls=True` 参数
- 添加 `enable_mkldnn=False` 参数
- 重写 `ocr_engine.py` 中的数据解析逻辑，同时兼容新旧两种返回格式
- 编写测试脚本 `test_ocr.py`，通过 OpenCV 生成带文字的测试图片验证

#### 3.2.3 测试结果
```
[1] Text: 'PaddleOCRTestRun', Confidence: 0.9898
    Bounding Box: [[0, 48], [375, 54], [375, 89], [0, 83]]
    Computed Height: 41.00, Computed Width: 375.00
Integration Test Passed Successfully.
```

---

### 3.3 纯文字排版模式实现（去除背景处理）

#### 3.3.1 用户需求变更
用户要求 **不处理原图的背景和字**，只根据原图的排版和字体重新排版文字，不保留背景和图片。

#### 3.3.2 修改内容
1. **`main.py`**：注释掉了 LaMa 背景修复相关的代码（`create_mask_from_boxes`、`inpaint_image`），将背景图参数改为 `None`
2. **`ppt_generator.py`**：在 `add_slide()` 方法中添加了 `if background_image_path:` 条件判断，使背景图渲染变为可选

#### 3.3.3 测试结果
成功生成了 `test_result_no_bg.pptx`，幻灯片上只有白底画布和精确坐标定位的可编辑文本框。

---

### 3.4 Node.js 技术栈引入（pptx-project Skill）

#### 3.4.1 用户指定的安装清单
```bash
npm init -y
npm install pptxgenjs playwright react-icons react react-dom sharp
npx playwright install
pip install "markitdown[pptx]"
```

#### 3.4.2 环境问题与解决
- **Node.js 未安装**：通过 `winget install -e --id OpenJS.NodeJS.LTS` 安装了 Node.js v24.14.0
- **PowerShell 执行策略限制**：`npm.ps1` 脚本被系统阻止，改用 `npm.cmd` 绕过
- **libreoffice 和 poppler 跳过**：这两个组件仅在 Linux/macOS 下用于 PDF 转换，在 Windows 下且当前需求中完全不需要

#### 3.4.3 安装结果
- `pptxgenjs`、`playwright`、`react`、`react-dom`、`react-icons`、`sharp` 全部成功安装到 `D:\maker\pptx-project\node_modules`
- Playwright 浏览器引擎（Chromium、Firefox、WebKit）全部下载完成
- `markitdown[pptx]` 成功安装到 Python 虚拟环境

#### 3.4.4 Node.js 排版引擎编写
创建了 `pptx-project/layout_engine.js`：
- 读取 Python 生成的 `ocr_data.json` 结构化坐标数据
- 使用 `pptxgenjs` 在空白画布上按绝对坐标放置文本框
- 支持自定义幻灯片尺寸（像素转英寸，DPI=96）
- 生成了 `test_result_skill.pptx`

---

### 3.5 文本框大小与换行问题迭代

#### 3.5.1 V1 问题：文本框太小导致自动换行
文本框的宽度严格等于 OCR 检测到的文字宽度，但不同系统的字体渲染差异导致实际文字比框宽，触发了自动换行。

**修复（V2）**：
- 关闭自动换行 `wrap: false`
- 扩大文本框：宽度乘以 1.4 倍 + 0.5 英寸缓冲，高度乘以 1.2 倍 + 0.3 英寸

#### 3.5.2 V2 问题：文本框过大导致重叠
放宽后的文本框侵占了相邻文本框的空间。

**修复（V3-V5）多次迭代**：
- 恢复 `wrap: true`
- 文本框尺寸恢复为严格匹配 OCR 坐标
- 启用 `fit: 'shrink'` 和 `autoFit: true` 让文字自动缩小适配
- 全局字号缩小 15%（`fontSize * 0.85`）抵消系统行高溢出
- 垂直居中 `valign: 'middle'`

#### 3.5.3 V6：段落聚类算法解决字号不统一问题
**问题**：同一段落的不同行被分成独立文本框，各自的 `autoFit` 导致字号参差不齐。

**解决方案 - 段落归并聚类算法**：
1. 将所有文本框按垂直位置排序
2. 如果两个文本框垂直间距小于 1.5 倍行高 **且** 水平方向有重叠，则合并为同一段落
3. 段落内取**最大字号**作为统一字号
4. 将段落内所有文字拼接为一个字符串，放入一个覆盖整个段落范围的大文本框

---

### 3.6 版本管理与分支备份

#### 3.6.1 问题
用户系统未安装 Git，无法使用 `git init` / `git branch` 命令。

#### 3.6.2 替代方案
- **main 分支备份**：将 `D:\maker` 的全部文件（不含 `venv`）物理拷贝到 `D:\maker_main_backup`
- **v2 工作区**：`D:\maker` 直接作为 v2 开发区继续工作

---

### 3.7 RapidOCR 替换 PaddleOCR（v2 轻量化）

#### 3.7.1 用户需求
将项目做成独立桌面 App，要求**完全不依赖 AI 大模型框架**（PaddlePaddle 打包后 2GB+）。

#### 3.7.2 方案选型
| 方案 | 体积 | 准确度 | 可行性 |
|------|------|--------|--------|
| Windows 原生 OCR API（WinRT） | 0 MB | 中 | ❌ Python WinRT 绑定库严重版本不兼容 |
| RapidOCR（ONNX Runtime） | ~15 MB | 高（与 PaddleOCR 同源） | ✅ 完美 |

#### 3.7.3 WinRT OCR 失败记录
- 安装了 `winsdk`（1.0.0b10）但模块无法被 Python 识别
- 安装了 `winrt-Windows.Media.Ocr`、`winrt-Windows.Graphics.Imaging`、`winrt-Windows.Storage`（v3.2.1）同样无法 import
- 由于 Python 3.10 与 WinRT 包的 ABI 不兼容，放弃此方案

#### 3.7.4 RapidOCR 实施
1. 卸载 `paddleocr` 和 `paddlepaddle`
2. 安装 `rapidocr_onnxruntime`（v1.4.4）
3. **注意**：pip 先安装到了旧 venv 路径（`C:\Users\lewis\.gemini\antigravity\scratch\...`），因为 `.\venv` 是符号链接。后改用 `d:\maker\venv\Scripts\python.exe -m pip install` 直接安装到正确路径

4. 重写 `ocr_engine.py`：
   ```python
   from rapidocr_onnxruntime import RapidOCR
   ocr = RapidOCR()
   # RapidOCR 返回格式：(results, elapsed)
   # results: [ ([[x1,y1],[x2,y2],[x3,y3],[x4,y4]], text, score), ... ]
   ```

5. **RapidOCR 的返回格式**与原始 PaddleOCR 旧版格式几乎一致（元组列表），无需额外的字典格式处理逻辑。

#### 3.7.5 测试结果
在测试图片上成功提取文字和坐标，Pipeline 全流程（Python OCR -> JSON -> Node.js PPTX 生成）运行正常。

---

### 3.8 英文分词空格修复（WordNinja）

#### 3.8.1 问题
RapidOCR 在识别英文时，会将相邻单词粘连在一起，如 `StaplestoGlobalFineDining`、`Worldflavors`、`approximately60guilders`。

#### 3.8.2 解决方案
引入 `wordninja` 库（基于维基百科语料的概率字典分词器）：

```python
import wordninja
wordninja.split("StaplestoGlobalFineDining")
# -> ['staples', 'to', 'global', 'fine', 'dining']
```

#### 3.8.3 实现细节
在 `ocr_engine.py` 中添加了 `fix_english_spacing()` 函数：
1. 使用正则表达式 `[A-Za-z]+` 匹配所有连续英文字母块
2. 对长度超过 3 的字母块调用 `wordninja.split()` 进行概率分词
3. **大小写保护算法**：通过索引回溯映射，从原始字符串中提取每个分词对应的原始大小写字符，避免 wordninja 的全小写输出破坏原文格式
4. 将分词结果用空格连接后替换回原始文本

#### 3.8.4 测试结果
```
原始：StaplestoGlobalFineDining
修复：Staples to Global Fine Dining

原始：Worldflavors
修复：World flavors
```

---

### 3.9 复杂排版压力测试（Slide2.JPG）

#### 3.9.1 测试图片描述
`Slide2.JPG`（1280×720）是一张来自 NotebookLM 的高复杂度幻灯片：
- **底层**：一张老旧的曼哈顿地图（深色调、纹理丰富）
- **中层**：三个半透明暗色卡片面板
- **顶层**：白色大标题 + 金色小标题 + 白色正文

#### 3.9.2 测试结果
排版引擎成功处理了所有文字块，段落聚类正确且字号统一。输出了 `Slide2_optimal.pptx`。

---

### 3.10 图片剥离与全保真 PPTX 重建

#### 3.10.1 用户需求
将原图中的**背景图像**与**文字**完全拆分。背景图像上被文字覆盖的区域需要被修补填充，文字相关部分则作为可编辑文本框在 PPT 中呈现。最终要求与原图接近 100% 视觉一致。

#### 3.10.2 迭代历程

##### 第一版：双算法全矩形修补（失败）
- 使用 `cv2.inpaint` 的 Telea 和 Navier-Stokes 两种算法，在文本框的**整个矩形区域**上做修补
- **问题**：大面积矩形遮罩 + 大修补半径（radius=12）导致严重的模糊涂抹

##### 第二版：局部背景色采样填充（失败）
- 对每个文本框采样其周围 8px 边缘条带的颜色，用该颜色直接填充文本区域
- 仅在接缝边缘做极小范围的修补
- **问题**：采样边缘时混入了文字像素，导致填充色与文字颜色相同，出现 "什么颜色的字体底下就有什么颜色的马赛克" 的现象

##### 第三版：原图直出 + 遮罩覆盖（被用户否定）
- 直接使用原图作为背景，文本框带有与背景匹配的实心填充色覆盖原文字
- **用户反馈**："你只是用后加的文字覆盖掉了原本图片上的文字"
- **用户明确要求**：必须真正删除原本的文字，再在原来的范围内添加新的文字

##### 第四版（当前版本）：像素级文字笔画精准修补
新建了全新的 `image_processor.py`，核心逻辑如下：

1. **像素级文字遮罩生成**（`create_pixel_text_mask`）：
   - 对每个 OCR 文本框区域提取 ROI
   - 采样文本框上下方的边缘条带，计算背景亮度中值
   - 自动判断文字是 "亮字暗底"（如白字黑底）还是 "暗字亮底"（如黑字白底）
   - 相应选择 `cv2.THRESH_BINARY`（亮字）或 `cv2.THRESH_BINARY_INV`（暗字）+ Otsu 自适应阈值
   - 对阈值化后的文字像素做轻微膨胀（`dilate`，kernel=5×5，1 次迭代）以覆盖抗锯齿边缘
   - 最终得到一个**紧贴文字笔画**的像素级二值遮罩

2. **精准修补**（`inpaint_background`）：
   - 使用 `cv2.inpaint(img, mask, radius=5, cv2.INPAINT_TELEA)` 对像素级遮罩进行修补
   - 由于遮罩仅覆盖极细的文字笔画（而非整个矩形），修补算法只需从紧邻的背景像素扩展极小的区域
   - 周围的纹理/卡片底色会自然延伸进来，不会产生大面积色块或模糊

---

### 3.11 字体颜色提取修复（K-means 聚类法）

#### 3.11.1 问题
之前的 `extract_text_color()` 使用 Otsu 二值化 + 反转阈值来提取文字颜色。在深色背景上的白色/金色文字场景中，该方法错误地将**深色背景像素**识别为 "文字"，导致提取出的颜色全是 `[11, 11, 11]`（近黑），而实际的白色/金色文字被忽略。

#### 3.11.2 修复方案
在 `utils.py` 中重写了 `extract_text_color()` 函数：
1. 采样文本框上下方 6px 的边缘条带，计算背景色均值
2. 对文本框内的所有像素执行 **K-means 聚类（k=2）**，分离出两个颜色簇
3. 计算两个聚类中心到背景色的欧氏距离
4. 选择**距离背景色更远**的聚类中心作为文字颜色（因为文字一定是与背景对比度最大的颜色）

#### 3.11.3 修复效果
```
修复前：白色标题文字 -> 提取颜色 [11, 11, 11]（黑色）❌
修复后：白色标题文字 -> 提取颜色 [245, 245, 243]（白色）✅

修复前：金色小标题 -> 提取颜色 [44, 40, 24]（深棕）❌
修复后：金色小标题 -> 提取颜色 [211, 198, 144]（金色）✅
```

---

### 3.13 Windows 中文路径兼容性修复
**问题**：在 Windows 系统下，`cv2.imread` 无法直接读取包含中文（如“未命名的设计.png”）的路径，会导致程序崩溃。
**解决方案**：在 `main.py`、`ocr_engine.py` 和 `image_processor.py` 中统一将：
```python
img = cv2.imread(path)
```
替换为更具鲁棒性的加载方式：
```python
import numpy as np
img = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
```

### 3.15 多页全自动批量转换 (Batch Processing)
**功能**：支持将一整个文件夹的图片，或从现有幻灯片中提取出的图片，一键批量转换为单份多页 PPTX。
**技术演进**：
1. **提取端**：新增 `extract_slides.py`，自动从图片版 PPTX 中剥离每一页的原始位图。
2. **处理端**：重构 `main.py`，将所有页面的 OCR 数据与 AI 修复背景路径统一汇总到 `ocr_data.json` 数组中。
3. **渲染端**：重构 `layout_engine.js`，改为循环遍历 JSON 数组，实现在单次 Node.js 运行中生成完整幻灯片集的功能。

### 3.16 实测记录：original.pptx (11页)
- **输入**：包含 11 张高清图片幻灯片的原始文档。
- **过程**：全自动批量执行 11 次 LaMa 离线 AI 修复，耗时约 90 秒。
- **输出**：生成 `Original_Reconstructed_Full.pptx`，所有页面均完成背景修复与文字原位重排。

---

## 四、当前完整技术架构 (更新)
... (已升级为多页批处理架构) ...

---

## 五、运行方式 (更新)
### 5.3 测试新图片
```powershell
# 处理包含中文名的图片
d:\maker\venv\Scripts\python.exe main.py --input "d:\maker\test\未命名的设计.png" --output "Untitled.pptx"
```

```
原始截图图片
    │
    ▼
┌─────────────────────────────┐
│  Python 数据提取层          │
│                             │
│  ocr_engine.py              │
│  ├── RapidOCR (ONNX)        │  ← 轻量级，~15MB
│  ├── WordNinja 英文分词     │
│  └── 输出：文字 + 坐标      │
│                             │
│  utils.py                   │
│  ├── K-means 颜色提取       │
│  └── 字号估算               │
│                             │
│  image_processor.py         │
│  ├── 像素级文字遮罩生成     │
│  └── cv2.inpaint 精准修补   │
│                             │
│  main.py                    │
│  └── 串联所有模块，输出 JSON │
└─────────────┬───────────────┘
              │ ocr_data.json
              ▼
┌─────────────────────────────┐
│  Node.js 渲染层             │
│                             │
│  layout_engine.js           │
│  ├── pptxgenjs              │
│  ├── 段落聚类算法           │
│  ├── 背景图铺底             │
│  └── 文本框坐标精准还原     │
│                             │
│  输出：最终 .pptx 文件      │
└─────────────────────────────┘
```

### 4.2 文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `ocr_engine.py` | RapidOCR 文字提取 + WordNinja 英文分词 | ✅ 已完成 |
| `image_processor.py` | 像素级文字遮罩 + cv2.inpaint 背景修补 | ✅ 已完成 |
| `utils.py` | K-means 颜色提取 + 遮罩生成 + 字号估算 | ✅ 已完成 |
| `main.py` | 主控调度（OCR → 颜色分析 → 修补 → JSON 导出） | ✅ 已完成 |
| `ppt_generator.py` | python-pptx PPT 生成器（同时生成 Python 版 PPTX） | ✅ 已完成 |
| `pptx-project/layout_engine.js` | pptxgenjs 排版引擎（聚类 + 背景图 + 文本叠加） | ✅ 已完成 |
| `pptx-project/ocr_data.json` | Python → Node.js 的数据桥接文件 | ✅ 自动生成 |
| `test_ocr.py` | OCR 引擎单元测试脚本 | ✅ 已完成 |
| `debug_ocr.py` | PaddleOCR 返回格式调试脚本 | ✅ 已完成 |
| `winrt_ocr_engine.py` | Windows 原生 OCR API 尝试（已弃用） | ⚠️ 弃用 |
| `inpainting_engine.py` | LaMa AI 修复引擎（main 分支备份中保留） | 📦 仅在 backup |

### 4.3 依赖清单

#### Python 依赖
```
rapidocr_onnxruntime  # ONNX 轻量 OCR
onnxruntime           # ONNX C++ 推理引擎
opencv-python         # 图像处理 + inpainting
Pillow                # 图像 I/O
python-pptx           # PPT 生成
wordninja             # 英文概率分词
markitdown[pptx]      # PPTX 解析
numpy, pyclipper, shapely, PyYAML, tqdm, six  # RapidOCR 依赖
```

#### Node.js 依赖
```
pptxgenjs             # PPT 生成（核心渲染引擎）
playwright            # 浏览器自动化（预留）
react, react-dom      # React（预留）
react-icons           # 图标库（预留）
sharp                 # 图像处理（预留）
```

---

## 五、运行方式

### 5.1 完整流水线（Python OCR + 背景修补 + Node.js 渲染）
```powershell
# 1. Python 提取文字 + 修补背景 + 导出 JSON
d:\maker\venv\Scripts\python.exe main.py --input "d:\maker\test\Slide2.JPG" --output "d:\maker\output.pptx"

# 2. Node.js 精美排版渲染
cd d:\maker\pptx-project
& "C:\Program Files\nodejs\node.exe" layout_engine.js ocr_data.json FinalSlide.pptx
```

### 5.2 输出文件位置
- Python 版 PPTX：`d:\maker\output.pptx`
- Node.js 版 PPTX：`d:\maker\pptx-project\FinalSlide.pptx`（同时也会输出到 `d:\maker\FinalSlide.pptx`）

---

## 六、已知问题与后续规划

### 6.1 已知限制
- OpenCV `cv2.inpaint` 在复杂纹理背景上可能留有轻微修补痕迹（纯数学方法的物理极限）
- 段落聚类算法对于非标准排版（如环形文字、斜体）可能误合并
- 字号估算基于简易公式 `pt = pixels * 0.75`，在不同 DPI 下可能存在偏差

### 6.2 后续规划（文档中的 Step 3 & 4）
- **Step 3：GUI 图形化界面**（PyQt6 / Tkinter）
- **Step 4：软件打包部署**（PyInstaller + 瘦身优化）
- **可选增强**：接入云端 AI 修补 API 提升复杂背景的修补质量
