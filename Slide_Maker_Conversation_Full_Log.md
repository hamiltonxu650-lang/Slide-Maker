# Slide Maker 本次对话完整实施记录

## 文档目的

这份文档用于完整记录本次对话里围绕 `D:\maker` 项目所做的工作、设计决策、代码改动、构建演进、验证结果、问题定位过程和当前状态。

目标是让任何接手这个项目的人，即使没有参与这次对话，也能看懂：

- 这个项目原来是什么状态。
- 本次对话里用户提出过哪些需求。
- 每一轮需求具体落到了哪些代码和分发结构上。
- 哪些问题已经解决，哪些问题曾经出现过但后来改了方案。
- 当前 `dist` 里的可交付版本到底是什么结构、怎样运行、有什么边界。

---

## 一、项目在本次对话开始前的大致基础

本项目原本已经有一套以 Python 为主的转换链路，核心能力集中在：

- `PDF -> 图片页`
- `OCR 识别`
- `去字 / 背景修复`
- `Python 版 PPTX 生成`
- `Node 高保真排版`

本次对话开始时，用户已经有一份项目开发记录文件：

- `D:\maker\Project_Development_Log.md`

从功能上看，用户明确说明当时主要只做了：

- `PDF -> PPTX`
- `PNG -> PPTX`

而桌面 UI、可分发版本、设置体系、品牌视觉、图标、快捷方式、无控制台启动、离线偏好系统等，都是在本次对话中逐步补上的。

---

## 二、本次对话中用户提出过的主要需求

本次对话里，用户先后明确提出了以下任务方向。这一节只列需求，不区分是否一次完成，后续章节会说明具体实现结果。

### 1. 首版桌面 UI

用户要求：

- 根据参考截图做一个现代化桌面 UI。
- 视觉方向参考主流图像工具的深色桌面风格。
- 首页要有两张主功能卡片。
- 当前先接通 `PDF 转 PPTX` 和 `图片转 PPTX`。
- 其他功能位先做成后续“各种格式转 PPTX”的扩展入口。
- 用户需要知道如何预览。

### 2. 桌面快捷方式

用户要求：

- 直接创建桌面快捷方式，方便双击启动。

### 3. 不要弹 PowerShell / 控制台

用户要求：

- 启动软件时不要弹出 PowerShell。
- GUI 运行时也不要再冒出黑框或控制台窗口。

### 4. 更改封面图和修复转换报错

用户要求：

- 修改首页两张封面图片。
- 修复 GUI 真转换时报错。

### 5. 离线“提示词”入口

用户要求：

- 用户如果对生成的 PPT 不满意，希望能提出具体要求。
- 这个功能必须能在别人的电脑上使用，不能只依赖本机、云端或联网服务。

### 6. 删除执行日志区

用户要求：

- 界面里不要展示执行日志板块。

### 7. 改软件名

用户要求：

- 将软件名改为 `Slide Maker`。

### 8. 做设置页，而且设置不能是摆设

用户要求：

- 参考主流桌面软件做设置板块。
- 如果某个设置是假的、没有真实作用，就删除。
- 如果某个设置是真的，要解释清楚它的作用和区别。

### 9. 修复右侧状态区与输入/输出板块问题

用户要求：

- 右侧状态面板不要乱码。
- 输入文件/输出文件板块在非全屏时不能显示错乱。

### 10. 改窗口外观

用户要求：

- 去掉难看的黑边。
- 更接近 Win11 风格。
- 现在进一步要求窗口外边缘做成圆角。

### 11. 图标设计

用户要求：

- 设计新的软件图标。
- 要更现代、简约。
- 之后又要求把图标外圈杂色去掉，只保留主体矩形。

### 12. 不要为了缩安装包体积而削弱功能

用户要求：

- 检查之前为了减小安装包体积是否删掉或削弱了实际功能。
- 如果有，重新编辑并恢复完整功能。

### 13. 生成完整 Markdown 记录

用户要求：

- 生成一份 Markdown 文档，总结本次对话里做过的所有事情。
- 不允许遗漏。
- 要确保任何人都能看懂。

---

## 三、本次对话中实际完成的工作总览

这一节先给出当前已经落地的总览，再在后面详细展开。

