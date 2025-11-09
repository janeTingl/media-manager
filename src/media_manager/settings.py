"""Settings management for the media manager application."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, cast

from PySide6.QtCore import QObject, QSettings


class SettingsManager(QObject):
    """Manages application settings with JSON persistence and QSettings fallback."""

    def __init__(
        self, settings_file: Optional[Path] = None, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self._settings_file = (
            settings_file or Path.home() / ".media-manager" / "settings.json"
        )
        self._settings: Dict[str, Any] = {}
        self._qsettings = QSettings("media-manager", "MediaManager")
        self._load_settings()

    def _load_settings(self) -> None:
        """Load settings from JSON file."""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, encoding="utf-8") as f:
                    self._settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            # If JSON loading fails, try to migrate from QSettings
            self._migrate_from_qsettings()

    def _migrate_from_qsettings(self) -> None:
        """Migrate settings from QSettings to JSON."""
        # Common settings keys
        keys = [
            "api_keys",
            "target_folders",
            "rename_templates",
            "window_geometry",
            "window_state",
            "theme",
            "language",
        ]

        for key in keys:
            if self._qsettings.contains(key):
                value = self._qsettings.value(key)
                if isinstance(value, str) and value.startswith("{"):
                    try:
                        # Try to parse as JSON
                        self._settings[key] = json.loads(value)
                    except json.JSONDecodeError:
                        self._settings[key] = value
                else:
                    self._settings[key] = value

        # Save migrated settings to JSON
        self.save_settings()

    def save_settings(self) -> None:
        """Save settings to JSON file."""
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except OSError:
            # Fallback to QSettings if JSON save fails
            for key, value in self._settings.items():
                if isinstance(value, (dict, list)):
                    self._qsettings.setValue(key, json.dumps(value))
                else:
                    self._qsettings.setValue(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings[key] = value

    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        api_keys = self.get("api_keys", {})
        return cast(Optional[str], api_keys.get(service))

    def set_api_key(self, service: str, api_key: str) -> None:
        """Set API key for a specific service."""
        api_keys = self.get("api_keys", {})
        api_keys[service] = api_key
        self.set("api_keys", api_keys)

    def get_target_folder(self, media_type: str) -> Optional[str]:
        """Get target folder for a media type."""
        folders = self.get("target_folders", {})
        return cast(Optional[str], folders.get(media_type))

    def set_target_folder(self, media_type: str, folder: str) -> None:
        """Set target folder for a media type."""
        folders = self.get("target_folders", {})
        folders[media_type] = folder
        self.set("target_folders", folders)

    def get_rename_template(self, template_name: str) -> Optional[str]:
        """Get rename template by name."""
        templates = self.get("rename_templates", {})
        return cast(Optional[str], templates.get(template_name))

    def set_rename_template(self, template_name: str, template: str) -> None:
        """Set rename template."""
        templates = self.get("rename_templates", {})
        templates[template_name] = template
        self.set("rename_templates", templates)

    def get_poster_setting(self, key: str, default: Any = None) -> Any:
        """Get a poster-related setting."""
        poster_settings = self.get("poster_settings", {})
        return poster_settings.get(key, default)

    def set_poster_setting(self, key: str, value: Any) -> None:
        """Set a poster-related setting."""
        poster_settings = self.get("poster_settings", {})
        poster_settings[key] = value
        self.set("poster_settings", poster_settings)

    def get_enabled_poster_types(self) -> list[str]:
        """Get the list of enabled poster types."""
        return self.get_poster_setting("enabled_types", ["poster"])

    def set_enabled_poster_types(self, types: list[str]) -> None:
        """Set the list of enabled poster types."""
        self.set_poster_setting("enabled_types", types)

    def get_poster_size(self, poster_type: str) -> str:
        """Get the preferred size for a poster type."""
        sizes = self.get_poster_setting("sizes", {})
        return sizes.get(poster_type, "medium")

    def set_poster_size(self, poster_type: str, size: str) -> None:
        """Set the preferred size for a poster type."""
        sizes = self.get_poster_setting("sizes", {})
        sizes[poster_type] = size
        self.set_poster_setting("sizes", sizes)

    def get_auto_download_posters(self) -> bool:
        """Get whether to automatically download posters."""
        return self.get_poster_setting("auto_download", True)

    def set_auto_download_posters(self, auto_download: bool) -> None:
        """Set whether to automatically download posters."""
        self.set_poster_setting("auto_download", auto_download)

    def get_max_retries(self) -> int:
        """Get the maximum number of download retries."""
        return self.get_poster_setting("max_retries", 3)

    def set_max_retries(self, max_retries: int) -> None:
        """Set the maximum number of download retries."""
        self.set_poster_setting("max_retries", max_retries)

    def get_cache_dir(self) -> Optional[str]:
        """Get the poster cache directory."""
        return self.get_poster_setting("cache_dir")

    def set_cache_dir(self, cache_dir: str) -> None:
        """Set the poster cache directory."""
        self.set_poster_setting("cache_dir", cache_dir)

    def get_subtitle_setting(self, key: str, default: Any = None) -> Any:
        """Get a subtitle-related setting."""
        subtitle_settings = self.get("subtitle_settings", {})
        return subtitle_settings.get(key, default)

    def set_subtitle_setting(self, key: str, value: Any) -> None:
        """Set a subtitle-related setting."""
        subtitle_settings = self.get("subtitle_settings", {})
        subtitle_settings[key] = value
        self.set("subtitle_settings", subtitle_settings)

    def get_enabled_subtitle_languages(self) -> list[str]:
        """Get the list of enabled subtitle languages."""
        return self.get_subtitle_setting("enabled_languages", ["en"])

    def set_enabled_subtitle_languages(self, languages: list[str]) -> None:
        """Set the list of enabled subtitle languages."""
        self.set_subtitle_setting("enabled_languages", languages)

    def get_auto_download_subtitles(self) -> bool:
        """Get whether to automatically download subtitles."""
        return self.get_subtitle_setting("auto_download", False)

    def set_auto_download_subtitles(self, auto_download: bool) -> None:
        """Set whether to automatically download subtitles."""
        self.set_subtitle_setting("auto_download", auto_download)

    def get_subtitle_format(self) -> str:
        """Get the preferred subtitle format."""
        return self.get_subtitle_setting("format", "srt")

    def set_subtitle_format(self, format: str) -> None:
        """Set the preferred subtitle format."""
        self.set_subtitle_setting("format", format)

    def get_subtitle_provider(self) -> str:
        """Get the subtitle provider to use."""
        return self.get_subtitle_setting("provider", "OpenSubtitles")

    def set_subtitle_provider(self, provider: str) -> None:
        """Set the subtitle provider."""
        self.set_subtitle_setting("provider", provider)

    def get_subtitle_cache_dir(self) -> Optional[str]:
        """Get the subtitle cache directory."""
        return self.get_subtitle_setting("cache_dir")

    def set_subtitle_cache_dir(self, cache_dir: str) -> None:
        """Set the subtitle cache directory."""
        self.set_subtitle_setting("cache_dir", cache_dir)

    def get_nfo_setting(self, key: str, default: Any = None) -> Any:
        """Get an NFO-related setting."""
        nfo_settings = self.get("nfo_settings", {})
        return nfo_settings.get(key, default)

    def set_nfo_setting(self, key: str, value: Any) -> None:
        """Set an NFO-related setting."""
        nfo_settings = self.get("nfo_settings", {})
        nfo_settings[key] = value
        self.set("nfo_settings", nfo_settings)

    def get_nfo_enabled(self) -> bool:
        """Get whether NFO generation is enabled."""
        return self.get_nfo_setting("enabled", True)

    def set_nfo_enabled(self, enabled: bool) -> None:
        """Set whether NFO generation is enabled."""
        self.set_nfo_setting("enabled", enabled)

    def get_nfo_target_subfolder(self) -> Optional[str]:
        """Get the target subfolder for NFO files."""
        return self.get_nfo_setting("target_subfolder")

    def set_nfo_target_subfolder(self, subfolder: Optional[str]) -> None:
        """Set the target subfolder for NFO files."""
        self.set_nfo_setting("target_subfolder", subfolder)


# Global settings instance
_settings_instance: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance
