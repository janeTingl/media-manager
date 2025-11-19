"""Settings management for the media manager application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QObject, QSettings, Signal

DEFAULT_SETTINGS_PATH = Path.home() / ".media-manager" / "settings.json"

DEFAULT_LANGUAGE = "zh-CN"
SUPPORTED_UI_LANGUAGES: tuple[str, ...] = (DEFAULT_LANGUAGE,)

LIBRARY_DOMAIN = "library_settings"
PROVIDER_DOMAIN = "providers"
CACHE_DOMAIN = "cache_settings"
DOWNLOAD_DOMAIN = "downloads"
METADATA_DOMAIN = "metadata_settings"
UI_DOMAIN = "ui_settings"
UI_LAYOUTS_DOMAIN = "ui_layouts"
ADVANCED_DOMAIN = "advanced_settings"


class SettingsManager(QObject):
    """Manages application settings with JSON persistence and QSettings fallback."""

    setting_changed = Signal(str, object)
    domain_changed = Signal(str, dict)
    settings_saved = Signal(dict)

    def __init__(
        self, settings_file: Path | None = None, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._settings_file = settings_file or DEFAULT_SETTINGS_PATH
        self._settings: dict[str, Any] = {}
        self._qsettings = QSettings("yingcang-media-manager", "影藏·媒体管理器")
        self._load_settings()
        self._ensure_default_domains()
        self._migrate_legacy_schema()
        self._ensure_language_defaults()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_settings(self) -> None:
        """Load settings from JSON file."""
        if self._settings_file.exists():
            try:
                with open(self._settings_file, encoding="utf-8") as f:
                    self._settings = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._settings = {}
                self._migrate_from_qsettings()
        else:
            self._settings = {}

    def _migrate_from_qsettings(self) -> None:
        """Migrate settings from QSettings to JSON."""
        keys = [
            "api_keys",
            "target_folders",
            "rename_templates",
            "window_geometry",
            "window_state",
            "theme",
            "language",
            "poster_settings",
            "subtitle_settings",
            "nfo_settings",
            "provider_settings",
        ]

        for key in keys:
            if self._qsettings.contains(key):
                value = self._qsettings.value(key)
                if isinstance(value, str) and value.startswith("{"):
                    try:
                        self._settings[key] = json.loads(value)
                    except json.JSONDecodeError:
                        self._settings[key] = value
                else:
                    self._settings[key] = value

        self.save_settings()

    def _ensure_default_domains(self) -> None:
        """Ensure all domain dictionaries exist."""
        for domain in (
            LIBRARY_DOMAIN,
            PROVIDER_DOMAIN,
            CACHE_DOMAIN,
            DOWNLOAD_DOMAIN,
            METADATA_DOMAIN,
            UI_DOMAIN,
            UI_LAYOUTS_DOMAIN,
            ADVANCED_DOMAIN,
        ):
            self._get_domain(domain)

    def _ensure_language_defaults(self) -> None:
        """Ensure UI and help locales default to Simplified Chinese."""
        ui_settings = self._get_domain(UI_DOMAIN)
        if ui_settings.get("language") not in SUPPORTED_UI_LANGUAGES:
            ui_settings["language"] = DEFAULT_LANGUAGE

        help_locale = ui_settings.get("help_locale")
        if help_locale not in SUPPORTED_UI_LANGUAGES:
            ui_settings["help_locale"] = DEFAULT_LANGUAGE

    def _migrate_legacy_schema(self) -> None:
        """Migrate legacy flat keys into the new domain-based schema."""
        downloads = self._get_domain(DOWNLOAD_DOMAIN)
        metadata = self._get_domain(METADATA_DOMAIN)
        providers = self._get_domain(PROVIDER_DOMAIN)
        ui_settings = self._get_domain(UI_DOMAIN)
        ui_layouts = self._get_domain(UI_LAYOUTS_DOMAIN)
        library_settings = self._get_domain(LIBRARY_DOMAIN)
        cache_settings = self._get_domain(CACHE_DOMAIN)
        advanced_settings = self._get_domain(ADVANCED_DOMAIN)

        legacy_posters = self._settings.pop("poster_settings", None)
        if isinstance(legacy_posters, dict):
            downloads.setdefault("poster_settings", legacy_posters)
        downloads.setdefault("poster_settings", {})

        legacy_subtitles = self._settings.pop("subtitle_settings", None)
        if isinstance(legacy_subtitles, dict):
            downloads.setdefault("subtitle_settings", legacy_subtitles)
        downloads.setdefault("subtitle_settings", {})

        legacy_nfo = self._settings.pop("nfo_settings", None)
        if isinstance(legacy_nfo, dict):
            downloads.setdefault("nfo_settings", legacy_nfo)
        downloads.setdefault("nfo_settings", {})

        legacy_templates = self._settings.pop("rename_templates", None)
        if isinstance(legacy_templates, dict):
            metadata.setdefault("rename_templates", legacy_templates)
        metadata.setdefault("rename_templates", {})

        legacy_api_keys = self._settings.pop("api_keys", None)
        if isinstance(legacy_api_keys, dict):
            providers.setdefault("api_keys", legacy_api_keys)
        providers.setdefault("api_keys", {})

        legacy_provider_opts = self._settings.pop("provider_settings", None)
        if isinstance(legacy_provider_opts, dict):
            providers.setdefault("options", legacy_provider_opts)
        providers.setdefault("options", {})

        legacy_theme = self._settings.pop("theme", None)
        if legacy_theme is not None and "theme" not in ui_settings:
            ui_settings["theme"] = legacy_theme

        legacy_language = self._settings.pop("language", None)
        if legacy_language is not None and "language" not in ui_settings:
            ui_settings["language"] = legacy_language

        legacy_window_geometry = self._settings.pop("window_geometry", None)
        if legacy_window_geometry and "main_window.geometry" not in ui_layouts:
            ui_layouts["main_window.geometry"] = legacy_window_geometry

        legacy_window_state = self._settings.pop("window_state", None)
        if legacy_window_state and "main_window.state" not in ui_layouts:
            ui_layouts["main_window.state"] = legacy_window_state

        for legacy_key in ("last_active_library_id", "default_library_id", "library_root"):
            if legacy_key in self._settings and legacy_key not in library_settings:
                library_settings[legacy_key] = self._settings.pop(legacy_key)

        legacy_cache_dir = downloads.get("poster_settings", {}).get("cache_dir")
        if legacy_cache_dir and "poster_cache_dir" not in cache_settings:
            cache_settings["poster_cache_dir"] = legacy_cache_dir

        advanced_settings.setdefault("batch_defaults", {})

    def _get_domain(self, domain: str) -> dict[str, Any]:
        value = self._settings.get(domain)
        if isinstance(value, dict):
            return value
        new_value: dict[str, Any] = {}
        self._settings[domain] = new_value
        return new_value

    def _get_downloads_section(self) -> dict[str, Any]:
        return self._get_domain(DOWNLOAD_DOMAIN)

    def _get_poster_settings(self) -> dict[str, Any]:
        downloads = self._get_downloads_section()
        poster_settings = downloads.get("poster_settings")
        if isinstance(poster_settings, dict):
            return poster_settings
        poster_settings = {}
        downloads["poster_settings"] = poster_settings
        return poster_settings

    def _get_subtitle_settings(self) -> dict[str, Any]:
        downloads = self._get_downloads_section()
        subtitle_settings = downloads.get("subtitle_settings")
        if isinstance(subtitle_settings, dict):
            return subtitle_settings
        subtitle_settings = {}
        downloads["subtitle_settings"] = subtitle_settings
        return subtitle_settings

    def _get_nfo_settings(self) -> dict[str, Any]:
        downloads = self._get_downloads_section()
        nfo_settings = downloads.get("nfo_settings")
        if isinstance(nfo_settings, dict):
            return nfo_settings
        nfo_settings = {}
        downloads["nfo_settings"] = nfo_settings
        return nfo_settings

    def _get_metadata_section(self) -> dict[str, Any]:
        return self._get_domain(METADATA_DOMAIN)

    def _get_rename_templates(self) -> dict[str, str]:
        metadata = self._get_metadata_section()
        templates = metadata.get("rename_templates")
        if isinstance(templates, dict):
            return cast(dict[str, str], templates)
        templates = {}
        metadata["rename_templates"] = templates
        return templates

    def _get_provider_keys_mutable(self) -> dict[str, str]:
        providers = self._get_domain(PROVIDER_DOMAIN)
        keys = providers.get("api_keys")
        if isinstance(keys, dict):
            return cast(dict[str, str], keys)
        keys = {}
        providers["api_keys"] = keys
        return keys

    def _get_provider_options(self) -> dict[str, Any]:
        providers = self._get_domain(PROVIDER_DOMAIN)
        options = providers.get("options")
        if isinstance(options, dict):
            return options
        options = {}
        providers["options"] = options
        return options

    def _get_batch_defaults_mutable(self) -> dict[str, Any]:
        advanced = self._get_domain(ADVANCED_DOMAIN)
        defaults = advanced.get("batch_defaults")
        if isinstance(defaults, dict):
            return defaults
        defaults = {}
        advanced["batch_defaults"] = defaults
        return defaults

    def _emit_change(self, key: str, value: Any, domain: str | None = None) -> None:
        self.setting_changed.emit(key, value)
        if domain is not None:
            self.domain_changed.emit(domain, {key: value})

    # ------------------------------------------------------------------
    # Persistence operations
    # ------------------------------------------------------------------
    def save_settings(self) -> None:
        """Save settings to JSON file."""
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            self.settings_saved.emit(dict(self._settings))
        except OSError:
            for key, value in self._settings.items():
                if isinstance(value, (dict, list)):
                    self._qsettings.setValue(key, json.dumps(value))
                else:
                    self._qsettings.setValue(key, value)

    # ------------------------------------------------------------------
    # Generic get/set
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings[key] = value
        self._emit_change(key, value)

    # ------------------------------------------------------------------
    # Library settings
    # ------------------------------------------------------------------
    def get_library_setting(self, key: str, default: Any = None) -> Any:
        library_settings = self._get_domain(LIBRARY_DOMAIN)
        if key in library_settings:
            return library_settings[key]
        return self._settings.get(key, default)

    def set_library_setting(self, key: str, value: Any | None) -> None:
        library_settings = self._get_domain(LIBRARY_DOMAIN)
        if value is None:
            library_settings.pop(key, None)
            if key in self._settings:
                self._settings.pop(key, None)
        else:
            library_settings[key] = value
            if key in {"default_library_id", "last_active_library_id", "library_root"}:
                self._settings[key] = value
        self._emit_change(f"{LIBRARY_DOMAIN}.{key}", value, "libraries")

    def get_last_active_library_id(self) -> int | None:
        value = self.get_library_setting("last_active_library_id")
        return cast(int | None, value)

    def set_last_active_library_id(self, library_id: int | None) -> None:
        self.set_library_setting("last_active_library_id", library_id)

    def get_default_library_id(self) -> int | None:
        value = self.get_library_setting("default_library_id")
        return cast(int | None, value)

    def set_default_library_id(self, library_id: int | None) -> None:
        self.set_library_setting("default_library_id", library_id)

    # ------------------------------------------------------------------
    # Provider keys and options
    # ------------------------------------------------------------------
    def get_provider_keys(self) -> dict[str, str]:
        return dict(self._get_provider_keys_mutable())

    def clear_provider_key(self, service: str) -> None:
        provider_keys = self._get_provider_keys_mutable()
        if service in provider_keys:
            provider_keys.pop(service, None)
            self._emit_change(f"{PROVIDER_DOMAIN}.api_keys.{service}", None, "providers")

    def get_api_key(self, service: str) -> str | None:
        provider_keys = self._get_provider_keys_mutable()
        return cast(str | None, provider_keys.get(service))

    def set_api_key(self, service: str, api_key: str | None) -> None:
        provider_keys = self._get_provider_keys_mutable()
        normalized = api_key.strip() if api_key else ""
        if normalized:
            provider_keys[service] = normalized
        else:
            provider_keys.pop(service, None)
        self._emit_change(f"{PROVIDER_DOMAIN}.api_keys.{service}", provider_keys.get(service), "providers")

    def get_tmdb_api_key(self) -> str | None:
        return self.get_api_key("tmdb")

    def set_tmdb_api_key(self, api_key: str | None) -> None:
        self.set_api_key("tmdb", api_key)

    def get_tvdb_api_key(self) -> str | None:
        return self.get_api_key("tvdb")

    def set_tvdb_api_key(self, api_key: str | None) -> None:
        self.set_api_key("tvdb", api_key)

    def get_provider_setting(self, key: str, default: Any = None) -> Any:
        options = self._get_provider_options()
        return options.get(key, default)

    def set_provider_setting(self, key: str, value: Any) -> None:
        options = self._get_provider_options()
        options[key] = value
        self._emit_change(f"{PROVIDER_DOMAIN}.options.{key}", value, "providers")

    def get_enabled_providers(self) -> list[str]:
        providers = self._get_domain(PROVIDER_DOMAIN)
        enabled = providers.get("enabled_providers")
        if isinstance(enabled, list):
            return [str(provider) for provider in enabled]
        return ["TMDB", "TVDB"]

    def set_enabled_providers(self, providers_list: list[str]) -> None:
        providers = self._get_domain(PROVIDER_DOMAIN)
        providers["enabled_providers"] = list(providers_list)
        self._emit_change(f"{PROVIDER_DOMAIN}.enabled_providers", list(providers_list), "providers")

    def get_provider_retry_count(self) -> int:
        value = self.get_provider_setting("retry_count", 3)
        return int(value)

    def set_provider_retry_count(self, count: int) -> None:
        self.set_provider_setting("retry_count", int(count))

    def get_provider_timeout(self) -> int:
        value = self.get_provider_setting("timeout", 10)
        return int(value)

    def set_provider_timeout(self, timeout: int) -> None:
        self.set_provider_setting("timeout", int(timeout))

    # ------------------------------------------------------------------
    # Cache settings
    # ------------------------------------------------------------------
    def get_cache_setting(self, key: str, default: Any = None) -> Any:
        cache_settings = self._get_domain(CACHE_DOMAIN)
        return cache_settings.get(key, default)

    def set_cache_setting(self, key: str, value: Any | None) -> None:
        cache_settings = self._get_domain(CACHE_DOMAIN)
        if value is None:
            cache_settings.pop(key, None)
        else:
            cache_settings[key] = value
        self._emit_change(f"{CACHE_DOMAIN}.{key}", value, "caching")

    def get_provider_cache_enabled(self) -> bool:
        """Get whether provider caching is enabled."""
        return bool(self.get_cache_setting("provider_cache_enabled", True))

    def set_provider_cache_enabled(self, enabled: bool) -> None:
        """Set whether provider caching is enabled."""
        self.set_cache_setting("provider_cache_enabled", enabled)

    def get_provider_cache_ttl(self) -> int:
        """Get provider cache TTL in seconds (default 1 hour)."""
        return int(self.get_cache_setting("provider_cache_ttl", 3600))

    def set_provider_cache_ttl(self, ttl: int) -> None:
        """Set provider cache TTL in seconds."""
        self.set_cache_setting("provider_cache_ttl", ttl)

    def get_cache_backend_type(self) -> str:
        """Get cache backend type: 'db', 'redis', or 'disk'."""
        return str(self.get_cache_setting("backend_type", "db"))

    def set_cache_backend_type(self, backend_type: str) -> None:
        """Set cache backend type."""
        self.set_cache_setting("backend_type", backend_type)

    def get_redis_url(self) -> str | None:
        """Get Redis connection URL."""
        return self.get_cache_setting("redis_url")

    def set_redis_url(self, url: str | None) -> None:
        """Set Redis connection URL."""
        self.set_cache_setting("redis_url", url)

    def get_disk_cache_dir(self) -> str | None:
        """Get disk cache directory."""
        return self.get_cache_setting("disk_cache_dir")

    def set_disk_cache_dir(self, directory: str | None) -> None:
        """Set disk cache directory."""
        self.set_cache_setting("disk_cache_dir", directory)

    def get_cache_dir(self) -> str | None:
        poster_settings = self._get_poster_settings()
        cache_dir = poster_settings.get("cache_dir")
        if cache_dir:
            return cast(str | None, cache_dir)
        cache_setting = self.get_cache_setting("poster_cache_dir")
        return cast(str | None, cache_setting)

    def set_cache_dir(self, cache_dir: str | None) -> None:
        poster_settings = self._get_poster_settings()
        if cache_dir:
            poster_settings["cache_dir"] = cache_dir
            self.set_cache_setting("poster_cache_dir", cache_dir)
        else:
            poster_settings.pop("cache_dir", None)
            self.set_cache_setting("poster_cache_dir", None)
        self._emit_change(f"{DOWNLOAD_DOMAIN}.poster_settings.cache_dir", cache_dir, "downloads")

    # ------------------------------------------------------------------
    # Metadata and rename templates
    # ------------------------------------------------------------------
    def get_target_folder(self, media_type: str) -> str | None:
        folders = self._settings.get("target_folders", {})
        if isinstance(folders, dict):
            return cast(str | None, folders.get(media_type))
        return None

    def set_target_folder(self, media_type: str, folder: str) -> None:
        folders = self._settings.get("target_folders")
        if not isinstance(folders, dict):
            folders = {}
            self._settings["target_folders"] = folders
        folders[media_type] = folder
        self._emit_change("target_folders", dict(folders))

    def get_rename_template(self, template_name: str) -> str | None:
        templates = self._get_rename_templates()
        return cast(str | None, templates.get(template_name))

    def set_rename_template(self, template_name: str, template: str) -> None:
        templates = self._get_rename_templates()
        if template:
            templates[template_name] = template
        else:
            templates.pop(template_name, None)
        self._emit_change(f"{METADATA_DOMAIN}.rename_templates.{template_name}", templates.get(template_name), "metadata")

    # ------------------------------------------------------------------
    # Poster settings
    # ------------------------------------------------------------------
    def get_poster_setting(self, key: str, default: Any = None) -> Any:
        poster_settings = self._get_poster_settings()
        return poster_settings.get(key, default)

    def set_poster_setting(self, key: str, value: Any) -> None:
        poster_settings = self._get_poster_settings()
        poster_settings[key] = value
        self._emit_change(f"{DOWNLOAD_DOMAIN}.poster_settings.{key}", value, "downloads")

    def get_enabled_poster_types(self) -> list[str]:
        types = self.get_poster_setting("enabled_types", ["poster"])
        if isinstance(types, list):
            return [str(item) for item in types]
        return ["poster"]

    def set_enabled_poster_types(self, types: list[str]) -> None:
        self.set_poster_setting("enabled_types", list(types))

    def get_poster_size(self, poster_type: str) -> str:
        sizes = self.get_poster_setting("sizes", {})
        if isinstance(sizes, dict):
            return str(sizes.get(poster_type, "medium"))
        return "medium"

    def set_poster_size(self, poster_type: str, size: str) -> None:
        sizes = self.get_poster_setting("sizes", {})
        if not isinstance(sizes, dict):
            sizes = {}
        sizes[poster_type] = size
        self.set_poster_setting("sizes", sizes)

    def get_auto_download_posters(self) -> bool:
        return bool(self.get_poster_setting("auto_download", True))

    def set_auto_download_posters(self, auto_download: bool) -> None:
        self.set_poster_setting("auto_download", bool(auto_download))

    def get_max_retries(self) -> int:
        return int(self.get_poster_setting("max_retries", 3))

    def set_max_retries(self, max_retries: int) -> None:
        self.set_poster_setting("max_retries", int(max_retries))

    # ------------------------------------------------------------------
    # Subtitle settings
    # ------------------------------------------------------------------
    def get_subtitle_setting(self, key: str, default: Any = None) -> Any:
        subtitle_settings = self._get_subtitle_settings()
        return subtitle_settings.get(key, default)

    def set_subtitle_setting(self, key: str, value: Any) -> None:
        subtitle_settings = self._get_subtitle_settings()
        subtitle_settings[key] = value
        self._emit_change(f"{DOWNLOAD_DOMAIN}.subtitle_settings.{key}", value, "downloads")

    def get_enabled_subtitle_languages(self) -> list[str]:
        languages = self.get_subtitle_setting("enabled_languages", ["en"])
        if isinstance(languages, list):
            return [str(lang) for lang in languages]
        return ["en"]

    def set_enabled_subtitle_languages(self, languages: list[str]) -> None:
        self.set_subtitle_setting("enabled_languages", list(languages))

    def get_auto_download_subtitles(self) -> bool:
        return bool(self.get_subtitle_setting("auto_download", False))

    def set_auto_download_subtitles(self, auto_download: bool) -> None:
        self.set_subtitle_setting("auto_download", bool(auto_download))

    def get_subtitle_format(self) -> str:
        return str(self.get_subtitle_setting("format", "srt"))

    def set_subtitle_format(self, format: str) -> None:
        self.set_subtitle_setting("format", format)

    def get_subtitle_provider(self) -> str:
        return str(self.get_subtitle_setting("provider", "OpenSubtitles"))

    def set_subtitle_provider(self, provider: str) -> None:
        self.set_subtitle_setting("provider", provider)

    def get_subtitle_cache_dir(self) -> str | None:
        cache_dir = self.get_subtitle_setting("cache_dir")
        if cache_dir:
            return cast(str | None, cache_dir)
        return None

    def set_subtitle_cache_dir(self, cache_dir: str | None) -> None:
        self.set_subtitle_setting("cache_dir", cache_dir)

    # ------------------------------------------------------------------
    # NFO settings
    # ------------------------------------------------------------------
    def get_nfo_setting(self, key: str, default: Any = None) -> Any:
        nfo_settings = self._get_nfo_settings()
        return nfo_settings.get(key, default)

    def set_nfo_setting(self, key: str, value: Any) -> None:
        nfo_settings = self._get_nfo_settings()
        nfo_settings[key] = value
        self._emit_change(f"{DOWNLOAD_DOMAIN}.nfo_settings.{key}", value, "downloads")

    def get_nfo_enabled(self) -> bool:
        return bool(self.get_nfo_setting("enabled", True))

    def set_nfo_enabled(self, enabled: bool) -> None:
        self.set_nfo_setting("enabled", bool(enabled))

    def get_nfo_target_subfolder(self) -> str | None:
        return cast(str | None, self.get_nfo_setting("target_subfolder"))

    def set_nfo_target_subfolder(self, subfolder: str | None) -> None:
        nfo_settings = self._get_nfo_settings()
        if subfolder:
            nfo_settings["target_subfolder"] = subfolder
        else:
            nfo_settings.pop("target_subfolder", None)
        self._emit_change(f"{DOWNLOAD_DOMAIN}.nfo_settings.target_subfolder", subfolder, "downloads")

    # ------------------------------------------------------------------
    # Trailer settings
    # ------------------------------------------------------------------
    def get_trailer_quality(self) -> str:
        downloads = self._get_downloads_section()
        quality = downloads.get("trailer_quality", "1080p")
        return str(quality)

    def set_trailer_quality(self, quality: str) -> None:
        downloads = self._get_downloads_section()
        downloads["trailer_quality"] = quality
        self._emit_change(f"{DOWNLOAD_DOMAIN}.trailer_quality", quality, "downloads")

    # ------------------------------------------------------------------
    # Database settings
    # ------------------------------------------------------------------
    def get_database_path(self) -> str:
        default_path = str(Path.home() / ".media-manager" / "media_manager.db")
        return str(self._settings.get("database_path", default_path))

    def set_database_path(self, path: str) -> None:
        self._settings["database_path"] = path
        self._emit_change("database_path", path)

    def get_database_url(self) -> str:
        db_path = self.get_database_path()
        return f"sqlite:///{db_path}"

    # ------------------------------------------------------------------
    # UI settings and layouts
    # ------------------------------------------------------------------
    def get_ui_setting(self, key: str, default: Any = None) -> Any:
        ui_settings = self._get_domain(UI_DOMAIN)
        return ui_settings.get(key, default)

    def set_ui_setting(self, key: str, value: Any) -> None:
        ui_settings = self._get_domain(UI_DOMAIN)
        ui_settings[key] = value
        self._emit_change(f"{UI_DOMAIN}.{key}", value, "ui")

    def get_ui_layout(self, key: str, default: Any = None) -> Any:
        layouts = self._get_domain(UI_LAYOUTS_DOMAIN)
        if key in layouts:
            return layouts[key]
        if key == "main_window.geometry":
            return self._settings.get("window_geometry", default)
        if key == "main_window.state":
            return self._settings.get("window_state", default)
        return default

    def set_ui_layout(self, key: str, value: Any | None) -> None:
        layouts = self._get_domain(UI_LAYOUTS_DOMAIN)
        if value is None:
            layouts.pop(key, None)
        else:
            layouts[key] = value
        if key == "main_window.geometry":
            if value is None:
                self._settings.pop("window_geometry", None)
            else:
                self._settings["window_geometry"] = value
        if key == "main_window.state":
            if value is None:
                self._settings.pop("window_state", None)
            else:
                self._settings["window_state"] = value
        self._emit_change(f"{UI_LAYOUTS_DOMAIN}.{key}", value, "ui")

    def clear_ui_layout(self, key: str) -> None:
        self.set_ui_layout(key, None)

    def get_language(self) -> str:
        """Get the UI language/locale setting."""
        return str(self.get_ui_setting("language", DEFAULT_LANGUAGE))

    def set_language(self, language: str) -> None:
        """Set the UI language/locale setting."""
        normalized = language if language in SUPPORTED_UI_LANGUAGES else DEFAULT_LANGUAGE
        self.set_ui_setting("language", normalized)

    def get_help_locale(self) -> str:
        """Get the help documentation locale (falls back to UI language)."""
        return str(self.get_ui_setting("help_locale", self.get_language()))

    def set_help_locale(self, locale: str) -> None:
        """Set the help documentation locale."""
        normalized = locale if locale in SUPPORTED_UI_LANGUAGES else DEFAULT_LANGUAGE
        self.set_ui_setting("help_locale", normalized)

    # ------------------------------------------------------------------
    # Advanced settings
    # ------------------------------------------------------------------
    def get_logging_level(self) -> str:
        advanced = self._get_domain(ADVANCED_DOMAIN)
        level = advanced.get("logging_level", "INFO")
        return str(level)

    def set_logging_level(self, level: str) -> None:
        advanced = self._get_domain(ADVANCED_DOMAIN)
        normalized = level.upper()
        advanced["logging_level"] = normalized
        self._emit_change(f"{ADVANCED_DOMAIN}.logging_level", normalized, "advanced")

    def get_batch_defaults(self) -> dict[str, Any]:
        defaults = self._get_batch_defaults_mutable()
        return dict(defaults)

    def set_batch_defaults(self, defaults: dict[str, Any]) -> None:
        advanced = self._get_domain(ADVANCED_DOMAIN)
        advanced["batch_defaults"] = dict(defaults)
        self._emit_change(f"{ADVANCED_DOMAIN}.batch_defaults", dict(defaults), "advanced")

    def update_batch_defaults(self, **kwargs: Any) -> None:
        defaults = self._get_batch_defaults_mutable()
        for key, value in kwargs.items():
            defaults[key] = value
        self._emit_change(f"{ADVANCED_DOMAIN}.batch_defaults", dict(defaults), "advanced")


_settings_instance: SettingsManager | None = None


def get_settings() -> SettingsManager:
    """Get the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager()
    return _settings_instance
