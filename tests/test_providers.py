"""Tests for provider clients and fuzzy matching."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date
from pathlib import Path

from media_manager.models import Movie, TVShow, Season, Episode, MediaType, SearchResult
from media_manager.providers import (
    TMDBClient,
    TheTVDBClient,
    FuzzyMatcher,
    FilenameParser,
    MediaSearcher,
    ParsedFilename,
    APIError,
    AuthenticationError,
    RateLimitError,
)
from media_manager.settings import SettingsManager


@pytest.fixture
def mock_settings():
    """Mock settings manager."""
    settings = MagicMock(spec=SettingsManager)
    settings.get_tmdb_api_key.return_value = "test_tmdb_key"
    settings.get_thetvdb_api_key.return_value = "test_thetvdb_key"
    return settings


@pytest.fixture
def tmdb_client(mock_settings):
    """Create TMDB client for testing."""
    return TMDBClient(mock_settings)


@pytest.fixture
def thetvdb_client(mock_settings):
    """Create TheTVDB client for testing."""
    return TheTVDBClient(mock_settings)


class TestTMDBClient:
    """Test TMDB client functionality."""
    
    @pytest.mark.asyncio
    async def test_search_movie(self, tmdb_client):
        """Test movie search."""
        mock_response = {
            "results": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "original_title": "Fight Club",
                    "overview": "An insomniac office worker...",
                    "release_date": "1999-10-15",
                    "runtime": 139,
                    "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
                    "backdrop_path": "/fCayJrkfRaCRCTh8GqN30f8oyQF.jpg",
                    "vote_average": 8.4,
                    "vote_count": 26280,
                    "popularity": 61.416,
                    "imdb_id": "tt0137523",
                    "genres": [{"name": "Drama"}]
                }
            ]
        }
        
        with patch.object(tmdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            movies = await tmdb_client.search_movie("Fight Club", 1999)
            
            assert len(movies) == 1
            movie = movies[0]
            assert isinstance(movie, Movie)
            assert movie.id == "550"
            assert movie.title == "Fight Club"
            assert movie.release_date == date(1999, 10, 15)
            assert movie.runtime_minutes == 139
            assert movie.metadata.rating == 8.4
            assert movie.external_ids["tmdb"] == "550"
            assert movie.external_ids["imdb"] == "tt0137523"
            assert movie.images.poster is not None
    
    @pytest.mark.asyncio
    async def test_search_tv_show(self, tmdb_client):
        """Test TV show search."""
        mock_response = {
            "results": [
                {
                    "id": 1396,
                    "name": "Breaking Bad",
                    "original_name": "Breaking Bad",
                    "overview": "A high school chemistry teacher...",
                    "first_air_date": "2008-01-20",
                    "last_air_date": "2013-09-29",
                    "status": "Ended",
                    "number_of_seasons": 5,
                    "number_of_episodes": 62,
                    "poster_path": "/gG2FEpycVhA1q8iLfC8QbARXHK1.jpg",
                    "vote_average": 8.9,
                    "vote_count": 12905,
                    "popularity": 417.863,
                    "external_ids": {
                        "imdb_id": "tt0903747",
                        "tvdb_id": 81189
                    }
                }
            ]
        }
        
        with patch.object(tmdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            shows = await tmdb_client.search_tv_show("Breaking Bad", 2008)
            
            assert len(shows) == 1
            show = shows[0]
            assert isinstance(show, TVShow)
            assert show.id == "1396"
            assert show.title == "Breaking Bad"
            assert show.first_air_date == date(2008, 1, 20)
            assert show.number_of_seasons == 5
            assert show.number_of_episodes == 62
            assert show.external_ids["tmdb"] == "1396"
            assert show.external_ids["imdb"] == "tt0903747"
            assert show.external_ids["tvdb"] == "81189"
    
    @pytest.mark.asyncio
    async def test_get_movie_details(self, tmdb_client):
        """Test getting detailed movie information."""
        mock_response = {
            "id": 550,
            "title": "Fight Club",
            "original_title": "Fight Club",
            "overview": "An insomniac office worker...",
            "release_date": "1999-10-15",
            "runtime": 139,
            "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
            "vote_average": 8.4,
            "vote_count": 26280,
            "popularity": 61.416,
            "imdb_id": "tt0137523",
            "genres": [{"name": "Drama"}]
        }
        
        with patch.object(tmdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            movie = await tmdb_client.get_movie_details("550")
            
            assert isinstance(movie, Movie)
            assert movie.id == "550"
            assert movie.title == "Fight Club"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, tmdb_client):
        """Test authentication error handling."""
        mock_settings = MagicMock(spec=SettingsManager)
        mock_settings.get_tmdb_api_key.return_value = None
        
        client = TMDBClient(mock_settings)
        
        with pytest.raises(APIError, match="TMDB API key not configured"):
            await client.search_movie("test")


class TestTheTVDBClient:
    """Test TheTVDB client functionality."""
    
    @pytest.mark.asyncio
    async def test_authentication_flow(self, thetvdb_client):
        """Test authentication token flow."""
        mock_auth_response = {
            "data": {
                "token": "test_auth_token"
            }
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock the login response
            mock_response = AsyncMock()
            mock_response.json = AsyncMock(return_value=mock_auth_response)
            mock_response.raise_for_status = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            
            # Trigger authentication
            await thetvdb_client._ensure_auth()
            
            assert thetvdb_client._auth_token == "test_auth_token"
            assert thetvdb_client._token_expires is not None
    
    @pytest.mark.asyncio
    async def test_search_movie(self, thetvdb_client):
        """Test movie search."""
        mock_auth_response = {
            "data": {"token": "test_token"}
        }
        
        mock_search_response = {
            "data": {
                "results": [
                    {
                        "id": 123,
                        "name": "Test Movie",
                        "original_name": "Test Movie",
                        "overview": "A test movie",
                        "first_air": "2023-01-01",
                        "type": "movie",
                        "imdb_id": "tt1234567"
                    }
                ]
            }
        }
        
        with patch.object(thetvdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            async def mock_request_side_effect(method, url, **kwargs):
                if "login" in url:
                    return mock_auth_response
                elif "search" in url:
                    return mock_search_response
                return {}
            
            mock_request.side_effect = mock_request_side_effect
            
            movies = await thetvdb_client.search_movie("Test Movie", 2023)
            
            assert len(movies) == 1
            movie = movies[0]
            assert isinstance(movie, Movie)
            assert movie.id == "123"
            assert movie.title == "Test Movie"
            assert movie.external_ids["tvdb"] == "123"
            assert movie.external_ids["imdb"] == "tt1234567"
    
    @pytest.mark.asyncio
    async def test_search_tv_show(self, thetvdb_client):
        """Test TV show search."""
        mock_auth_response = {
            "data": {"token": "test_token"}
        }
        
        mock_search_response = {
            "data": {
                "results": [
                    {
                        "id": 456,
                        "name": "Test Show",
                        "original_name": "Test Show",
                        "overview": "A test show",
                        "first_air": "2023-01-01",
                        "type": "series",
                        "imdb_id": "tt7654321"
                    }
                ]
            }
        }
        
        with patch.object(thetvdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            async def mock_request_side_effect(method, url, **kwargs):
                if "login" in url:
                    return mock_auth_response
                elif "search" in url:
                    return mock_search_response
                return {}
            
            mock_request.side_effect = mock_request_side_effect
            
            shows = await thetvdb_client.search_tv_show("Test Show", 2023)
            
            assert len(shows) == 1
            show = shows[0]
            assert isinstance(show, TVShow)
            assert show.id == "456"
            assert show.title == "Test Show"
            assert show.external_ids["tvdb"] == "456"
            assert show.external_ids["imdb"] == "tt7654321"


class TestFilenameParser:
    """Test filename parsing functionality."""
    
    def test_parse_tv_show_s01e01(self):
        """Test parsing TV show with S01E01 format."""
        parsed = FilenameParser.parse("My.Show.S01E01.1080p.WEB-DL.x264-GROUP")
        
        assert parsed.title == "My Show"
        assert parsed.season == 1
        assert parsed.episode == 1
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.quality == "1080p"
    
    def test_parse_tv_show_1x01(self):
        """Test parsing TV show with 1x01 format."""
        parsed = FilenameParser.parse("My.Show.1x01.HDTV.x264-GROUP")
        
        assert parsed.title == "My Show"
        assert parsed.season == 1
        assert parsed.episode == 1
        assert parsed.media_type == MediaType.TV_SHOW
    
    def test_parse_movie_with_year(self):
        """Test parsing movie with year in parentheses."""
        parsed = FilenameParser.parse("My.Movie.2023.1080p.BluRay.x264-GROUP")
        
        assert parsed.title == "My Movie"
        assert parsed.year == 2023
        assert parsed.media_type == MediaType.MOVIE
        assert parsed.quality == "1080p"
    
    def test_parse_movie_parentheses_year(self):
        """Test parsing movie with year in parentheses."""
        parsed = FilenameParser.parse("My.Movie.(2023).1080p.BluRay.x264-GROUP")
        
        assert parsed.title == "My Movie"
        assert parsed.year == 2023
        assert parsed.media_type == MediaType.MOVIE
    
    def test_parse_complex_filename(self):
        """Test parsing complex filename with multiple patterns."""
        filename = "Amazing.Show.S02E15.2023.1080p.WEB-DL.DD5.1.H.264-GROUP"
        parsed = FilenameParser.parse(filename)
        
        assert parsed.title == "Amazing Show"
        assert parsed.season == 2
        assert parsed.episode == 15
        assert parsed.year == 2023
        assert parsed.media_type == MediaType.TV_SHOW
        assert parsed.quality == "1080p"


class TestFuzzyMatcher:
    """Test fuzzy matching functionality."""
    
    def test_match_movie_perfect(self):
        """Test perfect movie match."""
        matcher = FuzzyMatcher(min_score=60.0)
        
        parsed = ParsedFilename(title="Fight Club", year=1999, media_type=MediaType.MOVIE)
        
        movie = Movie(
            id="550",
            title="Fight Club",
            release_date=date(1999, 10, 15)
        )
        
        results = matcher.match_movie(parsed, [movie])
        
        assert len(results) == 1
        assert results[0].score >= 90.0  # Should be very high for perfect match
        assert results[0].item == movie
    
    def test_match_movie_close(self):
        """Test close movie match."""
        matcher = FuzzyMatcher(min_score=60.0)
        
        parsed = ParsedFilename(title="Fight Club", year=1999, media_type=MediaType.MOVIE)
        
        movie = Movie(
            id="550",
            title="Fight Club: Director's Cut",
            release_date=date(1999, 10, 15)
        )
        
        results = matcher.match_movie(parsed, [movie])
        
        assert len(results) == 1
        assert results[0].score >= 60.0  # Should be high for close match
    
    def test_match_movie_poor(self):
        """Test poor movie match below threshold."""
        matcher = FuzzyMatcher(min_score=60.0)
        
        parsed = ParsedFilename(title="Fight Club", year=1999, media_type=MediaType.MOVIE)
        
        movie = Movie(
            id="123",
            title="Completely Different Movie",
            release_date=date(2020, 1, 1)
        )
        
        results = matcher.match_movie(parsed, [movie])
        
        assert len(results) == 0  # Should be below threshold
    
    def test_match_tv_show(self):
        """Test TV show matching."""
        matcher = FuzzyMatcher(min_score=60.0)
        
        parsed = ParsedFilename(
            title="Breaking Bad",
            year=2008,
            season=1,
            episode=1,
            media_type=MediaType.TV_SHOW
        )
        
        show = TVShow(
            id="1396",
            title="Breaking Bad",
            first_air_date=date(2008, 1, 20)
        )
        
        results = matcher.match_tv_show(parsed, [show])
        
        assert len(results) == 1
        assert results[0].score >= 90.0
        assert results[0].item == show


class TestMediaSearcher:
    """Test media search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_by_filename(self):
        """Test searching by filename."""
        # Create mock providers
        mock_tmdb = AsyncMock()
        mock_thetvdb = AsyncMock()
        
        # Mock movie search results
        movie = Movie(id="550", title="Fight Club", release_date=date(1999, 10, 15))
        mock_tmdb.search_movie.return_value = [movie]
        mock_thetvdb.search_movie.return_value = []
        
        providers = {"tmdb": mock_tmdb, "thetvdb": mock_thetvdb}
        searcher = MediaSearcher(providers)
        
        results = await searcher.search_by_filename("Fight.Club.1999.1080p.BluRay.x264-GROUP")
        
        assert len(results) == 1
        assert results[0].provider == "tmdb"
        assert results[0].item == movie
        assert results[0].media_type == MediaType.MOVIE
    
    @pytest.mark.asyncio
    async def test_search_by_query(self):
        """Test searching by query string."""
        mock_tmdb = AsyncMock()
        mock_thetvdb = AsyncMock()
        
        # Mock TV show search results
        show = TVShow(id="1396", title="Breaking Bad", first_air_date=date(2008, 1, 20))
        mock_tmdb.search_tv_show.return_value = [show]
        mock_thetvdb.search_tv_show.return_value = []
        
        providers = {"tmdb": mock_tmdb, "thetvdb": mock_thetvdb}
        searcher = MediaSearcher(providers)
        
        results = await searcher.search_by_query("Breaking Bad", MediaType.TV_SHOW)
        
        assert len(results) == 1
        assert results[0].provider == "tmdb"
        assert results[0].item == show
        assert results[0].media_type == MediaType.TV_SHOW
        assert results[0].score == 100.0  # Perfect score for query search


class TestErrorHandling:
    """Test error handling in provider clients."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_error(self, tmdb_client):
        """Test rate limit error handling."""
        with patch.object(tmdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            from httpx import HTTPStatusError
            from unittest.mock import Mock
            
            # Create mock response with 429 status
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_response.headers = {"content-type": "text/plain"}
            
            error = HTTPStatusError("Rate limit exceeded", request=Mock(), response=mock_response)
            mock_request.side_effect = RateLimitError(f"Rate limit exceeded: {mock_response.text}")
            
            with pytest.raises(RateLimitError):
                await tmdb_client.search_movie("test")
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, tmdb_client):
        """Test authentication error handling."""
        with patch.object(tmdb_client, '_make_request', new_callable=AsyncMock) as mock_request:
            from httpx import HTTPStatusError
            from unittest.mock import Mock
            
            # Create mock response with 401 status
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_response.headers = {"content-type": "text/plain"}
            
            error = HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)
            mock_request.side_effect = AuthenticationError(f"Authentication failed: {mock_response.text}")
            
            with pytest.raises(AuthenticationError):
                await tmdb_client.search_movie("test")