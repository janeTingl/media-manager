# 影藏·媒体管理器 - 自动构建打包系统

## 🎯 项目概述

这是一个完整的自动化构建和打包系统，用于将影藏·媒体管理器（MediaManager）打包成可分发的独立应用程序。

### 核心特性

- ✅ **全自动化** - 从环境检查到生成安装包，一键完成
- ✅ **跨平台支持** - Windows、macOS、Linux
- ✅ **中文界面** - 原生简体中文界面
- ✅ **多种分发格式** - 便携版 ZIP、Windows 安装程序
- ✅ **完整日志** - 详细记录每个构建步骤
- ✅ **哈希验证** - 自动生成文件完整性校验码
- ✅ **智能版本管理** - 自动从代码或 Git 获取版本号

---

## 📁 文件结构

```
project/
├── auto_build.py              # 主构建脚本（Python）
├── 一键构建.bat               # Windows 启动脚本
├── auto_build.sh              # Linux/macOS 启动脚本
├── test_auto_build.py         # 测试脚本
├── 构建指南.md                # 快速开始指南
├── AUTO_BUILD_README.md       # 详细使用文档
├── AUTO_BUILD_SYSTEM.md       # 本文档
│
├── src/
│   └── media_manager/
│       ├── main.py            # 应用主入口
│       ├── __init__.py        # 版本号定义
│       ├── media_manager.spec # PyInstaller 配置
│       └── resources/         # 资源文件
│
├── build/                     # 构建临时文件（自动生成）
├── dist/                      # 构建输出（自动生成）
├── package/                   # 最终打包文件（自动生成）
└── build_logs/                # 构建日志（自动生成）
```

---

## 🚀 快速开始

### 1. 环境准备

**最低要求：**
- Python 3.8+
- pip（Python 包管理器）
- 2GB 可用磁盘空间
- 4GB 内存（推荐）

**可选工具：**
- Inno Setup 6（Windows 安装程序制作）
- Git（版本管理）

### 2. 运行构建

**Windows：**
```cmd
双击运行: 一键构建.bat
```

**Linux/macOS：**
```bash
./auto_build.sh
# 或
chmod +x auto_build.sh && ./auto_build.sh
```

**直接使用 Python：**
```bash
python auto_build.py
# 或
python3 auto_build.py
```

### 3. 测试环境

在构建前测试环境：
```bash
python test_auto_build.py
```

---

## 🔧 构建流程详解

### 第 1 步：环境检查

自动检测并验证：
- ✓ Python 版本（需要 3.8+）
- ✓ pip 可用性
- ✓ 必需的 Python 包（PySide6、sqlalchemy 等）
- ✓ 项目文件结构

**如果缺少依赖，会自动安装。**

### 第 2 步：安装 PyInstaller

- 检查是否已安装 PyInstaller
- 如未安装，自动安装最新版本
- 如已安装但有新版本，提示更新

### 第 3 步：版本号管理

自动获取版本号，优先级：
1. `src/media_manager/__init__.py` 中的 `__version__`
2. Git 标签 (`git describe --tags`)
3. 默认版本 `0.1.0`

### 第 4 步：清理旧构建

删除并重建以下目录：
- `build/` - PyInstaller 临时文件
- `dist/` - 构建输出
- `package/` - 打包文件
- 清理所有 `__pycache__` 目录

### 第 5 步：构建可执行文件

使用 PyInstaller 根据 `media_manager.spec` 配置：

**配置要点：**
```python
# 单文件模式
--onefile

# 无控制台窗口（GUI 应用）
--windowed

# 包含资源文件
datas=[
    ('assets/*', 'assets'),
    ('config/*', 'config'),
]
```

**输出：**
- Windows: `MediaManager.exe`
- macOS: `MediaManager.app`
- Linux: `MediaManager`

### 第 7a 步：创建便携版包

生成免安装的便携版：

**包含文件：**
```
MediaManager-Portable-{version}/
├── MediaManager.exe       # 可执行文件
├── README.txt             # 使用说明（中文）
└── 启动.bat               # 启动脚本（Windows）
```

**特点：**
- 无需安装
- 可从 USB 运行
- 不修改系统注册表
- 解压即用

**最终输出：**
- `MediaManager-Portable-{version}.zip` (约 50-80MB)

### 第 7b 步：创建安装包（Windows）

使用 Inno Setup 创建专业的 Windows 安装程序：

