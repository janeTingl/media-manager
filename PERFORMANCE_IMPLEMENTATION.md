# Performance Testing Implementation

This document summarizes the implementation of automated performance testing for 影藏·媒体管理器.

## Overview

A comprehensive performance testing suite has been implemented using `pytest-benchmark` with synthetic data factories to validate application performance under realistic load conditions.

## Implementation Details

### 1. Dependencies and Configuration

**Updated pyproject.toml:**
- Added `pytest-benchmark>=4.0.0` to dev dependencies
- Configured benchmark settings:
  - `benchmark_min_rounds = 3`
  - `benchmark_max_time = 60.0` 
  - `benchmark_sort = "min"`
- Added `benchmark` marker to pytest configuration

### 2. Test Structure

**New Directory Structure:**
```
tests/performance/
├── __init__.py
├── conftest.py                 # Performance fixtures and thresholds
├── data_factories.py           # Synthetic data generation
├── runner.py                   # Performance test runner and utilities
├── test_database_performance.py
├── test_scanning_performance.py
├── test_ui_performance.py
└── test_matching_performance.py
```

### 3. Performance Thresholds

**Configured thresholds in conftest.py:**
- Database operations: Search < 500ms, Count < 50ms, Insert < 1ms
- UI operations: Initial load < 1s, Fetch more < 500ms, Filter < 300ms
- Scanning: < 10ms per item
- Matching: < 50ms per item
- Memory usage: < 500MB limit

### 4. Synthetic Data Factory

**data_factories.py features:**
- Creates realistic media libraries with full metadata
- Supports movies, TV episodes, persons, tags, collections, favorites
- Batch creation for performance testing (5000+ items)
- Configurable relationships and metadata complexity

### 5. Benchmark Categories

#### Database Performance (test_database_performance.py)
- Search queries with various filters
- Pagination performance
- Count query optimization
- Bulk insert operations
- Complex join queries
- Person/credit relationship queries

#### Scanning Performance (test_scanning_performance.py)
- File discovery in large directory structures
- Metadata extraction performance
- Full library scanning
- Filtered scanning operations
- Error handling performance

#### UI Performance (test_ui_performance.py)
- Model loading (lazy vs eager)
- Pagination and fetchMore operations
- Filtering and sorting performance
- Data conversion for UI models
- Memory usage monitoring

#### Matching Performance (test_matching_performance.py)
- Provider search performance
- Batch matching operations
- Fuzzy string matching
- Cache performance
- Error handling overhead

### 6. Performance Regression Detection

**Automated regression tests:**
- Uses `benchmark.pedantic()` for statistical accuracy
- Compares against configured thresholds
- Fails CI on significant performance degradation
- Tracks improvements and regressions

### 7. Performance Test Runner

**runner.py features:**
- Command-line interface for running benchmarks
- Baseline management and comparison
- Report generation in Markdown format
- System resource monitoring
- Historical result tracking

### 8. CI/CD Integration

**GitHub Actions workflow (.github/workflows/performance-tests.yml):**
- Dedicated performance job with 60-minute timeout
- Runs on all pushes and PRs
- Artifact upload for benchmark results
- PR comments with performance summaries
- Baseline updates for main branch
- Regression detection and failure handling

### 9. Documentation

**docs/performance.md:**
- Complete usage guide
- Performance threshold documentation
- Troubleshooting guide
- Best practices for writing benchmarks
- CI/CD integration instructions

## Key Features

### Synthetic Data Generation
- Realistic media libraries with 1000-5000 items
- Full metadata including credits, tags, collections
- Configurable complexity for different test scenarios
- Batch creation for efficient test setup

### Statistical Analysis
- Multiple rounds with warmup for stable measurements
- Min/max/mean/stddev reporting
- Outlier detection and handling
- Confidence intervals for performance claims

### Regression Detection
- Automated threshold checking
- Baseline comparison with percentage change tracking
- CI failure on performance regressions
- Improvement tracking and notification

### Comprehensive Reporting
- HTML and Markdown report generation
- System resource monitoring
- Historical trend tracking
- Performance warnings and recommendations

## Usage Examples

### Running All Benchmarks
```bash
pytest tests/performance/ -m benchmark --benchmark-only
python tests/performance/runner.py
```

### Running Specific Suites
```bash
python tests/performance/runner.py --suite database
python tests/performance/runner.py --suite ui
```

### Generating Reports
```bash
python tests/performance/runner.py --report
```

### Managing Baselines
```bash
python tests/performance/runner.py --set-baseline
```

## Migration from Legacy Tests

The original `test_performance_benchmarks.py` has been:
1. Migrated to the new modular structure
2. Enhanced with pytest-benchmark integration
3. Improved with synthetic data factories
4. Extended with regression detection
5. Backed by comprehensive CI/CD integration

Legacy file moved to `test_performance_benchmarks_legacy.py` for reference.

## Benefits

1. **Automated Regression Detection**: Catches performance issues early
2. **Statistical Rigor**: Multiple rounds and warmup for accurate measurements
3. **Comprehensive Coverage**: Database, UI, scanning, and matching performance
4. **CI/CD Integration**: Automated testing and reporting
5. **Documentation**: Complete usage and troubleshooting guides
6. **Scalability**: Handles large datasets (5000+ items) efficiently
7. **Maintainability**: Modular structure with clear separation of concerns

## Future Enhancements

- Memory profiling integration
- Load testing for concurrent operations
- Performance trend analysis over time
- Integration with application monitoring
- Automated performance optimization suggestions

This implementation provides a solid foundation for maintaining and improving 影藏·媒体管理器 performance as the application scales.