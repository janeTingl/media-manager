# 贡献指南

感谢您对影藏·媒体管理器项目的关注！我们欢迎所有形式的贡献，包括错误报告、功能建议、文档改进和代码贡献。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
  - [报告错误](#报告错误)
  - [建议功能](#建议功能)
  - [提交代码](#提交代码)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [测试要求](#测试要求)
- [提交指南](#提交指南)
- [Pull Request 流程](#pull-request-流程)

## 行为准则

参与本项目的所有贡献者都应遵守以下准则：

- 尊重所有贡献者
- 接受建设性的批评
- 关注对项目最有利的事情
- 对社区成员表现出同理心

## 如何贡献

### 报告错误

如果您发现了错误，请在 GitHub Issues 中创建问题报告，包括：

- **清晰的标题** - 简洁描述问题
- **详细描述** - 说明问题的具体表现
- **重现步骤** - 列出重现问题的详细步骤
- **预期行为** - 说明您期望的正确行为
- **实际行为** - 说明实际发生的情况
- **环境信息** - 操作系统、Python 版本、应用版本
- **日志文件** - 如果可能，附上相关日志

### 建议功能

我们欢迎功能建议！提交建议时请包括：

- **功能描述** - 清晰说明建议的功能
- **使用场景** - 说明该功能解决的问题
- **实现思路** - 如果有，可以提供实现建议
- **替代方案** - 考虑过的其他解决方案

### 提交代码

1. **Fork 仓库** - 点击 GitHub 上的 Fork 按钮
2. **克隆仓库** - 克隆您 fork 的仓库到本地
3. **创建分支** - 为您的更改创建新分支
4. **编写代码** - 实现您的功能或修复
5. **添加测试** - 为新代码编写测试
6. **运行测试** - 确保所有测试通过
7. **提交更改** - 遵循提交信息规范
8. **推送代码** - 推送到您的 fork
9. **创建 PR** - 在 GitHub 上创建 Pull Request

## 开发环境设置

### 前置要求

- Python 3.8 或更高版本
- Git

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/your-username/media-manager.git
   cd media-manager
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **安装开发依赖**
   ```bash
   pip install -e ".[dev]"
   ```

4. **验证安装**
   ```bash
   pytest
   ```

## 代码规范

### Python 代码规范

我们遵循 PEP 8 编码规范，并使用以下工具确保代码质量：

#### 代码格式化

使用 Black 进行代码格式化：

```bash
black src/ tests/
```

#### 代码检查

使用 Ruff 进行代码检查：

```bash
# 检查代码
ruff check src/ tests/

# 自动修复问题
ruff check --fix src/ tests/
```

#### 类型检查

使用 MyPy 进行类型检查：

```bash
mypy src/
```

### 代码风格要求

- **命名规范**
  - 类名：使用大驼峰命名法（PascalCase）
  - 函数/方法：使用小写下划线命名法（snake_case）
  - 常量：使用大写下划线命名法（UPPER_CASE）
  - 私有成员：以单下划线开头

- **类型提示**
  - 所有公共函数都应包含类型提示
  - 使用 `from __future__ import annotations` 以支持前向引用

- **文档字符串**
  - 所有公共模块、类、函数都应有文档字符串
  - 使用 Google 风格的文档字符串格式

- **注释**
  - 代码应该是自解释的
  - 只在必要时添加注释
  - 注释使用中文

### 示例代码

```python
"""模块描述。"""

from __future__ import annotations

from typing import Optional


class MediaManager:
    """媒体管理器类。
    
    负责管理媒体文件的扫描、匹配和整理。
    
    Attributes:
        settings: 设置管理器实例
        logger: 日志记录器
    """
    
    def __init__(self, settings: SettingsManager) -> None:
        """初始化媒体管理器。
        
        Args:
            settings: 设置管理器实例
        """
        self._settings = settings
        self._logger = get_logger().get_logger(__name__)
    
    def scan_directory(self, path: str, recursive: bool = True) -> list[MediaFile]:
        """扫描目录以查找媒体文件。
        
        Args:
            path: 要扫描的目录路径
            recursive: 是否递归扫描子目录
            
        Returns:
            找到的媒体文件列表
            
        Raises:
            ValueError: 如果路径不存在
        """
        # 实现代码...
        pass
```

## 测试要求

### 编写测试

- 所有新功能都必须包含测试
- 测试应该覆盖正常情况和边界情况
- 使用描述性的测试函数名

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_scanner.py

# 运行并显示覆盖率
pytest --cov=src/media_manager

# 详细输出
pytest -v
```

### 测试示例

```python
"""扫描器测试。"""

import pytest
from media_manager.scanner import Scanner


class TestScanner:
    """扫描器测试类。"""
    
    def test_scan_directory_finds_files(self, tmp_path):
        """测试扫描目录能找到文件。"""
        # 准备测试数据
        test_file = tmp_path / "movie.mp4"
        test_file.touch()
        
        # 执行扫描
        scanner = Scanner()
        results = scanner.scan_directory(str(tmp_path))
        
        # 验证结果
        assert len(results) == 1
        assert results[0].path == str(test_file)
    
    def test_scan_empty_directory(self, tmp_path):
        """测试扫描空目录。"""
        scanner = Scanner()
        results = scanner.scan_directory(str(tmp_path))
        assert len(results) == 0
```

## 提交指南

### 提交信息格式

使用以下格式编写提交信息：

```
<类型>: <简短描述>

<详细描述>（可选）

<相关问题>（可选）
```

### 提交类型

- **feat**: 新功能
- **fix**: 错误修复
- **docs**: 文档更改
- **style**: 代码格式更改（不影响功能）
- **refactor**: 代码重构
- **test**: 测试相关更改
- **chore**: 构建过程或辅助工具的变动

### 示例

```
feat: 添加批量重命名功能

实现了批量重命名媒体文件的功能，支持自定义命名模板。

相关问题: #123
```

## Pull Request 流程

### 创建 PR 前的检查清单

- [ ] 代码遵循项目的代码规范
- [ ] 已运行 Black、Ruff 和 MyPy
- [ ] 所有测试都通过
- [ ] 为新功能添加了测试
- [ ] 更新了相关文档
- [ ] 提交信息遵循规范

### PR 描述模板

```markdown
## 描述
简要描述此 PR 的目的和内容。

## 变更类型
- [ ] 错误修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 测试
描述如何测试这些更改。

## 截图（如适用）
添加相关截图。

## 相关问题
链接到相关的 GitHub Issues。
```

### 审查流程

1. 创建 PR 后，维护者会审查您的代码
2. 根据反馈进行必要的修改
3. 所有检查通过后，PR 将被合并

## 开发技巧

### 调试

```bash
# 启用调试日志
export MEDIA_MANAGER_LOG_LEVEL=DEBUG
python -m src.media_manager.main
```

### 性能分析

```bash
# 运行性能测试
python tests/performance/runner.py

# 生成性能报告
python tests/performance/runner.py --report
```

## 获取帮助

如果您在贡献过程中遇到问题：

- 查看现有的 Issues 和 Discussions
- 在 GitHub Discussions 中提问
- 查看项目文档

## 致谢

感谢所有贡献者对项目的支持！您的贡献让这个项目变得更好。

---

再次感谢您的贡献！🎉