- 新建了完整的 `PyQt6` 桌面 UI。
- 新建了 GUI 入口 `ui_app.py`。
- 新建了服务层 `services/conversion_service.py`，把 GUI 和 CLI 统一到底层转换能力上。
- 保留了 CLI 入口，不破坏 `run_pipeline.py` 的独立使用。
- 首页完成了双主卡片结构，接通 `PDF 转 PPTX` 和 `图片转 PPTX`。
- 其余入口改成占位卡，只提示“即将支持”，不会误触发真实转换。
- 新建了自定义标题栏、左侧导航、状态面板、设置页、偏好面板。
- 删除了原先界面中的“执行日志”展示区域。
- 把软件品牌统一改成了 `Slide Maker`。
- 新建并多次更新了图标资源。
- 修复了启动时弹控制台的问题。
- 新建并更新了桌面快捷方式。
- 加入了离线结构化“转换偏好”入口，用于表达“更在意排版 / 清晰 / 背景 / 速度”。
- 这些偏好会真实影响转换参数，而不是纯 UI 填充项。
- 设置页中的选项经过筛选，只保留真实可驱动行为或结果的项。
- 修复了右侧状态卡在小窗口下的路径显示 bug。
- 修复了结果区和状态区的乱码显示问题。
- 修复了打包版 worker 在 `--windowed` 下无法稳定通信的问题。
- 修复了打包版 OCR / RapidOCR / onnxruntime / WinRT fallback 等一系列运行时问题。
- 为高保真模式打包了 `runtime/node.exe` 和 `pptx-project/node_modules`。
- 发现为了缩包体积曾经错误排除了 `simple_lama_inpainting` 和 `torch`，随后恢复了相关能力。
- 发现 PyInstaller frozen worker 对 `torch/onnxruntime` 仍有 DLL 初始化问题，最后改成了更稳的分发结构：
  - GUI 主程序仍是无控制台 PyInstaller 可执行文件。
  - 真正的转换 worker 改为优先调用分发包内部的“便携 Python + 便携源码 + 便携依赖”。
- 这个最终结构已经验证可以在分发包里真实跑通：
  - `RapidOCR`
  - `LaMa AI`
  - `Node 高保真排版`

---

## 四、第一阶段：首版桌面 UI 落地

### 4.1 新增的桌面入口和 UI 结构

本次对话中新增或成体系整理的 GUI 入口和主要 UI 模块包括：

- `D:\maker\ui_app.py`
- `D:\maker\ui\main_window.py`
- `D:\maker\ui\title_bar.py`
- `D:\maker\ui\sidebar.py`
- `D:\maker\ui\status_panel.py`
- `D:\maker\ui\preferences_panel.py`
- `D:\maker\ui\theme.py`
- `D:\maker\ui\cards.py`
- `D:\maker\ui\cover_config.py`
- `D:\maker\ui\settings_store.py`

首页采用了以下布局思路：

- 左侧为固定导航栏。
- 顶部为自定义深色标题栏。
- 主区域左侧为首页内容滚动区。
- 主区域右侧为任务状态面板。

首页内容包含：

- 品牌标题。
- 两张主功能卡：
  - `PDF 转 PPTX`
  - `图片转 PPTX`
- 离线转换偏好区。
- 六个后续扩展入口卡片：
  - Word
  - Excel
  - Markdown
  - TXT
  - 网页
  - 批量导入

### 4.2 当前首页两个主功能入口

当前真实接通的入口只有两个：

- `PDF 转 PPTX`
- `图片转 PPTX`

图片入口当前支持：

- `PNG`
- `JPG`
- `JPEG`

其他模块只是 UI 占位，不会误触发转换。

---

## 五、第二阶段：提取转换服务层，保留 CLI 兼容

为了避免 GUI 直接硬连旧脚本，本次对话中把转换流程抽到统一的服务层。

核心文件：

- `D:\maker\services\conversion_service.py`
- `D:\maker\services\app_models.py`

服务层的作用是：

- 统一输入类型判断。
- 统一输出路径处理。
- 统一阶段性进度回调。
- 统一日志写入。
- 统一高保真 / 兼容模式切换逻辑。
- 统一 GUI 和 CLI 对参数的调用方式。

CLI 兼容性保留：

- `python run_pipeline.py <input>` 仍然可用。
- GUI 不会破坏命令行链路。

---

## 六、第三阶段：品牌、图标、封面图、快捷方式

### 6.1 品牌统一

软件名称最终统一为：

- `Slide Maker`

统一覆盖了：

