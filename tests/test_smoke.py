"""Smoke tests for the media manager application."""

import pytest
from PySide6.QtWidgets import QMenu

from src.media_manager import __version__
from src.media_manager.main import create_application
from src.media_manager.main_window import MainWindow


class TestApplicationSmoke:
    """Smoke tests for basic application functionality."""

    def test_import_application(self):
        """Test that the application can be imported."""
        from src.media_manager.main import main

        assert callable(main)

    def test_import_version(self):
        """Test that version can be imported."""
        assert isinstance(__version__, str)
        assert __version__ == "0.1.0"

    def test_create_application(self, qapp):
        """Test that QApplication can be created."""
        app = create_application()
        assert app is not None
        assert app.applicationName() == "影藏·媒体管理器"
        assert app.applicationVersion() == "0.1.0"

    @pytest.mark.gui
    def test_main_window_instantiation(self, qapp, temp_settings):
        """Test that main window can be instantiated."""
        window = MainWindow(temp_settings)
        assert window is not None
        assert window.windowTitle() == "影藏·媒体管理器"
        assert window.minimumWidth() == 1000
        assert window.minimumHeight() == 700

        # Test that UI components exist
        assert hasattr(window, "file_tree")
        assert hasattr(window, "tab_widget")
        assert hasattr(window, "properties_list")
        assert hasattr(window, "status_bar")

    @pytest.mark.gui
    def test_main_window_show_hide(self, qapp, temp_settings):
        """Test that main window can be shown and hidden."""
        window = MainWindow(temp_settings)

        # Show window
        window.show()
        assert window.isVisible()

        # Hide window
        window.hide()
        assert not window.isVisible()

    @pytest.mark.gui
    def test_main_window_menu_bar(self, qapp, temp_settings):
        """Test that menu bar is properly set up."""
        window = MainWindow(temp_settings)
        menu_bar = window.menuBar()

        # Check menu titles
        assert menu_bar is not None

        # Get menus by title
        menus = [menu.title() for menu in menu_bar.findChildren(QMenu)]
        assert "&File" in menus
        assert "&Edit" in menus
        assert "&View" in menus
        assert "&Help" in menus

    @pytest.mark.gui
    def test_main_window_status_bar(self, qapp, temp_settings):
        """Test that status bar is properly set up."""
        window = MainWindow(temp_settings)
        status_bar = window.statusBar()

        assert status_bar is not None
        assert hasattr(window, "status_label")
        assert hasattr(window, "item_count_label")

        # Test status update
        window.update_status("Test message")
        assert window.status_label.text() == "Test message"

        # Test item count update
        window.update_item_count(42)
        assert window.item_count_label.text() == "42 items"

    @pytest.mark.gui
    def test_main_window_tabs(self, qapp, temp_settings):
        """Test that tabs are properly created."""
        window = MainWindow(temp_settings)

        assert window.tab_widget.count() == 4

        # Check tab titles
        tab_titles = [
            window.tab_widget.tabText(i) for i in range(window.tab_widget.count())
        ]
        assert "Library" in tab_titles
        assert "Recent" in tab_titles
        assert "Favorites" in tab_titles
        assert "Search" in tab_titles

    @pytest.mark.gui
    def test_settings_manager_basic_operations(self, temp_settings):
        """Test basic settings manager operations."""
        settings = temp_settings

        # Test get/set
        settings.set("test_key", "test_value")
        assert settings.get("test_key") == "test_value"
        assert settings.get("nonexistent_key", "default") == "default"

        # Test API key operations
        settings.set_api_key("test_service", "test_api_key")
        assert settings.get_api_key("test_service") == "test_api_key"
        assert settings.get_api_key("nonexistent_service") is None

        # Test target folder operations
        settings.set_target_folder("images", "/path/to/images")
        assert settings.get_target_folder("images") == "/path/to/images"
        assert settings.get_target_folder("nonexistent_type") is None

        # Test rename template operations
        settings.set_rename_template("default", "{name}_{date}")
        assert settings.get_rename_template("default") == "{name}_{date}"
        assert settings.get_rename_template("nonexistent_template") is None

        # Test save
        settings.save_settings()
        assert settings._settings_file.exists()


class TestServiceRegistry:
    """Tests for the service registry."""

    def test_service_registry_basic_operations(self):
        """Test basic service registry operations."""
        from src.media_manager.services import ServiceRegistry

        registry = ServiceRegistry()

        # Test registration
        test_service = {"test": "data"}
        registry.register("TestService", test_service)

        # Test retrieval
        retrieved = registry.get("TestService")
        assert retrieved == test_service

        # Test has
        assert registry.has("TestService")
        assert not registry.has("NonexistentService")

        # Test clear
        registry.clear()
        assert not registry.has("TestService")

    def test_service_registry_singleton_factory(self):
        """Test service registry with singleton factories."""
        from src.media_manager.services import ServiceRegistry

        registry = ServiceRegistry()

        # Register factory
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"created": call_count}

        registry.register("FactoryService", factory, singleton=True)

        # First call should create instance
        instance1 = registry.get("FactoryService")
        assert instance1["created"] == 1
        assert call_count == 1

        # Second call should return same instance
        instance2 = registry.get("FactoryService")
        assert instance2 is instance1
        assert call_count == 1  # Factory not called again

    def test_service_registry_non_singleton(self):
        """Test service registry with non-singleton services."""
        from src.media_manager.services import ServiceRegistry

        registry = ServiceRegistry()

        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"created": call_count}

        registry.register("NonSingletonService", factory, singleton=False)

        # Each call should create new instance
        instance1 = registry.get("NonSingletonService")
        assert instance1["created"] == 1

        instance2 = registry.get("NonSingletonService")
        assert instance2["created"] == 2
        assert instance1 is not instance2


if __name__ == "__main__":
    pytest.main([__file__])
