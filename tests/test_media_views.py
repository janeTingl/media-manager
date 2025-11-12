"""Tests for the media view components and MVC architecture."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtGui import QPixmap

from src.media_manager.library_view_model import LibraryViewModel
from src.media_manager.media_grid_view import MediaGridView
from src.media_manager.media_table_view import MediaTableView
from src.media_manager.detail_panel import DetailPanel
from src.media_manager.persistence.models import MediaItem, MediaFile, Artwork, Credit, Person, Library


@pytest.fixture
def mock_media_items():
    """Create mock media items for testing."""
    items = []
    
    # Movie item
    movie = MediaItem(
        id=1,
        library_id=1,
        title="Test Movie",
        media_type="movie",
        year=2023,
        description="A test movie",
        rating=8.5,
        runtime=120
    )
    
    # Add files
    movie_file = MediaFile(
        id=1,
        media_item_id=1,
        path="/test/movie.mkv",
        filename="movie.mkv",
        file_size=1024*1024*1024,  # 1GB
        resolution="1920x1080"
    )
    movie.files = [movie_file]
    
    # Add artwork
    poster = Artwork(
        id=1,
        media_item_id=1,
        artwork_type="poster",
        local_path=Path("/test/poster.jpg"),
        url="http://example.com/poster.jpg"
    )
    movie.artworks = [poster]
    
    items.append(movie)
    
    # TV episode item
    episode = MediaItem(
        id=2,
        library_id=1,
        title="Test Episode",
        media_type="tv",
        year=2023,
        season=1,
        episode=1,
        description="A test episode",
        rating=7.8,
        runtime=45
    )
    
    episode_file = MediaFile(
        id=2,
        media_item_id=2,
        path="/test/episode.mkv",
        filename="episode.mkv",
        file_size=500*1024*1024,  # 500MB
        resolution="1920x1080"
    )
    episode.files = [episode_file]
    
    items.append(episode)
    
    return items


@pytest.fixture
def mock_repository(mock_media_items):
    """Create a mock repository."""
    repo = Mock()
    repo.get_all.return_value = mock_media_items
    repo.get_by_library.return_value = mock_media_items
    repo.get_by_id.return_value = mock_media_items[0]
    repo.search.return_value = mock_media_items
    return repo


class TestLibraryViewModel:
    """Test the LibraryViewModel class."""
    
    def test_initialization(self, qtbot):
        """Test view model initialization."""
        model = LibraryViewModel()
        qtbot.addWidget(model)
        
        assert model.rowCount() == 0
        assert model.columnCount() == 8
        assert model.total_count() == 0
        assert model.filtered_count() == 0
        assert not model.is_loading()
    
    def test_data_loading(self, qtbot, mock_repository, mock_media_items):
        """Test data loading functionality."""
        model = LibraryViewModel()
        qtbot.addWidget(model)
        
        # Mock the repository
        model._repository = mock_repository
        
        # Load data
        model.load_data()
        
        # Verify data loaded
        assert model.rowCount() == len(mock_media_items)
        assert model.total_count() == len(mock_media_items)
        assert model.filtered_count() == len(mock_media_items)
    
    def test_data_access(self, qtbot, mock_repository, mock_media_items):
        """Test data access methods."""
        model = LibraryViewModel()
        qtbot.addWidget(model)
        model._repository = mock_repository
        model.load_data()
        
        # Test index creation
        index = model.index(0, 0)
        assert index.isValid()
        assert index.row() == 0
        assert index.column() == 0
        
        # Test data retrieval
        title_data = model.data(index, Qt.DisplayRole)
        assert title_data == "Test Movie"
        
        # Test custom roles
        item_data = model.data(index, model.MediaItemRole)
        assert item_data == mock_media_items[0]
        
        year_data = model.data(index, model.YearRole)
        assert year_data == 2023
    
    def test_header_data(self, qtbot):
        """Test header data functionality."""
        model = LibraryViewModel()
        qtbot.addWidget(model)
        
        headers = ["Title", "Year", "Type", "Rating", "Duration", "Added", "Size", "Status"]
        
        for i, expected_header in enumerate(headers):
            header = model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
            assert header == expected_header
    
    def test_filtering(self, qtbot, mock_repository, mock_media_items):
        """Test filtering functionality."""
        model = LibraryViewModel()
        qtbot.addWidget(model)
        model._repository = mock_repository
        model.load_data()
        
        # Test text filter
        model.set_filter("Movie")
        assert model.filtered_count() == 1
        
        # Test media type filter
        model.set_media_type_filter("movie")
        assert model.filtered_count() == 1
        
        model.set_media_type_filter("tv")
        assert model.filtered_count() == 1
        
        model.set_media_type_filter("all")
        assert model.filtered_count() == 2
    
    def test_sorting(self, qtbot, mock_repository, mock_media_items):
        """Test sorting functionality."""
        model = LibraryViewModel()
        qtbot.addWidget(model)
        model._repository = mock_repository
        model.load_data()
        
        # Test title sorting
        model.sort(0, Qt.AscendingOrder)
        title_1 = model.data(model.index(0, 0), Qt.DisplayRole)
        title_2 = model.data(model.index(1, 0), Qt.DisplayRole)
        assert title_1 <= title_2
        
        # Test year sorting
        model.sort(1, Qt.DescendingOrder)
        year_1 = model.data(model.index(0, 1), Qt.DisplayRole)
        year_2 = model.data(model.index(1, 1), Qt.DisplayRole)
        assert year_1 >= year_2


class TestMediaGridView:
    """Test the MediaGridView class."""
    
    def test_initialization(self, qtbot):
        """Test grid view initialization."""
        view = MediaGridView()
        qtbot.addWidget(view)
        
        assert view.viewMode() == view.ViewMode.IconMode
        assert view.resizeMode() == view.ResizeMode.Adjust
        assert view.selectionMode() == view.SelectionMode.ExtendedSelection
        assert not view.editTriggers()
    
    def test_model_binding(self, qtbot, mock_repository):
        """Test model binding."""
        view = MediaGridView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        view.set_model(model)
        assert view.model() == model
        
        # Load data
        model.load_data()
        assert view.model().rowCount() > 0
    
    def test_thumbnail_size_adjustment(self, qtbot):
        """Test thumbnail size adjustment."""
        view = MediaGridView()
        qtbot.addWidget(view)
        
        # Test different thumbnail sizes
        view.set_thumbnail_size("small")
        assert view.iconSize().width() == 100
        assert view.iconSize().height() == 150
        
        view.set_thumbnail_size("large")
        assert view.iconSize().width() == 200
        assert view.iconSize().height() == 300
    
    def test_selection_handling(self, qtbot, mock_repository):
        """Test selection handling."""
        view = MediaGridView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        view.set_model(model)
        model.load_data()
        
        # Test item selection
        index = view.model().index(0, 0)
        view.setCurrentIndex(index)
        
        selected_items = view.get_selected_items()
        assert len(selected_items) == 1
        
        current_item = view.get_current_item()
        assert current_item is not None
    
    def test_signal_emission(self, qtbot, mock_repository):
        """Test signal emission."""
        view = MediaGridView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        view.set_model(model)
        model.load_data()
        
        # Track signals
        with qtbot.waitSignal(view.item_selected, timeout=1000):
            index = view.model().index(0, 0)
            view.setCurrentIndex(index)
            QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.visualRect(index).center())


class TestMediaTableView:
    """Test the MediaTableView class."""
    
    def test_initialization(self, qtbot):
        """Test table view initialization."""
        view = MediaTableView()
        qtbot.addWidget(view)
        
        assert view.selectionBehavior() == view.SelectionBehavior.SelectRows
        assert view.selectionMode() == view.SelectionMode.ExtendedSelection
        assert view.isSortingEnabled()
        assert view.alternatingRowColors()
    
    def test_model_binding(self, qtbot, mock_repository):
        """Test model binding."""
        view = MediaTableView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        view.set_model(model)
        assert view.model() == model
        
        # Load data
        model.load_data()
        assert view.model().rowCount() > 0
        assert view.model().columnCount() == 8
    
    def test_column_visibility(self, qtbot):
        """Test column visibility controls."""
        view = MediaTableView()
        qtbot.addWidget(view)
        
        # Test column hiding/showing
        view.set_column_visibility(0, False)
        assert view.isColumnHidden(0)
        
        view.set_column_visibility(0, True)
        assert not view.isColumnHidden(0)
        
        # Test toggle
        view.toggle_column_visibility(1)
        assert view.isColumnHidden(1)
        
        view.toggle_column_visibility(1)
        assert not view.isColumnHidden(1)
    
    def test_selection_handling(self, qtbot, mock_repository):
        """Test selection handling."""
        view = MediaTableView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        view.set_model(model)
        model.load_data()
        
        # Test selection
        view.selectRow(0)
        selected_items = view.get_selected_items()
        assert len(selected_items) == 1
        
        # Test select all
        view.selectAll()
        selected_items = view.get_selected_items()
        assert len(selected_items) == model.rowCount()
        
        view.clearSelection()
        selected_items = view.get_selected_items()
        assert len(selected_items) == 0
    
    def test_context_menu(self, qtbot, mock_repository):
        """Test context menu functionality."""
        view = MediaTableView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        view.set_model(model)
        model.load_data()
        
        # Test context menu creation
        menu = view.create_context_menu()
        assert menu is not None
        assert not menu.isEmpty()


class TestDetailPanel:
    """Test the DetailPanel class."""
    
    def test_initialization(self, qtbot):
        """Test detail panel initialization."""
        panel = DetailPanel()
        qtbot.addWidget(panel)
        
        assert panel.is_collapsed()
        assert panel.minimumWidth() == 300
        assert panel.maximumWidth() == 500
    
    def test_collapse_functionality(self, qtbot):
        """Test collapse/expand functionality."""
        panel = DetailPanel()
        qtbot.addWidget(panel)
        
        # Initially collapsed
        assert panel.is_collapsed()
        
        # Expand
        panel.expand()
        assert not panel.is_collapsed()
        
        # Collapse
        panel.collapse()
        assert panel.is_collapsed()
        
        # Toggle
        panel.toggle_collapse()
        assert not panel.is_collapsed()
        
        panel.toggle_collapse()
        assert panel.is_collapsed()
    
    def test_media_item_display(self, qtbot, mock_media_items):
        """Test media item display functionality."""
        panel = DetailPanel()
        qtbot.addWidget(panel)
        
        # Set media item
        item = mock_media_items[0]
        panel.set_media_item(item)
        
        # Panel should expand when item is set
        assert not panel.is_collapsed()
        
        # Test with None
        panel.set_media_item(None)
        assert panel.is_collapsed()
    
    def test_signal_emission(self, qtbot, mock_media_items):
        """Test signal emission."""
        panel = DetailPanel()
        qtbot.addWidget(panel)
        
        # Track signals
        with qtbot.waitSignal(panel.edit_requested, timeout=1000):
            item = mock_media_items[0]
            panel.set_media_item(item)
            QTest.mouseClick(panel._edit_button, Qt.MouseButton.LeftButton)
        
        with qtbot.waitSignal(panel.play_requested, timeout=1000):
            QTest.mouseClick(panel._play_button, Qt.MouseButton.LeftButton)


class TestViewIntegration:
    """Test integration between view components."""
    
    def test_selection_synchronization(self, qtbot, mock_repository):
        """Test selection synchronization between views."""
        grid_view = MediaGridView()
        table_view = MediaTableView()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        # Bind both views to same model
        grid_view.set_model(model)
        table_view.set_model(model)
        model.load_data()
        
        # Select in grid view
        grid_index = model.index(0, 0)
        grid_view.setCurrentIndex(grid_index)
        
        # Verify selection
        grid_selected = grid_view.get_selected_items()
        assert len(grid_selected) == 1
        
        # Select in table view
        table_view.selectRow(1)
        table_selected = table_view.get_selected_items()
        assert len(table_selected) >= 1
    
    def test_detail_panel_integration(self, qtbot, mock_repository, mock_media_items):
        """Test detail panel integration with views."""
        grid_view = MediaGridView()
        detail_panel = DetailPanel()
        model = LibraryViewModel()
        model._repository = mock_repository
        
        # Connect signals
        grid_view.item_selected.connect(detail_panel.set_media_item)
        
        # Set up model
        grid_view.set_model(model)
        model.load_data()
        
        # Select item in grid view
        index = model.index(0, 0)
        grid_view.setCurrentIndex(index)
        
        # Verify detail panel updated
        # Note: This would need to be tested with actual signal emission
        assert detail_panel._current_item is not None


if __name__ == "__main__":
    pytest.main([__file__])