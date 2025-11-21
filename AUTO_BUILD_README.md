# 影藏·媒体管理器 - 自动构建系统

## 简介

这是一个完全自动化的构建和打包系统，可以一键完成从环境检查到生成安装包的全部流程。

## 功能特性

✅ **自动检查环境** - 检测 Python 版本和必需的依赖包
✅ **自动安装 PyInstaller** - 自动安装或更新 PyInstaller
✅ **自动生成版本号** - 从代码或 Git 标签自动获取版本号
✅ **自动清理旧构建** - 清理之前的构建文件和缓存
✅ **自动构建可执行文件** - 使用 PyInstaller 打包单文件 EXE
✅ **自动创建便携版** - 生成免安装的便携版压缩包
✅ **自动生成安装包** - 使用 Inno Setup 创建专业安装程序
✅ **全过程日志记录** - 详细的日志记录，便于问题排查

## 快速开始

### 方法一：一键构建（推荐）

**Windows 用户：**
```bash
双击运行: 一键构建.bat
```

**Linux/macOS 用户：**
```bash
python3 auto_build.py
```

### 方法二：命令行构建

```bash
# 1. 克隆或下载项目
git clone <repository-url>
cd media-manager

# 2. 运行自动构建脚本
python auto_build.py
```

## 系统要求

### 开发环境
- **Python**: 3.8 或更高版本
- **操作系统**: Windows 7+, macOS 10.13+, Linux
- **磁盘空间**: 至少 2GB 可用空间
- **内存**: 建议 4GB 或以上

### 可选工具
- **Inno Setup 6**: 用于创建 Windows 安装程序
  - 下载地址: https://jrsoftware.org/isdl.php
  - 如未安装，将只生成便携版

## 构建流程

自动构建系统会按以下顺序执行：

```
1. 检查环境
   ├─ 检查 Python 版本 (需要 3.8+)
   ├─ 检查 pip 可用性
   ├─ 检查必需的 Python 包
   └─ 验证项目结构

2. 安装 PyInstaller
   ├─ 检测是否已安装
   ├─ 自动安装或更新
   └─ 验证版本

3. 生成版本号
   ├─ 从 __init__.py 读取
   ├─ 或从 Git 标签获取
   └─ 更新版本信息

4. 清理旧构建
   ├─ 删除 build 目录
   ├─ 删除 dist 目录
   ├─ 删除 package 目录
   └─ 清理 __pycache__

5. 构建可执行文件
   ├─ 读取 spec 配置文件
   ├─ 运行 PyInstaller
   ├─ 验证生成的文件
   └─ 计算文件大小和哈希

7a. 创建便携版包
    ├─ 复制可执行文件
    ├─ 创建 README 说明
    ├─ 创建启动脚本
    ├─ 打包为 ZIP
    └─ 计算哈希值

7b. 创建安装包
    ├─ 生成 Inno Setup 脚本
    ├─ 查找 Inno Setup 编译器
    ├─ 编译安装程序
    └─ 计算哈希值

8. 生成构建报告
   ├─ 汇总所有构建信息
   ├─ 记录文件哈希值
   ├─ 保存为文本和 JSON
   └─ 输出到控制台
```

## 输出文件

构建完成后，会在 `package/` 目录下生成以下文件：

```
package/
├── MediaManager.exe                          # Windows 可执行文件
├── MediaManager-Portable-{version}/          # 便携版目录
│   ├── MediaManager.exe
│   ├── README.txt
│   └── 启动.bat
├── MediaManager-Portable-{version}.zip       # 便携版压缩包
├── MediaManager-Setup-{version}.exe          # Windows 安装程序
├── MediaManager-Setup.iss                    # Inno Setup 脚本
├── BUILD_REPORT_{timestamp}.txt              # 构建报告
└── BUILD_INFO_{timestamp}.json               # 构建信息 (JSON)
```

## 日志文件

所有构建日志保存在 `build_logs/` 目录：

```
build_logs/
└── build_{timestamp}.log                     # 构建日志
```

日志包含：
- 每个步骤的详细输出
- 命令执行结果
- 错误和警告信息
- 性能指标

## 使用生成的文件

### 便携版（推荐给普通用户）

1. 解压 `MediaManager-Portable-{version}.zip`
2. 双击 `MediaManager.exe` 或 `启动.bat`
3. 无需安装，可从 USB 驱动器运行

**优点：**
- 无需管理员权限
- 不修改系统注册表
- 可随身携带
- 删除即卸载

### 安装版（推荐给高级用户）