- 窗口标题
- 标题栏品牌文案
- 侧边栏品牌文案
- 应用名
- 打包产物名
- 桌面快捷方式名
- UI 内部旧文案

相关核心文件：

- `D:\maker\services\app_models.py`
- `D:\maker\ui_app.py`
- `D:\maker\ui\title_bar.py`
- `D:\maker\ui\sidebar.py`
- `D:\maker\build.ps1`

### 6.2 封面图

首页两张主卡的封面图经过替换，当前由以下配置统一管理：

- `D:\maker\ui\cover_config.py`

曾使用仓库中更干净的测试图作为封面来源，便于先把 UI 跑起来，再等待正式物料替换。

### 6.3 图标设计与更新

图标资源文件：

- `D:\maker\assets\slide_maker_icon.png`
- `D:\maker\assets\slide_maker_icon.ico`

图标演进过程如下：

- 先做了一版现代风格图标。
- 用户认为过于复杂、外圈不好看。
- 后续重新设计成更简约的版本。
- 删除了外围杂色，只保留主体矩形。

图标接入位置：

- `D:\maker\ui_app.py`
- `D:\maker\ui\title_bar.py`
- `D:\maker\build.ps1`
- 桌面快捷方式

### 6.4 桌面快捷方式

本次对话中创建并持续更新了桌面快捷方式。

当前快捷方式路径：

- `C:\Users\lewis\Desktop\Slide Maker.lnk`

快捷方式演进过程：

- 最初创建了桌面快捷方式。
- 后续为避免弹 PowerShell，改成使用 `pythonw.exe`。
- 软件更名后，快捷方式名称也同步改成 `Slide Maker`。
- 图标更新后，快捷方式图标也同步刷新。

---

## 七、第四阶段：无控制台启动与隐藏 worker

### 7.1 启动时不再弹 PowerShell / 黑框

用户明确要求启动软件时不出现 PowerShell。为此做了两层处理：

- 桌面快捷方式改为使用 `pythonw.exe` 启动。
- GUI 内部的真实转换 worker 不再在主界面进程里直接跑，而是改成隐藏子进程。

### 7.2 GUI worker 通信协议

核心文件：

- `D:\maker\ui\main_window.py`
- `D:\maker\gui_conversion_runner.py`

演进过程：

- 早期 worker 依赖 stdout/stderr 传递 GUI 消息。
- 在 `PyInstaller --windowed` 模式下，这种方式不稳定。
- 后续改为文件通道协议：
  - `GUI_PROGRESS`
  - `GUI_RESULT`
  - `GUI_ERROR`
- 通过 `channel-file` 让 GUI 与 worker 通信。

这解决了打包版无控制台模式下的 GUI 通信问题。

---

## 八、第五阶段：状态面板、路径显示、乱码与小窗口布局修复

### 8.1 删除执行日志面板

用户明确要求：

- 不要在 GUI 中展示执行日志板块。

因此当前界面只保留：

- 当前阶段
- 进度条
- 输入文件
- 输出文件
- 结果摘要
- 操作按钮

诊断日志仍然保留在本地隐藏目录，便于排障：

- `%LOCALAPPDATA%\SlideMaker\logs`

### 8.2 结果摘要上方板块的乱码 / 折叠问题

用户后来指出：

- 结果摘要上面的输入/输出板块出现乱码和显示错乱。

实际定位结果：

- 不是字符编码本身出错，而是窄区域里长路径强行换行、文字叠压，看起来像乱码。

修复方式：

- 放弃容易被挤坏的自绘文字标签。
- 改为只读的路径输入框组件 `PathField`。
- 支持完整路径 tooltip。
- 用 `QScrollArea` 包住整个右侧状态面板内容，避免小窗口时内容挤坏。

核心文件：

- `D:\maker\ui\status_panel.py`

### 8.3 界面文案乱码源头整理

在排查过程中还发现：

- 有些文件在 PowerShell 里查看时会显示成乱码样式。
- 但 Python 按 UTF-8 读取时源码内容是正常的。

因此最终处理策略不是盲目重写所有文件编码，而是：

- 以 Python 真实读取结果为准。
- 对确实需要更新的用户可见文本继续按 UTF-8 正常维护。
- 重新打包，确保 `dist` 使用的是当前源码，而不是旧构建残留。

---

## 九、第六阶段：设置页、离线偏好系统和“提示词入口”

