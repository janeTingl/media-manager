"""Configuration for pytest and test fixtures."""

import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from src.media_manager.logging import setup_logging
from src.media_manager.services import get_service_registry
from src.media_manager.settings import SettingsManager


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
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


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers."""
    for item in items:
        # Add GUI marker to tests that use QApplication
        if "qapp" in item.fixturenames:
            item.add_marker(pytest.mark.gui)
