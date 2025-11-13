"""Tests for search UI components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication

from src.media_manager.search_filter_widget import SearchFilterWidget
from src.media_manager.search_results_widget import SearchResultsWidget
from src.media_manager.search_tab_widget import SearchTabWidget
from src.media_manager.search_results_model import SearchResultsModel
from src.media_manager.search_criteria import SearchCriteria
from src.media_manager.persistence.models import MediaItem, Tag, Person, Collection


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestSearchFilterWidget:
    """Tests for SearchFilterWidget."""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created."""
        widget = SearchFilterWidget()
        assert widget is not None
        assert widget.text_input is not None
        assert widget.type_combo is not None
    
    def test_get_criteria_default(self, qapp):
        """Test getting default criteria."""
        widget = SearchFilterWidget()
        criteria = widget.get_criteria()
        
        assert criteria.text_query == ""
        assert criteria.media_type is None
        assert criteria.sort_by == "title"
        assert criteria.sort_order == "asc"
    
    def test_get_criteria_with_text(self, qapp):
        """Test getting criteria with text search."""
        widget = SearchFilterWidget()
        widget.text_input.setText("test movie")
        
        criteria = widget.get_criteria()
        assert criteria.text_query == "test movie"
    
    def test_get_criteria_with_media_type(self, qapp):
        """Test getting criteria with media type."""
        widget = SearchFilterWidget()
        widget.type_combo.setCurrentText("Movies")
        
        criteria = widget.get_criteria()
        assert criteria.media_type == "movie"
        
        widget.type_combo.setCurrentText("TV Shows")
        criteria = widget.get_criteria()
        assert criteria.media_type == "tv"
    
    def test_get_criteria_with_year_range(self, qapp):
        """Test getting criteria with year range."""
        widget = SearchFilterWidget()
        widget.year_min_spin.setValue(2000)
        widget.year_max_spin.setValue(2020)
        
        criteria = widget.get_criteria()
        assert criteria.year_min == 2000
        assert criteria.year_max == 2020
    
    def test_get_criteria_with_rating_range(self, qapp):
        """Test getting criteria with rating range."""
        widget = SearchFilterWidget()
        widget.rating_min_spin.setValue(7.5)
        widget.rating_max_spin.setValue(9.5)
        
        criteria = widget.get_criteria()
        assert criteria.rating_min == 7.5
        assert criteria.rating_max == 9.5
    
    def test_get_criteria_with_runtime_range(self, qapp):
        """Test getting criteria with runtime range."""
        widget = SearchFilterWidget()
        widget.runtime_min_spin.setValue(90)
        widget.runtime_max_spin.setValue(150)
        
        criteria = widget.get_criteria()
        assert criteria.runtime_min == 90
        assert criteria.runtime_max == 150
    
    def test_get_criteria_with_quick_filter(self, qapp):
        """Test getting criteria with quick filter."""
        widget = SearchFilterWidget()
        widget.quick_filter_buttons["unmatched"].setChecked(True)
        
        criteria = widget.get_criteria()
        assert criteria.quick_filter == "unmatched"
    
    def test_get_criteria_with_sorting(self, qapp):
        """Test getting criteria with sorting."""
        widget = SearchFilterWidget()
        widget.sort_combo.setCurrentText("Rating")
        widget.sort_order_combo.setCurrentText("Descending")
        
        criteria = widget.get_criteria()
        assert criteria.sort_by == "rating"
        assert criteria.sort_order == "desc"
    
    def test_set_criteria(self, qapp):
        """Test setting criteria."""
        widget = SearchFilterWidget()
        
        criteria = SearchCriteria(
            text_query="test",
            media_type="movie",
            year_min=2000,
            year_max=2020,
            rating_min=8.0,
            sort_by="rating",
            sort_order="desc",
        )
        
        widget.set_criteria(criteria)
        
        assert widget.text_input.text() == "test"
        assert widget.type_combo.currentText() == "Movies"
        assert widget.year_min_spin.value() == 2000
        assert widget.year_max_spin.value() == 2020
        assert widget.rating_min_spin.value() == 8.0
    
    def test_clear_filters(self, qapp):
        """Test clearing filters."""
        widget = SearchFilterWidget()
        
        # Set some values
        widget.text_input.setText("test")
        widget.type_combo.setCurrentText("Movies")
        widget.year_min_spin.setValue(2000)
        widget.rating_min_spin.setValue(8.0)
        
        # Clear
        widget.clear_filters()
        
        # Verify cleared
        assert widget.text_input.text() == ""
        assert widget.type_combo.currentIndex() == 0
        assert widget.year_min_spin.value() == 1900
        assert widget.rating_min_spin.value() == 0.0
    
    @patch('src.media_manager.search_filter_widget.SearchService')
    def test_save_search(self, mock_service_class, qapp, qtbot):
        """Test saving a search."""
        widget = SearchFilterWidget()
        mock_service = Mock()
        widget._search_service = mock_service
        
        widget.text_input.setText("test")
        
        # Mock the input dialogs
        with patch('src.media_manager.search_filter_widget.QInputDialog.getText') as mock_input:
            mock_input.side_effect = [("My Search", True), ("Description", True)]
            
            with patch('src.media_manager.search_filter_widget.QMessageBox.information') as mock_msg:
                widget._on_save_clicked()
                
                # Verify save was called
                mock_service.save_search.assert_called_once()
                call_args = mock_service.save_search.call_args
                assert call_args[0][0] == "My Search"
                assert call_args[0][1].text_query == "test"
    
    @patch('src.media_manager.search_filter_widget.SearchService')
    def test_load_search(self, mock_service_class, qapp):
        """Test loading a search."""
        widget = SearchFilterWidget()
        mock_service = Mock()
        widget._search_service = mock_service
        
        # Mock saved searches
        from src.media_manager.persistence.models import SavedSearch
        import json
        
        saved_search = SavedSearch(
            id=1,
            name="My Search",
            criteria=json.dumps(SearchCriteria(text_query="test").to_dict()),
        )
        mock_service.get_saved_searches.return_value = [saved_search]
        mock_service.load_search.return_value = (
            saved_search,
            SearchCriteria(text_query="test"),
        )
        
        # Mock dialog
        with patch('src.media_manager.search_filter_widget.QInputDialog.getItem') as mock_input:
            mock_input.return_value = ("My Search", True)
            
            with patch.object(widget, '_on_search_clicked') as mock_search:
                widget._on_load_clicked()
                
                # Verify text was set
                assert widget.text_input.text() == "test"
                mock_search.assert_called_once()
    
    def test_quick_filter_mutual_exclusion(self, qapp):
        """Test that quick filters are mutually exclusive."""
        widget = SearchFilterWidget()
        
        # Check first button
        widget.quick_filter_buttons["unmatched"].setChecked(True)
        assert widget.quick_filter_buttons["unmatched"].isChecked()
        
        # Check second button - first should be unchecked
        widget.quick_filter_buttons["recent"].setChecked(True)
        widget._on_quick_filter_clicked("recent", True)
        assert not widget.quick_filter_buttons["unmatched"].isChecked()
        assert widget.quick_filter_buttons["recent"].isChecked()