### 9.1 离线偏好系统的设计原则

用户希望加入类似“提示词”的入口，让用户在不满意时能说出要求，但又要求：

- 必须离线
- 必须能在别人的电脑上使用
- 不依赖云端 AI

因此最终没有做“伪 AI 对话框”，而是做成了离线结构化偏好系统。

### 9.2 当前偏好入口

核心文件：

- `D:\maker\ui\preferences_panel.py`
- `D:\maker\services\app_models.py`

当前支持的主偏好选项：

- `优先还原版式`
- `优先文字清晰`
- `优先背景干净`
- `优先转换速度`

另外还提供：

- 一段补充备注文本框

补充备注不会联网，也不会调用云模型，而是做本地关键词映射。

### 9.3 当前设置页结构

核心文件：

- `D:\maker\ui\main_window.py`
- `D:\maker\ui\settings_store.py`
- `D:\maker\services\app_models.py`

当前设置页分组包括：

- 通用
- 输出
- 转换
- 高级

### 9.4 用户问过“这些设置是不是摆设”

用户后续专门追问：

- `默认渲染模式`
- `PDF 渲染质量`
- `背景净化强度`
- `文字模式`
- `优先还原版式`
- `优先背景干净`
- `优先文字清晰`
- `优先转换速度`

这些是不是假的。

经过审计，结论如下：

- 这些选项都是真实生效的，不是填充版面。
- 它们会进入真实转换参数，而不是只改文案。

### 9.5 每个真实设置当前如何运作

#### `默认渲染模式`

作用：

- 决定更偏向 `Node 高保真排版` 还是直接保留 `Python 兼容输出`。

结果：

- `高保真优先`：优先走 Node。
- `兼容优先`：直接使用 Python 生成的 PPTX。

#### `PDF 渲染质量`

作用：

- 影响 `extract_pdf.py` 在把 PDF 栅格化为图片时的 DPI。

结果：

- DPI 越高，页面越清晰，但速度和内存压力越高。

#### `背景净化强度`

作用：

- 影响文字区域掩膜扩张、颜色容差、膨胀核大小和迭代次数。

结果：

- `标准`：更保守。
- `强力`：去字更狠，但误伤背景细节的概率更高。

#### `文字模式`

作用：

- 影响字体缩放和文本框安全边界。

结果：

- `忠实还原`：更接近原始版式。
- `更清晰`：字更大，框更宽，更强调阅读性。

#### `优先还原版式`

作用：

- 会把任务级偏好覆盖成更倾向高保真与忠实还原。

#### `优先背景干净`

作用：

- 会把背景净化切到更强的参数组。

#### `优先文字清晰`

作用：

- 会把文字模式切到更清晰的参数组。

#### `优先转换速度`

作用：

- 会把渲染模式切向兼容模式。
- 会把 PDF DPI 压低到更快的级别。

### 9.6 被删掉的无关设置

对话过程中也做过一次收敛：

- 删除了“启动时默认进入首页”这类不影响转换质量的展示型选项。
- 固定应用默认从首页打开。

原则是：

- 不保留纯摆设开关。
- 保留的设置必须能落到真实行为或真实输出效果上。

---

## 十、第七阶段：窗口视觉、黑边、Win11 风格与外边缘圆角

### 10.1 先前做过的窗口风格调整

本次对话中已经做过一轮 Win11 风格收敛，核心文件包括：

- `D:\maker\ui\title_bar.py`
- `D:\maker\ui\main_window.py`
- `D:\maker\ui\theme.py`

这些调整包括：

- 标题栏高度缩减。
- 按钮尺寸和图标尺寸收紧。
- 标题栏拖动优先调用系统 `startSystemMove()`。
- 最大化时自动切换最大化/还原按钮图标。
- 最大化时移除内部圆角。

### 10.2 去掉黑边

用户曾指出应用边缘有明显黑边。

当时的处理是：

- 统一窗口背景和主面板背景。
- 去掉外层多余的黑底显露。

### 10.3 最新的外边缘圆角处理

用户最后进一步要求：

- “将窗口边缘圆角化”

为此当前实现改成了真正的外层圆角思路：

- 顶层窗口启用 `WA_TranslucentBackground`
- `QMainWindow` 背景改成透明
- 外层根布局增加常规状态下的边距
- 主内容面板 `AppSurface` 自己承担视觉圆角
- 最大化时自动把外边距清零
- 最大化时去掉主面板和标题栏的圆角

