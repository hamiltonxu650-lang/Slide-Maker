# Slide Maker 完整研发总记录

## 1. 文档定位

这份文档是当前项目的总说明书，用来替代此前两份已经出现编码混乱的历史文档：

- `D:\maker\Project_Development_Log.md`
- `D:\maker\Slide_Maker_Conversation_Full_Log.md`

本文件同时整合以下来源：

- 你最早提供的项目开发日志
- 仓库中已有的 `PROJECT_SUMMARY.md`
- 当前源码结构与运行方式
- 本次完整对话里所有需求、实现、修复、构建与验证结果

目标只有一个：让任何接手这个项目的人，不依赖聊天记录，也能看懂这款软件从最初原型到现在 `Slide Maker` 桌面版的完整开发过程。

---

## 2. 产品目标

`Slide Maker` 的目标不是简单“把图片塞进 PPT”。

它要解决的是更难的问题：

- 输入一张图片、一个 PDF，或者以后更多格式的页面内容
- 自动识别其中的文字和布局
- 尽可能清除原图中的文字痕迹
- 尽可能保留原背景视觉
- 最终输出一个可以继续编辑的 `.pptx`

这个目标可以拆成四条硬要求：

- 文字要尽量可编辑，而不是只导出成整页大图
- 背景要尽量干净，不能明显残留原字
- 排版要尽量接近原始页面，而不是全部打乱重排
- 软件要能离线运行，并最终可在 Windows 上分发给别人使用

---

## 3. 项目最早的技术路线

在本次对话开始之前，项目已经经历过一轮较深的原型开发。最早的路线不是 PyQt 桌面软件，而是以脚本链路为主。

最早的核心模块包括：

- `main.py`
- `ocr_engine.py`
- `image_processor.py`
- `ppt_generator.py`
- `extract_pdf.py`
- `pptx-project/layout_engine.js`

最早的目标已经涵盖了两个真实输入方向：

- `PDF -> PPTX`
- `PNG/JPG -> PPTX`

原始链路大致是：

1. 如果输入是 PDF，先把 PDF 拆成图片页
2. 对每页图片做 OCR
3. 根据 OCR 结果估算文字框位置、文字颜色、字号
4. 对背景做去字和修复
5. 先生成一版 Python PPTX
6. 如果高保真链路可用，再交给 Node 版排版引擎重排输出

---

## 4. 原始原型阶段的关键迭代

### 4.1 早期 OCR 方案

项目最初尝试过更早的 OCR 路线，后来逐步演进：

- 第一阶段曾用过 `pytesseract`
- 后来升级到 `PaddleOCR`
- 再后来为了减小依赖体积和便于分发，切换到 `RapidOCR + ONNX Runtime`

切换到 `RapidOCR` 的主要原因是：

- 保持本地离线
- OCR 精度仍可接受
- 依赖体积比 Paddle 系路线更轻
- 更适合作为桌面软件内部能力分发

### 4.2 英文连词和空格修复

OCR 识别英文时，出现过典型问题：多个英文单词被黏在一起。

为了解决这个问题，项目加入了 `wordninja`：

- 对连续英文字符串做概率切分
- 尽量恢复合理空格
- 同时保留原始大小写

这一步的价值是：

- 提升英文文本在 PPT 中的可读性
- 减少 OCR 输出的“整串英文粘连”

### 4.3 中文路径兼容

项目曾遇到 Windows 下带中文文件名的图片无法正常读取的问题，例如：

- `未命名的设计.png`

后续统一将图像读取方式改为：

- `cv2.imdecode(np.fromfile(...), cv2.IMREAD_COLOR)`

这样做的原因是：

- `cv2.imread()` 在 Windows 中文路径下并不稳定
- `np.fromfile + imdecode` 对中文路径更稳

这条修复现在仍然是项目的重要兼容性基础。

### 4.4 背景去字与修复

项目在背景修复上经历过几轮路线选择：

- 早期只用 OpenCV 修补
- 后续引入了 `LaMa AI`
- 当前策略是优先 LaMa，必要时降级到 OpenCV Telea

这条链路的目标不是“完全重新设计幻灯片”，而是尽量在原背景基础上把文字抹干净，再把可编辑文字覆盖回去。

### 4.5 高保真排版引擎

