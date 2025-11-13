"""Tests for CompanyService."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.media_manager.company_service import CompanyService, CompanyDetails, CompanyProduction
from src.media_manager.persistence.models import Company, MediaItem, Artwork, Library


@pytest.fixture
def mock_db_service(monkeypatch):
    """Mock database service."""
    mock_service = Mock()
    mock_session = Mock()
    mock_service.get_session.return_value.__enter__.return_value = mock_session
    mock_service.get_session.return_value.__exit__ = Mock(return_value=False)
    
    with patch("src.media_manager.company_service.get_database_service", return_value=mock_service):
        yield mock_service, mock_session


@pytest.fixture
def sample_company():
    """Create a sample company entity."""
    company = Company(
        id=1,
        name="Fox Searchlight Pictures",
        external_id="43",
        logo_url="https://image.tmdb.org/t/p/w154/logo.png",
        created_at=datetime.utcnow()
    )
    return company


@pytest.fixture
def sample_media_items():
    """Create sample media items."""
    library = Library(id=1, name="Test", path="/test", media_type="movie")
    
    item1 = MediaItem(
        id=1,
        library_id=1,
        title="Fight Club",
        media_type="movie",
        year=1999,
        rating=8.8,
        description="Produced by Fox Searchlight Pictures"
    )
    item1.library = library
    item1.artworks = [
        Artwork(
            id=1,
            media_item_id=1,
            artwork_type="poster",
            url="https://image.tmdb.org/t/p/w342/poster1.jpg",
            size="medium",
            download_status="completed"
        )
    ]
    
    return [item1]


class TestCompanyService:
    """Tests for CompanyService."""
    
    def test_initialization(self, mock_db_service):
        """Test service initialization."""
        service = CompanyService()
        
        assert service._db_service is not None
        assert service.CACHE_DIR.exists()
    
    def test_get_company_by_id_found(self, mock_db_service, sample_company, sample_media_items):
        """Test getting company by ID when found."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_company
        mock_session.exec.return_value.all.return_value = sample_media_items
        
        service = CompanyService()
        result = service.get_company_by_id(1)
        
        assert result is not None
        assert isinstance(result, CompanyDetails)
        assert result.id == 1
        assert result.name == "Fox Searchlight Pictures"
    
    def test_get_company_by_id_not_found(self, mock_db_service):
        """Test getting company by ID when not found."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = None
        
        service = CompanyService()
        result = service.get_company_by_id(999)
        
        assert result is None
    
    def test_get_company_by_name(self, mock_db_service, sample_company, sample_media_items):
        """Test getting company by name."""
        mock_service, mock_session = mock_db_service
        mock_session.exec.return_value.first.return_value = sample_company
        mock_session.exec.return_value.all.return_value = sample_media_items
        
        service = CompanyService()
        result = service.get_company_by_name("Fox Searchlight Pictures")
        
        assert result is not None
        assert result.name == "Fox Searchlight Pictures"
    
    def test_search_company(self, mock_db_service, sample_company, sample_media_items):
        """Test searching for companies."""
        mock_service, mock_session = mock_db_service
        
        # First exec for search query
        mock_search_result = Mock()
        mock_search_result.all.return_value = [sample_company]
        
        # Second exec for productions query
        mock_productions_result = Mock()
        mock_productions_result.all.return_value = sample_media_items
        
        mock_session.exec.side_effect = [mock_search_result, mock_productions_result]
        
        service = CompanyService()
        results = service.search_company("Fox")
        
        assert len(results) == 1
        assert results[0].name == "Fox Searchlight Pictures"
    
    def test_build_company_details_with_productions(self, mock_db_service, sample_company, sample_media_items):
        """Test building company details with productions."""
        mock_service, mock_session = mock_db_service
        mock_session.exec.return_value.all.return_value = sample_media_items
        
        service = CompanyService()
        details = service._build_company_details(sample_company, mock_session)
        
        assert details.id == 1
        assert details.name == "Fox Searchlight Pictures"
        assert len(details.productions) == 1
        
        # Check production entry
        assert details.productions[0].media_item_title == "Fight Club"
        assert details.productions[0].year == 1999
        assert details.productions[0].poster_url == "https://image.tmdb.org/t/p/w342/poster1.jpg"
    
    def test_needs_refresh_stale_data(self, sample_company):
        """Test needs_refresh with stale data."""
        sample_company.created_at = datetime.utcnow() - timedelta(days=35)
        
        service = CompanyService()
        needs_refresh = service._needs_refresh(sample_company)
        
        assert needs_refresh is True
    
    def test_needs_refresh_fresh_data(self, sample_company):
        """Test needs_refresh with fresh data."""
        sample_company.created_at = datetime.utcnow() - timedelta(days=5)
        
        service = CompanyService()
        needs_refresh = service._needs_refresh(sample_company)
        
        assert needs_refresh is False
    
    @patch("src.media_manager.company_service.requests.get")
    def test_download_logo_success(self, mock_get, mock_db_service, sample_company, tmp_path):
        """Test successful logo download."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_company
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = b"fake logo data"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = CompanyService()
        service.CACHE_DIR = tmp_path
        
        result_path = service.download_logo(1)
        
        assert result_path is not None
        assert result_path.exists()
        assert result_path.read_bytes() == b"fake logo data"
    
    def test_download_logo_no_url(self, mock_db_service, sample_company):
        """Test logo download with no logo URL."""
        mock_service, mock_session = mock_db_service
        sample_company.logo_url = None
        mock_session.get.return_value = sample_company
        
        service = CompanyService()
        result = service.download_logo(1)
        
        assert result is None
    
    def test_get_logo_path_exists(self, mock_db_service, sample_company, tmp_path):
        """Test getting logo path when it exists."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_company
        
        service = CompanyService()
        service.CACHE_DIR = tmp_path
        
        # Create fake cached file
        import hashlib
        url_hash = hashlib.md5(sample_company.logo_url.encode()).hexdigest()
        cache_file = tmp_path / f"{url_hash}.png"
        cache_file.write_bytes(b"fake logo")
        
        result = service.get_logo_path(1)
        
        assert result is not None
        assert result.exists()
    
    def test_get_logo_path_not_exists(self, mock_db_service, sample_company):
        """Test getting logo path when it doesn't exist."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_company
        
        service = CompanyService()
        result = service.get_logo_path(1)
        
        assert result is None
    
    def test_cache_operations(self, tmp_path):
        """Test cache save and load operations."""
        service = CompanyService()
        service.CACHE_DIR = tmp_path
        
        test_data = {"name": "Fox Searchlight", "id": 43}
        cache_key = "company_43"
        
        # Save to cache
        service._save_to_cache(cache_key, test_data)
        
        # Load from cache
        loaded_data = service._load_from_cache(cache_key)
        
        assert loaded_data == test_data


class TestCompanyProduction:
    """Tests for CompanyProduction dataclass."""
    
    def test_creation(self):
        """Test creating a company production."""
        production = CompanyProduction(
            media_item_id=1,
            media_item_title="Fight Club",
            media_type="movie",
            year=1999,
            rating=8.8
        )
        
        assert production.media_item_id == 1
        assert production.media_item_title == "Fight Club"
        assert production.year == 1999


class TestCompanyDetails:
    """Tests for CompanyDetails dataclass."""
    
    def test_creation(self):
        """Test creating company details."""
        details = CompanyDetails(
            id=1,
            name="Fox Searchlight Pictures",
            logo_url="https://example.com/logo.png"
        )
        
        assert details.id == 1
        assert details.name == "Fox Searchlight Pictures"
        assert details.productions == []
    
    def test_with_productions(self):
        """Test company details with productions."""
        production = CompanyProduction(
            media_item_id=1,
            media_item_title="Fight Club",
            media_type="movie",
            year=1999
        )
        
        details = CompanyDetails(
            id=1,
            name="Fox Searchlight Pictures",
            productions=[production]
        )
        
        assert len(details.productions) == 1
        assert details.productions[0].media_item_title == "Fight Club"
