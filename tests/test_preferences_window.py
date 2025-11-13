"""Tests for the preferences window and its sections."""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.media_manager.preferences_window import (
    AdvancedPreferencesWidget,
    DownloadsPreferencesWidget,
    LibrariesPreferencesWidget,
    MetadataPreferencesWidget,
    PreferencesWindow,
    ProvidersPreferencesWidget,
    UIPreferencesWidget,
)
from src.media_manager.settings import SettingsManager


@pytest.fixture
def temp_settings():
    with tempfile.TemporaryDirectory() as temp_dir:
        settings_file = Path(temp_dir) / "settings.json"
        yield SettingsManager(settings_file)


def _patch_libraries(monkeypatch, libraries):
    monkeypatch.setattr(
        "src.media_manager.preferences_window.LibraryRepository.get_active",
        lambda self: libraries,
    )


def test_preferences_window_tabs(qapp, temp_settings, monkeypatch):
    _patch_libraries(monkeypatch, [])
    monkeypatch.setattr(
        "src.media_manager.poster_settings_widget.get_settings",
        lambda: temp_settings,
    )

    window = PreferencesWindow(temp_settings)

    tab_titles = [window._tab_widget.tabText(i) for i in range(window._tab_widget.count())]
    assert tab_titles == ["Libraries", "Metadata", "Providers", "Downloads", "UI", "Advanced"]


def test_providers_preferences_validation(qapp, temp_settings):
    widget = ProvidersPreferencesWidget(temp_settings)

    widget.tmdb_key_edit.setText("short")
    success, error = widget.apply()
    assert success is False
    assert "TMDB" in (error or "")

    widget.tmdb_key_edit.setText("a" * 20)
    widget.tvdb_key_edit.setText("b" * 20)
    widget.tmdb_enabled_checkbox.setChecked(True)
    widget.tvdb_enabled_checkbox.setChecked(True)

    success, error = widget.apply()
    assert success is True
    assert temp_settings.get_tmdb_api_key() == "a" * 20
    assert temp_settings.get_tvdb_api_key() == "b" * 20
    assert set(temp_settings.get_enabled_providers()) == {"TMDB", "TVDB"}


def test_libraries_preferences_apply(qapp, temp_settings, monkeypatch):
    libraries = [SimpleNamespace(name="Movies", id=1), SimpleNamespace(name="TV", id=2)]
    _patch_libraries(monkeypatch, libraries)

    widget = LibrariesPreferencesWidget(temp_settings)
    widget.default_library_combo.setCurrentIndex(0)
    widget.auto_restore_checkbox.setChecked(True)

    with tempfile.TemporaryDirectory() as temp_dir:
        root_path = Path(temp_dir) / "library"
        widget.library_root_edit.setText(str(root_path))
        success, error = widget.apply()
        assert success is True

    assert temp_settings.get_default_library_id() == 1
    assert temp_settings.get_library_setting("auto_restore_last") is True
    assert temp_settings.get_library_setting("library_root") == str(root_path)


def test_downloads_preferences_apply(qapp, temp_settings, monkeypatch):
    monkeypatch.setattr(
        "src.media_manager.poster_settings_widget.get_settings",
        lambda: temp_settings,
    )
    widget = DownloadsPreferencesWidget(temp_settings)
    widget.trailer_quality_combo.setCurrentText("4K")

    success, error = widget.apply()
    assert success is True
    assert temp_settings.get_trailer_quality().upper() == "4K"


def test_ui_preferences_apply(qapp, temp_settings):
    widget = UIPreferencesWidget(temp_settings)
    widget.theme_combo.setCurrentIndex(widget.theme_combo.findData("dark"))
    widget.language_combo.setCurrentIndex(widget.language_combo.findData("de"))
    widget.remember_layout_checkbox.setChecked(False)

    success, error = widget.apply()
    assert success is True
    assert temp_settings.get_ui_setting("theme") == "dark"
    assert temp_settings.get_ui_setting("language") == "de"
    assert temp_settings.get_ui_setting("remember_layout") is False


def test_advanced_preferences_apply(qapp, temp_settings, monkeypatch):
    libraries = [SimpleNamespace(name="Movies", id=42)]
    _patch_libraries(monkeypatch, libraries)

    widget = AdvancedPreferencesWidget(temp_settings)

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "cache"
        widget.cache_dir_edit.setText(str(cache_dir))

        widget.cache_ttl_spin.setValue(120)
        widget.logging_combo.setCurrentText("WARNING")

        widget.batch_rename_checkbox.setChecked(True)
        widget.batch_move_checkbox.setChecked(True)
        widget.batch_move_combo.setCurrentIndex(0)
        widget.batch_delete_checkbox.setChecked(False)
        widget.batch_tags_checkbox.setChecked(True)
        widget.batch_tags_edit.setText("to-watch, favorites")
        widget.batch_metadata_checkbox.setChecked(True)
        widget.batch_genres_edit.setText("Drama, Mystery")
        widget.batch_rating_spin.setValue(85)
        widget.batch_resync_checkbox.setChecked(True)

        success, error = widget.apply()
        assert success is True

    assert temp_settings.get_cache_setting("shared_cache_dir") == str(cache_dir)
    assert temp_settings.get_cache_setting("provider_cache_ttl") == 120
    assert temp_settings.get_logging_level() == "WARNING"

    defaults = temp_settings.get_batch_defaults()
    assert defaults["rename"] is True
    assert defaults["move"] is True
    assert defaults["move_library_id"] == 42
    assert defaults["tags"] is True
    assert defaults["default_tags"] == ["to-watch", "favorites"]
    assert defaults["metadata"] is True
    assert defaults["default_genres"] == ["Drama", "Mystery"]
    assert defaults["default_rating"] == 85
    assert defaults["resync"] is True


def test_metadata_preferences_apply(qapp, temp_settings):
    widget = MetadataPreferencesWidget(temp_settings)
    widget.movie_template_edit.setText("{title}-{year}")
    widget.tv_template_edit.setText("{title}-S{season:02d}E{episode:02d}")
    widget.subtitle_provider_combo.setCurrentText("SubDB")
    widget.subtitle_languages_edit.setText("en, es")
    widget.subtitle_auto_checkbox.setChecked(True)
    widget.nfo_enabled_checkbox.setChecked(True)
    widget.nfo_subfolder_edit.setText("metadata")

    success, error = widget.apply()
    assert success is True

    assert temp_settings.get_rename_template("movie") == "{title}-{year}"
    assert temp_settings.get_rename_template("tv_episode") == "{title}-S{season:02d}E{episode:02d}"
    assert temp_settings.get_subtitle_provider() == "SubDB"
    assert temp_settings.get_enabled_subtitle_languages() == ["en", "es"]
    assert temp_settings.get_auto_download_subtitles() is True
    assert temp_settings.get_nfo_enabled() is True
    assert temp_settings.get_nfo_target_subfolder() == "metadata"