Python 侧的 PPT 生成能力有限，尤其是在复杂排版、自动换行、文本框尺寸控制方面不够稳定。

因此项目后面加入了 Node 侧的高保真引擎：

- 使用 `pptxgenjs`
- 通过 `pptx-project/layout_engine.js` 接收 Python 导出的结构化 OCR 数据
- 按更严格的坐标和文本框策略重建 PPT

因此项目从架构上形成了双路线：

- Python 兼容输出
- Node 高保真输出

---

## 5. 本次对话开始时的状态

在你发来参考图之前，项目已经基本能完成：

- `PDF -> PPTX`
- `PNG/JPG -> PPTX`

但缺少真正可交付的桌面软件形态，主要问题包括：

- 没有完整 GUI
- 没有可持久化设置页
- 没有统一产品品牌
- 没有桌面快捷方式
- 启动会出现 PowerShell / 控制台问题
- 打包后的分发结构还不稳定
- 缺少真正面向终端用户的操作界面

这也是本次对话后半段的主要开发目标。

---

## 6. 本次对话中的产品化目标

本次对话里，你逐步把项目从“脚本工具”推到了“桌面软件产品”阶段。明确提出过的需求包括：

- 按参考图做现代深色桌面 UI
- 首页用大卡片承载真实功能
- 当前只接通 `PDF 转 PPTX` 和 `图片转 PPTX`
- 其他入口先做占位，后续再扩展
- 创建桌面快捷方式
- 启动时不能弹 PowerShell
- 软件名改为 `Slide Maker`
- 删除执行日志显示区
- 做设置页，而且设置不能是摆设
- 加入离线的“提示词/偏好入口”
- 图标要重做，且要简约
- 窗口视觉要更接近 Win11
- 修复界面乱码、路径显示、尺寸、进度和转换 bug
- 最终既要能在 Windows 分发，也要能把源码带去 Mac 上继续编辑和运行

---

## 7. 本次对话完成的 GUI 架构

### 7.1 新增桌面入口

本次对话新增并稳定下来的桌面入口是：

- `D:\maker\ui_app.py`

它负责：

- 启动 `PyQt6` 桌面界面
- 在 `--demo` 模式下只预览 UI
- 在 `--worker` 模式下作为隐藏转换 worker 入口

### 7.2 新增 UI 子模块

桌面界面被拆成多个模块：

- `D:\maker\ui\main_window.py`
- `D:\maker\ui\title_bar.py`
- `D:\maker\ui\sidebar.py`
- `D:\maker\ui\status_panel.py`
- `D:\maker\ui\preferences_panel.py`
- `D:\maker\ui\cards.py`
- `D:\maker\ui\theme.py`
- `D:\maker\ui\cover_config.py`
- `D:\maker\ui\settings_store.py`

这些模块分别承担：

- 主窗口结构
- 自定义标题栏
- 左侧导航
- 右侧状态区
- 偏好设置区
- 首页卡片
- 主题与视觉样式
- 首页封面图配置
- `QSettings` 持久化

### 7.3 当前首页结构

当前首页结构是：

- 左侧导航栏
- 顶部自定义标题栏
- 中部左侧内容区
- 中部右侧任务状态区

首页左侧内容区包含：

- 软件品牌标题
- 两张真实功能主卡
- 一个“转换偏好”面板
- 六个后续扩展入口卡片

当前真实接通的两张主卡是：

- `PDF 转 PPTX`
- `图片转 PPTX`

当前占位但不触发真实转换的卡片包括：

- Word
- Excel
- Markdown
- TXT
- 网页
- 批量导入

---

## 8. 当前品牌、图标和视觉统一

### 8.1 软件品牌

软件品牌统一为：

- `Slide Maker`

统一覆盖的地方包括：

- 窗口标题
- 标题栏文案
- 侧边栏品牌文案
- 应用名
- 桌面快捷方式名
- 打包产物名
- 界面内部旧名称

相关核心文件包括：

- `D:\maker\services\app_models.py`
- `D:\maker\ui_app.py`
- `D:\maker\ui\title_bar.py`
- `D:\maker\ui\sidebar.py`
- `D:\maker\build.ps1`

### 8.2 图标

图标资源目前位于：

- `D:\maker\assets\slide_maker_icon.png`
- `D:\maker\assets\slide_maker_icon.ico`

图标在本次对话中重做过不止一次，最终方向是：

