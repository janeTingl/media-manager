# 自动构建快速开始 / Auto Build Quick Start

## 🇨🇳 中文版

### 一键运行

**Windows:**
```
双击运行: 一键构建.bat
```

**Linux/macOS:**
```bash
./auto_build.sh
```

### 功能

✅ 自动检查环境并安装依赖
✅ 自动编译中文翻译文件
✅ 自动打包为独立可执行程序
✅ 自动生成便携版和安装包
✅ 完整的日志记录

### 输出文件

构建完成后，在 `package/` 目录找到：

- **MediaManager-Portable-版本.zip** - 便携版（推荐）
- **MediaManager-Setup-版本.exe** - Windows 安装程序
- **BUILD_REPORT_*.txt** - 构建报告（含文件哈希值）

### 系统要求

- Python 3.8 或更高版本
- Windows 7+ / macOS 10.13+ / Linux
- 2GB 可用磁盘空间

### 首次使用

1. 确保已安装 Python 3.8+
2. 运行构建脚本（见上方）
3. 等待 3-7 分钟自动完成
4. 在 `package/` 目录找到生成的文件

### 可选工具

- **Inno Setup 6** - 生成 Windows 安装程序
  - 下载: https://jrsoftware.org/isdl.php
  - 不安装也可以，便携版仍可用

### 常见问题

**Q: 提示找不到 Python？**
A: 安装 Python 并确保添加到 PATH
   下载: https://www.python.org/downloads/

**Q: 构建失败？**
A: 查看日志文件 `build_logs/build_*.log`

**Q: 生成的程序无法运行？**
A: 可能需要安装 VC++ 运行库
   下载: https://aka.ms/vs/17/release/vc_redist.x64.exe

### 验证文件

使用 SHA256 验证文件完整性：

**Windows:**
```cmd
certutil -hashfile MediaManager.exe SHA256
```

**Linux/macOS:**
```bash
sha256sum MediaManager.exe
```

对比 `BUILD_REPORT_*.txt` 中的哈希值。

### 更多文档

- **快速指南**: `构建指南.md`
- **详细文档**: `AUTO_BUILD_README.md`
- **系统文档**: `AUTO_BUILD_SYSTEM.md`

---

## 🇬🇧 English Version

### One-Click Build

**Windows:**
```
Double-click: 一键构建.bat
```

**Linux/macOS:**
```bash
./auto_build.sh
```

### Features

✅ Auto environment check and dependency installation
✅ Auto compile Chinese translation files
✅ Auto package as standalone executable
✅ Auto generate portable and installer packages
✅ Complete logging

### Output Files

After build completes, find in `package/` directory:

- **MediaManager-Portable-{version}.zip** - Portable version (recommended)
- **MediaManager-Setup-{version}.exe** - Windows installer
- **BUILD_REPORT_*.txt** - Build report (with file hashes)

### Requirements

- Python 3.8 or higher
- Windows 7+ / macOS 10.13+ / Linux
- 2GB free disk space

### First Time Usage

1. Ensure Python 3.8+ is installed
2. Run build script (see above)
3. Wait 3-7 minutes for automatic completion
4. Find generated files in `package/` directory

### Optional Tools

- **Inno Setup 6** - Generate Windows installer
  - Download: https://jrsoftware.org/isdl.php
  - Not required, portable version still works

### Common Issues

**Q: Python not found?**
A: Install Python and ensure it's in PATH
   Download: https://www.python.org/downloads/

**Q: Build failed?**
A: Check log file `build_logs/build_*.log`

**Q: Generated program won't run?**
A: May need VC++ Redistributable
   Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Verify Files

Verify file integrity using SHA256:

**Windows:**
```cmd
certutil -hashfile MediaManager.exe SHA256
```

**Linux/macOS:**
```bash
sha256sum MediaManager.exe
```

Compare with hash in `BUILD_REPORT_*.txt`.

### More Documentation

- **Quick Guide**: `构建指南.md`
- **Detailed Docs**: `AUTO_BUILD_README.md`
- **System Docs**: `AUTO_BUILD_SYSTEM.md`

---

## 📋 Build Process / 构建流程

```
1. Check Environment / 检查环境
   ↓
2. Install PyInstaller / 安装 PyInstaller
   ↓
3. Generate Version / 生成版本号
   ↓
4. Clean Old Builds / 清理旧构建
   ↓
5. Compile Translations / 编译中文翻译
   ↓
6. Build Executable / 构建可执行文件
   ↓
7. Create Packages / 创建安装包
   ↓
8. Generate Reports / 生成构建报告
   ↓
✓ Done! / 完成！
```

---

## 🎯 Quick Commands / 快速命令

### Test Environment / 测试环境
```bash
python test_auto_build.py
```

### Run Build / 运行构建
```bash
python auto_build.py
```

### View Latest Log / 查看最新日志
```bash
# Linux/macOS
cat build_logs/build_*.log | tail -100

# Windows
type build_logs\build_*.log | more
```

### Clean All / 清理所有
```bash
# Linux/macOS
rm -rf build dist package build_logs

# Windows
rmdir /s /q build dist package build_logs
```

---

## 📞 Support / 技术支持

**Issues / 问题反馈:**
- Include log file / 包含日志文件
- System information / 系统信息
- Error screenshots / 错误截图

**Documentation / 文档:**
- 中文文档: `构建指南.md`, `AUTO_BUILD_SYSTEM.md`
- English docs: `AUTO_BUILD_README.md`

---

**影藏·媒体管理器 / MediaManager**
Version / 版本: 1.0.0