相关核心文件：

- `D:\maker\ui\main_window.py`
- `D:\maker\ui\theme.py`

当前效果目标是：

- 正常窗口状态显示圆角外边缘
- 最大化时像原生窗口一样贴边

---

## 十一、第八阶段：OCR、WinRT fallback、RapidOCR 和去字 / 背景修复链路

### 11.1 OCR 后端演进

核心文件：

- `D:\maker\ocr_engine.py`
- `D:\maker\winrt_ocr_engine.py`

演进过程如下：

- 初始链路优先用 `RapidOCR`。
- 打包环境里 `onnxruntime` 出现问题后，补加了 `Windows OCR` fallback。
- 当前源码和便携 worker 的优先级是：
  - 先尝试 `RapidOCR`
  - RapidOCR 不可用时再回退到 `WinRT OCR`
  - 两者都不行时才降级为纯图片型输出

### 11.2 背景修复与去字链路

核心文件：

- `D:\maker\image_processor.py`
- `D:\maker\inpainting_engine.py`
- `D:\maker\main.py`

当前背景修复链路包括：

- 生成文字区域智能掩膜
- 优先调用 `LaMa AI`
- 如果 LaMa 不可用，再回退 `OpenCV Telea`

在本次对话中还追加了新的日志输出：

- `[*] Background repair backend: LaMa AI`
- `[*] Background repair backend: OpenCV Telea`

这样在验证时可以清楚看到当前到底走的是哪一套背景修复后端。

---

## 十二、第九阶段：构建脚本的多轮演进

### 12.1 早期构建目标

早期 `build.ps1` 主要目标是：

- 把 GUI 入口打包为 `Slide_Maker.exe`
- 使用 `--windowed`
- 保留 Node 运行时和高保真排版资源

### 12.2 曾经出现的“为了缩包而误伤功能”

在对话中确实发生过一次错误方向：

- 为了缩减安装包体积，构建脚本排除了 `simple_lama_inpainting`
- 也排除了 `torch`
- 同时没有把 `models\big-lama.pt` 纳入分发包

这会导致：

- 分发包里 AI 去字 / 背景修复能力被削弱
- 只能回退到 OpenCV

用户后来明确要求不能为了缩体积而削弱功能，因此这部分后来被纠正。

### 12.3 后续恢复的构建内容

`build.ps1` 后来补回了：

- `models`
- `simple_lama_inpainting`
- `torch`
- `runtime\node.exe`
- `pptx-project\node_modules`
- `WinRT OCR` 相关依赖
- `MSVCP140` 系列运行库

### 12.4 发现 PyInstaller frozen worker 的深层 DLL 问题

虽然把模型和依赖重新打进了包里，但实际验证发现：

- PyInstaller frozen 的 `--worker` 路径里
  - `onnxruntime`
  - `torch`

仍然存在 DLL 初始化问题。

具体现象包括：

- `RapidOCR unavailable`
- `Failed to use LaMa AI, falling back to OpenCV inpaint`
- `Error loading c10.dll`
- `onnxruntime_pybind11_state` 初始化失败

### 12.5 最终改成“GUI + 便携 Python worker”的混合分发结构

这是本次对话最后的关键架构调整，也是当前推荐交付结构。

当前 `dist\Slide_Maker` 中不仅包含：

- `Slide_Maker.exe`
- `_internal`

还额外包含：

- `portable_python`
- `portable_site_packages`
- `portable_app`

含义如下：

- `Slide_Maker.exe`
  - 用于无控制台启动 GUI
- `portable_python`
  - 包内便携 Python 解释器
- `portable_site_packages`
  - 包内便携 Python 依赖
- `portable_app`
  - 包内便携 worker 源码、模型、Node 运行时、布局引擎等

最终 GUI worker 逻辑改为：

- 在 frozen GUI 环境里优先查找并调用 `portable_python`
- 用便携 Python 运行 `portable_app\ui_app.py --worker`
- 通过 `channel-file` 与 GUI 通信

这样可以避开 PyInstaller frozen worker 的 DLL 问题，同时保留：

- GUI 可执行文件的无控制台体验
- 分发包不依赖目标机本地 Python

这是当前真正可工作的分发方案。

---

## 十三、第十阶段：打包版功能回归与真实性验证

本次对话中不止做了代码改动，也反复做了运行验证。下面按时间顺序概括已经明确跑过的关键验证。

