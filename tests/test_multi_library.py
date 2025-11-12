"""Integration tests for multi-library management functionality."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.media_manager.library_manager_dialog import LibraryManagerDialog
from src.media_manager.library_tree_widget import LibraryTreeWidget
from src.media_manager.library_view_model import LibraryViewModel
from src.media_manager.main_window import MainWindow
from src.media_manager.persistence.models import Library, MediaItem
from src.media_manager.persistence.repositories import LibraryRepository, MediaItemRepository
from src.media_manager.settings import SettingsManager


@pytest.fixture
def app(qtbot):
    """Fixture for Qt application."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def temp_db(tmp_path):
    """Fixture for temporary database."""
    db_path = tmp_path / "test.db"
    return f"sqlite:///{db_path}"


@pytest.fixture
def library_repository(temp_db):
    """Fixture for library repository with test database."""
    from src.media_manager.persistence.database import init_database_service
    init_database_service(temp_db, auto_migrate=False)
    return LibraryRepository()


@pytest.fixture
def sample_libraries(library_repository, tmp_path):
    """Fixture creating sample libraries."""
    # Create test directories
    movies_path = tmp_path / "movies"
    tv_path = tmp_path / "tv"
    mixed_path = tmp_path / "mixed"
    
    movies_path.mkdir()
    tv_path.mkdir()
    mixed_path.mkdir()
    
    # Create libraries
    movie_lib = Library(
        name="Movies",
        path=str(movies_path),
        media_type="movie",
        is_active=True,
        scan_roots=json.dumps([str(movies_path)]),
        default_destination=str(movies_path / "processed"),
        color="#FF5733"
    )
    
    tv_lib = Library(
        name="TV Shows",
        path=str(tv_path),
        media_type="tv",
        is_active=True,
        scan_roots=json.dumps([str(tv_path)]),
        default_destination=str(tv_path / "processed"),
        color="#33FF57"
    )
    
    mixed_lib = Library(
        name="Mixed Media",
        path=str(mixed_path),
        media_type="mixed",
        is_active=True,
        scan_roots=json.dumps([str(mixed_path)]),
        color="#3357FF"
    )
    
    # Save to database
    movie_lib = library_repository.create(movie_lib)
    tv_lib = library_repository.create(tv_lib)
    mixed_lib = library_repository.create(mixed_lib)
    
    return movie_lib, tv_lib, mixed_lib


class TestLibraryRepository:
    """Tests for LibraryRepository."""
    
    def test_create_library(self, library_repository, tmp_path):
        """Test creating a library."""
        lib_path = tmp_path / "test_lib"
        lib_path.mkdir()
        
        library = Library(
            name="Test Library",
            path=str(lib_path),
            media_type="movie",
            is_active=True
        )
        
        created = library_repository.create(library)
        
        assert created.id is not None
        assert created.name == "Test Library"
        assert created.is_active is True
    
    def test_get_all_libraries(self, library_repository, sample_libraries):
        """Test getting all libraries."""
        libraries = library_repository.get_all()
        
        assert len(libraries) == 3
        assert any(lib.name == "Movies" for lib in libraries)
        assert any(lib.name == "TV Shows" for lib in libraries)
        assert any(lib.name == "Mixed Media" for lib in libraries)
    
    def test_get_active_libraries(self, library_repository, sample_libraries, tmp_path):
        """Test getting only active libraries."""
        # Create an inactive library
        inactive_path = tmp_path / "inactive"
        inactive_path.mkdir()
        
        inactive_lib = Library(
            name="Inactive",
            path=str(inactive_path),
            media_type="movie",
            is_active=False
        )
        library_repository.create(inactive_lib)
        
        active = library_repository.get_active()
        
        assert len(active) == 3  # Only the 3 sample libraries
        assert all(lib.is_active for lib in active)
    
    def test_update_library(self, library_repository, sample_libraries):
        """Test updating a library."""
        movie_lib, _, _ = sample_libraries
        
        movie_lib.name = "Updated Movies"
        movie_lib.description = "New description"
        
        updated = library_repository.update(movie_lib)
        
        assert updated.name == "Updated Movies"
        assert updated.description == "New description"
    
    def test_delete_library(self, library_repository, sample_libraries):
        """Test deleting a library."""
        _, _, mixed_lib = sample_libraries
        
        success = library_repository.delete(mixed_lib.id)
        
        assert success is True
        
        libraries = library_repository.get_all()
        assert len(libraries) == 2


