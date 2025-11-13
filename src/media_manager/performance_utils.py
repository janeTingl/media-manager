"""Utilities for performance monitoring and optimization."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

from .cache_service import (
    CacheService,
    DiskCacheBackend,
    RedisBackend,
    get_cache_service,
    initialize_cache_service,
)
from .instrumentation import get_instrumentation
from .logging import get_logger
from .settings import get_settings

if TYPE_CHECKING:
    pass

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


def setup_cache_backend() -> Optional[CacheService]:
    """Set up cache backend based on settings.

    Returns:
        Configured cache service or None if disabled
    """
    settings = get_settings()

    # Check if provider caching is enabled
    if not settings.get_provider_cache_enabled():
        logger.info("Provider caching is disabled")
        return None

    backend_type = settings.get_cache_backend_type()
    ttl = settings.get_provider_cache_ttl()

    backend = None

    if backend_type == "redis":
        redis_url = settings.get_redis_url()
        if redis_url:
            try:
                import redis

                redis_client = redis.from_url(redis_url)
                # Test connection
                redis_client.ping()
                backend = RedisBackend(redis_client)
                logger.info(f"Redis cache backend configured: {redis_url}")
            except ImportError:
                logger.warning("redis-py not installed, falling back to database cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}, falling back to database cache")
        else:
            logger.warning("Redis backend selected but no URL configured")

    elif backend_type == "disk":
        disk_cache_dir = settings.get_disk_cache_dir()
        if disk_cache_dir:
            try:
                backend = DiskCacheBackend(disk_cache_dir)
                logger.info(f"Disk cache backend configured: {disk_cache_dir}")
            except Exception as e:
                logger.warning(f"Failed to initialize disk cache: {e}, falling back to database cache")
        else:
            logger.warning("Disk backend selected but no directory configured")

    # Initialize cache service
    cache_service = initialize_cache_service(
        backend=backend,
        default_ttl=ttl,
        use_db_cache=True,  # Always use DB as fallback
    )

    logger.info(
        f"Cache service initialized: backend={backend_type}, ttl={ttl}s, "
        f"use_db_cache=True"
    )

    return cache_service


def get_performance_report() -> str:
    """Get a comprehensive performance report.

    Returns:
        Formatted performance report
    """
    instrumentation = get_instrumentation()
    cache_service = get_cache_service()

    lines = [
        "=" * 80,
        "PERFORMANCE REPORT",
        "=" * 80,
        "",
    ]

    # Instrumentation metrics
    metrics = instrumentation.get_all_metrics()

    if metrics["timers"]:
        lines.append("TIMING METRICS:")
        lines.append("-" * 80)
        sorted_timers = sorted(
            metrics["timers"].items(),
            key=lambda x: x[1]["avg_time"],
            reverse=True,
        )
        for name, timer_data in sorted_timers:
            lines.append(
                f"  {name}:"
                f"\n    Count: {timer_data['count']}"
                f"\n    Avg: {timer_data['avg_time'] * 1000:.2f}ms"
                f"\n    Min: {timer_data['min_time'] * 1000:.2f}ms"
                f"\n    Max: {timer_data['max_time'] * 1000:.2f}ms"
                f"\n    Total: {timer_data['total_time']:.2f}s"
            )
        lines.append("")

    if metrics["counters"]:
        lines.append("COUNTER METRICS:")
        lines.append("-" * 80)
        sorted_counters = sorted(
            metrics["counters"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        )
        for name, counter_data in sorted_counters:
            lines.append(f"  {name}: {counter_data['count']}")
        lines.append("")

    # Cache statistics
    try:
        cache_stats = cache_service.get_stats()
        if cache_stats:
            lines.append("CACHE STATISTICS:")
            lines.append("-" * 80)
            lines.append(f"  Total entries: {cache_stats.get('total_entries', 0)}")
            lines.append(f"  Active entries: {cache_stats.get('active_entries', 0)}")
            lines.append(f"  Expired entries: {cache_stats.get('expired_entries', 0)}")
            lines.append(f"  Total hits: {cache_stats.get('total_hits', 0)}")
            lines.append("")
    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")

    # System info
    lines.append("SYSTEM INFORMATION:")
    lines.append("-" * 80)
    lines.append(f"  CPU cores: {os.cpu_count()}")
    try:
        import psutil
        memory = psutil.virtual_memory()
        lines.append(f"  Memory usage: {memory.percent}%")
        lines.append(f"  Available memory: {memory.available / (1024**3):.2f} GB")
    except ImportError:
        lines.append("  psutil not installed - memory info unavailable")

    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)


def print_performance_report() -> None:
    """Print performance report to console."""
    report = get_performance_report()
    print(report)


def export_performance_metrics(filename: str) -> None:
    """Export performance metrics to a file.

    Args:
        filename: Output filename
    """
    import json
    from datetime import datetime

    instrumentation = get_instrumentation()
    cache_service = get_cache_service()

    metrics_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "instrumentation": instrumentation.get_all_metrics(),
        "cache_stats": cache_service.get_stats(),
        "system_info": {
            "cpu_cores": os.cpu_count(),
        },
    }

    try:
        import psutil
        memory = psutil.virtual_memory()
        metrics_data["system_info"]["memory_percent"] = memory.percent
        metrics_data["system_info"]["available_memory_gb"] = memory.available / (1024**3)
    except ImportError:
        pass

    with open(filename, "w") as f:
        json.dump(metrics_data, f, indent=2)

    logger.info(f"Performance metrics exported to {filename}")


def clear_expired_cache() -> int:
    """Clear expired cache entries.

    Returns:
        Number of entries cleared
    """
    cache_service = get_cache_service()
    count = cache_service.clear_expired()
    logger.info(f"Cleared {count} expired cache entries")
    return count


def optimize_thread_pool_size() -> int:
    """Calculate optimal thread pool size based on system resources.

    Returns:
        Recommended thread pool size
    """
    cpu_count = os.cpu_count() or 4

    # For I/O-bound operations (network requests), use more threads
    # Rule of thumb: 2x CPU count for I/O-bound work
    optimal_size = max(4, cpu_count * 2)

    logger.info(
        f"Recommended thread pool size: {optimal_size} "
        f"(based on {cpu_count} CPU cores)"
    )

    return optimal_size


def get_batch_size_recommendation(total_items: int) -> int:
    """Get recommended batch size for processing items.

    Args:
        total_items: Total number of items to process

    Returns:
        Recommended batch size
    """
    cpu_count = os.cpu_count() or 4

    # Base batch size on CPU count and total items
    if total_items < 100:
        return max(10, total_items // 4)
    elif total_items < 1000:
        return max(50, cpu_count * 10)
    else:
        return max(100, cpu_count * 25)


def run_cache_maintenance() -> dict[str, int]:
    """Run cache maintenance tasks.

    Returns:
        Dictionary with maintenance results
    """
    results = {}

    # Clear expired entries
    results["expired_cleared"] = clear_expired_cache()

    # Get cache stats
    cache_service = get_cache_service()
    stats = cache_service.get_stats()

    if stats:
        results["total_entries"] = stats.get("total_entries", 0)
        results["active_entries"] = stats.get("active_entries", 0)

        # If cache is too large, consider clearing older entries
        if results["total_entries"] > 10000:
            logger.warning(
                f"Cache has {results['total_entries']} entries. "
                "Consider adjusting TTL or clearing cache."
            )

    return results
