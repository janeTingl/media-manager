# Performance Optimization Guide

This document describes the performance optimizations implemented in the media manager application.

## Overview

The application has been optimized to handle large media libraries (10,000+ items) efficiently with the following features:

- **Provider result caching** with database and optional Redis/diskcache backends
- **Database indexing** for common query patterns
- **Lazy loading** for UI lists with virtual scrolling support
- **Optimized worker thread pools** based on CPU count
- **Performance instrumentation** for monitoring and profiling
- **Benchmark tests** to ensure performance targets are met

## Performance Targets

- **Search operations**: < 500ms for libraries with 10,000+ items
- **UI loading**: < 1s for initial page load
- **Pagination (fetchMore)**: < 500ms for subsequent pages
- **Person/credit queries**: < 100ms
- **Count queries**: < 50ms

## Features

### 1. Provider Caching

Provider API responses are cached to reduce external API calls and improve response times.

#### Configuration

```python
from media_manager.settings import get_settings

settings = get_settings()

# Enable/disable provider caching
settings.set_provider_cache_enabled(True)

# Set TTL (time-to-live) in seconds
settings.set_provider_cache_ttl(3600)  # 1 hour

# Choose backend: 'db', 'redis', or 'disk'
settings.set_cache_backend_type('db')
```

#### Using Redis Backend

Install Redis support:
```bash
pip install media-manager[cache]
```

Configure Redis URL:
```python
settings.set_redis_url('redis://localhost:6379/0')
```

#### Using Disk Cache Backend

Install diskcache:
```bash
pip install media-manager[cache]
```

Configure cache directory:
```python
settings.set_disk_cache_dir('/path/to/cache')
```

### 2. Database Indexes

The migration `001_performance_indexes.py` adds composite indexes for:

- **MediaItem**: library_id+title, library_id+year, library_id+media_type, title+year, season+episode
- **Credit**: media_item_id+role, person_id+role
- **ExternalId**: source+external_id
- **Artwork**: media_item_id+artwork_type, download_status+artwork_type
- **Subtitle**: media_item_id+language, download_status+language
- **HistoryEvent**: media_item_id+event_type, event_type+timestamp
- **JobRun**: library_id+status, job_type+status

Run migration:
```bash
alembic upgrade head
```

### 3. Lazy Loading Models

Use `LazyMediaItemModel` for efficient list rendering:

```python
from media_manager.lazy_model import LazyMediaItemModel

# Create lazy model
model = LazyMediaItemModel(
    page_size=100,  # Items per page
    prefetch_threshold=20,  # Prefetch when 20 items from end
    library_id=1  # Optional library filter
)

# Use with list view
list_view.setModel(model)

# The model automatically loads more data as the user scrolls
```

### 4. Performance Instrumentation

Track performance metrics in your code:

```python
from media_manager.instrumentation import get_instrumentation

instrumentation = get_instrumentation()

# Time operations
with instrumentation.timer("my_operation"):
    # ... perform operation ...
    pass

# Count events
instrumentation.increment_counter("api_calls")

# Get metrics
metrics = instrumentation.get_all_metrics()
summary = instrumentation.get_summary()
```

Use decorators:

```python
from media_manager.instrumentation import timed, counted

@timed("my_function")
def my_function():
    pass

@counted("function_calls")
def another_function():
    pass
```

### 5. Worker Thread Pool Optimization

The `WorkerManager` automatically configures thread pool size based on CPU count:

```python
from media_manager.workers import WorkerManager

# Auto-configure (2x CPU count for I/O-bound operations)
worker_manager = WorkerManager()

# Or specify manually
worker_manager = WorkerManager(max_thread_count=8)
```

### 6. Performance Utilities

```python
from media_manager.performance_utils import (
    setup_cache_backend,
    get_performance_report,
    print_performance_report,
    export_performance_metrics,
    clear_expired_cache,
    optimize_thread_pool_size,
    run_cache_maintenance,
)

# Setup cache on application start
setup_cache_backend()

# Get performance report
report = get_performance_report()
print(report)

# Export metrics to file
export_performance_metrics("metrics.json")

# Maintenance
cleared = clear_expired_cache()
results = run_cache_maintenance()

# Get recommendations
optimal_threads = optimize_thread_pool_size()
```

## Benchmark Tests

Run performance benchmarks:

```bash
# Run all benchmarks
pytest tests/test_performance_benchmarks.py -v -s -m benchmark

# Run specific benchmark
pytest tests/test_performance_benchmarks.py::test_benchmark_search_performance -v -s

# Skip benchmarks in regular test runs
pytest -m "not benchmark"
```

Benchmarks include:

- **Library creation**: Generate 10,000 synthetic items
- **Search performance**: Test various search patterns
- **UI loading**: Test initial load and pagination
- **Person queries**: Test credit/person lookups
- **Count queries**: Test counting operations

## Monitoring and Profiling

### View Performance Metrics

```python
from media_manager.instrumentation import get_instrumentation

instrumentation = get_instrumentation()

# Print summary to console
print(instrumentation.get_summary())

# Export to log
instrumentation.export_to_log()

# Get specific metrics
timer_metrics = instrumentation.get_timer_metrics("database_query")
counter_metrics = instrumentation.get_counter_metrics("cache_hits")
```

### Cache Statistics

```python
from media_manager.cache_service import get_cache_service

cache_service = get_cache_service()

stats = cache_service.get_stats()
print(f"Total entries: {stats['total_entries']}")
print(f"Active entries: {stats['active_entries']}")
print(f"Total hits: {stats['total_hits']}")
```

## Best Practices

1. **Use lazy loading** for large lists (100+ items)
2. **Enable provider caching** to reduce API calls
3. **Run cache maintenance** periodically to clear expired entries
4. **Monitor performance metrics** during development
5. **Run benchmark tests** before releases to catch regressions
6. **Use indexes** for frequently queried fields
7. **Batch operations** when processing multiple items
8. **Optimize thread pool size** for your workload

## Troubleshooting

### Slow Queries

1. Check if indexes are applied:
   ```bash
   alembic current
   alembic upgrade head
   ```

2. Enable query logging to identify slow queries

3. Use instrumentation to measure query times:
   ```python
   with instrumentation.timer("specific_query"):
       results = repository.search(query)
   ```

### High Memory Usage

1. Use lazy loading with smaller page sizes
2. Clear expired cache entries regularly
3. Reduce prefetch threshold
4. Use pagination instead of loading all items

### Cache Issues

1. Check cache backend configuration
2. Verify Redis/diskcache connection
3. Check cache TTL settings
4. Clear cache if stale:
   ```python
   cache_service.clear_all()
   ```

### Thread Pool Issues

1. Monitor active worker count
2. Adjust thread pool size if needed
3. Check for thread starvation
4. Use batch operations to reduce worker count

## Future Improvements

- **Query result caching** at the repository level
- **Background cache warming** for frequently accessed data
- **Adaptive prefetching** based on scroll speed
- **Database query plan analysis** and optimization
- **Compression** for large cache entries
- **Cache key namespacing** for multi-tenant scenarios
- **Distributed caching** with Redis cluster support
