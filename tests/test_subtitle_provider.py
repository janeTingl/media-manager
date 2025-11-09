"""Tests for subtitle provider functionality."""

from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import pytest

from src.media_manager.models import MediaType, SubtitleFormat, SubtitleLanguage
from src.media_manager.subtitle_provider import (
    MockSubtitleProvider,
    OpenSubtitlesProvider,
    SubtitleProvider,
    SubtitleResult,
)


class TestSubtitleResult:
    """Test cases for SubtitleResult."""

    def test_subtitle_result_creation(self) -> None:
        """Test creating a SubtitleResult."""
        result = SubtitleResult(
            subtitle_id="test_123",
            provider="TestProvider",
            language=SubtitleLanguage.ENGLISH,
            format=SubtitleFormat.SRT,
            download_url="https://example.com/subtitle.srt",
            file_size=50000,
            fps=23.976,
            release_name="Test Movie 2023",
            downloads=100,
            rating=4.5,
        )

        assert result.subtitle_id == "test_123"
        assert result.provider == "TestProvider"
        assert result.language == SubtitleLanguage.ENGLISH
        assert result.format == SubtitleFormat.SRT
        assert result.file_size == 50000
        assert result.downloads == 100
        assert result.rating == 4.5


class TestMockSubtitleProvider:
    """Test cases for MockSubtitleProvider."""

    def test_provider_initialization(self) -> None:
        """Test MockSubtitleProvider initialization."""
        provider = MockSubtitleProvider()
        assert provider is not None

    def test_search_returns_results(self) -> None:
        """Test search returns subtitle results."""
        provider = MockSubtitleProvider()
        
        results = provider.search(
            title="The Matrix",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.ENGLISH,
            year=1999,
        )

        assert len(results) > 0
        assert all(isinstance(r, SubtitleResult) for r in results)
        assert all(r.language == SubtitleLanguage.ENGLISH for r in results)
        assert all(r.provider == "MockProvider" for r in results)

    def test_search_movie(self) -> None:
        """Test searching for movie subtitles."""
        provider = MockSubtitleProvider()
        
        results = provider.search(
            title="Inception",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.SPANISH,
            year=2010,
        )

        assert len(results) >= 2
        for result in results:
            assert result.language == SubtitleLanguage.SPANISH
            assert result.download_url is not None
            assert result.format in [SubtitleFormat.SRT, SubtitleFormat.ASS, SubtitleFormat.VTT]

    def test_search_tv_episode(self) -> None:
        """Test searching for TV episode subtitles."""
        provider = MockSubtitleProvider()
        
        results = provider.search(
            title="Breaking Bad",
            media_type=MediaType.TV,
            language=SubtitleLanguage.FRENCH,
            season=1,
            episode=1,
        )

        assert len(results) > 0
        assert all(r.language == SubtitleLanguage.FRENCH for r in results)

    def test_search_different_languages(self) -> None:
        """Test searching in different languages."""
        provider = MockSubtitleProvider()
        languages = [
            SubtitleLanguage.ENGLISH,
            SubtitleLanguage.SPANISH,
            SubtitleLanguage.FRENCH,
            SubtitleLanguage.GERMAN,
        ]

        for language in languages:
            results = provider.search(
                title="Test Movie",
                media_type=MediaType.MOVIE,
                language=language,
            )
            assert len(results) > 0
            assert all(r.language == language for r in results)

    def test_download_creates_file(self) -> None:
        """Test that download creates a subtitle file."""
        provider = MockSubtitleProvider()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "subtitle.srt")
            
            result = SubtitleResult(
                subtitle_id="test_123",
                provider="MockProvider",
                language=SubtitleLanguage.ENGLISH,
                format=SubtitleFormat.SRT,
                download_url="https://example.com/subtitle.srt",
            )
            
            success = provider.download(result, output_path)
            
            assert success
            assert Path(output_path).exists()
            
            # Check file content
            content = Path(output_path).read_text()
            assert "mock subtitle" in content.lower()
            assert SubtitleLanguage.ENGLISH.value in content

    def test_download_handles_error(self) -> None:
        """Test download handles invalid paths gracefully."""
        provider = MockSubtitleProvider()
        
        result = SubtitleResult(
            subtitle_id="test_123",
            provider="MockProvider",
            language=SubtitleLanguage.ENGLISH,
            format=SubtitleFormat.SRT,
            download_url="https://example.com/subtitle.srt",
        )
        
        # Use an invalid path that can't be created
        success = provider.download(result, "/invalid/path/that/does/not/exist/subtitle.srt")
        
        assert not success


