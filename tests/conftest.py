"""Configuration for pytest and test fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Optional

import pytest

# Set up headless display for Qt before importing PySide6
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QApplication = None  # type: ignore

from src.media_manager.logging import setup_logging
from src.media_manager.services import get_service_registry
from src.media_manager.settings import SettingsManager


@pytest.fixture(scope="session")
def qapp() -> Optional[object]:
    """Create QApplication instance for tests."""
    if not HAS_QT or QApplication is None:
        return None
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit app here as it might be used by other tests


@pytest.fixture
def temp_settings():
    """Create temporary settings manager for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "test_settings.json"
        settings = SettingsManager(settings_file)
        yield settings


@pytest.fixture
def service_registry():
    """Get clean service registry for tests."""
    registry = get_service_registry()
    registry.clear()
    yield registry
    registry.clear()


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup logging for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"
        setup_logging("DEBUG", log_file)
        yield


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "gui: marks tests as GUI tests (may require display)"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "benchmark: marks tests as performance benchmarks (deselect with '-m \"not benchmark\"')")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add GUI marker to tests that use QApplication
        if "qapp" in item.fixturenames:
            item.add_marker(pytest.mark.gui)
