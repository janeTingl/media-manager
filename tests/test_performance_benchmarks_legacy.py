"""Legacy performance benchmarks - migrated to new structure."""

import pytest

# This file contains the original performance benchmarks that have been
# migrated to the new performance test structure in tests/performance/
# 
# The new structure provides:
# - Better organization by functionality (database, scanning, ui, matching)
# - pytest-benchmark integration with proper statistical analysis
# - Performance regression detection with thresholds
# - Synthetic data factories for consistent test data
# - Comprehensive reporting and CI integration
#
# To run performance tests, use:
#   pytest tests/performance/ -m benchmark --benchmark-only
#   python tests/performance/runner.py
#
# The old benchmarks are kept here for reference but should not be run.
# They will be removed in a future release.

@pytest.mark.skip(reason="Migrated to tests/performance/ - use new performance test suite")
def test_legacy_benchmarks():
    """Placeholder to indicate these tests are migrated."""
    pass