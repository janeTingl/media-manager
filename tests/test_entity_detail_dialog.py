"""Tests for EntityDetailDialog."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.media_manager.entity_detail_dialog import EntityDetailDialog
from src.media_manager.person_service import PersonDetails, FilmographyEntry
from src.media_manager.company_service import CompanyDetails, CompanyProduction


@pytest.fixture
def sample_person_details():
    """Create sample person details."""
    filmography = [
        FilmographyEntry(
            media_item_id=1,
            media_item_title="Fight Club",
            media_type="movie",
            year=1999,
            role="actor",
            character_name="Tyler Durden",
            rating=8.8,
            poster_url="https://example.com/poster1.jpg"
        ),
        FilmographyEntry(
            media_item_id=2,
            media_item_title="Troy",
            media_type="movie",
            year=2004,
            role="actor",
            character_name="Achilles",
            rating=7.2
        )
    ]
    
    return PersonDetails(
        id=1,
        name="Brad Pitt",
        biography="William Bradley Pitt is an American actor and film producer.",
        birthday="1963-12-18",
        image_url="https://image.tmdb.org/t/p/w342/profile.jpg",
        external_id="287",
        place_of_birth="Shawnee, Oklahoma, USA",
        known_for_department="Acting",
        filmography=filmography
    )


@pytest.fixture
def sample_company_details():
    """Create sample company details."""
    productions = [
        CompanyProduction(
            media_item_id=1,
            media_item_title="Fight Club",
            media_type="movie",
            year=1999,
            rating=8.8,
            poster_url="https://example.com/poster1.jpg"
        ),
        CompanyProduction(
            media_item_id=2,
            media_item_title="Slumdog Millionaire",
            media_type="movie",
            year=2008,
            rating=8.0
        )
    ]
    
    return CompanyDetails(
        id=1,
        name="Fox Searchlight Pictures",
        description="American film distribution company.",
        headquarters="Los Angeles, California",
        homepage="https://www.foxsearchlight.com",
        logo_url="https://image.tmdb.org/t/p/w154/logo.png",
        external_id="43",
        productions=productions
    )


class TestEntityDetailDialog:
    """Tests for EntityDetailDialog."""
    
    def test_initialization(self, qtbot):
        """Test dialog initialization."""
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Entity Details"
        assert dialog._person_service is not None
        assert dialog._company_service is not None
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_show_person(self, mock_person_service_class, qtbot, sample_person_details):
        """Test showing person details."""
        # Setup mock service
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = sample_person_details
        mock_service.get_headshot_path.return_value = None
        mock_service.download_headshot.return_value = None
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Verify window title
        assert "Brad Pitt" in dialog.windowTitle()
        
        # Verify name label
        assert dialog._name_label.text() == "Brad Pitt"
        
        # Verify info label contains birthday
        assert "1963-12-18" in dialog._info_label.text()
        
        # Verify biography
        assert "William Bradley Pitt" in dialog._biography_text.toPlainText()
        
        # Verify filmography table
        assert dialog._credits_table.rowCount() == 2
        assert dialog._credits_table.item(0, 0).text() == "Fight Club"
        assert dialog._credits_table.item(1, 0).text() == "Troy"
    
    @patch("src.media_manager.entity_detail_dialog.CompanyService")
    def test_show_company(self, mock_company_service_class, qtbot, sample_company_details):
        """Test showing company details."""
        # Setup mock service
        mock_service = Mock()
        mock_service.get_company_by_id.return_value = sample_company_details
        mock_service.get_logo_path.return_value = None
        mock_service.download_logo.return_value = None
        mock_company_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_company(1)
        
        # Verify window title
        assert "Fox Searchlight Pictures" in dialog.windowTitle()
        
        # Verify name label
        assert dialog._name_label.text() == "Fox Searchlight Pictures"
        
        # Verify info label contains headquarters
        assert "Los Angeles" in dialog._info_label.text()
        
        # Verify description
        assert "American film distribution" in dialog._biography_text.toPlainText()
        
        # Verify productions table
        assert dialog._credits_table.rowCount() == 2
        assert dialog._credits_table.item(0, 0).text() == "Fight Club"
        assert dialog._credits_table.item(1, 0).text() == "Slumdog Millionaire"
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_filmography_table_with_ratings(self, mock_person_service_class, qtbot, sample_person_details):
        """Test filmography table displays ratings correctly."""
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = sample_person_details
        mock_service.get_headshot_path.return_value = None
        mock_service.download_headshot.return_value = None
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Check first row rating
        rating_item = dialog._credits_table.item(0, 4)
        assert rating_item is not None
        assert "8.8" in rating_item.text()
        assert "★" in rating_item.text()
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_credit_double_click_emits_signal(self, mock_person_service_class, qtbot, sample_person_details):
        """Test double-clicking a credit emits media_item_selected signal."""
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = sample_person_details
        mock_service.get_headshot_path.return_value = None
        mock_service.download_headshot.return_value = None
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Setup signal spy
        with qtbot.waitSignal(dialog.media_item_selected, timeout=1000) as blocker:
            # Select first row
            dialog._credits_table.selectRow(0)
            # Double-click
            dialog._on_credit_double_clicked()
        
        # Verify signal was emitted with correct media_item_id
        assert blocker.args[0] == 1
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_load_headshot_cached(self, mock_person_service_class, qtbot, sample_person_details, tmp_path):
        """Test loading cached headshot."""
        # Create a fake cached image
        cached_image = tmp_path / "headshot.jpg"
        cached_image.write_bytes(b"fake image data")
        
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = sample_person_details
        mock_service.get_headshot_path.return_value = cached_image
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Verify headshot was loaded (download should not be called)
        mock_service.get_headshot_path.assert_called_once_with(1)
        mock_service.download_headshot.assert_not_called()
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_load_headshot_download(self, mock_person_service_class, qtbot, sample_person_details, tmp_path):
        """Test downloading headshot when not cached."""
        # Create a fake downloaded image
        downloaded_image = tmp_path / "headshot.jpg"
        downloaded_image.write_bytes(b"fake image data")
        
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = sample_person_details
        mock_service.get_headshot_path.return_value = None
        mock_service.download_headshot.return_value = downloaded_image
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Verify download was attempted
        mock_service.download_headshot.assert_called_once_with(1)
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_no_biography(self, mock_person_service_class, qtbot):
        """Test displaying person with no biography."""
        person_no_bio = PersonDetails(
            id=1,
            name="Test Person",
            biography=None
        )
        
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = person_no_bio
        mock_service.get_headshot_path.return_value = None
        mock_service.download_headshot.return_value = None
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Verify default text is shown
        assert "No biography available" in dialog._biography_text.toPlainText()
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    def test_empty_filmography(self, mock_person_service_class, qtbot):
        """Test displaying person with empty filmography."""
        person_no_films = PersonDetails(
            id=1,
            name="Test Person",
            filmography=[]
        )
        
        mock_service = Mock()
        mock_service.get_person_by_id.return_value = person_no_films
        mock_service.get_headshot_path.return_value = None
        mock_service.download_headshot.return_value = None
        mock_person_service_class.return_value = mock_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        dialog.show_person(1)
        
        # Verify table is empty
        assert dialog._credits_table.rowCount() == 0
    
    def test_close_button(self, qtbot):
        """Test close button functionality."""
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        # Setup signal spy for accepted signal
        with qtbot.waitSignal(dialog.accepted, timeout=1000):
            dialog._close_button.click()


class TestEntityDetailDialogIntegration:
    """Integration tests for EntityDetailDialog."""
    
    @patch("src.media_manager.entity_detail_dialog.PersonService")
    @patch("src.media_manager.entity_detail_dialog.CompanyService")
    def test_switch_between_person_and_company(
        self, mock_company_service_class, mock_person_service_class, qtbot,
        sample_person_details, sample_company_details
    ):
        """Test switching between person and company views."""
        # Setup mock services
        mock_person_service = Mock()
        mock_person_service.get_person_by_id.return_value = sample_person_details
        mock_person_service.get_headshot_path.return_value = None
        mock_person_service.download_headshot.return_value = None
        mock_person_service_class.return_value = mock_person_service
        
        mock_company_service = Mock()
        mock_company_service.get_company_by_id.return_value = sample_company_details
        mock_company_service.get_logo_path.return_value = None
        mock_company_service.download_logo.return_value = None
        mock_company_service_class.return_value = mock_company_service
        
        dialog = EntityDetailDialog()
        qtbot.addWidget(dialog)
        
        # Show person first
        dialog.show_person(1)
        assert "Brad Pitt" in dialog.windowTitle()
        assert dialog._credits_table.columnCount() == 5  # Person has 5 columns
        
        # Switch to company
        dialog.show_company(1)
        assert "Fox Searchlight Pictures" in dialog.windowTitle()
        assert dialog._credits_table.columnCount() == 4  # Company has 4 columns
