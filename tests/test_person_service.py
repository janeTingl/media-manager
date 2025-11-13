"""Tests for PersonService."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.media_manager.person_service import PersonService, PersonDetails, FilmographyEntry
from src.media_manager.persistence.models import Person, Credit, MediaItem, Artwork, Library


@pytest.fixture
def mock_db_service(monkeypatch):
    """Mock database service."""
    mock_service = Mock()
    mock_session = Mock()
    mock_service.get_session.return_value.__enter__.return_value = mock_session
    mock_service.get_session.return_value.__exit__ = Mock(return_value=False)
    
    with patch("src.media_manager.person_service.get_database_service", return_value=mock_service):
        yield mock_service, mock_session


@pytest.fixture
def sample_person():
    """Create a sample person entity."""
    person = Person(
        id=1,
        name="Brad Pitt",
        external_id="287",
        biography="William Bradley Pitt is an American actor and film producer.",
        birthday="1963-12-18",
        image_url="https://image.tmdb.org/t/p/w342/profile.jpg",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    return person


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
        rating=8.8
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
    
    item2 = MediaItem(
        id=2,
        library_id=1,
        title="Troy",
        media_type="movie",
        year=2004,
        rating=7.2
    )
    item2.library = library
    item2.artworks = []
    
    return [item1, item2]


@pytest.fixture
def sample_credits(sample_person, sample_media_items):
    """Create sample credits linking person to media items."""
    credits = []
    
    credit1 = Credit(
        id=1,
        media_item_id=1,
        person_id=1,
        role="actor",
        character_name="Tyler Durden",
        order=0
    )
    credit1.person = sample_person
    credit1.media_item = sample_media_items[0]
    credits.append(credit1)
    
    credit2 = Credit(
        id=2,
        media_item_id=2,
        person_id=1,
        role="actor",
        character_name="Achilles",
        order=0
    )
    credit2.person = sample_person
    credit2.media_item = sample_media_items[1]
    credits.append(credit2)
    
    return credits


class TestPersonService:
    """Tests for PersonService."""
    
    def test_initialization(self, mock_db_service):
        """Test service initialization."""
        service = PersonService()
        
        assert service._db_service is not None
        assert service.CACHE_DIR.exists()
    
    def test_get_person_by_id_found(self, mock_db_service, sample_person, sample_credits):
        """Test getting person by ID when found."""
        mock_service, mock_session = mock_db_service
        
        # Setup mock to return person with credits
        sample_person.credits = sample_credits
        mock_session.exec.return_value.first.return_value = sample_person
        
        service = PersonService()
        result = service.get_person_by_id(1)
        
        assert result is not None
        assert isinstance(result, PersonDetails)
        assert result.id == 1
        assert result.name == "Brad Pitt"
        assert result.biography == sample_person.biography
        assert len(result.filmography) == 2
    
    def test_get_person_by_id_not_found(self, mock_db_service):
        """Test getting person by ID when not found."""
        mock_service, mock_session = mock_db_service
        mock_session.exec.return_value.first.return_value = None
        
        service = PersonService()
        result = service.get_person_by_id(999)
        
        assert result is None
    
    def test_get_person_by_name(self, mock_db_service, sample_person, sample_credits):
        """Test getting person by name."""
        mock_service, mock_session = mock_db_service
        
        sample_person.credits = sample_credits
        mock_session.exec.return_value.first.return_value = sample_person
        
        service = PersonService()
        result = service.get_person_by_name("Brad Pitt")
        
        assert result is not None
        assert result.name == "Brad Pitt"
    
    def test_search_person(self, mock_db_service, sample_person, sample_credits):
        """Test searching for persons."""
        mock_service, mock_session = mock_db_service
        
        sample_person.credits = sample_credits
        mock_session.exec.return_value.all.return_value = [sample_person]
        
        service = PersonService()
        results = service.search_person("Brad")
        
        assert len(results) == 1
        assert results[0].name == "Brad Pitt"
    
    def test_build_person_details_with_filmography(self, sample_person, sample_credits):
        """Test building person details with filmography."""
        sample_person.credits = sample_credits
        
        service = PersonService()
        details = service._build_person_details(sample_person)
        
        assert details.id == 1
        assert details.name == "Brad Pitt"
        assert len(details.filmography) == 2
        
        # Check first entry (Troy, more recent)
        assert details.filmography[0].media_item_title == "Troy"
        assert details.filmography[0].year == 2004
        assert details.filmography[0].character_name == "Achilles"
        assert details.filmography[0].role == "actor"
        
        # Check second entry (Fight Club)
        assert details.filmography[1].media_item_title == "Fight Club"
        assert details.filmography[1].year == 1999
        assert details.filmography[1].poster_url == "https://image.tmdb.org/t/p/w342/poster1.jpg"
    
    def test_needs_refresh_stale_data(self, sample_person):
        """Test needs_refresh with stale data."""
        sample_person.updated_at = datetime.utcnow() - timedelta(days=35)
        
        service = PersonService()
        needs_refresh = service._needs_refresh(sample_person)
        
        assert needs_refresh is True
    
    def test_needs_refresh_fresh_data(self, sample_person):
        """Test needs_refresh with fresh data."""
        sample_person.updated_at = datetime.utcnow() - timedelta(days=5)
        
        service = PersonService()
        needs_refresh = service._needs_refresh(sample_person)
        
        assert needs_refresh is False
    
    def test_needs_refresh_missing_biography(self, sample_person):
        """Test needs_refresh with missing biography."""
        sample_person.biography = None
        sample_person.external_id = "287"
        
        service = PersonService()
        needs_refresh = service._needs_refresh(sample_person)
        
        assert needs_refresh is True
    
    @patch("src.media_manager.person_service.requests.get")
    def test_download_headshot_success(self, mock_get, mock_db_service, sample_person, tmp_path):
        """Test successful headshot download."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_person
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = b"fake image data"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        service = PersonService()
        service.CACHE_DIR = tmp_path
        
        result_path = service.download_headshot(1)
        
        assert result_path is not None
        assert result_path.exists()
        assert result_path.read_bytes() == b"fake image data"
    
    def test_download_headshot_no_url(self, mock_db_service, sample_person):
        """Test headshot download with no image URL."""
        mock_service, mock_session = mock_db_service
        sample_person.image_url = None
        mock_session.get.return_value = sample_person
        
        service = PersonService()
        result = service.download_headshot(1)
        
        assert result is None
    
    def test_get_headshot_path_exists(self, mock_db_service, sample_person, tmp_path):
        """Test getting headshot path when it exists."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_person
        
        service = PersonService()
        service.CACHE_DIR = tmp_path
        
        # Create fake cached file
        import hashlib
        url_hash = hashlib.md5(sample_person.image_url.encode()).hexdigest()
        cache_file = tmp_path / f"{url_hash}.jpg"
        cache_file.write_bytes(b"fake image")
        
        result = service.get_headshot_path(1)
        
        assert result is not None
        assert result.exists()
    
    def test_get_headshot_path_not_exists(self, mock_db_service, sample_person):
        """Test getting headshot path when it doesn't exist."""
        mock_service, mock_session = mock_db_service
        mock_session.get.return_value = sample_person
        
        service = PersonService()
        result = service.get_headshot_path(1)
        
        assert result is None
    
    def test_cache_operations(self, tmp_path):
        """Test cache save and load operations."""
        service = PersonService()
        service.CACHE_DIR = tmp_path
        
        test_data = {"name": "Brad Pitt", "id": 287}
        cache_key = "person_287"
        
        # Save to cache
        service._save_to_cache(cache_key, test_data)
        
        # Load from cache
        loaded_data = service._load_from_cache(cache_key)
        
        assert loaded_data == test_data
    
    def test_cache_expiration(self, tmp_path):
        """Test cache expiration with stale data."""
        service = PersonService()
        service.CACHE_DIR = tmp_path
        
        # Create cache file with old timestamp
        import json
        import hashlib
        
        cache_key = "person_test"
        cache_data = {
            "_cached_at": (datetime.utcnow() - timedelta(days=35)).isoformat(),
            "data": {"name": "Test"}
        }
        
        cache_path = tmp_path / f"{hashlib.md5(cache_key.encode()).hexdigest()}.json"
        with open(cache_path, "w") as f:
            json.dump(cache_data, f)
        
        # Should return None for stale data
        result = service._load_from_cache(cache_key)
        assert result is None