### 13.1 早期源码 / 打包验证

曾经验证通过过：

- `ui_app.py --demo`
- `ui_app.py` 实模式启动
- 打包版 GUI 启动
- 打包版图片转 PPTX
- 打包版 PDF 转 PPTX
- 打包版高保真图片转换
- 打包版高保真 PDF 转换

### 13.2 源码下 AI 去字验证

命令行验证过源码环境中：

- `RapidOCR` 正常
- `LaMa AI` 正常
- `Node 高保真排版` 正常

对应验证文件之一：

- `D:\maker\test\source_ai_verify.pptx`

从日志中已经确认出现过：

- `[*] OCR backend: rapidocr`
- `[*] Background repair backend: LaMa AI`
- `[*] Using Node runtime: D:\maker\runtime\node.exe`

### 13.3 frozen 直接 worker 路径的排障性验证

为了定位问题，曾经用打包后的 `Slide_Maker.exe --worker` 直接跑过多次。

这些测试生成过一些中间验证文件，例如：

- `D:\maker\test\dist_lama_verify_ascii.pptx`
- `D:\maker\test\dist_lama_verify_kmp.pptx`
- `D:\maker\test\dist_lama_verify_after_preload.pptx`
- `D:\maker\test\dist_lama_verify_after_msvc.pptx`

这些测试的价值主要是定位问题，而不是最终交付路径。定位结论是：

- frozen 直接 worker 路径仍然存在 `torch/onnxruntime` DLL 初始化问题
- 因此最终不再依赖这条路径承担真实转换

### 13.4 最终便携 worker 路径验证

最终验证通过的关键结果是：

- `D:\maker\dist\Slide_Maker\portable_python\python.exe`
- `D:\maker\dist\Slide_Maker\portable_app\ui_app.py --worker`

已在分发目录结构内跑通，并确认：

- `RapidOCR` 正常
- `LaMa AI` 正常
- `Node 高保真排版` 正常

对应验证文件：

- `D:\maker\test\portable_worker_verify.pptx`

该次验证日志明确出现了：

- `[*] OCR backend: rapidocr`
- `[*] Background repair backend: LaMa AI`
- `[*] Using Node runtime: D:\maker\dist\Slide_Maker\portable_app\runtime\node.exe`

这说明当前最终分发结构下，真实功能已经恢复完整，不再是为了缩包而阉割后的版本。

---

## 十四、当前分发目录结构

当前最终分发目录是：

- `D:\maker\dist\Slide_Maker`

关键内容：

- `D:\maker\dist\Slide_Maker\Slide_Maker.exe`
- `D:\maker\dist\Slide_Maker\_internal`
- `D:\maker\dist\Slide_Maker\portable_python`
- `D:\maker\dist\Slide_Maker\portable_site_packages`
- `D:\maker\dist\Slide_Maker\portable_app`

当前目录总大小大约为：

- `3.86 GB`

这比早期瘦身版大很多，但这是有意接受的结果，因为用户明确要求：

- 不允许通过删减真实功能来换取更小体积

---

## 十五、当前关键文件清单与职责

下面列出本次对话中最核心的文件及其职责，方便后续维护。

### GUI 与交互

- `D:\maker\ui_app.py`
  - 桌面应用入口
  - worker 模式入口
  - DLL 路径与预加载初始化

- `D:\maker\ui\main_window.py`
  - 主窗口
  - 页面切换
  - worker 启动
  - frozen GUI 下优先切到便携 worker

- `D:\maker\ui\title_bar.py`
  - 自定义标题栏
  - 最小化 / 最大化 / 关闭
  - Win11 风格拖动

- `D:\maker\ui\sidebar.py`
  - 左侧导航

- `D:\maker\ui\status_panel.py`
  - 右侧任务状态区
  - 输入/输出路径展示
  - 结果摘要

- `D:\maker\ui\preferences_panel.py`
  - 离线偏好面板

- `D:\maker\ui\theme.py`
  - 全局样式
  - 圆角、深色主题、标题栏/侧边栏/按钮样式

### 设置与参数模型

- `D:\maker\services\app_models.py`
  - 全局设置模型
  - 任务偏好模型
  - 偏好到真实转换参数的映射

- `D:\maker\ui\settings_store.py`
  - `QSettings` 持久化

### 转换服务与运行时

