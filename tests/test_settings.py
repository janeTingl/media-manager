"""Tests for the settings manager."""

import json
import tempfile
from pathlib import Path

from src.media_manager.settings import SettingsManager


class TestSettingsManager:
    """Tests for the settings manager."""

    def test_settings_creation_with_custom_file(self):
        """Test settings manager creation with custom file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "custom_settings.json"
            settings = SettingsManager(settings_file)

            assert settings._settings_file == settings_file
            assert isinstance(settings._settings, dict)

    def test_basic_get_set_operations(self):
        """Test basic get/set operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            # Test setting and getting values
            settings.set("test_key", "test_value")
            assert settings.get("test_key") == "test_value"

            # Test default values
            assert settings.get("nonexistent_key", "default") == "default"
            assert settings.get("nonexistent_key") is None

            # Test overwriting values
            settings.set("test_key", "new_value")
            assert settings.get("test_key") == "new_value"

    def test_json_persistence(self):
        """Test that settings are persisted to JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            # Set some values
            settings.set("string_value", "test")
            settings.set("int_value", 42)
            settings.set("dict_value", {"nested": "value"})
            settings.set("list_value", [1, 2, 3])

            # Save settings
            settings.save_settings()

            # Verify file exists and contains correct data
            assert settings_file.exists()

            with open(settings_file, encoding="utf-8") as f:
                data = json.load(f)

            assert data["string_value"] == "test"
            assert data["int_value"] == 42
            assert data["dict_value"]["nested"] == "value"
            assert data["list_value"] == [1, 2, 3]

            # Create new settings instance and verify loading
            new_settings = SettingsManager(settings_file)
            assert new_settings.get("string_value") == "test"
            assert new_settings.get("int_value") == 42
            assert new_settings.get("dict_value") == {"nested": "value"}
            assert new_settings.get("list_value") == [1, 2, 3]

    def test_api_key_operations(self):
        """Test API key specific operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            # Test setting and getting API keys
            settings.set_api_key("service1", "key1")
            settings.set_api_key("service2", "key2")

            assert settings.get_api_key("service1") == "key1"
            assert settings.get_api_key("service2") == "key2"
            assert settings.get_api_key("nonexistent") is None

            # Test that API keys are stored in the right place
            api_keys = settings.get("api_keys")
            assert api_keys == {"service1": "key1", "service2": "key2"}

    def test_target_folder_operations(self):
        """Test target folder specific operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            # Test setting and getting target folders
            settings.set_target_folder("images", "/path/to/images")
            settings.set_target_folder("videos", "/path/to/videos")

            assert settings.get_target_folder("images") == "/path/to/images"
            assert settings.get_target_folder("videos") == "/path/to/videos"
            assert settings.get_target_folder("nonexistent") is None

            # Test that folders are stored in the right place
            folders = settings.get("target_folders")
            assert folders == {"images": "/path/to/images", "videos": "/path/to/videos"}

    def test_rename_template_operations(self):
        """Test rename template specific operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            # Test setting and getting rename templates
            settings.set_rename_template("default", "{name}_{date}")
            settings.set_rename_template("custom", "{date}_{name}")

            assert settings.get_rename_template("default") == "{name}_{date}"
            assert settings.get_rename_template("custom") == "{date}_{name}"
            assert settings.get_rename_template("nonexistent") is None

            # Test that templates are stored in the right place
            templates = settings.get("rename_templates")
            assert templates == {"default": "{name}_{date}", "custom": "{date}_{name}"}

    def test_load_nonexistent_file(self):
        """Test loading settings when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "nonexistent.json"
            settings = SettingsManager(settings_file)

            # Should start with empty settings
            assert settings._settings == {}

            # Should be able to set and get values
            settings.set("test", "value")
            assert settings.get("test") == "value"

    def test_load_invalid_json(self):
        """Test loading settings when file contains invalid JSON."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "invalid.json"

            # Write invalid JSON
            with open(settings_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json }")

            settings = SettingsManager(settings_file)

            # Should start with empty settings (fallback behavior)
            assert settings._settings == {}

            # Should be able to set and get values
            settings.set("test", "value")
            assert settings.get("test") == "value"
