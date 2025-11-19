"""Comprehensive preferences window with multi-tab configuration widgets."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .library_manager_dialog import LibraryManagerDialog
from .persistence.repositories import LibraryRepository
from .poster_settings_widget import PosterSettingsWidget
from .settings import SettingsManager, get_settings


class BasePreferencesSection(QWidget):
    """Base class for preference sections with apply/refresh semantics."""

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._settings = settings

    def apply(self) -> Tuple[bool, Optional[str]]:
        """Apply current widget values to the settings manager."""
        return True, None

    def refresh(self) -> None:
        """Reload widget state from settings."""
        # Default implementation does nothing.
        return None


class PreferencesWindow(QDialog):
    """Top-level preferences window with dedicated configuration tabs."""

    preferences_applied = Signal()

    def __init__(
        self,
        settings: Optional[SettingsManager] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings or get_settings()
        self.setWindowTitle("Preferences")
        self.setMinimumSize(780, 580)

        layout = QVBoxLayout(self)
        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        self._sections: List[Tuple[BasePreferencesSection, str]] = []

        # Build tabs
        self._libraries_section = LibrariesPreferencesWidget(self._settings, parent=self)
        self._add_section(self._libraries_section, "Libraries")

        self._metadata_section = MetadataPreferencesWidget(self._settings, parent=self)
        self._add_section(self._metadata_section, "Metadata")

        self._providers_section = ProvidersPreferencesWidget(self._settings, parent=self)
        self._add_section(self._providers_section, "Providers")

        self._downloads_section = DownloadsPreferencesWidget(self._settings, parent=self)
        self._add_section(self._downloads_section, "Downloads")

        self._ui_section = UIPreferencesWidget(self._settings, parent=self)
        self._add_section(self._ui_section, "UI")

        self._advanced_section = AdvancedPreferencesWidget(self._settings, parent=self)
        self._add_section(self._advanced_section, "Advanced")

        # Dialog buttons
        self._button_box = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        self._button_box.button(QDialogButtonBox.Apply).clicked.connect(self._on_apply_clicked)
        self._button_box.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(self._button_box)

    def _add_section(self, section: BasePreferencesSection, title: str) -> None:
        """Register a section and add it to the tab stack."""
        self._sections.append((section, title))
        self._tab_widget.addTab(section, title)

    def _on_apply_clicked(self) -> None:
        """Apply all section changes and persist to disk."""
        for section, title in self._sections:
            success, error_message = section.apply()
            if not success:
                if error_message:
                    QMessageBox.warning(self, f"{title} Settings", error_message)
                self._tab_widget.setCurrentWidget(section)
                return

        self._settings.save_settings()
        self.preferences_applied.emit()


class LibrariesPreferencesWidget(BasePreferencesSection):
    """Preferences section for managing library defaults."""

    def __init__(
        self,
        settings: SettingsManager,
        repository: Optional[LibraryRepository] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(settings, parent)
        self._repository = repository or LibraryRepository()
        self._libraries: List[Tuple[str, Optional[int]]] = []

        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.default_library_combo = QComboBox()
        form.addRow("Default library:", self.default_library_combo)

        self.auto_restore_checkbox = QCheckBox("Restore last active library on startup")
        form.addRow("", self.auto_restore_checkbox)

        root_layout = QHBoxLayout()
        self.library_root_edit = QLineEdit()
        self.library_root_edit.setPlaceholderText("/path/to/default/library")
        browse_button = QPushButton("Browse…")
        browse_button.clicked.connect(self._on_browse_root)
        root_layout.addWidget(self.library_root_edit)
        root_layout.addWidget(browse_button)
        form.addRow("Library root:", root_layout)

        layout.addLayout(form)

        manage_button = QPushButton("Manage Libraries…")
        manage_button.clicked.connect(self._on_manage_libraries)
        layout.addWidget(manage_button, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addStretch()

    def refresh(self) -> None:
        self._load_libraries()
        self._restore_state()

    def _load_libraries(self) -> None:
        self.default_library_combo.clear()
        self._libraries.clear()

        try:
            libraries = self._repository.get_active()
        except Exception as exc:  # pragma: no cover - defensive fallback
            QMessageBox.warning(self, "Libraries", f"Failed to load libraries: {exc}")
            libraries = []

        for library in libraries:
            self.default_library_combo.addItem(library.name, library.id)
            self._libraries.append((library.name, library.id))

        if not libraries:
            self.default_library_combo.addItem("No libraries available", None)
            self.default_library_combo.setEnabled(False)
        else:
            self.default_library_combo.setEnabled(True)

    def _restore_state(self) -> None:
        default_id = self._settings.get_default_library_id()
        if default_id is not None:
            index = self.default_library_combo.findData(default_id)
            if index >= 0:
                self.default_library_combo.setCurrentIndex(index)

        auto_restore = bool(self._settings.get_library_setting("auto_restore_last", True))
        self.auto_restore_checkbox.setChecked(auto_restore)

        root_setting = self._settings.get_library_setting("library_root")
        if root_setting:
            self.library_root_edit.setText(str(root_setting))

    def _on_browse_root(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Library Root", self.library_root_edit.text())
        if directory:
            self.library_root_edit.setText(directory)

    def _on_manage_libraries(self) -> None:
        dialog = LibraryManagerDialog(self)
        dialog.library_created.connect(lambda _: self.refresh())
        dialog.library_updated.connect(lambda _: self.refresh())
        dialog.library_deleted.connect(lambda _: self.refresh())
        dialog.exec()

    def apply(self) -> Tuple[bool, Optional[str]]:
        root_text = self.library_root_edit.text().strip()
        if root_text:
            root_path = Path(root_text)
            try:
                root_path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return False, f"Unable to access library root: {exc}"
            self._settings.set_library_setting("library_root", str(root_path))
        else:
            self._settings.set_library_setting("library_root", None)

        selected_data = self.default_library_combo.currentData()
        if selected_data is not None:
            self._settings.set_default_library_id(int(selected_data))
        else:
            self._settings.set_default_library_id(None)

        self._settings.set_library_setting(
            "auto_restore_last", self.auto_restore_checkbox.isChecked()
        )

        return True, None


class MetadataPreferencesWidget(BasePreferencesSection):
    """Preferences section for metadata, subtitles, and NFO handling."""

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(settings, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.movie_template_edit = QLineEdit()
        self.movie_template_edit.setPlaceholderText("{title} ({year})")
        form.addRow("Movie rename template:", self.movie_template_edit)

        self.tv_template_edit = QLineEdit()
        self.tv_template_edit.setPlaceholderText("{title} - S{season:02d}E{episode:02d}")
        form.addRow("TV episode template:", self.tv_template_edit)

        self.subtitle_provider_combo = QComboBox()
        self.subtitle_provider_combo.addItems([
            "OpenSubtitles",
            "SubDB",
            "Addic7ed",
            "Podnapisi",
        ])
        form.addRow("Subtitle provider:", self.subtitle_provider_combo)

        self.subtitle_languages_edit = QLineEdit()
        self.subtitle_languages_edit.setPlaceholderText("en, es, fr")
        form.addRow("Subtitle languages:", self.subtitle_languages_edit)

        self.subtitle_auto_checkbox = QCheckBox("Automatically download subtitles")
        form.addRow("", self.subtitle_auto_checkbox)

        self.nfo_enabled_checkbox = QCheckBox("Generate NFO metadata files")
        form.addRow("", self.nfo_enabled_checkbox)

        self.nfo_subfolder_edit = QLineEdit()
        self.nfo_subfolder_edit.setPlaceholderText("optional/subfolder")
        form.addRow("NFO subfolder:", self.nfo_subfolder_edit)

        layout.addLayout(form)
        layout.addStretch()

    def refresh(self) -> None:
        movie_template = self._settings.get_rename_template("movie")
        if movie_template:
            self.movie_template_edit.setText(movie_template)

        tv_template = self._settings.get_rename_template("tv_episode")
        if tv_template:
            self.tv_template_edit.setText(tv_template)

        provider = self._settings.get_subtitle_provider()
        index = self.subtitle_provider_combo.findText(provider)
        if index >= 0:
            self.subtitle_provider_combo.setCurrentIndex(index)

        languages = ", ".join(self._settings.get_enabled_subtitle_languages())
        self.subtitle_languages_edit.setText(languages)

        self.subtitle_auto_checkbox.setChecked(self._settings.get_auto_download_subtitles())
        self.nfo_enabled_checkbox.setChecked(self._settings.get_nfo_enabled())

        nfo_subfolder = self._settings.get_nfo_target_subfolder()
        if nfo_subfolder:
            self.nfo_subfolder_edit.setText(nfo_subfolder)

    def apply(self) -> Tuple[bool, Optional[str]]:
        self._settings.set_rename_template("movie", self.movie_template_edit.text().strip())
        self._settings.set_rename_template("tv_episode", self.tv_template_edit.text().strip())

        provider = self.subtitle_provider_combo.currentText()
        self._settings.set_subtitle_provider(provider)

        languages_text = self.subtitle_languages_edit.text().strip()
        if languages_text:
            languages = [lang.strip() for lang in languages_text.split(",") if lang.strip()]
            self._settings.set_enabled_subtitle_languages(languages)
        else:
            self._settings.set_enabled_subtitle_languages(["en"])

        self._settings.set_auto_download_subtitles(self.subtitle_auto_checkbox.isChecked())
        self._settings.set_nfo_enabled(self.nfo_enabled_checkbox.isChecked())

        subfolder = self.nfo_subfolder_edit.text().strip() or None
        self._settings.set_nfo_target_subfolder(subfolder)

        return True, None


class ProvidersPreferencesWidget(BasePreferencesSection):
    """Preferences section for metadata providers and API keys."""

    API_KEY_MIN_LENGTH = 16

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(settings, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.tmdb_key_edit = QLineEdit()
        self.tmdb_key_edit.setPlaceholderText("TMDB API key")
        self.tmdb_error_label = QLabel()
        self.tmdb_error_label.setStyleSheet("color: #c62828;")
        tmdb_container = QVBoxLayout()
        tmdb_container.addWidget(self.tmdb_key_edit)
        tmdb_container.addWidget(self.tmdb_error_label)
        tmdb_widget = QWidget()
        tmdb_widget.setLayout(tmdb_container)
        form.addRow("TMDB API key:", tmdb_widget)

        self.tvdb_key_edit = QLineEdit()
        self.tvdb_key_edit.setPlaceholderText("TVDB API key")
        self.tvdb_error_label = QLabel()
        self.tvdb_error_label.setStyleSheet("color: #c62828;")
        tvdb_container = QVBoxLayout()
        tvdb_container.addWidget(self.tvdb_key_edit)
        tvdb_container.addWidget(self.tvdb_error_label)
        tvdb_widget = QWidget()
        tvdb_widget.setLayout(tvdb_container)
        form.addRow("TVDB API key:", tvdb_widget)

        self.tmdb_enabled_checkbox = QCheckBox("Enable TMDB provider")
        form.addRow("", self.tmdb_enabled_checkbox)

        self.tvdb_enabled_checkbox = QCheckBox("Enable TVDB provider")
        form.addRow("", self.tvdb_enabled_checkbox)

        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(0, 10)
        form.addRow("Retry attempts:", self.retry_spin)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        form.addRow("API timeout (seconds):", self.timeout_spin)

        layout.addLayout(form)
        layout.addStretch()

    def refresh(self) -> None:
        self.tmdb_key_edit.setText(self._settings.get_tmdb_api_key() or "")
        self.tvdb_key_edit.setText(self._settings.get_tvdb_api_key() or "")

        enabled = set(self._settings.get_enabled_providers())
        self.tmdb_enabled_checkbox.setChecked("TMDB" in enabled)
        self.tvdb_enabled_checkbox.setChecked("TVDB" in enabled)

        self.retry_spin.setValue(self._settings.get_provider_retry_count())
        self.timeout_spin.setValue(self._settings.get_provider_timeout())

        self.tmdb_error_label.clear()
        self.tvdb_error_label.clear()

    def apply(self) -> Tuple[bool, Optional[str]]:
        tmdb_key = self.tmdb_key_edit.text().strip()
        tvdb_key = self.tvdb_key_edit.text().strip()

        if tmdb_key and not self._is_valid_api_key(tmdb_key):
            self.tmdb_error_label.setText("Invalid TMDB API key")
            return False, "TMDB API key must be at least 16 characters."
        self.tmdb_error_label.clear()

        if tvdb_key and not self._is_valid_api_key(tvdb_key):
            self.tvdb_error_label.setText("Invalid TVDB API key")
            return False, "TVDB API key must be at least 16 characters."
        self.tvdb_error_label.clear()

        self._settings.set_tmdb_api_key(tmdb_key)
        self._settings.set_tvdb_api_key(tvdb_key)

        enabled: List[str] = []
        if self.tmdb_enabled_checkbox.isChecked():
            enabled.append("TMDB")
        if self.tvdb_enabled_checkbox.isChecked():
            enabled.append("TVDB")
        self._settings.set_enabled_providers(enabled or ["TMDB", "TVDB"])

        self._settings.set_provider_retry_count(self.retry_spin.value())
        self._settings.set_provider_timeout(self.timeout_spin.value())

        return True, None

    @classmethod
    def _is_valid_api_key(cls, key: str) -> bool:
        return len(key.strip()) >= cls.API_KEY_MIN_LENGTH


class DownloadsPreferencesWidget(BasePreferencesSection):
    """Preferences section for artwork and download behaviour."""

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(settings, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.poster_settings_widget = PosterSettingsWidget()
        layout.addWidget(self.poster_settings_widget)

        trailer_layout = QHBoxLayout()
        trailer_layout.addWidget(QLabel("Trailer quality:"))
        self.trailer_quality_combo = QComboBox()
        self.trailer_quality_combo.addItems(["auto", "720p", "1080p", "4K"])
        trailer_layout.addWidget(self.trailer_quality_combo)
        trailer_layout.addStretch()
        layout.addLayout(trailer_layout)

        layout.addStretch()

    def refresh(self) -> None:
        quality = self._settings.get_trailer_quality().lower()
        available = [option.lower() for option in ["auto", "720p", "1080p", "4K"]]
        if quality in available:
            index = available.index(quality)
            self.trailer_quality_combo.setCurrentIndex(index)
        else:
            self.trailer_quality_combo.setCurrentText("1080p")

    def apply(self) -> Tuple[bool, Optional[str]]:
        self.poster_settings_widget.save()
        selected_quality = self.trailer_quality_combo.currentText()
        self._settings.set_trailer_quality(selected_quality)
        return True, None


class UIPreferencesWidget(BasePreferencesSection):
    """Preferences section for UI-related options."""

    THEMES = ["system", "light", "dark"]
    LANGUAGES = [("zh-CN", "简体中文")]

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(settings, parent)
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.theme_combo = QComboBox()
        for theme in self.THEMES:
            self.theme_combo.addItem(theme.capitalize(), theme)
        form.addRow("Theme:", self.theme_combo)

        self.language_combo = QComboBox()
        for code, label in self.LANGUAGES:
            self.language_combo.addItem(label, code)
        form.addRow("Language:", self.language_combo)

        self.remember_layout_checkbox = QCheckBox("Remember window layout between sessions")
        form.addRow("", self.remember_layout_checkbox)

        layout.addLayout(form)
        layout.addStretch()

    def refresh(self) -> None:
        theme = self._settings.get_ui_setting("theme", "system")
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        language = self._settings.get_ui_setting("language", "zh-CN")
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        remember = bool(self._settings.get_ui_setting("remember_layout", True))
        self.remember_layout_checkbox.setChecked(remember)

    def apply(self) -> Tuple[bool, Optional[str]]:
        self._settings.set_ui_setting("theme", self.theme_combo.currentData())
        self._settings.set_ui_setting("language", self.language_combo.currentData())
        self._settings.set_ui_setting("remember_layout", self.remember_layout_checkbox.isChecked())
        return True, None


class AdvancedPreferencesWidget(BasePreferencesSection):
    """Preferences section for caching, logging, and batch-processing defaults."""

    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(settings, parent)
        self._repository = LibraryRepository()
        self._setup_ui()
        self.refresh()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        cache_group = QGroupBox("Caching")
        cache_layout = QFormLayout(cache_group)

        cache_dir_layout = QHBoxLayout()
        self.cache_dir_edit = QLineEdit()
        self.cache_dir_edit.setPlaceholderText("/path/to/cache")
        cache_browse = QPushButton("Browse…")
        cache_browse.clicked.connect(self._on_browse_cache)
        cache_dir_layout.addWidget(self.cache_dir_edit)
        cache_dir_layout.addWidget(cache_browse)
        cache_layout.addRow("Shared cache directory:", cache_dir_layout)

        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(1, 1440)
        cache_layout.addRow("Provider cache TTL (minutes):", self.cache_ttl_spin)

        layout.addWidget(cache_group)

        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        self.logging_combo = QComboBox()
        for level in self.LOG_LEVELS:
            self.logging_combo.addItem(level, level)
        logging_layout.addRow("Log level:", self.logging_combo)
        layout.addWidget(logging_group)

        batch_group = QGroupBox("Batch operation defaults")
        batch_layout = QFormLayout(batch_group)

        self.batch_rename_checkbox = QCheckBox("Rename using templates")
        batch_layout.addRow("", self.batch_rename_checkbox)

        self.batch_move_checkbox = QCheckBox("Move to library")
        move_layout = QHBoxLayout()
        self.batch_move_combo = QComboBox()
        self.batch_move_combo.setEnabled(False)
        self.batch_move_checkbox.toggled.connect(self.batch_move_combo.setEnabled)
        move_layout.addWidget(self.batch_move_combo)
        batch_layout.addRow(self.batch_move_checkbox, move_layout)

        self.batch_delete_checkbox = QCheckBox("Delete source files")
        batch_layout.addRow("", self.batch_delete_checkbox)

        self.batch_tags_checkbox = QCheckBox("Assign tags")
        self.batch_tags_edit = QLineEdit()
        self.batch_tags_edit.setEnabled(False)
        self.batch_tags_checkbox.toggled.connect(self.batch_tags_edit.setEnabled)
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(self.batch_tags_edit)
        batch_layout.addRow(self.batch_tags_checkbox, tag_layout)

        self.batch_metadata_checkbox = QCheckBox("Override metadata")
        metadata_layout = QHBoxLayout()
        self.batch_genres_edit = QLineEdit()
        self.batch_genres_edit.setPlaceholderText("genre1, genre2")
        self.batch_genres_edit.setEnabled(False)
        self.batch_rating_spin = QSpinBox()
        self.batch_rating_spin.setRange(0, 100)
        self.batch_rating_spin.setEnabled(False)
        self.batch_metadata_checkbox.toggled.connect(self.batch_genres_edit.setEnabled)
        self.batch_metadata_checkbox.toggled.connect(self.batch_rating_spin.setEnabled)
        metadata_layout.addWidget(self.batch_genres_edit)
        metadata_layout.addWidget(self.batch_rating_spin)
        batch_layout.addRow(self.batch_metadata_checkbox, metadata_layout)

        self.batch_resync_checkbox = QCheckBox("Re-sync provider metadata")
        batch_layout.addRow("", self.batch_resync_checkbox)

        layout.addWidget(batch_group)
        layout.addStretch()

    def refresh(self) -> None:
        cache_dir = self._settings.get_cache_setting("shared_cache_dir")
        if cache_dir:
            self.cache_dir_edit.setText(str(cache_dir))

        ttl_minutes = int(self._settings.get_cache_setting("provider_cache_ttl", 60))
        self.cache_ttl_spin.setValue(ttl_minutes)

        log_level = self._settings.get_logging_level()
        index = self.logging_combo.findData(log_level)
        if index >= 0:
            self.logging_combo.setCurrentIndex(index)

        self._reload_libraries()

        defaults = self._settings.get_batch_defaults()
        self.batch_rename_checkbox.setChecked(bool(defaults.get("rename", False)))
        move_default = bool(defaults.get("move", False))
        self.batch_move_checkbox.setChecked(move_default)
        move_library_id = defaults.get("move_library_id")
        if move_library_id is not None:
            idx = self.batch_move_combo.findData(move_library_id)
            if idx >= 0:
                self.batch_move_combo.setCurrentIndex(idx)

        self.batch_delete_checkbox.setChecked(bool(defaults.get("delete", False)))
        self.batch_tags_checkbox.setChecked(bool(defaults.get("tags", False)))
        if isinstance(defaults.get("default_tags"), list):
            tags_list = defaults.get("default_tags") or []
            self.batch_tags_edit.setText(", ".join(str(tag) for tag in tags_list))
        elif isinstance(defaults.get("default_tags"), str):
            self.batch_tags_edit.setText(str(defaults.get("default_tags")))
        else:
            self.batch_tags_edit.clear()

        self.batch_metadata_checkbox.setChecked(bool(defaults.get("metadata", False)))
        if isinstance(defaults.get("default_genres"), list):
            self.batch_genres_edit.setText(", ".join(str(g) for g in defaults.get("default_genres", [])))
        elif isinstance(defaults.get("default_genres"), str):
            self.batch_genres_edit.setText(str(defaults.get("default_genres")))
        else:
            self.batch_genres_edit.clear()

        rating_value = defaults.get("default_rating")
        if rating_value is not None:
            try:
                self.batch_rating_spin.setValue(int(rating_value))
            except (TypeError, ValueError):
                self.batch_rating_spin.setValue(0)
        else:
            self.batch_rating_spin.setValue(0)

        self.batch_resync_checkbox.setChecked(bool(defaults.get("resync", False)))

    def _reload_libraries(self) -> None:
        self.batch_move_combo.clear()
        try:
            libraries = self._repository.get_active()
        except Exception:  # pragma: no cover - defensive fallback
            libraries = []
        for library in libraries:
            self.batch_move_combo.addItem(library.name, library.id)
        if not libraries:
            self.batch_move_combo.addItem("No libraries", None)
            self.batch_move_combo.setEnabled(False)
        else:
            self.batch_move_combo.setEnabled(True)

    def _on_browse_cache(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select Cache Directory", self.cache_dir_edit.text())
        if directory:
            self.cache_dir_edit.setText(directory)

    def apply(self) -> Tuple[bool, Optional[str]]:
        cache_dir_text = self.cache_dir_edit.text().strip()
        if cache_dir_text:
            cache_path = Path(cache_dir_text)
            try:
                cache_path.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                return False, f"Unable to access cache directory: {exc}"
            self._settings.set_cache_setting("shared_cache_dir", str(cache_path))
        else:
            self._settings.set_cache_setting("shared_cache_dir", None)

        self._settings.set_cache_setting("provider_cache_ttl", self.cache_ttl_spin.value())
        self._settings.set_logging_level(self.logging_combo.currentData())

        defaults: Dict[str, Optional[object]] = {
            "rename": self.batch_rename_checkbox.isChecked(),
            "move": self.batch_move_checkbox.isChecked(),
            "delete": self.batch_delete_checkbox.isChecked(),
            "tags": self.batch_tags_checkbox.isChecked(),
            "metadata": self.batch_metadata_checkbox.isChecked(),
            "resync": self.batch_resync_checkbox.isChecked(),
        }

        move_id = self.batch_move_combo.currentData()
        if defaults["move"] and move_id is not None:
            defaults["move_library_id"] = int(move_id)
        else:
            defaults["move_library_id"] = None

        tags_text = self.batch_tags_edit.text().strip()
        if defaults["tags"] and tags_text:
            defaults["default_tags"] = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        else:
            defaults["default_tags"] = None

        genres_text = self.batch_genres_edit.text().strip()
        if defaults["metadata"] and genres_text:
            defaults["default_genres"] = [genre.strip() for genre in genres_text.split(",") if genre.strip()]
        else:
            defaults["default_genres"] = None

        if defaults["metadata"]:
            defaults["default_rating"] = self.batch_rating_spin.value()
        else:
            defaults["default_rating"] = None

        self._settings.set_batch_defaults(defaults)

        return True, None
