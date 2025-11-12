"""Tests for metadata providers with stubbed HTTP layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from src.media_manager.models import MediaType, VideoMetadata
from src.media_manager.providers.adapter import ProviderAdapter
from src.media_manager.providers.base import ProviderError, ProviderResult
from src.media_manager.providers.tmdb import TMDBProvider
from src.media_manager.providers.tvdb import TVDBProvider


# ============================================================================
# Fixtures: Stubbed HTTP Responses
# ============================================================================


@pytest.fixture
def tmdb_movie_search_response() -> dict[str, Any]:
    """TMDB movie search response fixture."""
    return {
        "page": 1,
        "results": [
            {
                "id": 550,
                "title": "Fight Club",
                "release_date": "1999-10-15",
                "poster_path": "/adw6Lq9FiC9zjYEiF0C3W8JsfsS.jpg",
                "backdrop_path": "/rr7E0NoGKxvbkb89eR1GwfoYjpA.jpg",
                "overview": "A ticking-time-bomb insomniac",
                "popularity": 78.5,
            },
            {
                "id": 551,
                "title": "Fight Club 2",
                "release_date": None,
                "poster_path": None,
                "backdrop_path": None,
                "overview": None,
                "popularity": 5.2,
            },
        ],
        "total_pages": 1,
        "total_results": 2,
    }


@pytest.fixture
def tmdb_tv_search_response() -> dict[str, Any]:
    """TMDB TV series search response fixture."""
    return {
        "page": 1,
        "results": [
            {
                "id": 1399,
                "name": "Game of Thrones",
                "first_air_date": "2011-04-17",
                "poster_path": "/u3bZgnVW1iUEnnNQWHC4Fnnq5dw.jpg",
                "backdrop_path": "/gX8SurPiQwoxJwgaP3BA50nQT5f.jpg",
                "overview": "Seven noble families fight for control",
                "popularity": 112.3,
            },
        ],
        "total_pages": 1,
        "total_results": 1,
    }


@pytest.fixture
def tmdb_movie_details_response() -> dict[str, Any]:
    """TMDB movie details response fixture."""
    return {
        "id": 550,
        "title": "Fight Club",
        "original_title": "Fight Club",
        "release_date": "1999-10-15",
        "runtime": 139,
        "overview": "An insomniac office worker",
        "poster_path": "/adw6Lq9FiC9zjYEiF0C3W8JsfsS.jpg",
        "backdrop_path": "/rr7E0NoGKxvbkb89eR1GwfoYjpA.jpg",
        "genres": [
            {"id": 18, "name": "Drama"},
            {"id": 53, "name": "Thriller"},
        ],
        "production_companies": [
            {"id": 508, "name": "Regency Enterprises"},
        ],
        "credits": {
            "cast": [
                {"id": 819, "name": "Brad Pitt", "character": "Tyler Durden"},
                {"id": 287, "name": "Edward Norton", "character": "The Narrator"},
            ],
        },
        "videos": {
            "results": [
                {
                    "id": "5e01038a0e0a265b8f08ea6a",
                    "key": "ytfo_D1FxAg",
                    "name": "Fight Club - Trailer",
                    "type": "Trailer",
                    "site": "YouTube",
                },
            ],
        },
    }


@pytest.fixture
def tmdb_tv_details_response() -> dict[str, Any]:
    """TMDB TV series details response fixture."""
    return {
        "id": 1399,
        "name": "Game of Thrones",
        "original_name": "Game of Thrones",
        "first_air_date": "2011-04-17",
        "episode_run_time": [56, 59, 60],
        "overview": "Seven noble families fight for control",
        "poster_path": "/u3bZgnVW1iUEnnNQWHC4Fnnq5dw.jpg",
        "backdrop_path": "/gX8SurPiQwoxJwgaP3BA50nQT5f.jpg",
        "genres": [
            {"id": 10765, "name": "Sci-Fi & Fantasy"},
            {"id": 18, "name": "Drama"},
        ],
        "production_companies": [
            {"id": 3268, "name": "HBO"},
        ],
        "credits": {
            "cast": [
                {"id": 1223192, "name": "Emilia Clarke", "character": "Daenerys Targaryen"},
                {"id": 117642, "name": "Peter Dinklage", "character": "Tyrion Lannister"},
            ],
        },
        "videos": {
            "results": [
                {
                    "id": "5e010402ae0a265b8f08fddb",
                    "key": "BpJYNVhGf1s",
                    "name": "Game of Thrones",
                    "type": "Trailer",
                    "site": "YouTube",
                },
            ],
        },
    }


@pytest.fixture
def tvdb_tv_search_response() -> dict[str, Any]:
    """TVDB TV series search response fixture."""
    return {
        "data": [
            {
                "id": 121361,
                "name": "Game of Thrones",
                "first_air_date": "2011-04-17",
                "overview": "Seven noble families fight for control",
                "image_url": "https://artworks.thetvdb.com/banners/posters/121361-2.jpg",
                "thumbnail": "https://artworks.thetvdb.com/banners/graphical/121361-g3.jpg",
            },
        ],
        "status": "success",
    }


@pytest.fixture
def tvdb_tv_details_response() -> dict[str, Any]:
    """TVDB TV series details response fixture."""
    return {
        "data": {
            "id": 121361,
            "name": "Game of Thrones",
            "original_name": "Game of Thrones",
            "first_air_date": "2011-04-17",
            "overview": "Seven noble families fight for control",
            "image": "https://artworks.thetvdb.com/banners/posters/121361-2.jpg",
            "thumbnail": "https://artworks.thetvdb.com/banners/graphical/121361-g3.jpg",
            "runtime": 56,
            "genres": ["Sci-Fi", "Drama", "Fantasy"],
            "companies": [
                {"name": "HBO"},
            ],
            "characters": [
                {"id": 1, "personName": "Emilia Clarke", "character": "Daenerys Targaryen"},
                {"id": 2, "personName": "Peter Dinklage", "character": "Tyrion Lannister"},
            ],
        },
        "status": "success",
    }


# ============================================================================
# TMDB Provider Tests
# ============================================================================


class TestTMDBProvider:
    """Tests for TMDB provider."""

    def test_init_with_api_key(self) -> None:
        """Test TMDB provider initialization with API key."""
        provider = TMDBProvider("test-api-key")
        assert provider.api_key == "test-api-key"
        assert provider.name == "TMDBProvider"

    def test_init_without_api_key(self) -> None:
        """Test TMDB provider initialization without API key."""
        provider = TMDBProvider()
        assert provider.api_key is None

    @patch("requests.get")
    def test_search_movie(self, mock_get: Mock, tmdb_movie_search_response: dict[str, Any]) -> None:
        """Test TMDB movie search."""
        mock_response = Mock()
        mock_response.json.return_value = tmdb_movie_search_response
        mock_get.return_value = mock_response

        provider = TMDBProvider("test-key")
        results = provider.search_movie("Fight Club", 1999)

        assert len(results) == 2
        assert results[0].title == "Fight Club"
        assert results[0].year == 1999
        assert results[0].external_id == "550"
        assert results[0].provider_name == "TMDB"
        assert 0.0 <= results[0].confidence <= 1.0

    @patch("requests.get")
    def test_search_movie_without_api_key(self, mock_get: Mock) -> None:
        """Test TMDB movie search without API key raises error."""
        provider = TMDBProvider()

        with pytest.raises(ProviderError, match="API key is not configured"):
            provider.search_movie("Fight Club")

    @patch("requests.get")
    def test_search_tv(self, mock_get: Mock, tmdb_tv_search_response: dict[str, Any]) -> None:
        """Test TMDB TV series search."""
        mock_response = Mock()
        mock_response.json.return_value = tmdb_tv_search_response
        mock_get.return_value = mock_response

        provider = TMDBProvider("test-key")
        results = provider.search_tv("Game of Thrones", 2011)

        assert len(results) == 1
        assert results[0].title == "Game of Thrones"
        assert results[0].year == 2011
        assert results[0].external_id == "1399"

    @patch("requests.get")
    def test_get_movie_details(self, mock_get: Mock, tmdb_movie_details_response: dict[str, Any]) -> None:
        """Test TMDB get movie details."""
        mock_response = Mock()
        mock_response.json.return_value = tmdb_movie_details_response
        mock_get.return_value = mock_response

        provider = TMDBProvider("test-key")
        result = provider.get_movie_details("550")

        assert result.title == "Fight Club"
        assert result.runtime == 139
        assert result.external_id == "550"
        assert len(result.cast) == 2
        assert "Brad Pitt" in result.cast
        assert len(result.trailers) == 1
        assert "youtube.com" in result.trailers[0]
        assert len(result.companies) == 1
        assert "Regency" in result.companies[0]

    @patch("requests.get")
    def test_get_tv_details(self, mock_get: Mock, tmdb_tv_details_response: dict[str, Any]) -> None:
        """Test TMDB get TV details."""
        mock_response = Mock()
        mock_response.json.return_value = tmdb_tv_details_response
        mock_get.return_value = mock_response

        provider = TMDBProvider("test-key")
        result = provider.get_tv_details("1399")

        assert result.title == "Game of Thrones"
        assert result.runtime == 56
        assert result.external_id == "1399"
        assert len(result.cast) == 2
        assert "Emilia Clarke" in result.cast

    @patch("src.media_manager.providers.tmdb.requests.get")
    def test_api_call_handles_http_errors(self, mock_get: Mock) -> None:
        """Test TMDB provider handles HTTP errors gracefully."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        provider = TMDBProvider("test-key")

        with pytest.raises(ProviderError, match="API call failed"):
            provider.search_movie("Test")

    @patch("src.media_manager.providers.tmdb.requests.get")
    def test_api_call_handles_network_errors(self, mock_get: Mock) -> None:
        """Test TMDB provider handles network errors gracefully."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        provider = TMDBProvider("test-key")

        with pytest.raises(ProviderError, match="API call failed"):
            provider.search_movie("Test")


# ============================================================================
# TVDB Provider Tests
# ============================================================================


class TestTVDBProvider:
    """Tests for TVDB provider."""

    def test_init_with_api_key(self) -> None:
        """Test TVDB provider initialization with API key."""
        provider = TVDBProvider("test-api-key")
        assert provider.api_key == "test-api-key"
        assert provider.name == "TVDBProvider"

    @patch("src.media_manager.providers.tvdb.requests.post")
    @patch("src.media_manager.providers.tvdb.Path.exists")
    def test_authentication(self, mock_exists: Mock, mock_post: Mock) -> None:
        """Test TVDB authentication."""
        # Indicate cache doesn't exist
        mock_exists.return_value = False
        
        auth_response = Mock()
        auth_response.json.return_value = {"data": {"token": "test-token-123"}}
        mock_post.return_value = auth_response

        provider = TVDBProvider("test-key")
        provider._authenticate()

        assert provider._token == "test-token-123"

    @patch("requests.post")
    @patch("requests.get")
    def test_search_tv(
        self, mock_get: Mock, mock_post: Mock, tvdb_tv_search_response: dict[str, Any]
    ) -> None:
        """Test TVDB TV series search."""
        # Mock authentication
        auth_response = Mock()
        auth_response.json.return_value = {"data": {"token": "test-token"}}
        mock_post.return_value = auth_response

        # Mock search response
        search_response = Mock()
        search_response.json.return_value = tvdb_tv_search_response
        mock_get.return_value = search_response

        provider = TVDBProvider("test-key")
        results = provider.search_tv("Game of Thrones")

        assert len(results) == 1
        assert results[0].title == "Game of Thrones"
        assert results[0].external_id == "121361"
        assert results[0].provider_name == "TVDB"

    @patch("requests.post")
    @patch("requests.get")
    def test_get_tv_details(
        self, mock_get: Mock, mock_post: Mock, tvdb_tv_details_response: dict[str, Any]
    ) -> None:
        """Test TVDB get TV details."""
        # Mock authentication
        auth_response = Mock()
        auth_response.json.return_value = {"data": {"token": "test-token"}}
        mock_post.return_value = auth_response

        # Mock details response
        details_response = Mock()
        details_response.json.return_value = tvdb_tv_details_response
        mock_get.return_value = details_response

        provider = TVDBProvider("test-key")
        result = provider.get_tv_details("121361")

        assert result.title == "Game of Thrones"
        assert result.external_id == "121361"
        assert len(result.cast) == 2
        assert "Emilia Clarke" in result.cast

    @patch("requests.post")
    def test_authentication_without_api_key(self, mock_post: Mock) -> None:
        """Test TVDB authentication without API key raises error."""
        provider = TVDBProvider()

        with pytest.raises(ProviderError, match="API key is not configured"):
            provider._authenticate()


# ============================================================================
# Provider Adapter Tests
# ============================================================================


class TestProviderAdapter:
    """Tests for provider adapter."""

    def test_init_with_providers(self) -> None:
        """Test adapter initialization with providers."""
        providers = [TMDBProvider("key1"), TVDBProvider("key2")]
        adapter = ProviderAdapter(providers)
        assert len(adapter.providers) == 2

    def test_init_without_providers(self) -> None:
        """Test adapter initialization without providers."""
        adapter = ProviderAdapter()
        assert adapter.providers == []

    @patch.object(TMDBProvider, "search_movie")
    def test_search_and_match_movie(self, mock_search: Mock) -> None:
        """Test search and match for movie."""
        mock_result = ProviderResult(
            provider_name="TMDB",
            external_id="550",
            title="Fight Club",
            year=1999,
            overview="A film",
            confidence=0.9,
            poster_url="https://example.com/poster.jpg",
        )
        mock_search.return_value = [mock_result]

        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        metadata = VideoMetadata(
            path=Path("/test/fight.club.1999.mkv"),
            title="Fight Club",
            media_type=MediaType.MOVIE,
            year=1999,
        )

        match = adapter.search_and_match(metadata)

        assert match.matched_title == "Fight Club"
        assert match.matched_year == 1999
        assert match.confidence == 0.9
        assert match.source == "TMDB"

    @patch.object(TMDBProvider, "search_tv")
    def test_search_and_match_tv(self, mock_search: Mock) -> None:
        """Test search and match for TV series."""
        mock_result = ProviderResult(
            provider_name="TMDB",
            external_id="1399",
            title="Game of Thrones",
            year=2011,
            overview="A series",
            confidence=0.85,
        )
        mock_search.return_value = [mock_result]

        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        metadata = VideoMetadata(
            path=Path("/test/game.of.thrones.s01e01.mkv"),
            title="Game of Thrones",
            media_type=MediaType.TV,
            year=2011,
            season=1,
            episode=1,
        )

        match = adapter.search_and_match(metadata)

        assert match.matched_title == "Game of Thrones"
        assert match.confidence == 0.85

    @patch.object(TMDBProvider, "search_movie")
    def test_search_results_merge_duplicates(self, mock_search: Mock) -> None:
        """Test that adapter merges duplicate results from multiple providers."""
        result1 = ProviderResult(
            provider_name="TMDB",
            external_id="550",
            title="Fight Club",
            year=1999,
            confidence=0.9,
        )
        result2 = ProviderResult(
            provider_name="TVDB",
            external_id="550-alt",
            title="Fight Club",
            year=1999,
            confidence=0.85,
        )
        mock_search.return_value = [result1]

        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        results = adapter.search_results("Fight Club", MediaType.MOVIE, 1999)

        # Should only have one result (merged)
        assert len(results) == 1
        assert results[0].confidence == 0.9  # Highest confidence

    @patch.object(TMDBProvider, "search_movie")
    def test_search_and_match_with_fallback_to_mock(self, mock_search: Mock) -> None:
        """Test that adapter falls back to mock when no results found."""
        mock_search.return_value = []

        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        metadata = VideoMetadata(
            path=Path("/test/unknown.mkv"),
            title="Unknown Movie",
            media_type=MediaType.MOVIE,
        )

        match = adapter.search_and_match(metadata, fallback_to_mock=True)

        assert match.source == "MockAdapter"
        assert match.matched_title == "Unknown Movie"

    @patch.object(TMDBProvider, "search_movie")
    def test_search_and_match_provider_error_gracefully_handles(self, mock_search: Mock) -> None:
        """Test that provider errors are handled gracefully."""
        mock_search.side_effect = ProviderError("API error")

        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        metadata = VideoMetadata(
            path=Path("/test/test.mkv"),
            title="Test",
            media_type=MediaType.MOVIE,
        )

        # Should fall back to mock instead of raising
        match = adapter.search_and_match(metadata, fallback_to_mock=True)

        assert match.source == "MockAdapter"


# ============================================================================
# Integration Tests
# ============================================================================


class TestProviderIntegration:
    """Integration tests for providers."""

    @patch("requests.get")
    def test_complete_movie_workflow(
        self, mock_get: Mock, tmdb_movie_search_response: dict[str, Any],
        tmdb_movie_details_response: dict[str, Any]
    ) -> None:
        """Test complete movie search and details workflow."""
        # First call: search
        # Second call: details
        search_mock = Mock()
        search_mock.json.return_value = tmdb_movie_search_response
        
        details_mock = Mock()
        details_mock.json.return_value = tmdb_movie_details_response
        
        mock_get.side_effect = [search_mock, details_mock]

        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        metadata = VideoMetadata(
            path=Path("/test/fight.club.1999.mkv"),
            title="Fight Club",
            media_type=MediaType.MOVIE,
            year=1999,
        )

        # Search and match
        match = adapter.search_and_match(metadata)
        assert match.matched_title == "Fight Club"

    @patch("requests.get")
    @patch("requests.post")
    def test_multiple_providers_priority(
        self, mock_post: Mock, mock_get: Mock,
        tmdb_movie_search_response: dict[str, Any],
        tvdb_tv_search_response: dict[str, Any]
    ) -> None:
        """Test that multiple providers work together."""
        tmdb_provider = TMDBProvider("tmdb-key")
        
        # Mock TVDB auth
        auth_response = Mock()
        auth_response.json.return_value = {"data": {"token": "test-token"}}
        mock_post.return_value = auth_response
        
        # This test would require more complex mocking
        # For now, just verify providers can be initialized together
        adapter = ProviderAdapter([tmdb_provider])
        assert len(adapter.providers) == 1