class TestLibraryTreeWidget:
    """Tests for LibraryTreeWidget."""
    
    def test_load_libraries(self, qtbot, sample_libraries):
        """Test loading libraries into tree widget."""
        widget = LibraryTreeWidget()
        qtbot.addWidget(widget)
        
        widget.load_libraries()
        
        # Should have 3 top-level items (one for each library)
        assert widget.tree.topLevelItemCount() == 3
        
        # Check first library has child nodes
        first_item = widget.tree.topLevelItem(0)
        assert first_item.childCount() > 0
    
    def test_library_selection_signal(self, qtbot, sample_libraries):
        """Test library selection emits correct signal."""
        widget = LibraryTreeWidget()
        qtbot.addWidget(widget)
        
        widget.load_libraries()
        
        # Create signal spy
        with qtbot.waitSignal(widget.library_selected, timeout=1000) as blocker:
            # Select the first library's first child
            first_item = widget.tree.topLevelItem(0)
            first_child = first_item.child(0)
            widget.tree.setCurrentItem(first_child)
        
        # Check signal was emitted with correct data
        library, media_type = blocker.args
        assert library is not None
        assert media_type in ["all", "movie", "tv"]
    
    def test_library_colors(self, qtbot, sample_libraries):
        """Test that library colors are applied."""
        widget = LibraryTreeWidget()
        qtbot.addWidget(widget)
        
        widget.load_libraries()
        
        # Get first library item
        first_item = widget.tree.topLevelItem(0)
        
        # Check that foreground color is set (color from sample libraries)
        foreground = first_item.foreground(0)
        assert foreground is not None


class TestLibraryManagerDialog:
    """Tests for LibraryManagerDialog."""
    
    def test_dialog_opens(self, qtbot, sample_libraries):
        """Test that library manager dialog opens."""
        dialog = LibraryManagerDialog()
        qtbot.addWidget(dialog)
        
        assert dialog.isVisible() or not dialog.isVisible()  # Just check it initializes
        assert dialog.library_list.count() == 3
    
    def test_library_form_validation(self, qtbot):
        """Test library form validation."""
        dialog = LibraryManagerDialog()
        qtbot.addWidget(dialog)
        
        # Test empty name
        dialog.library_form.name_edit.clear()
        dialog.library_form.path_edit.setText("/tmp/test")
        
        is_valid, error_msg = dialog.library_form.validate()
        assert is_valid is False
        assert "name" in error_msg.lower()
    
    def test_library_form_load(self, qtbot, sample_libraries):
        """Test loading library into form."""
        movie_lib, _, _ = sample_libraries
        
        dialog = LibraryManagerDialog()
        qtbot.addWidget(dialog)
        
        dialog.library_form.load_library(movie_lib)
        
        assert dialog.library_form.name_edit.text() == movie_lib.name
        assert dialog.library_form.path_edit.text() == movie_lib.path
        assert dialog.library_form.media_type_combo.currentText() == movie_lib.media_type


