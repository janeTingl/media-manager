"""Tests for subtitle downloader functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.media_manager.models import DownloadStatus, SubtitleFormat, SubtitleLanguage, SubtitleInfo
from src.media_manager.subtitle_downloader import SubtitleDownloader
from src.media_manager.subtitle_provider import MockSubtitleProvider, SubtitleResult


class TestSubtitleDownloader:
    """Test cases for SubtitleDownloader."""

    def test_init_default_cache_dir(self) -> None:
        """Test SubtitleDownloader initialization with default cache directory."""
        downloader = SubtitleDownloader()
        expected_cache_dir = Path.home() / ".media-manager" / "subtitle-cache"
        assert downloader._cache_dir == expected_cache_dir

    def test_init_custom_cache_dir(self) -> None:
        """Test SubtitleDownloader initialization with custom cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_cache = Path(temp_dir) / "custom_cache"
            downloader = SubtitleDownloader(cache_dir=custom_cache)
            assert downloader._cache_dir == custom_cache
            assert custom_cache.exists()

    def test_get_subtitle_path_movie(self) -> None:
        """Test getting subtitle path for movie."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "MovieName (2023).mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloader = SubtitleDownloader()
            subtitle_path = downloader.get_subtitle_path(media_path, SubtitleLanguage.ENGLISH)
            
            expected = media_path.parent / "MovieName (2023).en.srt"
            assert subtitle_path == expected

    def test_get_subtitle_path_tv_episode(self) -> None:
        """Test getting subtitle path for TV episode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "ShowName" / "S01E01.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloader = SubtitleDownloader()
            subtitle_path = downloader.get_subtitle_path(media_path, SubtitleLanguage.SPANISH)
            
            expected = media_path.parent / "S01E01.es.srt"
            assert subtitle_path == expected

    def test_get_subtitle_path_different_languages(self) -> None:
        """Test getting subtitle paths for different languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloader = SubtitleDownloader()
            
            path_en = downloader.get_subtitle_path(media_path, SubtitleLanguage.ENGLISH)
            path_es = downloader.get_subtitle_path(media_path, SubtitleLanguage.SPANISH)
            path_fr = downloader.get_subtitle_path(media_path, SubtitleLanguage.FRENCH)
            
            assert "en" in path_en.name
            assert "es" in path_es.name
            assert "fr" in path_fr.name

    def test_get_subtitle_path_no_media_dir(self) -> None:
        """Test getting subtitle path when media directory doesn't exist."""
        media_path = Path("/nonexistent/path/movie.mkv")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = SubtitleDownloader(cache_dir=Path(temp_dir))
            subtitle_path = downloader.get_subtitle_path(media_path, SubtitleLanguage.ENGLISH)
            
            # Should fall back to cache directory
            assert subtitle_path.parent == downloader._cache_dir

    def test_download_subtitle_no_url(self) -> None:
        """Test downloading subtitle with no URL."""
        subtitle_info = SubtitleInfo(language=SubtitleLanguage.ENGLISH)
        media_path = Path("/test/movie.mkv")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = SubtitleDownloader(cache_dir=Path(temp_dir))
            result = downloader.download_subtitle(subtitle_info, media_path)
            
            assert not result
            assert subtitle_info.download_status == DownloadStatus.FAILED
            assert subtitle_info.error_message == "No URL provided"

    def test_download_subtitle_already_exists(self) -> None:
        """Test downloading subtitle when file already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create existing subtitle file
            subtitle_path = media_path.parent / "movie.en.srt"
            subtitle_path.write_text("1\n00:00:00,000 --> 00:00:05,000\nTest subtitle")
            
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url="https://example.com/subtitle.srt"
            )
            
            downloader = SubtitleDownloader(cache_dir=Path(temp_dir))
            result = downloader.download_subtitle(subtitle_info, media_path)
            
            assert result
            assert subtitle_info.download_status == DownloadStatus.COMPLETED
            assert subtitle_info.local_path == subtitle_path

    def test_download_subtitle_with_provider(self) -> None:
        """Test downloading subtitle using provider."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url="https://example.com/subtitle.srt",
            )
            
            subtitle_result = SubtitleResult(
                subtitle_id="test_123",
                provider="TestProvider",
                language=SubtitleLanguage.ENGLISH,
                format=SubtitleFormat.SRT,
                download_url="https://example.com/subtitle.srt",
            )
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir))
            
            result = downloader.download_subtitle(
                subtitle_info, media_path, subtitle_result=subtitle_result
            )
            
            assert result
            assert subtitle_info.download_status == DownloadStatus.COMPLETED
            assert subtitle_info.local_path is not None
            assert subtitle_info.local_path.exists()

    def test_search_subtitles(self) -> None:
        """Test searching for subtitles."""
        from src.media_manager.models import MediaType
        
        provider = MockSubtitleProvider()
        downloader = SubtitleDownloader(provider=provider)
        
        results = downloader.search_subtitles(
            title="Inception",
            media_type=MediaType.MOVIE,
            language=SubtitleLanguage.ENGLISH,
            year=2010,
        )
        
        assert len(results) > 0
        assert all(isinstance(r, SubtitleResult) for r in results)

    def test_clear_cache(self) -> None:
        """Test clearing the subtitle cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            # Create some cache files
            (cache_dir / "test1.srt").write_text("Test subtitle 1")
            (cache_dir / "test2.srt").write_text("Test subtitle 2")
            
            assert len(list(cache_dir.iterdir())) == 2
            
            downloader = SubtitleDownloader(cache_dir=cache_dir)
            downloader.clear_cache()
            
            assert len(list(cache_dir.iterdir())) == 0

    def test_get_cache_size(self) -> None:
        """Test getting cache size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            
            # Create cache files
            (cache_dir / "test1.srt").write_bytes(b"x" * 1000)
            (cache_dir / "test2.srt").write_bytes(b"y" * 2000)
            
            downloader = SubtitleDownloader(cache_dir=cache_dir)
            size = downloader.get_cache_size()
            
            assert size == 3000

    def test_is_downloading(self) -> None:
        """Test checking if subtitle is being downloaded."""
        downloader = SubtitleDownloader()
        
        subtitle_info = SubtitleInfo(
            language=SubtitleLanguage.ENGLISH,
            url="https://example.com/subtitle.srt",
        )
        
        # Initially should not be downloading
        assert not downloader.is_downloading(subtitle_info)

    def test_set_provider(self) -> None:
        """Test setting a different provider."""
        downloader = SubtitleDownloader()
        
        mock_provider = MockSubtitleProvider()
        downloader.set_provider(mock_provider)
        
        assert downloader._provider == mock_provider

    def test_cached_path_extraction(self) -> None:
        """Test cache path generation and extension extraction."""
        downloader = SubtitleDownloader()
        
        # Test with various URL formats
        urls = [
            "https://example.com/subtitle.srt",
            "https://example.com/subtitle.ass",
            "https://example.com/subtitle.vtt",
            "https://example.com/subtitle?format=srt",
        ]
        
        paths = [downloader._get_cached_path(url) for url in urls]
        
        # Paths should be different for different URLs
        assert len(set(str(p) for p in paths)) == len(urls)
        
        # All should be in cache directory
        assert all(p.parent == downloader._cache_dir for p in paths)


