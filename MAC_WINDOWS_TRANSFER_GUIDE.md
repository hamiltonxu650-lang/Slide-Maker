# Slide Maker 跨平台迁移说明

## 1. 先说结论

当前项目的正确跨平台策略是：

- 在 Windows 上发行
- 在 Mac 上继续编辑和运行源码
- 不把 Windows 的 `.exe` 当成 Mac 可运行应用

## 2. 什么可以直接带走

可以直接带去 Mac 的是：

- 项目源码
- UI 代码
- 服务层代码
- 模型文件
- 图标与资源
- 测试样例
- 文档
- `package.json` / `package-lock.json`

## 3. 什么不能直接在 Mac 上用

下面这些是 Windows 专用产物：

- `Slide_Maker.exe`
- `portable_python`
- `portable_site_packages`
- `runtime/node.exe`

## 4. 在 Mac 上怎么继续开发

把源码包解压到 Mac 后执行：

```bash
chmod +x scripts/setup_macos.sh
./scripts/setup_macos.sh
source .venv/bin/activate
python ui_app.py --demo
python ui_app.py
```

## 5. 回到 Windows 怎么发版

当你在 Mac 上改完源码后，把源码带回 Windows，再执行：

```powershell
.\scripts\setup_windows.ps1
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

## 6. 兼容性原则

后续继续改代码时，尽量遵守这些规则：

- 不把绝对 Windows 路径写死进源码
- 不把 `os.startfile` 作为唯一打开方式
- 运行时优先通过 `Path` 和平台判断处理路径
- Windows 专用依赖必须加平台条件
- GUI 逻辑尽量和平台无关
- 最终发行相关脚本仍以 Windows 为准
