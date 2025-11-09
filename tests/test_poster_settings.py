"""Tests for the poster settings widget."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from PySide6.QtTest import QTest

from src.media_manager.models import PosterType, PosterSize
from src.media_manager.poster_settings_widget import PosterSettingsWidget


class TestPosterSettingsWidget:
    """Test cases for PosterSettingsWidget."""

    def test_init(self, qapp) -> None:
        """Test widget initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                # Check that all UI elements exist
                assert widget.auto_download_checkbox is not None
                assert widget.poster_checkbox is not None
                assert widget.fanart_checkbox is not None
                assert widget.banner_checkbox is not None
                assert widget.poster_size_combo is not None
                assert widget.fanart_size_combo is not None
                assert widget.banner_size_combo is not None
                assert widget.max_retries_spinbox is not None
                assert widget.timeout_spinbox is not None
                assert widget.cache_dir_edit is not None
                assert widget.clear_cache_button is not None

    def test_load_settings(self, qapp) -> None:
        """Test loading settings from storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            # Set some test settings
            settings.set_auto_download_posters(True)
            settings.set_enabled_poster_types(["poster", "fanart"])
            settings.set_poster_size("poster", "large")
            settings.set_max_retries(5)
            settings.set_cache_dir("/test/cache")
            settings.save_settings()
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                # Check that settings were loaded
                assert widget.auto_download_checkbox.isChecked()
                assert widget.poster_checkbox.isChecked()
                assert widget.fanart_checkbox.isChecked()
                assert not widget.banner_checkbox.isChecked()
                assert widget.poster_size_combo.currentText() == "large"
                assert widget.max_retries_spinbox.value() == 5
                assert widget.cache_dir_edit.text() == "/test/cache"

    def test_save_settings(self, qapp) -> None:
        """Test saving settings to storage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                # Change some settings
                widget.auto_download_checkbox.setChecked(True)
                widget.poster_checkbox.setChecked(True)
                widget.fanart_checkbox.setChecked(False)
                widget.banner_checkbox.setChecked(True)
                widget.poster_size_combo.setCurrentText("small")
                widget.fanart_size_combo.setCurrentText("medium")
                widget.banner_size_combo.setCurrentText("large")
                widget.max_retries_spinbox.setValue(7)
                widget.timeout_spinbox.setValue(60)
                widget.cache_dir_edit.setText("/new/cache")
                
                # Trigger save
                widget._save_settings()
                
                # Check that settings were saved
                assert settings.get_auto_download_posters() is True
                enabled_types = settings.get_enabled_poster_types()
                assert "poster" in enabled_types
                assert "fanart" not in enabled_types
                assert "banner" in enabled_types
                assert settings.get_poster_size("poster") == "small"
                assert settings.get_poster_size("fanart") == "medium"
                assert settings.get_poster_size("banner") == "large"
                assert settings.get_max_retries() == 7
                assert settings.get_cache_dir() == "/new/cache"

    def test_setting_changed_signal(self, qapp) -> None:
        """Test that settings_changed signal is emitted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                signal_received = False
                
                def on_settings_changed():
                    nonlocal signal_received
                    signal_received = True
                
                widget.settings_changed.connect(on_settings_changed)
                
                # Change a setting
                widget.auto_download_checkbox.setChecked(True)
                
                assert signal_received

    def test_get_enabled_poster_types(self, qapp) -> None:
        """Test getting enabled poster types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                # Enable some types
                widget.poster_checkbox.setChecked(True)
                widget.fanart_checkbox.setChecked(True)
                widget.banner_checkbox.setChecked(False)
                
                enabled_types = widget.get_enabled_poster_types()
                
                assert PosterType.POSTER in enabled_types
                assert PosterType.FANART in enabled_types
                assert PosterType.BANNER not in enabled_types

    @patch('src.media_manager.poster_settings_widget.QFileDialog.getExistingDirectory')
    def test_browse_cache(self, mock_get_directory, qapp) -> None:
        """Test browsing for cache directory."""
        mock_get_directory.return_value = "/selected/directory"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                # Click browse button
                QTest.mouseClick(widget.browse_cache_button, Qt.LeftButton)
                
                assert widget.cache_dir_edit.text() == "/selected/directory"

    @patch('src.media_manager.poster_settings_widget.QMessageBox.question')
    @patch('src.media_manager.poster_settings_widget.QMessageBox.information')
    def test_clear_cache_success(self, mock_info, mock_question, qapp) -> None:
        """Test successful cache clearing."""
        mock_question.return_value = mock_question.Yes
        
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                # Create a mock downloader
                mock_downloader = Mock()
                
                with patch('src.media_manager.poster_settings_widget.PosterDownloader', return_value=mock_downloader):
                    # Click clear cache button
                    QTest.mouseClick(widget.clear_cache_button, Qt.LeftButton)
                    
                    mock_downloader.clear_cache.assert_called_once()
                    mock_info.assert_called_once()

    @patch('src.media_manager.poster_settings_widget.QMessageBox.question')
    @patch('src.media_manager.poster_settings_widget.QMessageBox.warning')
    def test_clear_cache_cancelled(self, mock_warning, mock_question, qapp) -> None:
        """Test cache clearing when user cancels."""
        mock_question.return_value = mock_question.No
        
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                mock_downloader = Mock()
                
                with patch('src.media_manager.poster_settings_widget.PosterDownloader', return_value=mock_downloader):
                    # Click clear cache button
                    QTest.mouseClick(widget.clear_cache_button, Qt.LeftButton)
                    
                    mock_downloader.clear_cache.assert_not_called()
                    mock_warning.assert_not_called()

    @patch('src.media_manager.poster_settings_widget.QMessageBox.question')
    @patch('src.media_manager.poster_settings_widget.QMessageBox.warning')
    def test_clear_cache_error(self, mock_warning, mock_question, qapp) -> None:
        """Test cache clearing with error."""
        mock_question.return_value = mock_question.Yes
        
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            from src.media_manager.settings import SettingsManager
            settings = SettingsManager(settings_file)
            
            with patch('src.media_manager.poster_settings_widget.get_settings', return_value=settings):
                widget = PosterSettingsWidget()
                
                mock_downloader = Mock()
                mock_downloader.clear_cache.side_effect = Exception("Cache error")
                
                with patch('src.media_manager.poster_settings_widget.PosterDownloader', return_value=mock_downloader):
                    # Click clear cache button
                    QTest.mouseClick(widget.clear_cache_button, Qt.LeftButton)
                    
                    mock_warning.assert_called_once()
                    assert "Cache error" in str(mock_warning.call_args)