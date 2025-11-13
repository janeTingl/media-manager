"""Configuration for performance tests."""

import pytest
from pathlib import Path


@pytest.fixture
def perf_data_dir():
    """Get the directory for performance test data."""
    return Path(__file__).parent / "data"


@pytest.fixture
def perf_thresholds():
    """Performance thresholds for benchmarks."""
    return {
        # Database operations (in seconds)
        "db_search_max_time": 0.5,      # Search queries should be < 500ms
        "db_count_max_time": 0.05,      # Count queries should be < 50ms
        "db_insert_max_time": 0.001,    # Single insert should be < 1ms
        "db_batch_insert_max_time": 0.1,  # Batch insert (100 items) should be < 100ms
        
        # UI operations (in seconds)
        "ui_initial_load_max_time": 1.0,  # Initial UI load should be < 1s
        "ui_fetch_more_max_time": 0.5,    # Fetch more should be < 500ms
        "ui_filter_max_time": 0.3,        # Filtering should be < 300ms
        
        # Scanning operations (in seconds per item)
        "scan_max_time_per_item": 0.01,   # Scanning should be < 10ms per item
        
        # Matching operations (in seconds per item)
        "match_max_time_per_item": 0.05,  # Matching should be < 50ms per item
        
        # Memory usage (in MB)
        "memory_max_usage_mb": 500,       # Maximum memory usage during tests
        
        # Database size limits
        "max_db_size_mb": 100,           # Maximum test database size
    }