- `D:\maker\services\conversion_service.py`
  - GUI / CLI 统一转换入口
  - 阶段进度控制
  - 高保真 / 兼容模式切换

- `D:\maker\services\runtime_env.py`
  - 运行时根目录判断
  - 图标、Node、DLL 搜索路径处理

- `D:\maker\gui_conversion_runner.py`
  - 隐藏 worker 入口
  - GUI 协议消息输出

### OCR / 去字 / 背景修复

- `D:\maker\ocr_engine.py`
  - OCR 统一入口
  - RapidOCR 与 WinRT fallback

- `D:\maker\winrt_ocr_engine.py`
  - Windows OCR fallback

- `D:\maker\image_processor.py`
  - 文字掩膜
  - 去字 / 背景修复
  - 背景修复后端日志

- `D:\maker\inpainting_engine.py`
  - LaMa AI 背景修复

- `D:\maker\main.py`
  - 图片到 PPTX 主处理流程

- `D:\maker\extract_pdf.py`
  - PDF 栅格化为图片页

### 构建与资源

- `D:\maker\build.ps1`
  - GUI 打包
  - Node 运行时打包
  - 便携 Python / 便携依赖 / 便携源码复制

- `D:\maker\assets\slide_maker_icon.ico`
- `D:\maker\assets\slide_maker_icon.png`
  - 软件图标

---

## 十六、当前软件怎样预览和使用

### 16.1 源码预览界面

只预览界面，不执行真实转换：

```powershell
D:\maker\venv\Scripts\python.exe D:\maker\ui_app.py --demo
```

### 16.2 源码真实运行

打开桌面 GUI 并手动测试：

```powershell
D:\maker\venv\Scripts\python.exe D:\maker\ui_app.py
```

### 16.3 打包版 GUI

直接运行：

- `D:\maker\dist\Slide_Maker\Slide_Maker.exe`

或者双击桌面快捷方式：

- `C:\Users\lewis\Desktop\Slide Maker.lnk`

### 16.4 样例文件

本次对话中反复使用过的样例包括：

- `D:\maker\test\Quiz 1.pdf`
- `D:\maker\test\未命名的设计.png`
- `D:\maker\test\Slide1.JPG`
- `D:\maker\test\Slide2.JPG`

---

## 十七、当前已知边界与真实说明

这一节只写真实情况，不做粉饰。

### 17.1 当前真正可交付的分发路径

当前真正推荐的分发使用方式是：

- 用户双击 `Slide_Maker.exe`
- GUI 启动后，真实转换优先走包内便携 Python worker

这是当前已经验证过能跑通 `RapidOCR + LaMa AI + Node 高保真` 的路径。

### 17.2 当前不再推荐依赖的路径

`PyInstaller` frozen 的直接 `--worker` 路径仍然有以下问题：

- `torch` DLL 初始化问题
- `onnxruntime` DLL 初始化问题

因此当前没有再把它作为真实转换主路径，而是保留 GUI EXE，只把转换执行迁移到包内便携 Python。

### 17.3 为什么现在分发包这么大

当前体积增大不是意外，而是为了满足以下要求：

- 不削弱真实功能
- 不依赖目标机本地 Python
- 保留高保真 Node
- 保留 RapidOCR
- 保留 LaMa AI

因此包内现在同时包含：

- PyInstaller GUI
- Node runtime
- 便携 Python
- 便携 site-packages
- 便携项目源码
- OCR / AI / 模型资源

### 17.4 本次对话后续新增的 PDF 大页面修复

在文档初版生成之后，又新增修复了一类真实用户 bug：

- 某些高 DPI PDF 页面在生成 PPTX 时会报错：
  - `value must be in range(914400, 51206400) (1-56 inches)`

根因是：

- 之前会把高 DPI 渲染出来的像素尺寸按 96 DPI 的屏幕图方式直接映射到 PPT 页面尺寸。
- 当用户把 PDF 渲染质量设到 300 DPI 时，页面像素尺寸会非常大。
- `python-pptx` 对单边尺寸有 56 英寸上限，因此会直接报错。

修复内容：

- `ppt_generator.py`
  - 改为按真实 `canvas_dpi` 计算页面英寸尺寸。
  - 超过 PowerPoint 上限时，整页按比例缩放。
  - 文字框坐标和尺寸与页面一起等比缩放。
- `main.py`
  - 新增 `canvas_dpi` 参数传递。
  - 当页面超限被缩放时输出日志说明。