class TestSubtitleDownloadIntegration:
    """Integration tests for subtitle downloading."""

    def test_download_and_verify_format(self) -> None:
        """Test downloading a subtitle and verifying its format."""
        from src.media_manager.models import MediaType
        
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            # Search for subtitles
            results = downloader.search_subtitles(
                title="Test",
                media_type=MediaType.MOVIE,
                language=SubtitleLanguage.ENGLISH,
            )
            
            assert len(results) > 0
            
            # Download first result
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results[0].download_url,
            )
            
            success = downloader.download_subtitle(
                subtitle_info, media_path, subtitle_result=results[0]
            )
            
            assert success
            assert subtitle_info.local_path.exists()
            
            # Verify file content
            content = subtitle_info.local_path.read_text()
            assert len(content) > 0

    def test_multiple_language_downloads(self) -> None:
        """Test downloading subtitles in multiple languages."""
        from src.media_manager.models import MediaType
        
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            languages = [SubtitleLanguage.ENGLISH, SubtitleLanguage.SPANISH, SubtitleLanguage.FRENCH]
            
            for language in languages:
                results = downloader.search_subtitles(
                    title="Test",
                    media_type=MediaType.MOVIE,
                    language=language,
                )
                
                assert len(results) > 0
                
                subtitle_info = SubtitleInfo(
                    language=language,
                    url=results[0].download_url,
                )
                
                success = downloader.download_subtitle(
                    subtitle_info, media_path, subtitle_result=results[0]
                )
                
                assert success