class TestOpenSubtitlesProvider:
    """Test cases for OpenSubtitlesProvider."""

    def test_provider_initialization(self) -> None:
        """Test OpenSubtitlesProvider initialization."""
        provider = OpenSubtitlesProvider()
        assert provider is not None
        assert provider.api_key is None

    def test_provider_with_api_key(self) -> None:
        """Test OpenSubtitlesProvider with API key."""
        provider = OpenSubtitlesProvider(api_key="test_key")
        assert provider.api_key == "test_key"

    def test_search_returns_results(self) -> None:
        """Test search returns results."""
        provider = OpenSubtitlesProvider()
        
        results = provider.search(
            title="Avatar",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.ENGLISH,
            year=2009,
        )

        assert len(results) >= 3
        assert all(isinstance(r, SubtitleResult) for r in results)
        assert all(r.provider == "OpenSubtitles" for r in results)

    def test_download_with_opensubtitles(self) -> None:
        """Test downloading from OpenSubtitles provider."""
        provider = OpenSubtitlesProvider()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "subtitle.srt")
            
            result = SubtitleResult(
                subtitle_id="os_123",
                provider="OpenSubtitles",
                language=SubtitleLanguage.ENGLISH,
                format=SubtitleFormat.SRT,
                download_url="https://api.opensubtitles.com/download/123",
            )
            
            success = provider.download(result, output_path)
            
            assert success
            assert Path(output_path).exists()


class TestSubtitleProviderInterface:
    """Test cases for the SubtitleProvider interface."""

    def test_provider_is_abstract(self) -> None:
        """Test that SubtitleProvider is abstract."""
        with pytest.raises(TypeError):
            SubtitleProvider()

    def test_mock_provider_implements_interface(self) -> None:
        """Test that MockSubtitleProvider implements the interface."""
        provider = MockSubtitleProvider()
        assert isinstance(provider, SubtitleProvider)
        assert hasattr(provider, 'search')
        assert hasattr(provider, 'download')

    def test_opensubtitles_provider_implements_interface(self) -> None:
        """Test that OpenSubtitlesProvider implements the interface."""
        provider = OpenSubtitlesProvider()
        assert isinstance(provider, SubtitleProvider)
        assert hasattr(provider, 'search')
        assert hasattr(provider, 'download')


class TestSubtitleSearchConsistency:
    """Test consistency of subtitle searches."""

    def test_same_search_returns_results(self) -> None:
        """Test that the same search always returns results."""
        provider = MockSubtitleProvider()
        
        # Search twice with same parameters
        results1 = provider.search(
            title="Titanic",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.ENGLISH,
            year=1997,
        )
        
        results2 = provider.search(
            title="Titanic",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.ENGLISH,
            year=1997,
        )

        assert len(results1) == len(results2)
        assert results1[0].language == results2[0].language

    def test_different_languages_return_different_results(self) -> None:
        """Test that searching different languages returns appropriately."""
        provider = MockSubtitleProvider()
        
        results_en = provider.search(
            title="Test",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.ENGLISH,
        )
        
        results_es = provider.search(
            title="Test",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.SPANISH,
        )

        assert all(r.language == SubtitleLanguage.ENGLISH for r in results_en)
        assert all(r.language == SubtitleLanguage.SPANISH for r in results_es)
