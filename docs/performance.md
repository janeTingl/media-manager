# Performance Testing

This directory contains automated performance benchmarks for the 影藏·媒体管理器 application using pytest-benchmark.

## Overview

The performance test suite covers:

- **Database Operations**: Search queries, pagination, count queries, bulk inserts
- **Scanning Performance**: File discovery, metadata extraction, library scanning
- **UI Performance**: Model loading, pagination, filtering, sorting
- **Matching Performance**: Provider searches, fuzzy matching, batch operations

## Running Performance Tests

### Prerequisites

Install development dependencies with pytest-benchmark:

```bash
pip install -e ".[dev]"
```

### Running All Benchmarks

```bash
# Run all performance benchmarks
pytest tests/performance/ -m benchmark --benchmark-only

# Or use the performance runner
python tests/performance/runner.py
```

### Running Specific Suites

```bash
# Database performance
pytest tests/performance/test_database_performance.py -m benchmark --benchmark-only

# Scanning performance  
pytest tests/performance/test_scanning_performance.py -m benchmark --benchmark-only

# UI performance
pytest tests/performance/test_ui_performance.py -m benchmark --benchmark-only

# Matching performance
pytest tests/performance/test_matching_performance.py -m benchmark --benchmark-only

# Or use the runner
python tests/performance/runner.py --suite database
python tests/performance/runner.py --suite scanning
python tests/performance/runner.py --suite ui
python tests/performance/runner.py --suite matching
```

### Generating Reports

```bash
# Generate performance report
python tests/performance/runner.py --report

# Save results and generate report
python tests/performance/runner.py --output my_benchmark --report
```

### Managing Baselines

```bash
# Set current results as baseline
python tests/performance/runner.py --set-baseline

# Compare with baseline (default behavior)
python tests/performance/runner.py

# Skip baseline comparison
python tests/performance/runner.py --no-compare
```

## Performance Thresholds

The benchmarks include automated regression tests with the following thresholds:

### Database Operations
- Search queries: < 500ms
- Count queries: < 50ms  
- Single insert: < 1ms
- Batch insert (100 items): < 100ms

### UI Operations
- Initial load: < 1s
- Fetch more: < 500ms
- Filtering: < 300ms

### Scanning Operations
- Per item processing: < 10ms

### Matching Operations
- Per item matching: < 50ms

### Memory Usage
- Maximum during tests: < 500MB

## Test Data

The performance tests use synthetic data factories to generate realistic test data:

- **Libraries**: Up to 5000 media items
- **Media Items**: Movies and TV episodes with full metadata
- **Supporting Data**: Persons, tags, collections, favorites, credits
- **File Structure**: Nested directories for scanning tests

### Data Factory Features

```python
from tests.performance.data_factories import SyntheticDataFactory

# Create synthetic library with 1000 items
factory = SyntheticDataFactory(session)
library = factory.create_synthetic_library(
    item_count=1000,
    with_tags=True,
    with_collections=True,
    with_favorites=True,
    with_credits=True
)
```

## Benchmark Configuration

Performance tests are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
benchmark_min_rounds = 3
benchmark_max_time = 60.0
benchmark_sort = "min"
```

## Continuous Integration

Performance tests run in CI with:

- **Relaxed Timeouts**: Performance tests can take longer than unit tests
- **Regression Detection**: Automated comparison with baseline performance
- **Artifact Upload**: Benchmark results saved as CI artifacts
- **Failure on Regression**: Tests fail if performance degrades significantly

## Interpreting Results

### Benchmark Output

```
-------------------------------------------------------------------------------------------------
benchmark (min)    min (max)    mean (std)   median (iqr)   iqr (outliers)  OPS (Kops/s)    rounds  -------------------------------------------------------------------------------------------------
test_search_performance    0.0234 (0.0456)    0.0289 (0.0067)    0.0278 (0.0234-0.0322)    0.0088 (2)      34.6025 (34.6025)     7
-------------------------------------------------------------------------------------------------
```

### Performance Regression Detection

The system automatically detects regressions:

- **>10% slower**: Flagged as regression
- **>5% faster**: Noted as improvement
- **Within ±5%**: Considered stable

### Memory Usage

Monitor memory consumption during UI tests:

```
UI model memory usage: 245.3MB / 500MB limit ✅
```

## Writing New Benchmarks

### Basic Benchmark

```python
import pytest

@pytest.mark.benchmark
def test_my_operation(benchmark):
    result = benchmark(my_function, arg1, arg2)
    assert result is not None
```

### Benchmark with Performance Regression Test

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
        f"Performance regression: {result.min:.3f}s > "
        f"{thresholds['my_operation_max_time']}s"
    )
```

### Using Data Factories

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

## Troubleshooting

### Common Issues

1. **Slow Tests**: Reduce data size or increase thresholds
2. **Memory Issues**: Use smaller datasets or lazy loading
3. **Flaky Tests**: Increase warmup rounds or min_rounds
4. **CI Timeouts**: Use dedicated performance job with relaxed timeouts

### Debugging

```bash
# Run with verbose output
pytest tests/performance/ -v -s

# Run specific test with debugging
pytest tests/performance/test_database_performance.py::test_search_performance -v -s

# Generate detailed benchmark report
pytest tests/performance/ --benchmark-only --benchmark-html=report.html
```

## Best Practices

1. **Isolate Operations**: Test one operation at a time
2. **Use Realistic Data**: Synthetic data should match production patterns
3. **Warm Up**: Include warmup rounds for stable measurements
4. **Multiple Iterations**: Run multiple rounds for statistical significance
5. **Clean State**: Use fresh databases for each test
6. **Mock External Services**: Avoid network latency in benchmarks
7. **Monitor Resources**: Track memory and CPU usage
8. **Regular Baselines**: Update baselines when performance improvements are made

## Performance Monitoring

### Local Development

```bash
# Quick performance check
python tests/performance/runner.py --suite database

# Full performance suite
python tests/performance/runner.py --report
```

### Before Release

```bash
# Complete performance validation
python tests/performance/runner.py --set-baseline
python tests/performance/runner.py --report
```

Review the generated report for:

- All benchmarks passing thresholds
- No performance regressions
- Acceptable memory usage
- Stable performance across runs