class TestSearchResultsModel:
    """Tests for SearchResultsModel."""
    
    def test_model_creation(self, qapp):
        """Test model can be created."""
        model = SearchResultsModel()
        assert model is not None
        assert model.rowCount() == 0
        assert model.columnCount() == 8
    
    def test_model_headers(self, qapp):
        """Test model headers."""
        from PySide6.QtCore import Qt
        
        model = SearchResultsModel()
        headers = [
            "Title", "Year", "Type", "Rating",
            "Duration", "Added", "Size", "Status"
        ]
        
        for i, header in enumerate(headers):
            result = model.headerData(i, Qt.Horizontal, Qt.DisplayRole)
            assert result == header
    
    @patch('src.media_manager.search_results_model.SearchService')
    def test_model_search(self, mock_service_class, qapp):
        """Test model search."""
        from datetime import datetime
        
        model = SearchResultsModel()
        mock_service = Mock()
        model._search_service = mock_service
        
        # Mock search results
        item1 = MediaItem(
            id=1,
            library_id=1,
            title="Test Movie",
            media_type="movie",
            year=2020,
            rating=8.5,
        )
        item1.files = []
        item1.artworks = []
        item1.credits = []
        item1.tags = []
        item1.collections = []
        
        mock_service.search.return_value = ([item1], 1)
        
        # Execute search
        criteria = SearchCriteria(text_query="test")
        model.search(criteria)
        
        # Verify results
        assert model.rowCount() == 1
        assert model.get_total_count() == 1
    
    def test_model_clear(self, qapp):
        """Test clearing model."""
        model = SearchResultsModel()
        model._items = [Mock(), Mock()]
        model._total_count = 2
        
        model.clear()
        
        assert model.rowCount() == 0
        assert model.get_total_count() == 0