- 更简约
- 去掉多余外圈和杂色
- 保留主体矩形轮廓和现代感

### 8.3 封面图

首页两张功能主卡的封面图由下列配置统一管理：

- `D:\maker\ui\cover_config.py`

本次对话里已经替换为更适合当前 UI 的本地示例图。

---

## 9. 当前桌面快捷方式

桌面快捷方式路径是：

- `C:\Users\lewis\Desktop\Slide Maker.lnk`

它经历过几个阶段：

- 最早创建快捷方式
- 后来为避免 PowerShell 弹窗改为 `pythonw.exe`
- 随着软件名修改改名为 `Slide Maker`
- 随着图标更新同步刷新图标

当前快捷方式的核心作用是：

- 直接启动源码版 GUI
- 不弹控制台
- 方便继续开发和即时预览

---

## 10. 当前转换服务层

### 10.1 统一服务层

本次对话中把底层转换逻辑抽到了统一服务层：

- `D:\maker\services\conversion_service.py`

它负责：

- 统一 GUI 和 CLI 的转换调用方式
- 统一输入类型判断
- 统一输出路径处理
- 统一分阶段进度回调
- 统一日志记录
- 统一高保真与兼容模式选择

### 10.2 当前支持的输入类型

当前真实支持的输入类型只有两类：

- `pdf`
- `image`

其中图片目前只支持：

- `.png`
- `.jpg`
- `.jpeg`

### 10.3 CLI 兼容

CLI 并没有被桌面化改造破坏，依然可以单独运行：

- `D:\maker\run_pipeline.py`

这意味着项目仍保留了脚本工具的基础能力。

---

## 11. 当前离线偏好系统

### 11.1 为什么做这个功能

你提出过一个重要要求：

- 如果用户对输出不满意，希望能表达“哪里不满意”
- 但这个能力必须离线
- 不能依赖云端 AI
- 不能只在本机生效

因此最终没有做“联网大模型提示词框”，而是做了结构化的离线偏好系统。

### 11.2 偏好入口

当前偏好面板位于：

- `D:\maker\ui\preferences_panel.py`

对应的数据模型位于：

- `D:\maker\services\app_models.py`

### 11.3 当前偏好选项

当前四个主偏好是：

- `默认`
- `优先文字清晰`
- `优先背景干净`
- `优先转换速度`

其中“默认”原来叫“优先还原版式”，后来按你的要求改成了“默认”。

### 11.4 补充备注

除了单选偏好，还支持一段补充备注文本。

备注不会联网，也不会调用云端 AI，而是只做本地关键词映射。

例如会识别这类词：

- 排版
- 对齐
- 还原
- 清晰
- 字体
- 背景
- 水印
- 速度

### 11.5 这些偏好是否真实生效

这些不是摆设，都会真实影响转换参数。

具体影响如下：

- `默认`
  - 更偏向高保真渲染
  - 更偏向忠实还原原始排版

- `优先文字清晰`
  - 提高字体缩放
  - 增大文本框安全边界

- `优先背景干净`
  - 使用更强的背景净化参数
  - 增强去字遮罩范围

- `优先转换速度`
  - 优先走兼容模式
  - 降低 PDF 栅格化 DPI

这些映射在：

- `D:\maker\services\app_models.py`

---

## 12. 当前设置页

### 12.1 设置页位置

当前设置页主要由以下文件负责：

- `D:\maker\ui\main_window.py`
- `D:\maker\ui\settings_store.py`
- `D:\maker\services\app_models.py`

### 12.2 设置页分组

当前设置页分成四组：

- 通用
- 输出
- 转换
- 高级

### 12.3 当前保留的有效设置

在本次对话中，已经清理过“摆设设置”，只保留了真正有效的选项。当前有效设置包括：

- 记住最近任务
- 保存位置策略
- 默认文件名后缀
- 完成后自动打开 PPTX
- 完成后自动打开文件夹
- 默认渲染模式
- PDF 渲染质量
- 背景净化强度
- 文字模式
- 启用隐藏诊断日志

### 12.4 设置如何落地

这些设置分别影响：

- GUI 行为
- 输出路径策略
- 转换参数
- 日志开关

并通过 `QSettings` 持久化保存。

---

## 13. 当前状态面板

右侧状态区的核心文件是：

- `D:\maker\ui\status_panel.py`

