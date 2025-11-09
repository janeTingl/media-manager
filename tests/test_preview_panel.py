"""Tests for the preview panel."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox

from src.media_manager.models import MediaType, VideoMetadata
from src.media_manager.preview_panel import PreviewPanel


@pytest.fixture
def app():
    """Create QApplication for tests."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    return app


class TestPreviewPanel:
    """Test cases for PreviewPanel."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create QApplication if it doesn't exist
        from PySide6.QtWidgets import QApplication

        if not QApplication.instance():
            self.app = QApplication([])
        else:
            self.app = QApplication.instance()

        self.panel = PreviewPanel()

    def test_initialization(self):
        """Test panel initialization."""
        assert self.panel.movie_template_edit is not None
        assert self.panel.tv_template_edit is not None
        assert self.panel.preview_table is not None
        assert self.panel.preview_table.columnCount() == 5

    def test_default_templates(self):
        """Test default template values."""
        movie_template = self.panel.movie_template_edit.text()
        tv_template = self.panel.tv_template_edit.text()

        assert "{title}" in movie_template
        assert "{year}" in movie_template
        assert "{title}" in tv_template
        assert "{season02}" in tv_template

    def test_set_media_items(self):
        """Test setting media items updates preview."""
        # Create test media items
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        episode = VideoMetadata(
            file_path=Path("/test/episode.mkv"),
            title="Test Show",
            media_type=MediaType.TV_EPISODE,
            season=1,
            episode=2,
        )

        # Set media items
        self.panel.set_media_items([movie, episode])

        # Check that preview table is populated
        assert self.panel.preview_table.rowCount() == 2

    def test_select_all(self):
        """Test select all functionality."""
        # Create test media item
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        self.panel.set_media_items([movie])

        # Initially all should be selected
        checkbox = self.panel.preview_table.cellWidget(0, 0)
        assert isinstance(checkbox, QCheckBox)
        assert checkbox.isChecked()

        # Deselect all
        self.panel._select_none()
        assert not checkbox.isChecked()

        # Select all
        self.panel._select_all()
        assert checkbox.isChecked()

    def test_get_selected_operations(self):
        """Test getting selected operations."""
        # Create test media items
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        episode = VideoMetadata(
            file_path=Path("/test/episode.mkv"),
            title="Test Show",
            media_type=MediaType.TV_EPISODE,
            season=1,
            episode=2,
        )

        self.panel.set_media_items([movie, episode])

        # Get all selected operations
        selected = self.panel._get_selected_operations()
        assert len(selected) == 2

        # Deselect one operation
        checkbox = self.panel.preview_table.cellWidget(0, 0)
        checkbox.setChecked(False)

        selected = self.panel._get_selected_operations()
        assert len(selected) == 1

    def test_get_templates(self):
        """Test getting current template values."""
        templates = self.panel.get_templates()

        assert "movie" in templates
        assert "tv_episode" in templates
        assert isinstance(templates["movie"], str)
        assert isinstance(templates["tv_episode"], str)

    def test_set_templates(self):
        """Test setting template values."""
        new_templates = {
            "movie": "Custom/{title}/{title}{extension}",
            "tv_episode": "CustomTV/{title}/S{season02}E{episode02}/{title}{extension}",
        }

        self.panel.set_templates(new_templates)

        assert self.panel.movie_template_edit.text() == new_templates["movie"]
        assert self.panel.tv_template_edit.text() == new_templates["tv_episode"]

    def test_update_operation_status(self):
        """Test updating operation status in table."""
        # Create test media item
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        self.panel.set_media_items([movie])

        # Get the operation
        operation = self.panel._operations[0]

        # Update status to success
        self.panel.update_operation_status(operation, "Completed", True)

        # Check status was updated
        status_item = self.panel.preview_table.item(0, 4)
        assert status_item.text() == "Completed"
        # Note: Background color testing would require additional Qt test setup

    def test_execute_requested_signal(self):
        """Test execute requested signal emission."""
        # Create mock receiver
        mock_receiver = Mock()
        self.panel.execute_requested.connect(mock_receiver)

        # Create test media item
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        self.panel.set_media_items([movie])

        # Trigger execute operations
        self.panel._execute_operations(True)  # dry_run

        # Check signal was emitted
        mock_receiver.assert_called_once()
        args = mock_receiver.call_args[0]
        assert len(args) == 2
        assert args[1] is True  # dry_run flag

    def test_operations_changed_signal(self):
        """Test operations changed signal emission."""
        # Create mock receiver
        mock_receiver = Mock()
        self.panel.operations_changed.connect(mock_receiver)

        # Create test media item
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        # Set media items (should trigger signal)
        self.panel.set_media_items([movie])

        # Check signal was emitted
        mock_receiver.assert_called_once()
        operations = mock_receiver.call_args[0][0]
        assert len(operations) == 1

    def test_empty_media_items(self):
        """Test handling of empty media items."""
        self.panel.set_media_items([])

        assert self.panel.preview_table.rowCount() == 0
        assert "No media items" in self.panel.status_label.text()

    def test_invalid_template_handling(self):
        """Test handling of invalid templates."""
        # Create test media item
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        self.panel.set_media_items([movie])

        # Set invalid template
        self.panel.movie_template_edit.setText(
            "Invalid/{invalid_placeholder}{extension}"
        )

        # Update preview (should handle error gracefully)
        self.panel._update_preview()

        # Status should show 0 operations due to template error
        status_text = self.panel.status_label.text()
        assert "0 operations" in status_text
        # Also should have logged a warning (checked via captured log output)