**自动生成的安装脚本包含：**
- 应用程序信息和版本
- 安装位置选择
- 开始菜单快捷方式
- 桌面快捷方式（可选）
- 卸载程序
- 64 位系统检测

**输出：**
- `MediaManager-Setup-{version}.exe` (安装程序)
- `MediaManager-Setup.iss` (Inno Setup 脚本)

**注意：** 需要预先安装 Inno Setup 6

### 第 8 步：生成构建报告

创建详细的构建报告：

**文本报告 (BUILD_REPORT_*.txt)：**
```
- 版本信息
- 构建时间
- 平台信息
- 生成的文件列表
- 文件大小
- SHA256 哈希值
- 构建步骤摘要
- 使用说明
```

**JSON 报告 (BUILD_INFO_*.json)：**
```json
{
  "version": "0.1.0",
  "build_time": "2024-01-01T12:00:00",
  "platform": "Windows",
  "python_version": "3.10.0",
  "steps": [
    {
      "name": "检查环境",
      "status": "completed",
      "timestamp": "...",
      "details": "..."
    },
    ...
  ]
}
```

---

## 📦 输出文件说明

### 构建产物目录结构

```
package/
├── MediaManager.exe                           # 原始可执行文件
│
├── MediaManager-Portable-{version}/           # 便携版目录
│   ├── MediaManager.exe
│   ├── README.txt
│   └── 启动.bat
│
├── MediaManager-Portable-{version}.zip        # 便携版压缩包 ⭐
│
├── MediaManager-Setup-{version}.exe           # Windows 安装程序 ⭐
├── MediaManager-Setup.iss                     # Inno Setup 脚本
│
├── BUILD_REPORT_{timestamp}.txt               # 构建报告（文本）
└── BUILD_INFO_{timestamp}.json                # 构建信息（JSON）
```

**⭐ 标记的文件是用于分发的主要文件**

### 文件用途

| 文件 | 用途 | 目标用户 |
|------|------|----------|
| `MediaManager-Portable-{version}.zip` | 便携版压缩包 | 普通用户 |
| `MediaManager-Setup-{version}.exe` | Windows 安装程序 | 希望标准安装的用户 |
| `BUILD_REPORT_*.txt` | 构建报告 | 开发者、质量保证 |
| `MediaManager.exe` | 原始可执行文件 | 测试、开发 |

---

## 📝 日志系统

### 日志文件位置

```
build_logs/
└── build_{YYYYMMDD_HHMMSS}.log    # 每次构建的完整日志
```

### 日志内容

每个构建日志包含：

1. **环境信息**
   - Python 版本
   - 操作系统
   - 依赖包版本

2. **构建步骤**
   - 每个步骤的开始/结束时间
   - 执行的命令
   - 命令输出
   - 错误和警告

3. **文件操作**
   - 创建的文件
   - 文件大小
   - 文件哈希值

4. **性能指标**
   - 每个步骤的耗时
   - 总构建时间

### 日志级别

- `INFO`: 正常流程信息
- `WARNING`: 非关键警告
- `ERROR`: 错误信息
- `DEBUG`: 详细调试信息（命令输出）

### 查看日志

```bash
# 查看最新日志
cat build_logs/build_*.log | tail -100

# 搜索错误
grep "ERROR" build_logs/build_*.log

# 查看特定步骤
grep "构建可执行文件" build_logs/build_*.log -A 20
```

---

## 🔍 故障排除

### 常见问题和解决方案

#### 1. Python 环境问题

**问题：** `'python' 不是内部或外部命令`

**解决：**
```bash
# 下载并安装 Python 3.8+
# https://www.python.org/downloads/

# 确保添加到 PATH
# 安装时勾选 "Add Python to PATH"

# 验证
python --version
# 或
python3 --version
```

#### 2. PyInstaller 导入错误

**问题：** `ModuleNotFoundError: No module named 'PyInstaller'`

**解决：**
```bash
# 手动安装
pip install pyinstaller

# 或升级
pip install --upgrade pyinstaller

# 验证
pyinstaller --version
```

#### 3. 依赖包缺失

**问题：** `No module named 'PySide6'` 等

**解决：**
```bash
# 安装所有依赖
pip install PySide6 sqlalchemy sqlmodel requests tenacity openpyxl

# 或使用 requirements 文件（如果有）
pip install -r requirements.txt
```

#### 4. Inno Setup 未找到

**问题：** `未找到 Inno Setup，无法创建安装程序`

**影响：** 不生成安装程序，但便携版可用