class TestFilmographyEntry:
    """Tests for FilmographyEntry dataclass."""
    
    def test_creation(self):
        """Test creating a filmography entry."""
        entry = FilmographyEntry(
            media_item_id=1,
            media_item_title="Fight Club",
            media_type="movie",
            year=1999,
            role="actor",
            character_name="Tyler Durden",
            rating=8.8
        )
        
        assert entry.media_item_id == 1
        assert entry.media_item_title == "Fight Club"
        assert entry.year == 1999
        assert entry.character_name == "Tyler Durden"


class TestPersonDetails:
    """Tests for PersonDetails dataclass."""
    
    def test_creation(self):
        """Test creating person details."""
        details = PersonDetails(
            id=1,
            name="Brad Pitt",
            biography="Test bio",
            birthday="1963-12-18"
        )
        
        assert details.id == 1
        assert details.name == "Brad Pitt"
        assert details.filmography == []
    
    def test_with_filmography(self):
        """Test person details with filmography."""
        entry = FilmographyEntry(
            media_item_id=1,
            media_item_title="Fight Club",
            media_type="movie",
            year=1999,
            role="actor"
        )
        
        details = PersonDetails(
            id=1,
            name="Brad Pitt",
            filmography=[entry]
        )
        
        assert len(details.filmography) == 1
        assert details.filmography[0].media_item_title == "Fight Club"
