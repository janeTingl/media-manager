"""Integration tests for providers with workers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.media_manager.models import MediaType, VideoMetadata
from src.media_manager.providers.adapter import ProviderAdapter
from src.media_manager.providers.base import ProviderResult
from src.media_manager.providers.tmdb import TMDBProvider
from src.media_manager.workers import MatchWorker, SearchWorker
from src.media_manager.models import SearchRequest
from src.media_manager.settings import get_settings


class TestWorkerProviderIntegration:
    """Test integration of providers with workers."""

    @patch.object(TMDBProvider, "search_movie")
    def test_match_worker_uses_provider(self, mock_search: Mock) -> None:
        """Test that MatchWorker uses provider adapter instead of mock."""
        # Mock provider result
        mock_result = ProviderResult(
            provider_name="TMDB",
            external_id="550",
            title="Fight Club",
            year=1999,
            overview="A film",
            confidence=0.95,
            runtime=139,
            cast=["Brad Pitt", "Edward Norton"],
        )
        mock_search.return_value = [mock_result]

        # Create test metadata
        metadata = VideoMetadata(
            path=Path("/test/fight.club.1999.mkv"),
            title="Fight Club",
            media_type=MediaType.MOVIE,
            year=1999,
        )

        # Create worker with settings that have TMDB enabled
        with patch.object(get_settings(), "get_enabled_providers", return_value=["TMDB"]):
            with patch.object(get_settings(), "get_tmdb_api_key", return_value="test-key"):
                worker = MatchWorker([metadata])
                
                # Simulate running worker
                results = []
                worker.signals.match_found.connect(lambda match: results.append(match))
                
                # Run matching
                worker.run()
                
                # Verify provider was called
                assert mock_search.called
                
                # Verify result was emitted
                assert len(results) == 1
                match = results[0]
                assert match.matched_title == "Fight Club"
                assert match.source == "TMDB"
                assert match.confidence == 0.95

    @patch.object(TMDBProvider, "search_movie")
    def test_search_worker_uses_provider(self, mock_search: Mock) -> None:
        """Test that SearchWorker uses provider adapter."""
        # Mock provider results
        mock_result1 = ProviderResult(
            provider_name="TMDB",
            external_id="550",
            title="Fight Club",
            year=1999,
            confidence=0.95,
            poster_url="https://example.com/poster.jpg",
        )
        mock_result2 = ProviderResult(
            provider_name="TMDB",
            external_id="551",
            title="Fight Club 2",
            year=None,
            confidence=0.3,
            poster_url=None,
        )
        mock_search.return_value = [mock_result1, mock_result2]

        # Create search request
        request = SearchRequest(
            query="Fight Club",
            media_type=MediaType.MOVIE,
            year=1999,
        )

        # Create worker with TMDB enabled
        with patch.object(get_settings(), "get_enabled_providers", return_value=["TMDB"]):
            with patch.object(get_settings(), "get_tmdb_api_key", return_value="test-key"):
                worker = SearchWorker(request)
                
                # Simulate running worker
                results_list = []
                worker.signals.search_completed.connect(lambda results: results_list.append(results))
                
                # Run search
                worker.run()
                
                # Verify provider was called
                assert mock_search.called
                
                # Verify results were converted and emitted
                assert len(results_list) == 1
                results = results_list[0]
                assert len(results) >= 1
                assert results[0].title == "Fight Club"
                assert results[0].source == "TMDB"

    @patch.object(TMDBProvider, "search_movie")
    def test_match_worker_graceful_error_handling(self, mock_search: Mock) -> None:
        """Test that MatchWorker gracefully handles provider errors."""
        # Simulate provider error
        from src.media_manager.providers.base import ProviderError
        mock_search.side_effect = ProviderError("API Error")

        # Create test metadata
        metadata = VideoMetadata(
            path=Path("/test/test.mkv"),
            title="Test",
            media_type=MediaType.MOVIE,
        )

        # Create worker
        with patch.object(get_settings(), "get_enabled_providers", return_value=["TMDB"]):
            with patch.object(get_settings(), "get_tmdb_api_key", return_value="test-key"):
                worker = MatchWorker([metadata])
                
                # Simulate running worker
                results = []
                worker.signals.match_found.connect(lambda match: results.append(match))
                
                # Run matching (should not crash)
                worker.run()
                
                # Verify fallback to mock was used
                assert len(results) == 1
                match = results[0]
                assert match.source == "MockAdapter"
                assert match.matched_title == "Test"

    def test_match_worker_no_providers_configured(self) -> None:
        """Test MatchWorker with no providers configured (falls back to mock)."""
        metadata = VideoMetadata(
            path=Path("/test/test.mkv"),
            title="Test",
            media_type=MediaType.MOVIE,
        )

        # Create worker with no providers enabled
        with patch.object(get_settings(), "get_enabled_providers", return_value=[]):
            worker = MatchWorker([metadata])
            
            # Simulate running worker
            results = []
            worker.signals.match_found.connect(lambda match: results.append(match))
            
            # Run matching
            worker.run()
            
            # Verify mock adapter was used
            assert len(results) == 1
            match = results[0]
            assert match.source == "MockAdapter"

    @patch.object(TMDBProvider, "search_movie")
    def test_provider_adapter_direct_usage(self, mock_search: Mock) -> None:
        """Test provider adapter can be used directly."""
        # Mock result
        mock_result = ProviderResult(
            provider_name="TMDB",
            external_id="550",
            title="Fight Club",
            year=1999,
            confidence=0.9,
            poster_url="https://example.com/poster.jpg",
        )
        mock_search.return_value = [mock_result]

        # Create adapter with provider
        provider = TMDBProvider("test-key")
        adapter = ProviderAdapter([provider])

        # Test search and match
        metadata = VideoMetadata(
            path=Path("/test/fight.club.1999.mkv"),
            title="Fight Club",
            media_type=MediaType.MOVIE,
            year=1999,
        )

        match = adapter.search_and_match(metadata)

        # Verify match was created from provider result
        assert match.matched_title == "Fight Club"
        assert match.source == "TMDB"
        assert match.confidence == 0.9
        assert match.poster_url == "https://example.com/poster.jpg"

    @patch.object(TMDBProvider, "search_tv")
    def test_adapter_handles_tv_series(self, mock_search: Mock) -> None:
        """Test adapter handles TV series searches."""
        mock_result = ProviderResult(
            provider_name="TMDB",
            external_id="1399",
            title="Game of Thrones",
            year=2011,
            confidence=0.9,
            runtime=56,
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
        assert match.source == "TMDB"
        assert match.runtime == 56