当前它只展示这些信息：

- 当前阶段
- 进度条
- 各阶段状态
- 输入文件
- 输出文件
- 结果摘要
- 再次转换 / 打开 PPTX / 打开文件夹

你曾明确要求删除“执行日志板块”，所以界面里已经不再显示滚动日志。

但诊断日志依然会写入本地目录，默认在：

- `%LOCALAPPDATA%\SlideMaker\logs`

---

## 14. 本次对话中的主要 UI 问题与修复

### 14.1 PowerShell / 控制台弹窗

你提出软件启动时会弹出 PowerShell 或黑框。

处理结果：

- 桌面快捷方式改用 `pythonw.exe`
- GUI 内部转换 worker 改为隐藏子进程
- frozen GUI 下也尽量避免控制台输出

### 14.2 结果区和路径显示错乱

你指出过右侧状态区中：

- 输入文件
- 输出文件
- 结果摘要上方模块

会在非全屏时出现叠字、看起来像乱码。

处理结果：

- 改成只读路径框
- 增加 tooltip
- 整个右侧状态区放入滚动区域
- 避免窄窗口下内容被压坏

### 14.3 执行结果乱码

你多次指出界面里出现了“乱码 bug”。

实际定位后发现有两种情况：

- 一部分是终端编码显示问题，不是源文件内容真的损坏
- 另一部分是长文本或路径在窄面板里被挤压，看起来像乱码

处理结果：

- 按 Python 真实读取结果核对源码
- 对用户可见文本持续做 UTF-8 维护
- 修复布局和路径显示方式

### 14.4 窗口边缘黑边与 Win11 风格

你要求：

- 去掉大黑边
- 更接近 Win11 风格
- 后续再把窗口边缘做圆角

处理结果：

- 调整外层边距
- 自定义标题栏支持更接近 Win11 的按钮和拖动逻辑
- 常规窗口下启用圆角外观
- 最大化时自动贴边并取消圆角

涉及文件：

- `D:\maker\ui\main_window.py`
- `D:\maker\ui\title_bar.py`
- `D:\maker\ui\theme.py`

---

## 15. 打包与分发架构的演进

### 15.1 最早的想法

最早的目标是把整个 GUI 打成一个 Windows 可执行目录。

主要构建脚本是：

- `D:\maker\build.ps1`

### 15.2 体积压缩导致的功能损伤

本次对话中一度为了减小体积，错误地排除了部分真实功能依赖，包括：

- `simple_lama_inpainting`
- `torch`
- LaMa 模型相关内容

这会直接削弱：

- AI 去字
- 背景修复

后来你明确要求不要为缩包而削弱功能，因此这部分已经恢复。

### 15.3 frozen worker 的 DLL 问题

虽然把依赖重新打进了包里，但 `PyInstaller` 直接冻结出来的 worker 仍然存在底层 DLL 问题，表现包括：

- `onnxruntime` 初始化失败
- `torch` 相关 DLL 初始化失败
- GUI worker 在 `--windowed` 模式下通信不稳定

### 15.4 最终采用的分发结构

当前最终采用的是混合结构：

- GUI 外壳仍然是 PyInstaller 生成的 `Slide_Maker.exe`
- 真正的转换任务优先交给包内的便携 Python worker 执行

当前分发目录核心结构是：

- `D:\maker\dist\Slide_Maker\Slide_Maker.exe`
- `D:\maker\dist\Slide_Maker\_internal`
- `D:\maker\dist\Slide_Maker\portable_python`
- `D:\maker\dist\Slide_Maker\portable_site_packages`
- `D:\maker\dist\Slide_Maker\portable_app`

这样做的好处是：

- 终端用户仍然双击 EXE 即可启动 GUI
- 真正转换时不依赖目标机器本地 Python
- 避开 frozen worker 直接加载复杂 DLL 的问题

### 15.5 当前 Windows 分发链路

当前 Windows 分发链路已经验证通过：

- GUI 启动
- 图片转 PPTX
- PDF 转 PPTX
- 高保真 Node 排版
- RapidOCR
- LaMa AI

---

## 16. 本次对话中的关键 bug 修复

### 16.1 `onnxruntime_pybind11_state` 失败

你曾遇到 GUI 转换时报：

- `onnxruntime_pybind11_state` DLL 初始化失败