class TestSearchResultsWidget:
    """Tests for SearchResultsWidget."""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created."""
        widget = SearchResultsWidget()
        assert widget is not None
        assert widget.grid_view is not None
        assert widget.table_view is not None
    
    def test_view_switching(self, qapp):
        """Test switching between grid and table view."""
        widget = SearchResultsWidget()
        
        # Default is grid
        assert widget.view_stack.currentIndex() == 0
        assert widget.grid_btn.isChecked()
        
        # Switch to table
        widget._switch_view("table")
        assert widget.view_stack.currentIndex() == 1
        assert widget.table_btn.isChecked()
        assert not widget.grid_btn.isChecked()
        
        # Switch back to grid
        widget._switch_view("grid")
        assert widget.view_stack.currentIndex() == 0
        assert widget.grid_btn.isChecked()
    
    def test_size_change(self, qapp):
        """Test changing thumbnail size."""
        widget = SearchResultsWidget()
        
        with patch.object(widget.grid_view, 'set_thumbnail_size') as mock_set_size:
            widget._on_size_changed("Large")
            mock_set_size.assert_called_once_with("large")
    
    def test_pagination_buttons(self, qapp):
        """Test pagination button states."""
        widget = SearchResultsWidget()
        
        # Initially disabled
        assert not widget.prev_btn.isEnabled()
        assert not widget.next_btn.isEnabled()
        
        # Simulate search results
        widget._current_page = 1
        widget._total_pages = 3
        widget._on_search_finished(100)
        
        # Both should be enabled
        assert widget.prev_btn.isEnabled()
        assert widget.next_btn.isEnabled()
        
        # First page
        widget._current_page = 0
        widget._on_search_finished(100)
        assert not widget.prev_btn.isEnabled()
        assert widget.next_btn.isEnabled()
        
        # Last page
        widget._current_page = 2
        widget._on_search_finished(100)
        assert widget.prev_btn.isEnabled()
        assert not widget.next_btn.isEnabled()
    
    def test_results_label(self, qapp):
        """Test results label updates."""
        widget = SearchResultsWidget()
        
        # No results
        widget._model._total_count = 0
        widget._on_search_finished(0)
        assert "No results" in widget.results_label.text()
        
        # Single page of results
        widget._model._items = [Mock(), Mock()]
        widget._current_criteria = SearchCriteria(page_size=50)
        widget._current_page = 0
        widget._on_search_finished(2)
        assert "2 result" in widget.results_label.text()
        
        # Multiple pages
        widget._model._items = [Mock()] * 50
        widget._on_search_finished(150)
        assert "Showing" in widget.results_label.text()
        assert "150" in widget.results_label.text()
    
    def test_clear(self, qapp):
        """Test clearing results."""
        widget = SearchResultsWidget()
        widget._current_page = 2
        widget._total_pages = 5
        
        widget.clear()
        
        assert widget.results_label.text() == "No results"
        assert widget._current_page == 0
        assert widget._total_pages == 0


class TestSearchTabWidget:
    """Tests for SearchTabWidget."""
    
    def test_widget_creation(self, qapp):
        """Test widget can be created."""
        widget = SearchTabWidget()
        assert widget is not None
        assert widget.filter_widget is not None
        assert widget.results_widget is not None
    
    def test_signal_connections(self, qapp, qtbot):
        """Test signals are connected."""
        widget = SearchTabWidget()
        
        # Mock the search method
        with patch.object(widget.results_widget, 'search') as mock_search:
            # Emit search_requested signal
            criteria = SearchCriteria(text_query="test")
            widget.filter_widget.search_requested.emit(criteria)
            
            # Verify search was called
            mock_search.assert_called_once()
    
    def test_item_selected_signal(self, qapp, qtbot):
        """Test item_selected signal propagation."""
        widget = SearchTabWidget()
        
        with qtbot.waitSignal(widget.item_selected, timeout=1000) as blocker:
            # Emit from results widget
            mock_item = Mock(spec=MediaItem)
            widget.results_widget.item_selected.emit(mock_item)
        
        # Signal should have been received
        assert blocker.signal_triggered


class TestSearchIntegration:
    """Integration tests for search functionality."""
    
    @patch('src.media_manager.search_service.SearchService')
    def test_full_search_workflow(self, mock_service_class, qapp):
        """Test complete search workflow."""
        from datetime import datetime
        
        # Create widgets
        tab_widget = SearchTabWidget()
        
        # Mock service
        mock_service = Mock()
        tab_widget.filter_widget._search_service = mock_service
        tab_widget.results_widget.get_model()._search_service = mock_service
        
        # Mock search results
        item1 = MediaItem(
            id=1,
            library_id=1,
            title="Test Movie",
            media_type="movie",
            year=2020,
            rating=8.5,
            created_at=datetime.utcnow(),
        )
        item1.files = []
        item1.artworks = []
        item1.credits = []
        item1.tags = []
        item1.collections = []
        
        mock_service.search.return_value = ([item1], 1)
        
        # Set filter criteria
        tab_widget.filter_widget.text_input.setText("test")
        tab_widget.filter_widget.type_combo.setCurrentText("Movies")
        
        # Execute search
        tab_widget.filter_widget._on_search_clicked()
        
        # Verify search was called with correct criteria
        mock_service.search.assert_called_once()
        call_args = mock_service.search.call_args[0][0]
        assert call_args.text_query == "test"
        assert call_args.media_type == "movie"
        
        # Verify results are displayed
        model = tab_widget.results_widget.get_model()
        assert model.rowCount() == 1
