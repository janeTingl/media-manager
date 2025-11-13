"""Performance instrumentation for monitoring and profiling."""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Generator, Optional

from .logging import get_logger

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


@dataclass
class TimerMetrics:
    """Metrics for a timed operation."""

    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    last_time: float = 0.0
    last_timestamp: Optional[datetime] = None

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.count if self.count > 0 else 0.0

    def record(self, duration: float) -> None:
        """Record a new timing measurement."""
        self.count += 1
        self.total_time += duration
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
        self.last_time = duration
        self.last_timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "count": self.count,
            "total_time": self.total_time,
            "avg_time": self.avg_time,
            "min_time": self.min_time if self.min_time != float("inf") else 0.0,
            "max_time": self.max_time,
            "last_time": self.last_time,
            "last_timestamp": self.last_timestamp.isoformat()
            if self.last_timestamp
            else None,
        }


@dataclass
class CounterMetrics:
    """Metrics for a counter."""

    name: str
    count: int = 0
    last_value: Any = None
    last_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def increment(self, value: int = 1, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Increment counter."""
        self.count += value
        self.last_value = value
        self.last_timestamp = datetime.utcnow()
        if metadata:
            self.metadata.update(metadata)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "count": self.count,
            "last_value": self.last_value,
            "last_timestamp": self.last_timestamp.isoformat()
            if self.last_timestamp
            else None,
            "metadata": self.metadata,
        }


class Instrumentation:
    """Central instrumentation for performance monitoring."""

    def __init__(self) -> None:
        """Initialize instrumentation."""
        self.timers: Dict[str, TimerMetrics] = {}
        self.counters: Dict[str, CounterMetrics] = {}
        self._enabled = True

    def enable(self) -> None:
        """Enable instrumentation."""
        self._enabled = True

    def disable(self) -> None:
        """Disable instrumentation."""
        self._enabled = False

    @contextmanager
    def timer(self, name: str) -> Generator[None, None, None]:
        """Context manager for timing operations.

        Args:
            name: Timer name

        Example:
            with instrumentation.timer("database_query"):
                # ... perform operation ...
        """
        if not self._enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            self.record_timer(name, duration)

    def record_timer(self, name: str, duration: float) -> None:
        """Record a timer measurement.

        Args:
            name: Timer name
            duration: Duration in seconds
        """
        if not self._enabled:
            return

        if name not in self.timers:
            self.timers[name] = TimerMetrics(name=name)

        self.timers[name].record(duration)

        # Log slow operations
        if duration > 1.0:  # > 1 second
            logger.warning(f"Slow operation: {name} took {duration:.3f}s")

    def increment_counter(
        self, name: str, value: int = 1, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Increment a counter.

        Args:
            name: Counter name
            value: Value to add
            metadata: Optional metadata
        """
        if not self._enabled:
            return

        if name not in self.counters:
            self.counters[name] = CounterMetrics(name=name)

        self.counters[name].increment(value, metadata)

    def get_timer_metrics(self, name: str) -> Optional[TimerMetrics]:
        """Get metrics for a specific timer.

        Args:
            name: Timer name

        Returns:
            Timer metrics or None
        """
        return self.timers.get(name)

    def get_counter_metrics(self, name: str) -> Optional[CounterMetrics]:
        """Get metrics for a specific counter.

        Args:
            name: Counter name

        Returns:
            Counter metrics or None
        """
        return self.counters.get(name)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "timers": {name: timer.to_dict() for name, timer in self.timers.items()},
            "counters": {
                name: counter.to_dict() for name, counter in self.counters.items()
            },
        }

    def get_summary(self) -> str:
        """Get a human-readable summary of metrics.

        Returns:
            Summary string
        """
        lines = ["=== Performance Metrics Summary ===", ""]

        if self.timers:
            lines.append("Timers:")
            for name, timer in sorted(self.timers.items()):
                lines.append(
                    f"  {name}: "
                    f"count={timer.count}, "
                    f"avg={timer.avg_time:.3f}s, "
                    f"min={timer.min_time:.3f}s, "
                    f"max={timer.max_time:.3f}s"
                )
            lines.append("")

        if self.counters:
            lines.append("Counters:")
            for name, counter in sorted(self.counters.items()):
                lines.append(f"  {name}: count={counter.count}")
            lines.append("")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics."""
        self.timers.clear()
        self.counters.clear()
        logger.info("Instrumentation metrics reset")

    def export_to_log(self) -> None:
        """Export metrics to log."""
        summary = self.get_summary()
        logger.info(f"\n{summary}")


def timed(name: Optional[str] = None) -> Callable:
    """Decorator for timing function execution.

    Args:
        name: Timer name (defaults to function name)

    Example:
        @timed("my_function")
        def my_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        timer_name = name or f"{func.__module__}.{func.__name__}"

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with get_instrumentation().timer(timer_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def counted(name: Optional[str] = None) -> Callable:
    """Decorator for counting function calls.

    Args:
        name: Counter name (defaults to function name)

    Example:
        @counted("my_function_calls")
        def my_function():
            pass
    """

    def decorator(func: Callable) -> Callable:
        counter_name = name or f"{func.__module__}.{func.__name__}.calls"

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            get_instrumentation().increment_counter(counter_name)
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Global instrumentation instance
_instrumentation: Optional[Instrumentation] = None


def get_instrumentation() -> Instrumentation:
    """Get or create the global instrumentation instance.

    Returns:
        Instrumentation instance
    """
    global _instrumentation
    if _instrumentation is None:
        _instrumentation = Instrumentation()
    return _instrumentation


def reset_instrumentation() -> None:
    """Reset global instrumentation."""
    global _instrumentation
    if _instrumentation:
        _instrumentation.reset()