这类问题最终没有继续强行依赖 frozen worker 解决，而是通过“GUI EXE + 便携 Python worker”架构绕开。

### 16.2 `wordninja` 打包后资源缺失

打包版一度出现 `wordninja` 资源问题，导致 OCR 导入链路不稳定。

后续已经做了容错和降级处理。

### 16.3 高保真 Node 运行时缺失

高保真模式要依赖 Node。

后续构建中已经把这些内容纳入或兼容：

- `runtime/node.exe`
- `pptx-project/node_modules`

并在运行时优先查找包内 Node。

### 16.4 PowerPoint 页面尺寸越界

你遇到过这个典型错误：

- `value must be in range(914400, 51206400) (1-56 inches)`

根因是：

- 高 DPI PDF 页面被错误地按屏幕 DPI 逻辑映射到 PPT 尺寸

修复结果：

- 根据真实 `canvas_dpi` 计算页面尺寸
- 超过 PowerPoint 上限时按比例整体缩放
- 文本框也跟着等比缩放

涉及文件：

- `D:\maker\ppt_generator.py`
- `D:\maker\main.py`
- `D:\maker\services\conversion_service.py`

### 16.5 大页面 LaMa 过慢或卡死

对超大页面继续跑 LaMa 会出现极慢甚至卡住的问题。

修复结果：

- 大页面达到阈值时跳过 LaMa
- 自动退到 OpenCV Telea

### 16.6 结果区上方模块“乱码”

这个问题本质是布局挤压，不是单纯字符损坏。

修复方式：

- 路径改为只读路径框
- 加入滚动区
- 避免路径挤成重叠文本

### 16.7 当前运行那一栏乱码

你后来又指出过“运行”区域显示异常。

处理方式：

- 将运行信息简化为更短的稳定文案
- 不再塞长句到窄卡片里

---

## 17. 本次对话中的性能优化

你提出当前生成速度偏慢，但又要求不牺牲原本质量。

本次对话中已经做了两项真实优化：

### 17.1 OCR 分析图降采样，但不降最终输出质量

实现位置：

- `D:\maker\main.py`

做法是：

- 保留原始高分辨率图做最终背景和 PPT 输出
- 仅为 OCR 识别临时生成一张“高但受控”的缩放图
- OCR 完成后，把识别框坐标映射回原图尺寸

这样做的效果是：

- 文字识别更快
- 最终导出的背景质量不变
- 高保真排版链路不变

### 17.2 PDF 渲染去掉 alpha 通道

实现位置：

- `D:\maker\extract_pdf.py`

做法是：

- PDF 栅格化时不再额外生成 alpha 通道

这样做的效果是：

- 少一点像素处理开销
- 不影响最终页面清晰度

---

## 18. 当前跨平台状态

### 18.1 当前可以明确保证的事情

当前可以明确保证的是：

- Windows 上的发行目标保持不变
- Windows 上的 GUI、打包、分发链路仍是主路径
- 源码项目可以整理成跨平台源码包，便于转移到 Mac 上继续编辑

### 18.2 不能误导的事情

不能把当前 Windows 分发包直接当成 Mac 可运行应用。

也就是说：

- `Slide_Maker.exe` 不能直接在 Mac 上运行
- `portable_python` 是 Windows 版解释器，不适合 Mac
- `runtime/node.exe` 是 Windows Node，不适合 Mac

因此，面向 Mac 的正确方案是：

- 转移源码包
- 在 Mac 上重新创建 Python 环境
- 在 Mac 上重新安装 Node 依赖
- 继续运行源码版 `ui_app.py`

### 18.3 为了 Mac 继续开发，本次对话补上的兼容收口

为了让你把工程带到 Mac 上继续编辑和运行，本次又额外做了这些工作：

- 把 `requirements.txt` 中的 WinRT 依赖改成 Windows 平台限定安装
- 增加了平台工具模块：
  - `D:\maker\services\platform_utils.py`
- GUI 中“打开文件 / 打开文件夹 / 打开诊断目录”不再只依赖 `os.startfile`
- `open_ppt_helper.py` 增加了非 Windows 的打开策略
- `ui_app.py` 使用平台适配的默认字体
- `runtime_env.py` 开始支持查找 POSIX 风格的 `node`
- 新增 Mac 环境初始化脚本：
  - `D:\maker\scripts\setup_macos.sh`