1. 运行 `MediaManager-Setup-{version}.exe`
2. 按照安装向导完成安装
3. 从开始菜单或桌面快捷方式启动

**优点：**
- 标准 Windows 应用程序
- 集成到开始菜单
- 创建桌面快捷方式
- 提供专业的卸载程序

## 验证文件完整性

使用构建报告中的 SHA256 哈希值验证文件：

**Windows (PowerShell):**
```powershell
Get-FileHash MediaManager.exe -Algorithm SHA256
```

**Windows (命令提示符):**
```cmd
certutil -hashfile MediaManager.exe SHA256
```

**Linux/macOS:**
```bash
shasum -a 256 MediaManager.exe
```

## 故障排除

### 构建失败

1. **检查日志文件**
   ```
   查看 build_logs/build_*.log 获取详细错误信息
   ```

2. **清理并重试**
   ```bash
   # 手动清理
   rm -rf build dist package
   
   # 重新构建
   python auto_build.py
   ```

3. **检查依赖**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### 常见问题

#### 1. Python 未找到
```
错误: 'python' 不是内部或外部命令
```

**解决方案：**
- 安装 Python 3.8 或更高版本
- 确保 Python 添加到 PATH 环境变量

#### 2. PyInstaller 导入错误
```
错误: No module named 'PyInstaller'
```

**解决方案：**
- 脚本会自动安装，如果失败请手动安装：
  ```bash
  pip install pyinstaller
  ```

#### 3. 未找到 Inno Setup
```
警告: 未找到 Inno Setup，无法创建安装程序
```

**解决方案：**
- 下载并安装 Inno Setup 6: https://jrsoftware.org/isdl.php
- 或使用已生成的 `.iss` 脚本手动编译
- 便携版仍可正常使用

#### 5. 生成的 EXE 很大
```
问题: 可执行文件超过 150MB
```

**解决方案：**
- 这是正常的，包含了完整的 Python 环境和依赖
- 便携版压缩包会更小（约 50-80MB）
- 可以使用 UPX 进一步压缩（可选）

## 高级配置

### 自定义构建参数

编辑 `auto_build.py` 中的配置部分：

```python
# 配置 Configuration
APP_NAME = "影藏·媒体管理器"
APP_NAME_EN = "MediaManager"
SPEC_FILE = SRC_DIR / "media_manager" / "media_manager.spec"
```

### 修改 PyInstaller 配置

编辑 `src/media_manager/media_manager.spec` 文件：

```python
# 添加额外的数据文件
datas=[
    ('path/to/assets', 'assets'),
    # ...
]

# 排除不需要的模块
excludes=[
    'tkinter',
    # ...
]
```

### 自定义安装程序

编辑生成的 `MediaManager-Setup.iss` 文件，然后手动编译：

```bash
# 使用 Inno Setup 命令行编译
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" MediaManager-Setup.iss
```

## 持续集成 (CI/CD)

可以将此脚本集成到 CI/CD 流程中：

### GitHub Actions 示例

```yaml
name: Build Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Run Auto Build
        run: python auto_build.py
      - name: Upload Artifacts
        uses: actions/upload-artifact@v2
        with:
          name: release-packages
          path: package/
```

## 版本管理

### 更新版本号

有三种方式设置版本号：

1. **自动从 Git 标签获取**
   ```bash
   git tag v1.0.0
   git push --tags
   python auto_build.py
   ```

2. **手动修改 __init__.py**
   ```python
   # src/media_manager/__init__.py
   __version__ = "1.0.1"
   ```

3. **构建时自动使用默认版本**
   - 如果以上都不可用，将使用 0.1.0

## 最佳实践

1. **构建前检查**
   - 确保所有测试通过
   - 更新 CHANGELOG.md
   - 更新版本号

2. **测试构建**
   - 在干净的虚拟机上测试
   - 测试所有主要功能
   - 验证文件哈希

3. **发布**
   - 保存构建报告
   - 创建 GitHub Release
   - 上传所有包文件
   - 在 Release 说明中包含哈希值

## 技术支持

如果遇到问题：

1. 查看构建日志: `build_logs/build_*.log`
2. 查看构建报告: `package/BUILD_REPORT_*.txt`
3. 搜索常见问题（见上文）
4. 提交 Issue 到项目仓库

## 许可证

本构建系统是 影藏·媒体管理器 项目的一部分，遵循相同的许可证。

---

**影藏·媒体管理器** - 影视媒体管理专家

构建时间: {datetime.now().strftime('%Y-%m-%d')}
