# 帮助系统快速参考

## 用户指南

### 访问帮助

| 操作 | 方法 |
|------|------|
| 打开帮助中心 | 按 **F1** 或选择 **帮助 → 帮助中心** |
| 上下文相关帮助 | 在任何界面按 **F1** |
| 运行新手引导 | 选择 **帮助 → 显示新手引导向导** |

### 导航

| 按键 | 操作 |
|-----|------|
| **F1** | 打开帮助中心 |
| **Ctrl+F** | 聚焦搜索框 |
| **Alt+Left** 或 **后退** | 向后导航 |
| **Alt+Right** 或 **前进** | 向前导航 |
| **Esc** | 关闭帮助中心 |

### 搜索技巧

- 按主题标题搜索
- 按关键词搜索
- 搜索不区分大小写
- 清除搜索以显示所有主题

## 开发者指南

### 文件结构

```
docs/
  zh-CN/                  # 简体中文语言环境
    index.json            # 主题索引
    *.html                # 帮助页面

src/media_manager/
  help_center_dialog.py   # 帮助中心实现
  onboarding_wizard.py    # 新手引导向导

tests/
  test_help_center.py     # 测试
```

### 添加新的帮助主题

1. **在 `docs/zh-CN/` 创建 HTML 文件**：
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="UTF-8">
       <title>您的主题</title>
       <style>
           body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
           h1 { color: #2c3e50; }
       </style>
   </head>
   <body>
       <h1>您的主题</h1>
       <p>内容...</p>
       <a href="other-topic.html">链接到其他主题</a>
   </body>
   </html>
   ```

2. **添加到 index.json**：
   ```json
   {
     "id": "your-topic",
     "title": "您的主题",
     "file": "your-topic.html",
     "keywords": ["关键词1", "关键词2"]
   }
   ```

3. **从其他页面链接**：
   ```html
   <a href="your-topic.html">您的主题</a>
   ```

### 本地化政策

简体中文（`zh-CN`）是唯一支持的语言环境。保持 `docs/zh-CN/` 下的所有帮助内容与应用程序的功能同步。产品不提供其他语言的翻译。

### 测试

```bash
# 验证帮助系统
python3 validate_help.py

# 运行测试
pytest tests/test_help_center.py -v

# 编译检查
python3 -m py_compile src/media_manager/help_center_dialog.py
python3 -m py_compile src/media_manager/onboarding_wizard.py
```

### 上下文映射

编辑 `main_window.py` 以添加/修改上下文映射：

```python
topic_map = {
    0: "library-setup",      # 媒体库标签页
    1: "search",             # 搜索标签页
    2: "welcome",            # 仪表板标签页
    3: "metadata-editing",   # 元数据编辑器标签页
    4: "scanning",           # 匹配/扫描队列标签页
}
```

## API 参考

### HelpCenterDialog

```python
from src.media_manager.help_center_dialog import HelpCenterDialog

# 使用默认主题打开
dialog = HelpCenterDialog()
dialog.exec()

# 使用特定主题打开
dialog = HelpCenterDialog(initial_topic="library-setup")
dialog.exec()

# 以编程方式显示主题
dialog.show_topic("providers")

# 更改语言环境（zh-CN 是唯一支持的选项）
dialog.set_locale("zh-CN")
```

### OnboardingWizard

```python
from src.media_manager.onboarding_wizard import OnboardingWizard

wizard = OnboardingWizard(settings)
if wizard.exec():
    # 用户完成了向导
    pass
```

### Settings

```python
from src.media_manager.settings import get_settings

settings = get_settings()

# 语言设置（仅支持 zh-CN）
locale = settings.get_language()           # 获取界面语言
settings.set_language("zh-CN")             # 重新应用界面语言

# 帮助语言环境（镜像界面语言）
help_locale = settings.get_help_locale()   # 获取帮助语言环境
settings.set_help_locale("zh-CN")          # 重新应用帮助语言环境

# 新手引导
completed = settings.get("onboarding_completed", False)
settings.set("onboarding_completed", True)
```

## 故障排除

### 帮助文件无法加载

**问题**：帮助中心显示"错误"或空白内容

**解决方案**：
1. 检查 `docs/zh-CN/` 目录是否存在
2. 验证 `index.json` 是否为有效的 JSON
3. 确保 HTML 文件存在且可读
4. 运行 `python3 validate_help.py`

### 首次运行时新手引导未显示

**问题**：新手引导向导未出现

**解决方案**：
1. 删除或清除设置文件
2. 或在设置中将 `onboarding_completed` 设置为 `false`
3. 重启应用程序

### 上下文帮助显示错误的主题

**问题**：F1 打开了错误的帮助主题

**解决方案**：
1. 检查 `main_window.py` 中的主题映射
2. 验证主题 ID 是否存在于 `index.json` 中
3. 更新 `_open_context_help()` 方法

### 帮助中的链接损坏

**问题**：点击链接显示"未找到"

**解决方案**：
1. 运行 `python3 validate_help.py` 检查链接
2. 验证目标文件是否存在于 `docs/zh-CN/` 中
3. 确保文件名完全匹配（区分大小写）
4. 检查目标是否列在 `index.json` 中

## 常见自定义

### 更改帮助窗口大小

编辑 `help_center_dialog.py`：
```python
self.resize(900, 700)  # 宽度, 高度
```

### 向帮助页面添加自定义 CSS

添加到 HTML `<style>` 部分：
```html
<style>
    body { font-family: Arial, sans-serif; }
    .custom-class { color: blue; }
</style>
```

### 修改新手引导页面

编辑 `onboarding_wizard.py`：
- 修改现有页面：`WelcomePage`、`LibrarySetupPage` 等
- 添加新页面：创建新的 `QWizardPage` 子类
- 更改顺序：调整 `__init__` 中的 `addPage()` 调用

### 首次运行时跳过新手引导

在 `main_window.py` 中，注释掉：
```python
# self._check_first_run()
```

或在设置中设置：
```python
settings.set("onboarding_completed", True)
```

## 最佳实践

### 对于文档作者

1. **保持简单**：使用清晰简洁的语言
2. **添加关键词**：帮助用户通过搜索找到主题
3. **使用示例**：展示实际用法
4. **链接相关主题**：帮助用户发现相关内容
5. **测试链接**：定期运行验证脚本

### 对于开发者

1. **验证更改**：修改后运行 `validate_help.py`
2. **测试导航**：确保所有链接正常工作
3. **更新测试**：为新主题添加测试
4. **记录上下文**：更新上下文映射
5. **维护索引**：保持 `index.json` 同步