- 新增 Windows 环境初始化脚本：
  - `D:\maker\scripts\setup_windows.ps1`

### 18.4 最终建议的迁移方式

如果你要把工程带去 Mac 上继续开发，正确流程是：

1. 用本次生成的源码包拷到 Mac
2. 解压后进入项目目录
3. 运行 `scripts/setup_macos.sh`
4. 使用源码版运行：
   - `python ui_app.py --demo`
   - `python ui_app.py`
5. 后续如果要正式发 Windows 版，再把修改后的源码带回 Windows，继续使用 `build.ps1`

---

## 19. 当前仓库里最关键的文件

### GUI 与交互

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

### 配置与参数

- `D:\maker\services\app_models.py`
- `D:\maker\services\platform_utils.py`

### 转换服务与运行时

- `D:\maker\services\conversion_service.py`
- `D:\maker\services\runtime_env.py`
- `D:\maker\gui_conversion_runner.py`

### OCR / 去字 / 背景修复

- `D:\maker\ocr_engine.py`
- `D:\maker\winrt_ocr_engine.py`
- `D:\maker\image_processor.py`
- `D:\maker\inpainting_engine.py`
- `D:\maker\main.py`
- `D:\maker\extract_pdf.py`
- `D:\maker\ppt_generator.py`
- `D:\maker\utils.py`

### 构建与迁移

- `D:\maker\build.ps1`
- `D:\maker\scripts\setup_windows.ps1`
- `D:\maker\scripts\setup_macos.sh`
- `D:\maker\scripts\create_source_bundle.py`

### 资源

- `D:\maker\assets\slide_maker_icon.ico`
- `D:\maker\assets\slide_maker_icon.png`
- `D:\maker\models\big-lama.pt`
- `D:\maker\pptx-project\layout_engine.js`
- `D:\maker\pptx-project\package.json`
- `D:\maker\pptx-project\package-lock.json`

---

## 20. 当前运行方式

### 20.1 Windows 源码模式

预览界面：

```powershell
D:\maker\venv\Scripts\python.exe D:\maker\ui_app.py --demo
```

真实运行：

```powershell
D:\maker\venv\Scripts\python.exe D:\maker\ui_app.py
```

### 20.2 Windows 分发模式

当前分发可执行入口：

- `D:\maker\dist\Slide_Maker\Slide_Maker.exe`

### 20.3 Mac 源码模式

把项目源码包带到 Mac 后：

```bash
chmod +x scripts/setup_macos.sh
./scripts/setup_macos.sh
source .venv/bin/activate
python ui_app.py --demo
python ui_app.py
```

---

## 21. 当前已知边界

到当前为止，项目虽然已经能用，但仍然有边界需要明确：

- 当前真正完成产品化的真实输入只有 PDF 和图片
- 其他格式入口只是未来扩展位
- Mac 侧目前是源码运行方案，不是 Mac 原生 `.app`
- Windows 仍然是最终发行主平台
- 构建脚本 `build.ps1` 仍然是 Windows 发行脚本，不是跨平台打包脚本

---

## 22. 当前最终结论

截至现在，项目已经从“本地脚本工具”升级成了“可操作、可设置、可分发的桌面软件雏形”，当前状态可以概括为：

- 已有可用的 `Slide Maker` GUI
- 已接通 `PDF 转 PPTX` 与 `图片转 PPTX`
- 已支持离线偏好系统
- 已支持设置持久化
- 已支持隐藏 worker 与无控制台启动
- 已修复多个真实分发 bug
- 已恢复之前误伤的 AI 能力
- 已形成当前稳定的 Windows 分发结构
- 已补上源码迁移到 Mac 继续开发所需的最低兼容收口

如果后续继续开发，建议坚持当前原则：

- Windows 作为最终发行平台
- Mac 作为源码编辑和运行平台
- 不再回退到“只靠 frozen worker”的旧分发思路
- 不为压缩体积而删除真实能力

---

## 23. 本文件的维护建议

后续每次再有较大改动，建议只更新这份文件，而不是继续扩写旧的乱码历史文档。

建议保留顺序：

1. 产品目标
2. 关键技术路线
3. 新增需求
4. 本轮实现
5. bug 修复
6. 验证结果
7. 当前边界

这样以后无论谁接手，都能最快看懂项目。
