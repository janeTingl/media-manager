"""Unit tests for metadata editor widget and validator."""

import pytest
from datetime import datetime
from pathlib import Path

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from src.media_manager.metadata_editor_widget import MetadataEditorWidget
from src.media_manager.metadata_validator import MetadataValidator
from src.media_manager.persistence.models import MediaItem, Library
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool


@pytest.fixture
def in_memory_db() -> tuple:
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
def media_library(in_memory_db):
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
def media_item(media_library, in_memory_db):
    """Create a test media item."""
    db_service, session = in_memory_db
    item = MediaItem(
        library_id=media_library.id,
        title="Test Movie",
        media_type="movie",
        year=2020,
        runtime=120,
        description="A test movie description",
        rating=7.5,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


class TestMetadataValidator:
    """Test cases for MetadataValidator."""

    def test_validate_valid_movie(self) -> None:
        """Test validation of valid movie metadata."""
        validator = MetadataValidator()
        data = {
            "title": "Test Movie",
            "year": 2020,
            "runtime": 120,
            "rating": 7.5,
        }
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_title(self) -> None:
        """Test validation fails when title is missing."""
        validator = MetadataValidator()
        data = {
            "year": 2020,
            "runtime": 120,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("Title" in err for err in errors)

    def test_validate_empty_title(self) -> None:
        """Test validation fails when title is empty."""
        validator = MetadataValidator()
        data = {
            "title": "   ",
            "year": 2020,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_title_too_long(self) -> None:
        """Test validation fails when title is too long."""
        validator = MetadataValidator()
        data = {
            "title": "x" * 300,
            "year": 2020,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("exceed" in err for err in errors)

    def test_validate_invalid_year(self) -> None:
        """Test validation fails with invalid year."""
        validator = MetadataValidator()
        
        # Too old
        data = {"title": "Test", "year": 1700}
        is_valid, errors = validator.validate(data)
        assert not is_valid
        
        # Too new
        data = {"title": "Test", "year": 2200}
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_runtime(self) -> None:
        """Test validation fails with invalid runtime."""
        validator = MetadataValidator()
        
        # Negative runtime
        data = {"title": "Test", "year": 2020, "runtime": -10}
        is_valid, errors = validator.validate(data)
        assert not is_valid
        
        # Too large runtime
        data = {"title": "Test", "year": 2020, "runtime": 2000}
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_season(self) -> None:
        """Test validation fails with invalid season."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "season": 150,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_episode(self) -> None:
        """Test validation fails with invalid episode."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "episode": 2000,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_aired_date(self) -> None:
        """Test validation fails with invalid aired date."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "aired_date": "2020/01/01",  # Wrong format
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_valid_aired_date(self) -> None:
        """Test validation passes with valid aired date."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "aired_date": "2020-01-15",
        }
        is_valid, errors = validator.validate(data)
        assert is_valid

    def test_validate_invalid_rating(self) -> None:
        """Test validation fails with invalid rating."""
        validator = MetadataValidator()
        
        # Negative rating
        data = {"title": "Test", "year": 2020, "rating": -5}
        is_valid, errors = validator.validate(data)
        assert not is_valid
        
        # Too high rating
        data = {"title": "Test", "year": 2020, "rating": 150}
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_title_single(self) -> None:
        """Test single title validation."""
        validator = MetadataValidator()
        
        # Valid
        assert validator.validate_title("Test Movie") is None
        
        # Empty
        assert validator.validate_title("") is not None
        
        # Too long
        assert validator.validate_title("x" * 300) is not None

    def test_validate_year_single(self) -> None:
        """Test single year validation."""
        validator = MetadataValidator()
        
        # Valid
        assert validator.validate_year(2020) is None
        
        # Invalid
        assert validator.validate_year(1700) is not None
        assert validator.validate_year(2200) is not None

    def test_validate_runtime_single(self) -> None:
        """Test single runtime validation."""
        validator = MetadataValidator()
        
        # Valid
        assert validator.validate_runtime(120) is None
        assert validator.validate_runtime(0) is None
        
        # Invalid
        assert validator.validate_runtime(-10) is not None
        assert validator.validate_runtime(2000) is not None

    def test_validate_date_single(self) -> None:
        """Test single date validation."""
        validator = MetadataValidator()
        
        # Valid
        assert validator.validate_date("2020-01-15") is None
        assert validator.validate_date("") is None  # Empty is OK
        
        # Invalid
        assert validator.validate_date("2020/01/15") is not None
        assert validator.validate_date("01-15-2020") is not None


class TestMetadataEditorWidget:
    """Test cases for MetadataEditorWidget."""

    def test_widget_initialization(self, qapp) -> None:
        """Test widget initializes correctly."""
        widget = MetadataEditorWidget()
        assert widget is not None
        assert widget.title_label.text() == "No media selected"
        assert widget._current_media_item is None
        assert not widget._is_dirty

    def test_set_media_item_none(self, qapp) -> None:
        """Test setting media item to None."""
        widget = MetadataEditorWidget()
        widget.set_media_item(None)
        
        assert widget._current_media_item is None
        assert widget.title_label.text() == "No media selected"
        assert not widget.save_button.isEnabled()

    def test_set_media_item(self, qapp, media_item) -> None:
        """Test setting a media item."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        assert widget._current_media_item == media_item
        assert "Test Movie" in widget.title_label.text()
        assert widget.title_input.text() == "Test Movie"
        assert widget.year_input.value() == 2020
        assert widget.runtime_input.value() == 120

    def test_field_change_sets_dirty_flag(self, qapp, media_item) -> None:
        """Test that changing fields sets dirty flag."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        assert not widget._is_dirty
        assert not widget.save_button.isEnabled()
        
        widget.title_input.setText("Modified Movie")
        
        assert widget._is_dirty
        assert widget.save_button.isEnabled()

    def test_reset_button_clears_changes(self, qapp, media_item) -> None:
        """Test reset button clears changes."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        original_title = widget.title_input.text()
        widget.title_input.setText("Modified")
        assert widget._is_dirty
        
        widget._on_reset_clicked()
        
        assert widget.title_input.text() == original_title
        assert not widget._is_dirty

    def test_validate_form_empty_title(self, qapp, media_item) -> None:
        """Test form validation with empty title."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        widget.title_input.clear()
        
        assert not widget._validate_form()

    def test_validate_form_valid(self, qapp, media_item) -> None:
        """Test form validation with valid data."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        assert widget._validate_form()

    def test_match_updated_signal_emitted(self, qapp, media_item) -> None:
        """Test that match_updated signal is emitted on save."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        signal_spy = QSignalSpy(widget.match_updated)
        
        widget.title_input.setText("Modified Movie")
        widget._on_save_clicked()
        
        assert len(signal_spy) >= 1

    def test_save_button_disabled_when_not_dirty(self, qapp, media_item) -> None:
        """Test save button is disabled when no changes made."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        assert not widget.save_button.isEnabled()

    def test_save_button_enabled_when_dirty(self, qapp, media_item) -> None:
        """Test save button is enabled when changes made."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        widget.title_input.setText("Modified")
        
        assert widget.save_button.isEnabled()

    def test_add_cast_row(self, qapp, media_item) -> None:
        """Test adding a cast member row."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        initial_count = widget.cast_table.rowCount()
        widget._add_cast_row("Test Actor", "Test Character", None)
        
        assert widget.cast_table.rowCount() == initial_count + 1
        assert widget.cast_table.item(initial_count, 0).text() == "Test Actor"
        assert widget.cast_table.item(initial_count, 1).text() == "Test Character"

    def test_add_crew_row(self, qapp, media_item) -> None:
        """Test adding a crew member row."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        initial_count = widget.crew_table.rowCount()
        widget._add_crew_row("Test Director", "director", None)
        
        assert widget.crew_table.rowCount() == initial_count + 1
        assert widget.crew_table.item(initial_count, 0).text() == "Test Director"
        assert widget.crew_table.item(initial_count, 1).text() == "director"

    def test_add_collection_row(self, qapp, media_item) -> None:
        """Test adding a collection row."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        initial_count = widget.collections_table.rowCount()
        widget._add_collection_row("Test Collection", None)
        
        assert widget.collections_table.rowCount() == initial_count + 1
        assert widget.collections_table.item(initial_count, 0).text() == "Test Collection"

    def test_update_media_item_from_form(self, qapp, media_item) -> None:
        """Test updating media item from form values."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        widget.title_input.setText("Modified Title")
        widget.year_input.setValue(2021)
        widget.runtime_input.setValue(150)
        widget.plot_input.setPlainText("Modified plot")
        widget.rating_input.setValue(8)
        
        widget._update_media_item_from_form()
        
        assert widget._current_media_item.title == "Modified Title"
        assert widget._current_media_item.year == 2021
        assert widget._current_media_item.runtime == 150
        assert widget._current_media_item.description == "Modified plot"
        assert widget._current_media_item.rating == 8.0

    def test_is_valid_date(self, qapp) -> None:
        """Test date validation."""
        widget = MetadataEditorWidget()
        
        assert widget._is_valid_date("2020-01-15")
        assert widget._is_valid_date("1999-12-31")
        assert not widget._is_valid_date("2020/01/15")
        assert not widget._is_valid_date("01-15-2020")
        assert not widget._is_valid_date("invalid")

    def test_load_media_item_episodic(self, qapp, in_memory_db) -> None:
        """Test loading episodic media item."""
        db_service, session = in_memory_db
        
        library = Library(
            name="Test Library",
            path="/test/library",
            media_type="tv",
        )
        session.add(library)
        session.commit()
        
        item = MediaItem(
            library_id=library.id,
            title="Test Episode",
            media_type="tv",
            year=2020,
            season=2,
            episode=3,
            aired_date="2020-05-15",
            runtime=45,
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        
        widget = MetadataEditorWidget()
        widget.set_media_item(item)
        
        assert widget.season_input.value() == 2
        assert widget.episode_input.value() == 3
        assert widget.aired_input.text() == "2020-05-15"
        assert widget.runtime_input.value() == 45

    def test_controls_disabled_when_no_item(self, qapp) -> None:
        """Test controls are disabled when no item selected."""
        widget = MetadataEditorWidget()
        widget.set_media_item(None)
        
        assert not widget.title_input.isEnabled()
        assert not widget.save_button.isEnabled()
        assert not widget.open_tmdb_button.isEnabled()

    def test_controls_enabled_when_item_selected(self, qapp, media_item) -> None:
        """Test controls are enabled when item selected."""
        widget = MetadataEditorWidget()
        widget.set_media_item(media_item)
        
        assert widget.title_input.isEnabled()
        assert widget.open_tmdb_button.isEnabled()
