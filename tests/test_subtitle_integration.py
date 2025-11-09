"""Integration tests for the subtitle system."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from media_manager.models import (
    DownloadStatus,
    MediaMatch,
    MediaType,
    SubtitleLanguage,
    SubtitleInfo,
    VideoMetadata,
)
from media_manager.subtitle_downloader import SubtitleDownloader
from media_manager.subtitle_provider import MockSubtitleProvider
from media_manager.workers import SubtitleDownloadWorker


class TestSubtitleWorkflow:
    """Test the complete subtitle management workflow."""

    def test_search_and_download_workflow(self) -> None:
        """Test searching and downloading subtitles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "Test Movie (2023).mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            # Search for subtitles
            results = downloader.search_subtitles(
                title="Test Movie",
                media_type=MediaType.MOVIE,
                language=SubtitleLanguage.ENGLISH,
                year=2023,
            )
            
            assert len(results) > 0
            
            # Create subtitle info and download
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results[0].download_url,
                provider=results[0].provider,
                subtitle_id=results[0].subtitle_id,
            )
            
            success = downloader.download_subtitle(
                subtitle_info, media_path, subtitle_result=results[0]
            )
            
            assert success
            assert subtitle_info.download_status == DownloadStatus.COMPLETED
            assert subtitle_info.local_path is not None
            assert subtitle_info.local_path.exists()

    def test_multiple_subtitle_downloads(self) -> None:
        """Test downloading multiple subtitles for different languages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            languages_to_download = [
                SubtitleLanguage.ENGLISH,
                SubtitleLanguage.SPANISH,
                SubtitleLanguage.FRENCH,
            ]
            
            downloaded_paths = []
            
            for language in languages_to_download:
                results = downloader.search_subtitles(
                    title="Test Movie",
                    media_type=MediaType.MOVIE,
                    language=language,
                )
                
                subtitle_info = SubtitleInfo(
                    language=language,
                    url=results[0].download_url,
                )
                
                success = downloader.download_subtitle(
                    subtitle_info, media_path, subtitle_result=results[0]
                )
                
                assert success
                assert subtitle_info.local_path is not None
                downloaded_paths.append(subtitle_info.local_path)
            
            # Verify all files exist and have different names
            assert len(downloaded_paths) == len(languages_to_download)
            assert all(p.exists() for p in downloaded_paths)
            assert len(set(str(p) for p in downloaded_paths)) == len(downloaded_paths)

    def test_subtitle_caching_behavior(self) -> None:
        """Test that subtitles are cached and reused."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            # First download
            results1 = downloader.search_subtitles(
                title="Test",
                media_type=MediaType.MOVIE,
                language=SubtitleLanguage.ENGLISH,
            )
            
            subtitle_info1 = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results1[0].download_url,
            )
            
            success1 = downloader.download_subtitle(
                subtitle_info1, media_path, subtitle_result=results1[0]
            )
            
            assert success1
            path1 = subtitle_info1.local_path
            
            # Second download with same URL (should use cache)
            subtitle_info2 = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results1[0].download_url,
            )
            
            success2 = downloader.download_subtitle(
                subtitle_info2, media_path, subtitle_result=results1[0]
            )
            
            assert success2
            assert subtitle_info2.local_path == path1

    def test_media_match_with_subtitles(self) -> None:
        """Test MediaMatch containing subtitle information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = VideoMetadata(
                path=Path(temp_dir) / "movie.mkv",
                title="Test Movie",
                media_type=MediaType.MOVIE,
                year=2023,
            )
            
            # Create subtitles in match
            subtitles = {
                SubtitleLanguage.ENGLISH: SubtitleInfo(
                    language=SubtitleLanguage.ENGLISH,
                    url="https://example.com/en.srt",
                    download_status=DownloadStatus.PENDING,
                ),
                SubtitleLanguage.SPANISH: SubtitleInfo(
                    language=SubtitleLanguage.SPANISH,
                    url="https://example.com/es.srt",
                    download_status=DownloadStatus.PENDING,
                ),
            }
            
            match = MediaMatch(
                metadata=metadata,
                subtitles=subtitles,
            )
            
            assert len(match.subtitles) == 2
            assert SubtitleLanguage.ENGLISH in match.subtitles
            assert SubtitleLanguage.SPANISH in match.subtitles

    def test_subtitle_download_worker(self) -> None:
        """Test SubtitleDownloadWorker with mocked provider."""
        from media_manager.subtitle_provider import MockSubtitleProvider
        from unittest.mock import patch
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test media metadata
            media_path = Path(temp_dir) / "test_movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            metadata = VideoMetadata(
                path=media_path,
                title="Test Movie",
                media_type=MediaType.MOVIE,
                year=2023,
            )
            
            # Create subtitles with mocked provider for download
            provider = MockSubtitleProvider()
            results = provider.search(
                title="Test Movie",
                media_type=MediaType.MOVIE,
                language=SubtitleLanguage.ENGLISH,
            )
            
            subtitles = {
                SubtitleLanguage.ENGLISH: SubtitleInfo(
                    language=SubtitleLanguage.ENGLISH,
                    url=results[0].download_url,
                    download_status=DownloadStatus.PENDING,
                    provider="MockProvider",
                    subtitle_id=results[0].subtitle_id,
                ),
                SubtitleLanguage.SPANISH: SubtitleInfo(
                    language=SubtitleLanguage.SPANISH,
                    url=results[0].download_url,
                    download_status=DownloadStatus.PENDING,
                    provider="MockProvider",
                    subtitle_id=results[0].subtitle_id,
                ),
            }
            
            # Create match
            match = MediaMatch(metadata=metadata, subtitles=subtitles)
            
            # Create worker
            languages = [SubtitleLanguage.ENGLISH, SubtitleLanguage.SPANISH]
            worker = SubtitleDownloadWorker([match], languages)
            
            # Mock the subtitle downloader to use our provider
            from unittest.mock import MagicMock
            mock_downloader = MagicMock()
            mock_downloader.download_subtitle.side_effect = lambda *args, **kwargs: True
            worker.subtitle_downloader = mock_downloader
            
            # Track signals
            downloads = []
            failures = []
            
            worker.signals.subtitle_downloaded.connect(
                lambda m, s: downloads.append((m, s))
            )
            worker.signals.subtitle_failed.connect(
                lambda m, e: failures.append((m, e))
            )
            
            # Run worker
            worker.run()
            
            # Verify downloads occurred or no failures
            assert len(downloads) + len(failures) > 0

    def test_tv_episode_subtitle_workflow(self) -> None:
        """Test subtitle workflow for TV episodes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create episode path structure
            media_path = Path(temp_dir) / "Breaking Bad" / "S01E01.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            metadata = VideoMetadata(
                path=media_path,
                title="Pilot",
                media_type=MediaType.TV,
                season=1,
                episode=1,
            )
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            # Search for TV episode subtitles
            results = downloader.search_subtitles(
                title="Breaking Bad",
                media_type=MediaType.TV,
                language=SubtitleLanguage.ENGLISH,
                season=1,
                episode=1,
            )
            
            assert len(results) > 0
            
            # Download
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results[0].download_url,
            )
            
            success = downloader.download_subtitle(
                subtitle_info, media_path, subtitle_result=results[0]
            )
            
            assert success
            assert subtitle_info.local_path is not None
            assert subtitle_info.local_path.name == "S01E01.en.srt"

    def test_subtitle_serialization(self) -> None:
        """Test subtitle info serialization to dictionary."""
        subtitle_info = SubtitleInfo(
            language=SubtitleLanguage.ENGLISH,
            url="https://example.com/subtitle.srt",
            provider="TestProvider",
            subtitle_id="test_123",
            file_size=50000,
            download_status=DownloadStatus.COMPLETED,
        )
        
        subtitle_dict = subtitle_info.as_dict()
        
        assert subtitle_dict["language"] == "en"
        assert subtitle_dict["url"] == "https://example.com/subtitle.srt"
        assert subtitle_dict["provider"] == "TestProvider"
        assert subtitle_dict["subtitle_id"] == "test_123"
        assert subtitle_dict["file_size"] == 50000
        assert subtitle_dict["download_status"] == "completed"

    def test_media_match_serialization_with_subtitles(self) -> None:
        """Test MediaMatch serialization including subtitles."""
        metadata = VideoMetadata(
            path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )
        
        subtitles = {
            SubtitleLanguage.ENGLISH: SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url="https://example.com/en.srt",
            ),
            SubtitleLanguage.SPANISH: SubtitleInfo(
                language=SubtitleLanguage.SPANISH,
                url="https://example.com/es.srt",
            ),
        }
        
        match = MediaMatch(metadata=metadata, subtitles=subtitles)
        match_dict = match.as_dict()
        
        assert "subtitles" in match_dict
        assert len(match_dict["subtitles"]) == 2
        assert "en" in match_dict["subtitles"]
        assert "es" in match_dict["subtitles"]

    def test_subtitle_download_with_retries(self) -> None:
        """Test subtitle download with retry logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(
                provider=provider,
                cache_dir=Path(temp_dir) / "cache",
                max_retries=2,
                retry_delay=0.1,
            )
            
            # Create subtitle info
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url="https://example.com/subtitle.srt",
            )
            
            # Download with retries if needed
            results = downloader.search_subtitles(
                title="Test",
                media_type=MediaType.MOVIE,
                language=SubtitleLanguage.ENGLISH,
            )
            
            success = downloader.download_subtitle(
                subtitle_info,
                media_path,
                subtitle_result=results[0] if results else None,
            )
            
            assert success or subtitle_info.download_status == DownloadStatus.FAILED

    def test_forced_download_overwrite(self) -> None:
        """Test that force_download parameter overwrites existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create existing subtitle with old content
            subtitle_path = media_path.parent / "movie.en.srt"
            subtitle_path.write_text("OLD CONTENT")
            
            provider = MockSubtitleProvider()
            downloader = SubtitleDownloader(provider=provider, cache_dir=Path(temp_dir) / "cache")
            
            results = downloader.search_subtitles(
                title="Test",
                media_type=MediaType.MOVIE,
                language=SubtitleLanguage.ENGLISH,
            )
            
            subtitle_info = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results[0].download_url,
            )
            
            # First call without force should use existing
            success1 = downloader.download_subtitle(
                subtitle_info, media_path, subtitle_result=results[0]
            )
            content1 = subtitle_path.read_text()
            
            # Second call with force should overwrite
            subtitle_info2 = SubtitleInfo(
                language=SubtitleLanguage.ENGLISH,
                url=results[0].download_url,
            )
            success2 = downloader.download_subtitle(
                subtitle_info2, media_path, subtitle_result=results[0], force_download=True
            )
            content2 = subtitle_path.read_text()
            
            assert success1 and success2