**解决：**
```bash
# 下载并安装 Inno Setup 6
# https://jrsoftware.org/isdl.php

# 默认安装路径：
# C:\Program Files (x86)\Inno Setup 6\

# 或手动编译生成的 .iss 脚本
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" package/MediaManager-Setup.iss
```

#### 6. 构建失败但无明确错误

**解决步骤：**

1. **清理环境**
   ```bash
   # 删除所有构建产物
   rm -rf build dist package __pycache__
   
   # 清理 Python 缓存
   find . -type d -name "__pycache__" -exec rm -rf {} +
   ```

2. **检查日志**
   ```bash
   # 查看最新日志的最后 50 行
   tail -50 build_logs/build_*.log
   ```

3. **验证环境**
   ```bash
   # 运行测试脚本
   python test_auto_build.py
   ```

4. **重新构建**
   ```bash
   python auto_build.py
   ```

#### 7. 生成的 EXE 无法运行

**问题：** 双击无反应或立即关闭

**排查：**

1. **从命令行运行**
   ```cmd
   cd package
   MediaManager.exe
   # 查看错误信息
   ```

2. **检查依赖**
   ```cmd
   # 可能缺少 Visual C++ 运行库
   # 下载安装：
   # https://aka.ms/vs/17/release/vc_redist.x64.exe
   ```

3. **查看应用日志**
   ```
   %USERPROFILE%\.media-manager\logs\app.log
   ```

4. **杀毒软件拦截**
   - 将程序添加到杀毒软件白名单
   - 或暂时禁用杀毒软件测试

#### 8. 构建速度慢

**优化方法：**

1. **首次构建慢是正常的**
   - 需要下载和安装依赖
   - 后续构建会快很多

2. **使用 SSD**
   - 将项目移动到 SSD
   - 可显著提升速度

3. **关闭实时扫描**
   - 暂时禁用杀毒软件的实时扫描
   - 构建目录添加到排除列表

4. **增加系统资源**
   - 关闭其他应用程序
   - 确保有足够的内存和磁盘空间

---

## 🎨 自定义配置

### 修改应用信息

编辑 `src/media_manager/__init__.py`：

```python
__version__ = "1.0.0"              # 版本号
APP_DISPLAY_NAME = "影藏·媒体管理器"  # 显示名称
APP_ORGANIZATION_NAME = "你的团队"    # 组织名称
```

### 修改构建配置

编辑 `auto_build.py` 顶部配置：

```python
# 应用名称
APP_NAME = "影藏·媒体管理器"
APP_NAME_EN = "MediaManager"

# 路径配置
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_DIR = PROJECT_ROOT / "package"
```

### 修改 PyInstaller 配置

编辑 `src/media_manager/media_manager.spec`：

```python
# 添加额外的数据文件
datas=[
    ('assets/*', 'assets'),
    ('config/*', 'config'),
    # ...
]

# 添加隐藏导入
hiddenimports=[
    'custom_module',
    # ...
]

# 排除不需要的模块
excludes=[
    'tkinter',
    'matplotlib',
    # ...
]

# 修改图标
icon='custom_icon.ico'
```

### 修改安装程序配置

构建后编辑 `package/MediaManager-Setup.iss`：

```pascal
[Setup]
AppName=自定义名称
AppVersion=1.0.0
AppPublisher=你的公司
DefaultDirName={autopf}\自定义目录

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
```

---

## 🔐 安全和验证

### 文件完整性验证

每个构建会生成 SHA256 哈希值，用于验证文件完整性。

**Windows (PowerShell):**
```powershell
Get-FileHash MediaManager.exe -Algorithm SHA256
```

**Windows (CMD):**
```cmd
certutil -hashfile MediaManager.exe SHA256
```

**Linux/macOS:**
```bash
shasum -a 256 MediaManager.exe
# 或
sha256sum MediaManager.exe
```

**对比哈希值：**
1. 打开构建报告 `BUILD_REPORT_*.txt`
2. 找到文件的 SHA256 值
3. 与计算结果对比

### 代码签名（推荐）

对于生产环境，建议对可执行文件进行代码签名：

**Windows:**
```cmd
# 需要代码签名证书
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com MediaManager.exe

# 验证签名
signtool verify /pa MediaManager.exe
```

**macOS:**
```bash
# 需要 Apple Developer 账号
codesign --sign "Developer ID Application: Your Name" MediaManager.app

# 验证
codesign --verify --verbose MediaManager.app
```

---

## 📊 构建统计

### 典型构建时间

