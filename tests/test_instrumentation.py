"""Tests for performance instrumentation."""

import time

import pytest

from media_manager.instrumentation import (
    Instrumentation,
    counted,
    get_instrumentation,
    reset_instrumentation,
    timed,
)


@pytest.fixture
def instrumentation() -> Instrumentation:
    """Create a fresh instrumentation instance."""
    inst = Instrumentation()
    inst.reset()
    return inst


def test_timer_basic(instrumentation: Instrumentation) -> None:
    """Test basic timer functionality."""
    with instrumentation.timer("test_operation"):
        time.sleep(0.01)  # 10ms

    metrics = instrumentation.get_timer_metrics("test_operation")
    assert metrics is not None
    assert metrics.count == 1
    assert metrics.total_time >= 0.01
    assert metrics.min_time >= 0.01
    assert metrics.max_time >= 0.01
    assert metrics.avg_time >= 0.01


def test_timer_multiple_calls(instrumentation: Instrumentation) -> None:
    """Test timer with multiple calls."""
    for i in range(5):
        with instrumentation.timer("multi_operation"):
            time.sleep(0.001 * (i + 1))  # Variable sleep time

    metrics = instrumentation.get_timer_metrics("multi_operation")
    assert metrics is not None
    assert metrics.count == 5
    assert metrics.min_time < metrics.max_time
    assert abs(metrics.avg_time - metrics.total_time / 5) < 0.0001


def test_timer_disabled(instrumentation: Instrumentation) -> None:
    """Test that timers can be disabled."""
    instrumentation.disable()

    with instrumentation.timer("disabled_operation"):
        time.sleep(0.01)

    metrics = instrumentation.get_timer_metrics("disabled_operation")
    assert metrics is None

    instrumentation.enable()


def test_counter_basic(instrumentation: Instrumentation) -> None:
    """Test basic counter functionality."""
    instrumentation.increment_counter("test_counter")
    instrumentation.increment_counter("test_counter", value=5)

    metrics = instrumentation.get_counter_metrics("test_counter")
    assert metrics is not None
    assert metrics.count == 6
    assert metrics.last_value == 5


def test_counter_with_metadata(instrumentation: Instrumentation) -> None:
    """Test counter with metadata."""
    instrumentation.increment_counter(
        "api_calls", metadata={"endpoint": "/search", "status": 200}
    )
    instrumentation.increment_counter(
        "api_calls", metadata={"endpoint": "/details", "status": 200}
    )

    metrics = instrumentation.get_counter_metrics("api_calls")
    assert metrics is not None
    assert metrics.count == 2
    assert "endpoint" in metrics.metadata
    assert "status" in metrics.metadata


def test_get_all_metrics(instrumentation: Instrumentation) -> None:
    """Test getting all metrics."""
    with instrumentation.timer("operation1"):
        time.sleep(0.001)

    with instrumentation.timer("operation2"):
        time.sleep(0.001)

    instrumentation.increment_counter("counter1")
    instrumentation.increment_counter("counter2", value=3)

    metrics = instrumentation.get_all_metrics()
    assert "timers" in metrics
    assert "counters" in metrics
    assert "operation1" in metrics["timers"]
    assert "operation2" in metrics["timers"]
    assert "counter1" in metrics["counters"]
    assert "counter2" in metrics["counters"]


def test_get_summary(instrumentation: Instrumentation) -> None:
    """Test getting metrics summary."""
    with instrumentation.timer("test_op"):
        time.sleep(0.001)

    instrumentation.increment_counter("test_count", value=10)

    summary = instrumentation.get_summary()
    assert "Performance Metrics Summary" in summary
    assert "test_op" in summary
    assert "test_count" in summary


def test_reset(instrumentation: Instrumentation) -> None:
    """Test resetting metrics."""
    with instrumentation.timer("operation"):
        time.sleep(0.001)

    instrumentation.increment_counter("counter")

    assert len(instrumentation.timers) > 0
    assert len(instrumentation.counters) > 0

    instrumentation.reset()

    assert len(instrumentation.timers) == 0
    assert len(instrumentation.counters) == 0


def test_timed_decorator() -> None:
    """Test timed decorator."""
    reset_instrumentation()
    inst = get_instrumentation()

    @timed("decorated_function")
    def slow_function():
        time.sleep(0.01)
        return "result"

    result = slow_function()
    assert result == "result"

    metrics = inst.get_timer_metrics("decorated_function")
    assert metrics is not None
    assert metrics.count == 1
    assert metrics.total_time >= 0.01


def test_counted_decorator() -> None:
    """Test counted decorator."""
    reset_instrumentation()
    inst = get_instrumentation()

    @counted("function_calls")
    def my_function():
        return "result"

    for _ in range(5):
        my_function()

    metrics = inst.get_counter_metrics("function_calls")
    assert metrics is not None
    assert metrics.count == 5


def test_timer_nested(instrumentation: Instrumentation) -> None:
    """Test nested timers."""
    with instrumentation.timer("outer"):
        time.sleep(0.005)
        with instrumentation.timer("inner"):
            time.sleep(0.005)

    outer_metrics = instrumentation.get_timer_metrics("outer")
    inner_metrics = instrumentation.get_timer_metrics("inner")

    assert outer_metrics is not None
    assert inner_metrics is not None
    assert outer_metrics.total_time >= inner_metrics.total_time


def test_timer_exception_handling(instrumentation: Instrumentation) -> None:
    """Test that timers work correctly even with exceptions."""
    try:
        with instrumentation.timer("exception_operation"):
            time.sleep(0.001)
            raise ValueError("Test exception")
    except ValueError:
        pass

    metrics = instrumentation.get_timer_metrics("exception_operation")
    assert metrics is not None
    assert metrics.count == 1
    assert metrics.total_time >= 0.001


def test_record_timer_directly(instrumentation: Instrumentation) -> None:
    """Test recording timer values directly."""
    instrumentation.record_timer("manual_timer", 0.123)
    instrumentation.record_timer("manual_timer", 0.456)

    metrics = instrumentation.get_timer_metrics("manual_timer")
    assert metrics is not None
    assert metrics.count == 2
    assert metrics.min_time == 0.123
    assert metrics.max_time == 0.456
    assert abs(metrics.avg_time - (0.123 + 0.456) / 2) < 0.0001


def test_global_instrumentation() -> None:
    """Test global instrumentation singleton."""
    inst1 = get_instrumentation()
    inst2 = get_instrumentation()
    assert inst1 is inst2

    reset_instrumentation()
    inst3 = get_instrumentation()
    assert len(inst3.timers) == 0
    assert len(inst3.counters) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
