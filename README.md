# 影藏·媒体管理器

一款基于 PySide6 开发的现代化媒体管理应用程序。

## 项目简介

影藏·媒体管理器是一款功能强大的跨平台媒体资源管理工具，帮助您轻松整理、分类和管理影视资源。支持自动识别媒体信息、智能重命名、海报下载等功能。

## 主要特性

### 核心功能
- 🎬 **智能媒体识别** - 自动匹配 TMDB/TVDB 数据库，获取影视资源详细信息
- 📁 **多媒体库管理** - 支持创建多个独立媒体库，分类管理不同类型的内容
- 🔍 **高级搜索过滤** - 强大的搜索和筛选功能，快速定位所需资源
- ✏️ **元数据编辑器** - 批量编辑媒体文件的元数据信息
- 🖼️ **海报管理** - 自动下载和管理影视海报、背景图
- 📝 **NFO 文件导出** - 支持导出 Kodi/Jellyfin 兼容的 NFO 元数据文件

### 用户界面
- 🎨 **现代化界面** - 基于 Qt6 的美观界面设计
- 📊 **仪表盘视图** - 可视化展示媒体库统计信息
- 🗂️ **多视图模式** - 支持网格视图、列表视图、详情视图
- ⚡ **高性能显示** - 优化的渲染性能，流畅浏览大型媒体库

### 数据管理
- 💾 **SQLite 数据库** - 本地数据库存储，快速检索
- 📤 **导入导出** - 支持媒体库数据的备份和恢复
- 🔄 **批量操作** - 批量重命名、移动、删除等操作
- 🏷️ **标签系统** - 自定义标签分类管理

## 系统要求

- **操作系统**: Windows 10/11, macOS 10.14+, Linux
- **Python 版本**: Python 3.8 或更高版本
- **内存**: 至少 4GB RAM
- **硬盘空间**: 至少 500MB 可用空间

## 安装说明

### 方式一：使用预编译版本（推荐）

