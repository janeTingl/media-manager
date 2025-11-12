"""Integration tests for metadata editor with database and signals."""

import pytest
from pathlib import Path

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from src.media_manager.metadata_editor_widget import MetadataEditorWidget
from src.media_manager.persistence.models import (
    MediaItem,
    Library,
    Credit,
    Person,
    Tag,
    Collection,
)
from src.media_manager.persistence.repositories import UnitOfWork, transactional_context
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    import media_manager.persistence.database as db_module
    from media_manager.persistence.database import DatabaseService
    
    db_service = DatabaseService("sqlite://", auto_migrate=False)
    db_service._engine = engine
    db_module._database_service = db_service
    
    session = Session(engine)
    yield db_service, session
    
    session.close()
    engine.dispose()
    db_module._database_service = None


@pytest.fixture
def test_library(in_memory_db):
    """Create a test library."""
    db_service, session = in_memory_db
    library = Library(
        name="Test Library",
        path="/test/library",
        media_type="movie",
    )
    session.add(library)
    session.commit()
    return library


@pytest.fixture
def test_movie(test_library, in_memory_db):
    """Create a test movie media item."""
    db_service, session = in_memory_db
    movie = MediaItem(
        library_id=test_library.id,
        title="The Matrix",
        media_type="movie",
        year=1999,
        runtime=136,
        description="A computer hacker learns from mysterious rebels.",
        rating=8.7,
    )
    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie


@pytest.fixture
def test_episode(test_library, in_memory_db):
    """Create a test TV episode media item."""
    db_service, session = in_memory_db
    library = Library(
        name="TV Library",
        path="/test/tv",
        media_type="tv",
    )
    session.add(library)
    session.commit()
    
    episode = MediaItem(
        library_id=library.id,
        title="Dark - Season 1 Episode 1",
        media_type="tv",
        year=2017,
        season=1,
        episode=1,
        aired_date="2017-12-01",
        runtime=56,
        description="A child goes missing and the town is turned upside down.",
        rating=9.0,
    )
    session.add(episode)
    session.commit()
    session.refresh(episode)
    return episode