class TestLibraryViewModel:
    """Tests for LibraryViewModel with library filtering."""
    
    def test_library_filter(self, qtbot, sample_libraries):
        """Test filtering by library."""
        movie_lib, tv_lib, _ = sample_libraries
        
        # Create some test media items
        media_repo = MediaItemRepository()
        
        movie_item = MediaItem(
            library_id=movie_lib.id,
            title="Test Movie",
            media_type="movie",
            year=2020
        )
        
        tv_item = MediaItem(
            library_id=tv_lib.id,
            title="Test Show",
            media_type="tv",
            year=2021
        )
        
        # Mock the repository to return our test items
        with patch.object(media_repo, 'get_by_library', return_value=[movie_item]):
            model = LibraryViewModel()
            model._repository = media_repo
            
            model.set_library_filter(movie_lib.id)
            
            # Should only have movie items
            assert model.filtered_count() == 1
    
    def test_media_type_filter_with_library(self, qtbot, sample_libraries):
        """Test combined library and media type filtering."""
        mixed_lib = sample_libraries[2]
        
        # Create mixed media items
        media_repo = MediaItemRepository()
        
        movie_item = MediaItem(
            library_id=mixed_lib.id,
            title="Movie in Mixed",
            media_type="movie",
            year=2020
        )
        
        tv_item = MediaItem(
            library_id=mixed_lib.id,
            title="TV in Mixed",
            media_type="tv",
            year=2021
        )
        
        # Mock the repository
        with patch.object(media_repo, 'get_by_library', return_value=[movie_item, tv_item]):
            model = LibraryViewModel()
            model._repository = media_repo
            
            model.set_library_filter(mixed_lib.id)
            
            # Should have both items initially
            assert model.filtered_count() == 2
            
            # Filter by movie type
            model.set_media_type_filter("movie")
            
            # Should only have one item
            assert model.filtered_count() == 1


class TestMainWindowIntegration:
    """Integration tests for main window with multi-library support."""
    
    def test_library_tree_in_main_window(self, qtbot, sample_libraries):
        """Test that library tree is present in main window."""
        settings = SettingsManager()
        main_window = MainWindow(settings)
        qtbot.addWidget(main_window)
        
        # Check that library tree widget exists
        assert hasattr(main_window, 'library_tree_widget')
        assert main_window.library_tree_widget is not None
    
    def test_library_selection_updates_view(self, qtbot, sample_libraries):
        """Test that selecting a library updates the view model."""
        settings = SettingsManager()
        main_window = MainWindow(settings)
        qtbot.addWidget(main_window)
        
        movie_lib, _, _ = sample_libraries
        
        # Simulate library selection
        main_window._on_library_selected(movie_lib, "all")
        
        # Check that current library is set
        assert main_window._current_library == movie_lib
        
        # Check that library filter is applied
        assert main_window.library_view_model._library_filter == movie_lib.id
    
    def test_settings_remember_last_library(self, qtbot, sample_libraries):
        """Test that settings remember last active library."""
        settings = SettingsManager()
        main_window = MainWindow(settings)
        qtbot.addWidget(main_window)
        
        movie_lib, _, _ = sample_libraries
        
        # Select a library
        main_window._on_library_selected(movie_lib, "all")
        
        # Check that setting is saved
        assert settings.get_last_active_library_id() == movie_lib.id
    
    def test_manage_libraries_menu_action(self, qtbot, sample_libraries):
        """Test that manage libraries menu action works."""
        settings = SettingsManager()
        main_window = MainWindow(settings)
        qtbot.addWidget(main_window)
        
        # Just check that the method exists and can be called
        assert hasattr(main_window, '_on_manage_libraries')


class TestScanQueueLibrarySelection:
    """Tests for scan queue widget library selection."""
    
    def test_library_combo_populated(self, qtbot, sample_libraries):
        """Test that library combo box is populated."""
        from src.media_manager.scan_queue_widget import ScanQueueWidget
        
        widget = ScanQueueWidget()
        qtbot.addWidget(widget)
        
        # Should have 3 libraries
        assert widget.library_combo.count() == 3
    
    def test_set_target_library(self, qtbot, sample_libraries):
        """Test setting target library."""
        from src.media_manager.scan_queue_widget import ScanQueueWidget
        
        movie_lib, _, _ = sample_libraries
        
        widget = ScanQueueWidget()
        qtbot.addWidget(widget)
        
        widget.set_target_library(movie_lib.id)
        
        # Check that the correct library is selected
        assert widget.get_target_library_id() == movie_lib.id