- `services/conversion_service.py`
  - 对 PDF 输入自动把 `canvas_dpi` 设为当前 `pdf_dpi`。
  - 图片输入仍默认按 96 DPI 处理。

另外还顺带修复了大页面 LaMa 运行过慢的问题：

- 对超大页面不再强行跑 LaMa AI。
- 超过阈值时会直接切到 `OpenCV Telea`，避免 CPU 上尝试分配几十 GB 内存而长时间卡死。

验证结果：

- 单页 PDF 路径：
  - `D:\maker\test\Barcelona_Redefined_page1_fixed_via_uiapp_retry.pptx`
- 单页大图路径：
  - `D:\maker\test\barcelona_page1_fixed.pptx`
  - `D:\maker\test\barcelona_page1_portable_fixed.pptx`

这些验证说明：

- 这类“页面尺寸超过 56 英寸上限”的 bug 已经修复。
- 当前 `dist` 中实际被 GUI 使用的便携 worker 也已经同步了这一修复。

---

## 十八、本次对话里的关键问题与最终处理结论

### 问题 1：启动会弹 PowerShell

最终结论：

- 已修复
- 通过 `pythonw.exe` 快捷方式和隐藏 worker 处理

### 问题 2：界面要像参考图一样现代化

最终结论：

- 已完成首版实现
- 不是像素级照抄，但整体结构和气质已经对齐

### 问题 3：执行日志太乱，不要展示

最终结论：

- 已删除界面展示
- 仅保留隐藏诊断日志

### 问题 4：设置页是不是假的

最终结论：

- 经审计后只保留真实设置
- 这些设置会实际影响转换链路

### 问题 5：右侧板块乱码 / 显示错乱

最终结论：

- 已修复
- 改为只读路径框 + 滚动容器

### 问题 6：图标不好看

最终结论：

- 已重做为更简约版本

### 问题 7：为了缩包删掉了功能

最终结论：

- 确实发生过误伤
- 已恢复完整功能
- 最终用“GUI EXE + 便携 Python worker”保证分发能力

### 问题 8：窗口边缘需要圆角

最终结论：

- 已在当前源码中实现
- 正常窗口状态显示圆角外边缘
- 最大化时自动去圆角并贴边

---

## 十九、本次对话里生成或验证过的重要文件

这一节列出本次对话中明确提到并实际用于验证或输出的重要文件，便于后续排查历史结果。

- `D:\maker\test\source_high_fidelity_result.pptx`
- `D:\maker\test\dist_worker_verify_image.pptx`
- `D:\maker\test\dist_worker_verify_pdf.pptx`
- `D:\maker\test\dist_worker_verify_high_fidelity.pptx`
- `D:\maker\test\dist_worker_verify_pdf_high_fidelity.pptx`
- `D:\maker\test\source_ai_verify.pptx`
- `D:\maker\test\dist_lama_verify_ascii.pptx`
- `D:\maker\test\dist_lama_verify_kmp.pptx`
- `D:\maker\test\dist_lama_verify_after_preload.pptx`
- `D:\maker\test\dist_lama_verify_after_msvc.pptx`
- `D:\maker\test\portable_worker_verify.pptx`

这些文件里有一部分是成功验证当前正式链路，有一部分是排查历史问题时留下的诊断性输出。最终应以最新的：

- `portable_worker_verify.pptx`

这一类便携 worker 验证结果为准。

---

## 二十、当前最终状态

截至本次对话结束时，项目的最终状态可以概括为：

- 已经拥有可用的 `Slide Maker` 桌面 GUI。
- 当前 GUI 能在无控制台情况下启动。
- 当前首页、设置页、状态区、偏好区、快捷方式、图标、品牌文案都已落地。
- `PDF 转 PPTX` 和 `图片转 PPTX` 两个入口已接通。
- 离线偏好系统已落地，并真实影响转换参数。
- 原先为了缩包而误伤的 AI 功能已经恢复。
- 分发结构已经升级为：
  - GUI 使用 PyInstaller EXE
  - 真正转换使用分发包里的便携 Python worker
- 这条最终分发链路已经验证可以跑通：
  - `RapidOCR`
  - `LaMa AI`
  - `Node 高保真排版`

如果后续继续开发，建议优先沿用当前这套结构，而不是再退回到只依赖 frozen `--worker` 的模式。