class TestMetadataEditorIntegration:
    """Integration tests for metadata editor."""

    def test_edit_and_save_movie(self, qapp, test_movie, in_memory_db) -> None:
        """Test editing and saving a movie."""
        db_service, session = in_memory_db
        
        widget = MetadataEditorWidget()
        save_spy = QSignalSpy(widget.match_updated)
        
        widget.set_media_item(test_movie)
        
        # Modify fields
        widget.title_input.setText("The Matrix Reloaded")
        widget.year_input.setValue(2003)
        widget.runtime_input.setValue(138)
        widget.rating_input.setValue(72)
        
        # Save
        widget._on_save_clicked()
        
        # Verify signal was emitted
        assert len(save_spy) >= 1
        
        # Verify dirty flag cleared
        assert not widget._is_dirty

    def test_edit_and_save_episode(self, qapp, test_episode, in_memory_db) -> None:
        """Test editing and saving a TV episode."""
        db_service, session = in_memory_db
        
        widget = MetadataEditorWidget()
        widget.set_media_item(test_episode)
        
        # Modify episodic fields
        widget.season_input.setValue(1)
        widget.episode_input.setValue(2)
        widget.aired_input.setText("2017-12-08")
        widget.runtime_input.setValue(60)
        
        # Save
        widget._on_save_clicked()
        
        # Verify dirty flag cleared
        assert not widget._is_dirty

    def test_add_cast_and_save(self, qapp, test_movie, in_memory_db) -> None:
        """Test adding cast members and saving."""
        db_service, session = in_memory_db
        
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add cast members
        widget._add_cast_row("Keanu Reeves", "Thomas Anderson", None)
        widget._add_cast_row("Laurence Fishburne", "Morpheus", None)
        
        assert widget.cast_table.rowCount() == 2
        
        # Mark as dirty and save
        widget._is_dirty = True
        widget._on_save_clicked()

    def test_add_crew_and_save(self, qapp, test_movie, in_memory_db) -> None:
        """Test adding crew members and saving."""
        db_service, session = in_memory_db
        
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add crew members
        widget._add_crew_row("The Wachowskis", "director", None)
        widget._add_crew_row("David Mitchel", "writer", None)
        
        assert widget.crew_table.rowCount() == 2
        
        # Mark as dirty and save
        widget._is_dirty = True
        widget._on_save_clicked()

    def test_add_collections_and_save(self, qapp, test_movie, in_memory_db) -> None:
        """Test adding collections and saving."""
        db_service, session = in_memory_db
        
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add collections
        widget._add_collection_row("Sci-Fi Classics", None)
        widget._add_collection_row("90s Action", None)
        
        assert widget.collections_table.rowCount() == 2
        
        # Mark as dirty and save
        widget._is_dirty = True
        widget._on_save_clicked()

    def test_validation_error_prevents_save(self, qapp, test_movie) -> None:
        """Test that validation errors prevent saving."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        error_spy = QSignalSpy(widget.validation_error)
        
        # Clear title
        widget.title_input.clear()
        widget._is_dirty = True
        
        # Try to save
        widget._on_save_clicked()
        
        # Verify error signal was emitted
        assert len(error_spy) >= 1

    def test_reset_discards_changes(self, qapp, test_movie) -> None:
        """Test that reset discards changes."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        original_title = widget.title_input.text()
        original_year = widget.year_input.value()
        
        # Make changes
        widget.title_input.setText("Modified")
        widget.year_input.setValue(2000)
        assert widget._is_dirty
        
        # Reset
        widget._on_reset_clicked()
        
        # Verify changes were discarded
        assert widget.title_input.text() == original_title
        assert widget.year_input.value() == original_year
        assert not widget._is_dirty

    def test_field_changed_signal_flow(self, qapp, test_movie) -> None:
        """Test that field changes trigger dirty flag and signal flow."""
        widget = MetadataEditorWidget()
        save_spy = QSignalSpy(widget.match_updated)
        
        widget.set_media_item(test_movie)
        assert not widget._is_dirty
        
        # Change a field
        widget.title_input.setText("New Title")
        assert widget._is_dirty
        assert widget.save_button.isEnabled()
        
        # Save
        widget._on_save_clicked()
        
        # Verify signal emitted
        assert len(save_spy) >= 1

    def test_clear_media_item_disables_controls(self, qapp, test_movie) -> None:
        """Test that clearing media item disables controls."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        assert widget.title_input.isEnabled()
        
        # Clear
        widget.set_media_item(None)
        
        assert not widget.title_input.isEnabled()
        assert not widget.save_button.isEnabled()

    def test_switch_media_item_updates_form(self, qapp, test_movie, test_episode, in_memory_db) -> None:
        """Test switching between different media items."""
        widget = MetadataEditorWidget()
        
        # Load first item
        widget.set_media_item(test_movie)
        assert widget.title_input.text() == "The Matrix"
        assert widget.year_input.value() == 1999
        
        # Switch to second item
        widget.set_media_item(test_episode)
        assert widget.title_input.text() == "Dark - Season 1 Episode 1"
        assert widget.year_input.value() == 2017
        assert widget.season_input.value() == 1
        assert widget.episode_input.value() == 1

    def test_validate_all_required_fields(self, qapp, test_movie) -> None:
        """Test validation of all required fields."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Title is required
        widget.title_input.clear()
        assert not widget._validate_form()
        
        # Restore title
        widget.title_input.setText("Test Movie")
        assert widget._validate_form()

    def test_episodic_fields_validation(self, qapp, test_episode) -> None:
        """Test validation of episodic fields."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_episode)
        
        # Valid episodic data
        widget.season_input.setValue(2)
        widget.episode_input.setValue(5)
        assert widget._validate_form()
        
        # Invalid aired date format
        widget.aired_input.setText("2020/01/15")
        assert not widget._validate_form()
        
        # Valid aired date format
        widget.aired_input.setText("2020-01-15")
        assert widget._validate_form()

    def test_cast_table_operations(self, qapp, test_movie) -> None:
        """Test cast table add and remove operations."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add cast
        initial_count = widget.cast_table.rowCount()
        widget._add_cast_row("Actor 1", "Role 1", None)
        widget._add_cast_row("Actor 2", "Role 2", None)
        
        assert widget.cast_table.rowCount() == initial_count + 2
        
        # Verify data
        assert widget.cast_table.item(0, 0).text() == "Actor 1"
        assert widget.cast_table.item(0, 1).text() == "Role 1"
        assert widget.cast_table.item(1, 0).text() == "Actor 2"
        assert widget.cast_table.item(1, 1).text() == "Role 2"

    def test_crew_table_operations(self, qapp, test_movie) -> None:
        """Test crew table add and remove operations."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add crew
        initial_count = widget.crew_table.rowCount()
        widget._add_crew_row("Director 1", "director", None)
        widget._add_crew_row("Writer 1", "writer", None)
        
        assert widget.crew_table.rowCount() == initial_count + 2
        
        # Verify data
        assert widget.crew_table.item(0, 0).text() == "Director 1"
        assert widget.crew_table.item(0, 1).text() == "director"
        assert widget.crew_table.item(1, 0).text() == "Writer 1"
        assert widget.crew_table.item(1, 1).text() == "writer"

    def test_collections_table_operations(self, qapp, test_movie) -> None:
        """Test collections table add operations."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add collections
        initial_count = widget.collections_table.rowCount()
        widget._add_collection_row("Collection 1", None)
        widget._add_collection_row("Collection 2", None)
        
        assert widget.collections_table.rowCount() == initial_count + 2
        
        # Verify data
        assert widget.collections_table.item(0, 0).text() == "Collection 1"
        assert widget.collections_table.item(1, 0).text() == "Collection 2"

    def test_tags_input_operations(self, qapp, test_movie) -> None:
        """Test tags input field."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Add tags
        widget.tags_input.setText("action, sci-fi, classic")
        
        assert widget.tags_input.text() == "action, sci-fi, classic"
        assert widget._is_dirty

    def test_plot_description_editing(self, qapp, test_movie) -> None:
        """Test editing plot/description field."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        original_plot = widget.plot_input.toPlainText()
        
        new_plot = "Modified plot description"
        widget.plot_input.setPlainText(new_plot)
        
        assert widget.plot_input.toPlainText() == new_plot
        assert widget._is_dirty
        
        # Reset
        widget._on_reset_clicked()
        assert widget.plot_input.toPlainText() == original_plot

    def test_year_validation_boundary_values(self, qapp, test_movie) -> None:
        """Test year validation at boundary values."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Minimum valid year
        widget.year_input.setValue(1800)
        assert widget._validate_form()
        
        # Maximum valid year
        widget.year_input.setValue(2100)
        assert widget._validate_form()
        
        # Invalid: too early
        widget.year_input.setValue(1799)
        assert not widget._validate_form()
        
        # Invalid: too late
        widget.year_input.setValue(2101)
        assert not widget._validate_form()

    def test_runtime_validation_boundary_values(self, qapp, test_movie) -> None:
        """Test runtime validation at boundary values."""
        widget = MetadataEditorWidget()
        widget.set_media_item(test_movie)
        
        # Minimum valid runtime
        widget.runtime_input.setValue(0)
        assert widget._validate_form()
        
        # Maximum valid runtime
        widget.runtime_input.setValue(1000)
        assert widget._validate_form()
        
        # Invalid: negative
        widget.runtime_input.setValue(-1)
        assert not widget._validate_form()
        
        # Invalid: too high
        widget.runtime_input.setValue(1001)
        assert not widget._validate_form()
