# 性能测试

本目录包含使用 pytest-benchmark 的影藏·媒体管理器应用程序自动化性能基准测试。

## 概述

性能测试套件涵盖：

- **数据库操作**：搜索查询、分页、计数查询、批量插入
- **扫描性能**：文件发现、元数据提取、媒体库扫描
- **界面性能**：模型加载、分页、过滤、排序
- **匹配性能**：提供商搜索、模糊匹配、批量操作

## 运行性能测试

### 前提条件

使用 pytest-benchmark 安装开发依赖：

```bash
pip install -e ".[dev]"
```

### 运行所有基准测试

```bash
# 运行所有性能基准测试
pytest tests/performance/ -m benchmark --benchmark-only

# 或使用性能运行器
python tests/performance/runner.py
```

### 运行特定测试套件

```bash
# 数据库性能
pytest tests/performance/test_database_performance.py -m benchmark --benchmark-only

# 扫描性能
pytest tests/performance/test_scanning_performance.py -m benchmark --benchmark-only

# 界面性能
pytest tests/performance/test_ui_performance.py -m benchmark --benchmark-only

# 匹配性能
pytest tests/performance/test_matching_performance.py -m benchmark --benchmark-only

# 或使用运行器
python tests/performance/runner.py --suite database
python tests/performance/runner.py --suite scanning
python tests/performance/runner.py --suite ui
python tests/performance/runner.py --suite matching
```

### 生成报告

```bash
# 生成性能报告
python tests/performance/runner.py --report

# 保存结果并生成报告
python tests/performance/runner.py --output my_benchmark --report
```

### 管理基准线

```bash
# 将当前结果设置为基准线
python tests/performance/runner.py --set-baseline

# 与基准线比较（默认行为）
python tests/performance/runner.py

# 跳过基准线比较
python tests/performance/runner.py --no-compare
```

## 性能阈值

基准测试包含以下阈值的自动回归测试：

### 数据库操作
- 搜索查询：< 500ms
- 计数查询：< 50ms
- 单条插入：< 1ms
- 批量插入（100 项）：< 100ms

### 界面操作
- 初始加载：< 1s
- 加载更多：< 500ms
- 过滤：< 300ms

### 扫描操作
- 每项处理：< 10ms

### 匹配操作
- 每项匹配：< 50ms

### 内存使用
- 测试期间最大值：< 500MB

## 测试数据

性能测试使用合成数据工厂生成真实的测试数据：

- **媒体库**：最多 5000 个媒体项目
- **媒体项目**：带有完整元数据的电影和电视剧集
- **支持数据**：人物、标签、合集、收藏、演职人员
- **文件结构**：用于扫描测试的嵌套目录

### 数据工厂功能

```python
from tests.performance.data_factories import SyntheticDataFactory

# 创建包含 1000 项的合成媒体库
factory = SyntheticDataFactory(session)
library = factory.create_synthetic_library(
    item_count=1000,
    with_tags=True,
    with_collections=True,
    with_favorites=True,
    with_credits=True
)
```

## 基准测试配置

性能测试在 `pyproject.toml` 中配置：

```toml
[tool.pytest.ini_options]
benchmark_min_rounds = 3
benchmark_max_time = 60.0
benchmark_sort = "min"
```

## 持续集成

性能测试在 CI 中运行：

- **宽松的超时**：性能测试可能比单元测试花费更长时间
- **回归检测**：自动与基准性能比较
- **上传产物**：基准测试结果保存为 CI 产物
- **回归失败**：如果性能显著下降，测试将失败

## 解读结果

### 基准测试输出

```
-------------------------------------------------------------------------------------------------
benchmark (min)    min (max)    mean (std)   median (iqr)   iqr (outliers)  OPS (Kops/s)    rounds
-------------------------------------------------------------------------------------------------
test_search_performance    0.0234 (0.0456)    0.0289 (0.0067)    0.0278 (0.0234-0.0322)    0.0088 (2)      34.6025 (34.6025)     7
-------------------------------------------------------------------------------------------------
```

### 性能回归检测

系统自动检测回归：

- **慢 >10%**：标记为回归
- **快 >5%**：记录为改进
- **±5% 以内**：视为稳定

### 内存使用

监控界面测试期间的内存消耗：

```
界面模型内存使用：245.3MB / 500MB 限制 ✅
```

## 编写新的基准测试

### 基本基准测试

```python
import pytest

@pytest.mark.benchmark
def test_my_operation(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result is not None
```

### 带性能回归测试的基准测试

```python
from tests.performance.conftest import perf_thresholds

@pytest.mark.benchmark
def test_my_operation_regression(benchmark):
    thresholds = perf_thresholds()
    
    result = benchmark.pedantic(
        my_function,
        args=(arg1, arg2),
        iterations=10,
        warmup_rounds=3,
    )
    
    assert result.min < thresholds["my_operation_max_time"], (
        f"性能回归：{result.min:.3f}s > "
        f"{thresholds['my_operation_max_time']}s"
    )
```

### 使用数据工厂

```python
from tests.performance.data_factories import SyntheticDataFactory

@pytest.fixture
def test_data(benchmark_db):
    with benchmark_db.get_session() as session:
        factory = SyntheticDataFactory(session)
        return factory.create_synthetic_library(item_count=1000)

@pytest.mark.benchmark
def test_with_synthetic_data(benchmark, test_data):
    result = benchmark(my_operation, test_data.id)
```

## 故障排除

### 常见问题

1. **测试缓慢**：减少数据大小或增加阈值
2. **内存问题**：使用较小的数据集或延迟加载
3. **不稳定的测试**：增加预热轮次或最小轮次
4. **CI 超时**：使用具有宽松超时的专用性能作业

### 调试

```bash
# 使用详细输出运行
pytest tests/performance/ -v -s

# 使用调试运行特定测试
pytest tests/performance/test_database_performance.py::test_search_performance -v -s

# 生成详细的基准测试报告
pytest tests/performance/ --benchmark-only --benchmark-html=report.html
```

## 最佳实践

1. **隔离操作**：一次测试一个操作
2. **使用真实数据**：合成数据应匹配生产模式
3. **预热**：包含预热轮次以获得稳定的测量
4. **多次迭代**：运行多轮以获得统计显著性
5. **清洁状态**：为每个测试使用新的数据库
6. **模拟外部服务**：避免基准测试中的网络延迟
7. **监控资源**：跟踪内存和 CPU 使用情况
8. **定期基准线**：在进行性能改进时更新基准线

## 性能监控

### 本地开发

```bash
# 快速性能检查
python tests/performance/runner.py --suite database

# 完整性能套件
python tests/performance/runner.py --report
```

### 发布前

```bash
# 完整性能验证
python tests/performance/runner.py --set-baseline
python tests/performance/runner.py --report
```

查看生成的报告：

- 所有基准测试通过阈值
- 无性能回归
- 可接受的内存使用
- 跨运行稳定的性能