| 阶段 | 时间 | 说明 |
|------|------|------|
| 环境检查 | 10-30秒 | 首次运行需要安装依赖 |
| 清理 | 5-10秒 | 删除旧文件 |
| PyInstaller 构建 | 2-5分钟 | 取决于系统性能 |
| 打包 | 30-60秒 | 创建 ZIP 和安装程序 |
| **总计** | **3-6分钟** | 首次可能需要更长 |

### 文件大小估算

| 文件类型 | 大小范围 | 说明 |
|---------|---------|------|
| 可执行文件 (.exe) | 80-150 MB | 包含 Python 和所有依赖 |
| 便携版 (.zip) | 50-100 MB | 压缩后 |
| 安装程序 (.exe) | 50-100 MB | LZMA 压缩 |

---

## 🚢 发布流程

### 准备发布

1. **更新版本号**
   ```python
   # src/media_manager/__init__.py
   __version__ = "1.0.0"
   ```

2. **更新 CHANGELOG**
   - 记录新功能
   - 记录修复的问题
   - 记录重大变更

3. **运行测试**
   ```bash
   # 单元测试
   pytest
   
   # 构建测试
   python test_auto_build.py
   ```

4. **构建发布版本**
   ```bash
   python auto_build.py
   ```

5. **验证构建**
   - 测试可执行文件
   - 测试安装程序
   - 验证哈希值

### 创建 GitHub Release

1. **提交代码**
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   git push
   ```

2. **创建标签**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **上传构建产物**
   - `MediaManager-Portable-{version}.zip`
   - `MediaManager-Setup-{version}.exe`
   - `BUILD_REPORT_*.txt`

4. **编写 Release Notes**
   ```markdown
   ## 新功能
   - 功能 A
   - 功能 B
   
   ## 修复
   - 问题 X
   - 问题 Y
   
   ## 下载
   
   - 便携版: MediaManager-Portable-1.0.0.zip (SHA256: ...)
   - 安装版: MediaManager-Setup-1.0.0.exe (SHA256: ...)
   
   ## 系统要求
   - Windows 7 或更高版本 (64位)
   - 4GB 内存
   - 100MB 可用磁盘空间
   ```

---

## 🛠️ 高级功能

### 持续集成 (CI/CD)

#### GitHub Actions 配置

创建 `.github/workflows/build.yml`：

```yaml
name: Auto Build

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run auto build
        run: python auto_build.py
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: windows-build
          path: package/
      
      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: |
            package/MediaManager-Portable-*.zip
            package/MediaManager-Setup-*.exe
            package/BUILD_REPORT_*.txt
```

### 多平台构建

#### macOS 构建

```yaml
build-macos:
  runs-on: macos-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Run auto build
      run: python3 auto_build.py
```

#### Linux 构建

```yaml
build-linux:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y qt6-tools-dev
    - name: Run auto build
      run: python3 auto_build.py
```

---

## 📚 相关文档

- **快速开始**: `构建指南.md`
- **详细文档**: `AUTO_BUILD_README.md`
- **打包指南**: `PACKAGING_GUIDE.md`

---

## 🤝 贡献

欢迎改进自动构建系统！

### 报告问题

如果遇到问题，请提供：
1. 完整的构建日志 (`build_logs/build_*.log`)
2. 构建报告 (`BUILD_REPORT_*.txt`)
3. 系统信息（操作系统、Python 版本）
4. 错误截图或消息

### 提交改进

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/improvement`)
3. 提交更改 (`git commit -am 'Add improvement'`)
4. 推送到分支 (`git push origin feature/improvement`)
5. 创建 Pull Request

---

## 📄 许可证

本构建系统是 影藏·媒体管理器 项目的一部分，遵循项目的开源许可证。

---

## 💡 最佳实践总结

1. ✅ **构建前测试** - 运行 `test_auto_build.py`
2. ✅ **保持依赖更新** - 定期更新 Python 包
3. ✅ **验证哈希值** - 确保文件完整性
4. ✅ **测试构建产物** - 在干净环境中测试
5. ✅ **保存构建日志** - 便于问题排查
6. ✅ **使用版本控制** - 标记每个发布版本
7. ✅ **自动化 CI/CD** - 减少手动操作
8. ✅ **代码签名** - 提高用户信任
9. ✅ **文档更新** - 保持文档与代码同步
10. ✅ **用户反馈** - 持续改进构建流程

---

**影藏·媒体管理器 - 自动构建打包系统**

版本: 1.0.0
更新时间: 2024