1. 从 [Releases 页面](https://github.com/your-repo/media-manager/releases) 下载最新版本
2. **Windows 用户**: 下载 `.exe` 安装程序，双击运行
3. **macOS 用户**: 下载 `.dmg` 文件，拖拽到应用程序文件夹
4. **Linux 用户**: 下载 AppImage，添加执行权限后运行

### 方式二：一键自动构建

项目提供了完整的自动化构建系统：

```bash
# Windows 系统
一键构建.bat

# Linux/macOS 系统
./auto_build.sh

# 或直接使用 Python
python auto_build.py
```

构建完成后，可执行文件和安装包将生成在 `package/` 目录中。

**自动构建功能包括：**
- ✅ 自动检查和安装构建依赖
- ✅ 自动构建独立可执行文件
- ✅ 自动创建便携版 ZIP 和安装程序
- ✅ 完整的构建日志和文件完整性验证

详细说明请参考 `构建指南.md`

### 方式三：从源码安装

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd media-manager
```

#### 2. 创建虚拟环境

```bash
python -m venv venv

# Windows 激活
venv\Scripts\activate

# Linux/macOS 激活
source venv/bin/activate
```

#### 3. 安装依赖

```bash
# 开发环境（包含测试工具）
pip install -e ".[dev]"

# 生产环境
pip install -e .
```

## 使用方法

### 启动应用

#### 开发模式
```bash
# 使用安装的命令
media-manager

# 或直接运行 Python 模块
python -m src.media_manager.main

# 或直接运行主文件
python src/media_manager/main.py
```

#### 预编译版本
- **Windows**: 双击 `影藏·媒体管理器.exe`
- **macOS**: 从启动台打开 `影藏·媒体管理器`
- **Linux**: 运行 AppImage 文件

### 首次使用向导

首次启动时，将显示快速设置向导：

1. **设置 API 密钥** - 配置 TMDB/TVDB API 密钥（可选，用于自动识别）
2. **创建媒体库** - 指定媒体文件存储位置
3. **配置扫描选项** - 设置自动扫描和监控选项

### 主要功能使用

#### 创建和管理媒体库

1. 点击 **文件 → 媒体库管理**
2. 点击 **新建媒体库**
3. 设置媒体库名称和路径
4. 选择媒体类型（电影/电视剧/音乐等）
5. 点击 **扫描** 开始导入媒体文件

#### 媒体匹配和识别

1. 在媒体列表中选择未识别的项目
2. 点击 **匹配** 按钮
3. 应用将自动搜索 TMDB/TVDB 数据库
4. 从搜索结果中选择正确的匹配项
5. 系统自动下载海报和元数据

#### 批量重命名

1. 选中需要重命名的文件
2. 点击 **工具 → 批量操作**
3. 在批量操作对话框中选择 **重命名**
4. 配置重命名模板（如：`{title} ({year})`）
5. 预览重命名结果
6. 点击 **执行** 完成批量重命名

#### 元数据编辑

1. 在媒体列表中双击项目或选择后点击 **编辑**
2. 在元数据编辑器中修改信息
3. 可编辑：标题、年份、简介、演员、导演等
4. 点击 **保存** 应用更改

#### 导出 NFO 文件

1. 选择媒体项目
2. 点击 **工具 → NFO 导出**
3. 选择导出格式（Kodi/Jellyfin）
4. 设置导出路径
5. NFO 文件将与媒体文件保存在一起

## 配置说明

### 配置文件位置

- **Windows**: `%USERPROFILE%\.media-manager\settings.json`
- **Linux/macOS**: `~/.media-manager/settings.json`

### 主要配置项

```json
{
  "api_keys": {
    "tmdb": "你的-TMDB-API-密钥",
    "tvdb": "你的-TVDB-API-密钥"
  },
  "libraries": [
    {
      "name": "电影库",
      "path": "/path/to/movies",
      "type": "movie"
    },
    {
      "name": "电视剧库",
      "path": "/path/to/tv_shows",
      "type": "tv"
    }
  ],
  "rename_templates": {
    "movie": "{title} ({year})",
    "tv_episode": "{show_name} - S{season:02d}E{episode:02d} - {title}"
  },
  "poster_settings": {
    "download_enabled": true,
    "quality": "high",
    "language": "zh-CN"
  }
}
```

### 日志文件

日志文件位置：
- **Windows**: `%USERPROFILE%\.media-manager\logs\app.log`
- **Linux/macOS**: `~/.media-manager/logs/app.log`

日志级别：DEBUG, INFO, WARNING, ERROR

## 开发说明

### 项目结构

```
media-manager/
├── src/
│   └── media_manager/
│       ├── __init__.py              # 包初始化
│       ├── main.py                  # 应用入口点
│       ├── main_window.py           # 主窗口
│       ├── settings.py              # 设置管理
│       ├── logging.py               # 日志配置
│       ├── services.py              # 依赖注入
│       ├── persistence/             # 数据持久化
│       │   ├── database.py         # 数据库管理
│       │   └── repositories/       # 数据仓库
│       ├── providers/               # 外部 API 提供者
│       │   ├── tmdb_provider.py    # TMDB API
│       │   └── tvdb_provider.py    # TVDB API
│       └── resources/               # 资源文件
│           └── icons/              # 图标
├── tests/                          # 测试文件
│   ├── conftest.py                # Pytest 配置
│   └── test_*.py                  # 各模块测试
├── pyproject.toml                  # 项目配置
├── auto_build.py                   # 自动构建脚本
└── README.md                       # 项目说明
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并显示覆盖率
pytest --cov=src/media_manager

# 运行特定测试文件
pytest tests/test_smoke.py

# 详细输出
pytest -v

# 跳过性能测试（更快）
pytest -m "not benchmark"
```

### 代码质量检查

```bash
# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/

# 类型检查
mypy src/
```

### 性能测试

```bash
# 运行性能基准测试
python tests/performance/runner.py

# 运行特定测试套件
python tests/performance/runner.py --suite database
python tests/performance/runner.py --suite ui

# 生成性能报告
python tests/performance/runner.py --report
```

### 构建可执行文件

#### 使用自动构建（推荐）

```bash
python auto_build.py
```

#### 手动构建

```bash
# Windows
python build_windows.py

# macOS
python build_macos.py

# 跨平台统一构建
python build.py --platform windows --package
python build.py --platform macos --package
```

构建输出位于 `dist/` 和 `package/` 目录。

### 添加新功能

1. 在 `src/media_manager/` 中创建新模块
2. 在 `tests/` 中添加相应测试
3. 如需依赖注入，在服务注册表中注册
4. 更新配置文件结构（如有新配置项）
5. 运行测试确保兼容性

## 常见问题

### 应用无法启动

**问题**：双击程序没有反应或闪退

**解决方案**：
1. 检查 Python 版本是否为 3.8 或更高
2. 确认已安装 PySide6：`pip install PySide6`
3. 查看日志文件：`~/.media-manager/logs/app.log`
4. 在命令行中运行查看错误信息

### API 密钥配置

**问题**：无法获取媒体信息

**解决方案**：
1. 注册 TMDB 账号：https://www.themoviedb.org/
2. 在账号设置中申请 API 密钥
3. 在应用的 **编辑 → 首选项 → API 设置** 中配置密钥
4. 如使用 TVDB，需单独注册：https://www.thetvdb.com/

### 中文乱码问题

**问题**：界面或文件名显示乱码

**解决方案**：
1. 确保系统支持 UTF-8 编码
2. Windows 用户：在区域设置中启用 UTF-8 支持
3. 检查文件系统是否支持 Unicode 文件名
4. 重启应用程序

### 扫描速度慢

**问题**：媒体库扫描非常缓慢

**解决方案**：
1. 检查网络连接（如需在线匹配）
2. 在首选项中调整并发扫描线程数
3. 禁用不需要的扫描选项（如自动下载海报）
4. 对大型媒体库分批次扫描

### 数据库损坏

**问题**：提示数据库错误或无法打开

**解决方案**：
1. 备份现有数据库文件
2. 使用 **文件 → 导出媒体库** 导出数据
3. 删除损坏的数据库文件
4. 重新创建媒体库并导入数据

## 获取帮助

- **应用内帮助**：点击 **帮助 → 帮助中心**
- **问题反馈**：在 GitHub Issues 中提交问题
- **功能建议**：在 GitHub Discussions 中讨论

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 如何贡献

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加某个很棒的功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 编码规范
- 使用 Black 进行代码格式化
- 为新功能添加测试
- 编写清晰的中文注释和文档

## 致谢

本项目使用了以下优秀的开源项目：

- [PySide6](https://www.qt.io/qt-for-python) - Qt for Python
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL 工具包
- [Requests](https://requests.readthedocs.io/) - HTTP 库
- [Pytest](https://pytest.org/) - 测试框架

感谢 [TMDB](https://www.themoviedb.org/) 和 [TVDB](https://www.thetvdb.com/) 提供的 API 服务。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**影藏·媒体管理器** - 让媒体管理更简单
