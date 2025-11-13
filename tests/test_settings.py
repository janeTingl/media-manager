"""Tests for the settings manager."""

import json
import tempfile
from pathlib import Path

from src.media_manager.settings import SettingsManager


class TestSettingsManager:
    """Tests for the settings manager."""

    def test_settings_creation_with_custom_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "custom_settings.json"
            settings = SettingsManager(settings_file)

            assert settings._settings_file == settings_file
            # Default domains should be initialized
            assert "library_settings" in settings._settings
            assert "providers" in settings._settings

    def test_basic_get_set_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set("test_key", "test_value")
            assert settings.get("test_key") == "test_value"

            assert settings.get("nonexistent_key", "default") == "default"
            assert settings.get("nonexistent_key") is None

            settings.set("test_key", "new_value")
            assert settings.get("test_key") == "new_value"

    def test_json_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set("string_value", "test")
            settings.set("int_value", 42)
            settings.set("dict_value", {"nested": "value"})
            settings.set("list_value", [1, 2, 3])

            settings.save_settings()
            assert settings_file.exists()

            with open(settings_file, encoding="utf-8") as f:
                data = json.load(f)

            assert data["string_value"] == "test"
            assert data["int_value"] == 42
            assert data["dict_value"]["nested"] == "value"
            assert data["list_value"] == [1, 2, 3]

            new_settings = SettingsManager(settings_file)
            assert new_settings.get("string_value") == "test"
            assert new_settings.get("int_value") == 42
            assert new_settings.get("dict_value") == {"nested": "value"}
            assert new_settings.get("list_value") == [1, 2, 3]

    def test_api_key_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set_api_key("service1", "key1")
            settings.set_api_key("service2", "key2")

            assert settings.get_api_key("service1") == "key1"
            assert settings.get_api_key("service2") == "key2"
            assert settings.get_api_key("nonexistent") is None

            provider_keys = settings.get_provider_keys()
            assert provider_keys == {"service1": "key1", "service2": "key2"}

            settings.set_api_key("service1", "")
            assert "service1" not in settings.get_provider_keys()

    def test_target_folder_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set_target_folder("images", "/path/to/images")
            settings.set_target_folder("videos", "/path/to/videos")

            assert settings.get_target_folder("images") == "/path/to/images"
            assert settings.get_target_folder("videos") == "/path/to/videos"
            assert settings.get_target_folder("nonexistent") is None

            folders = settings.get("target_folders")
            assert folders == {"images": "/path/to/images", "videos": "/path/to/videos"}

    def test_rename_template_operations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set_rename_template("default", "{name}_{date}")
            settings.set_rename_template("custom", "{date}_{name}")

            assert settings.get_rename_template("default") == "{name}_{date}"
            assert settings.get_rename_template("custom") == "{date}_{name}"
            assert settings.get_rename_template("nonexistent") is None

            metadata_settings = settings._settings["metadata_settings"]
            assert metadata_settings["rename_templates"] == {
                "default": "{name}_{date}",
                "custom": "{date}_{name}",
            }

    def test_library_settings_domain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set_default_library_id(5)
            settings.set_last_active_library_id(3)
            settings.set_library_setting("auto_restore_last", True)

            assert settings.get_default_library_id() == 5
            assert settings.get_last_active_library_id() == 3
            assert settings.get_library_setting("auto_restore_last") is True

    def test_cache_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir) / "cache"
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            settings.set_cache_dir(str(cache_dir))
            assert settings.get_cache_dir() == str(cache_dir)
            assert settings.get_cache_setting("poster_cache_dir") == str(cache_dir)

            settings.set_cache_setting("shared_cache_dir", str(cache_dir))
            assert settings.get_cache_setting("shared_cache_dir") == str(cache_dir)

    def test_ui_layout_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            geometry = "abcd"
            state = "1234"
            settings.set_ui_layout("main_window.geometry", geometry)
            settings.set_ui_layout("main_window.state", state)

            assert settings.get_ui_layout("main_window.geometry") == geometry
            assert settings.get_ui_layout("main_window.state") == state

    def test_trailer_quality_setting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SettingsManager(Path(temp_dir) / "test_settings.json")

            settings.set_trailer_quality("4K")
            assert settings.get_trailer_quality().upper() == "4K"

    def test_logging_and_batch_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SettingsManager(Path(temp_dir) / "test_settings.json")

            settings.set_logging_level("debug")
            assert settings.get_logging_level() == "DEBUG"

            defaults = {
                "rename": True,
                "move": False,
                "delete": True,
                "tags": True,
                "metadata": False,
                "resync": True,
                "move_library_id": 7,
            }
            settings.set_batch_defaults(defaults)
            stored = settings.get_batch_defaults()
            assert stored["rename"] is True
            assert stored["delete"] is True
            assert stored["move_library_id"] == 7

    def test_setting_changed_signal_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = SettingsManager(Path(temp_dir) / "test_settings.json")

            captured = []
            settings.setting_changed.connect(lambda key, value: captured.append((key, value)))

            settings.set_ui_setting("theme", "dark")

            assert ("ui_settings.theme", "dark") in captured

    def test_load_nonexistent_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "nonexistent.json"
            settings = SettingsManager(settings_file)

            assert settings.get_default_library_id() is None
            settings.set("test", "value")
            assert settings.get("test") == "value"

    def test_load_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "invalid.json"

            with open(settings_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json }")

            settings = SettingsManager(settings_file)

            assert settings.get_default_library_id() is None
            settings.set("test", "value")
            assert settings.get("test") == "value"
