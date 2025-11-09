"""Integration tests for poster download functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from media_manager.models import (
    DownloadStatus,
    MediaMatch,
    PosterInfo,
    PosterType,
    PosterSize,
    VideoMetadata,
)
from media_manager.poster_downloader import PosterDownloader
from media_manager.workers import PosterDownloadWorker


class TestPosterIntegration:
    """Integration tests for poster download workflow."""

    def test_full_poster_download_workflow(self) -> None:
        """Test complete poster download workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test media file
            media_dir = Path(temp_dir) / "media"
            media_dir.mkdir()
            media_file = media_dir / "TestMovie (2023).mkv"
            media_file.write_bytes(b"fake video data")
            
            # Create video metadata
            metadata = VideoMetadata(
                path=media_file,
                title="TestMovie",
                media_type="movie",
                year=2023
            )
            
            # Create poster info
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg",
                size=PosterSize.MEDIUM
            )
            
            # Create media match with poster
            match = MediaMatch(
                metadata=metadata,
                status="matched",
                confidence=0.9,
                matched_title="TestMovie",
                matched_year=2023,
                external_id="test_123",
                source="TestAPI",
                poster_url="https://example.com/poster.jpg",
                posters={PosterType.POSTER: poster_info}
            )
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.headers = {
                'content-type': 'image/jpeg',
                'content-length': '2048'
            }
            image_data = b"fake image data for testing"
            mock_response.read.side_effect = [image_data, b""]
            
            with patch('media_manager.poster_downloader.urlopen') as mock_urlopen:
                mock_urlopen.return_value.__enter__.return_value = mock_response
                
                # Create downloader and worker
                cache_dir = Path(temp_dir) / "cache"
                downloader = PosterDownloader(cache_dir=cache_dir)
                worker = PosterDownloadWorker([match], [PosterType.POSTER])
                worker.poster_downloader = downloader
                
                # Track signals
                downloaded_signals = []
                failed_signals = []
                
                def on_poster_downloaded(match_received, poster_info_received):
                    downloaded_signals.append((match_received, poster_info_received))
                
                def on_poster_failed(match_received, error):
                    failed_signals.append((match_received, error))
                
                worker.signals.poster_downloaded.connect(on_poster_downloaded)
                worker.signals.poster_failed.connect(on_poster_failed)
                
                # Run the worker
                worker.run()
                
                # Verify download
                assert len(downloaded_signals) == 1
                assert len(failed_signals) == 0
                
                downloaded_match, downloaded_poster = downloaded_signals[0]
                assert downloaded_match == match
                assert downloaded_poster.poster_type == PosterType.POSTER
                assert downloaded_poster.download_status == DownloadStatus.COMPLETED
                assert downloaded_poster.local_path is not None
                assert downloaded_poster.local_path.exists()
                assert downloaded_poster.file_size == len(image_data)
                
                # Verify file location
                expected_path = media_dir / "TestMovie (2023)-poster.jpg"
                assert downloaded_poster.local_path == expected_path

    def test_multiple_poster_types_download(self) -> None:
        """Test downloading multiple poster types for one match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test media file
            media_dir = Path(temp_dir) / "media"
            media_dir.mkdir()
            media_file = media_dir / "TestShow S01E01.mkv"
            media_file.write_bytes(b"fake video data")
            
            # Create video metadata
            metadata = VideoMetadata(
                path=media_file,
                title="TestShow",
                media_type="tv",
                year=2023,
                season=1,
                episode=1
            )
            
            # Create multiple poster infos
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg",
                size=PosterSize.MEDIUM
            )
            fanart_info = PosterInfo(
                poster_type=PosterType.FANART,
                url="https://example.com/fanart.jpg",
                size=PosterSize.LARGE
            )
            
            # Create media match with multiple posters
            match = MediaMatch(
                metadata=metadata,
                status="matched",
                confidence=0.9,
                matched_title="TestShow",
                matched_year=2023,
                external_id="test_456",
                source="TestAPI",
                posters={
                    PosterType.POSTER: poster_info,
                    PosterType.FANART: fanart_info
                }
            )
            
            # Mock HTTP responses
            def mock_urlopen_side_effect(request):
                mock_response = Mock()
                if "poster" in request.full_url:
                    mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '1024'}
                    mock_response.read.side_effect = [b"poster data", b""]
                elif "fanart" in request.full_url:
                    mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '2048'}
                    mock_response.read.side_effect = [b"fanart data", b""]
                return mock_response.__enter__.return_value
            
            with patch('media_manager.poster_downloader.urlopen', side_effect=mock_urlopen_side_effect):
                # Create downloader and worker
                cache_dir = Path(temp_dir) / "cache"
                downloader = PosterDownloader(cache_dir=cache_dir)
                worker = PosterDownloadWorker([match], [PosterType.POSTER, PosterType.FANART])
                worker.poster_downloader = downloader
                
                # Track signals
                downloaded_signals = []
                
                def on_poster_downloaded(match_received, poster_info_received):
                    downloaded_signals.append((match_received, poster_info_received))
                
                worker.signals.poster_downloaded.connect(on_poster_downloaded)
                
                # Run the worker
                worker.run()
                
                # Verify both downloads
                assert len(downloaded_signals) == 2
                
                # Check poster
                poster_match, poster_poster = downloaded_signals[0]
                assert poster_poster.poster_type == PosterType.POSTER
                assert poster_poster.download_status == DownloadStatus.COMPLETED
                assert poster_poster.file_size == len(b"poster data")
                
                # Check fanart
                fanart_match, fanart_poster = downloaded_signals[1]
                assert fanart_poster.poster_type == PosterType.FANART
                assert fanart_poster.download_status == DownloadStatus.COMPLETED
                assert fanart_poster.file_size == len(b"fanart data")

    def test_download_with_caching(self) -> None:
        """Test that caching works for repeated downloads."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test media file
            media_dir = Path(temp_dir) / "media"
            media_dir.mkdir()
            media_file = media_dir / "CachedMovie.mkv"
            media_file.write_bytes(b"fake video data")
            
            # Create video metadata and match
            metadata = VideoMetadata(
                path=media_file,
                title="CachedMovie",
                media_type="movie"
            )
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/cached_poster.jpg"
            )
            
            match = MediaMatch(
                metadata=metadata,
                status="matched",
                posters={PosterType.POSTER: poster_info}
            )
            
            # Mock HTTP response for first download
            mock_response = Mock()
            mock_response.headers = {
                'content-type': 'image/jpeg',
                'content-length': '1536'
            }
            image_data = b"cached image data"
            mock_response.read.side_effect = [image_data, b""]
            
            with patch('media_manager.poster_downloader.urlopen') as mock_urlopen:
                mock_urlopen.return_value.__enter__.return_value = mock_response
                
                # Create downloader
                cache_dir = Path(temp_dir) / "cache"
                downloader = PosterDownloader(cache_dir=cache_dir)
                
                # First download - should hit network
                result1 = downloader.download_poster(poster_info, media_file)
                assert result1
                assert poster_info.download_status == DownloadStatus.COMPLETED
                assert mock_urlopen.call_count == 1
                
                # Reset poster info for second download
                poster_info.download_status = DownloadStatus.PENDING
                poster_info.local_path = None
                
                # Second download - should use cache
                result2 = downloader.download_poster(poster_info, media_file)
                assert result2
                assert poster_info.download_status == DownloadStatus.COMPLETED
                assert poster_info.local_path is not None
                assert poster_info.local_path.exists()
                
                # Should not have made another network request
                assert mock_urlopen.call_count == 1

    def test_download_with_retries(self) -> None:
        """Test download retry functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test media file
            media_dir = Path(temp_dir) / "media"
            media_dir.mkdir()
            media_file = media_dir / "RetryMovie.mkv"
            media_file.write_bytes(b"fake video data")
            
            # Create video metadata and match
            metadata = VideoMetadata(
                path=media_file,
                title="RetryMovie",
                media_type="movie"
            )
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/retry_poster.jpg"
            )
            
            match = MediaMatch(
                metadata=metadata,
                status="matched",
                posters={PosterType.POSTER: poster_info}
            )
            
            # Mock HTTP responses - fail twice, succeed on third
            call_count = 0
            def mock_urlopen_side_effect(request):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise Exception(f"Network error {call_count}")
                
                mock_response = Mock()
                mock_response.headers = {
                    'content-type': 'image/jpeg',
                    'content-length': '1024'
                }
                mock_response.read.side_effect = [b"retry image data", b""]
                return mock_response.__enter__.return_value
            
            with patch('media_manager.poster_downloader.urlopen', side_effect=mock_urlopen_side_effect):
                # Create downloader with retries
                cache_dir = Path(temp_dir) / "cache"
                downloader = PosterDownloader(cache_dir=cache_dir, max_retries=3)
                
                with patch('time.sleep'):  # Skip actual sleep
                    result = downloader.download_poster(poster_info, media_file)
                
                assert result
                assert poster_info.download_status == DownloadStatus.COMPLETED
                assert poster_info.retry_count == 2  # Should have retried twice
                assert call_count == 3  # Should have made 3 attempts total

    def test_download_failure_max_retries(self) -> None:
        """Test download failure when max retries are exceeded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup test media file
            media_dir = Path(temp_dir) / "media"
            media_dir.mkdir()
            media_file = media_dir / "FailMovie.mkv"
            media_file.write_bytes(b"fake video data")
            
            # Create video metadata and match
            metadata = VideoMetadata(
                path=media_file,
                title="FailMovie",
                media_type="movie"
            )
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/fail_poster.jpg"
            )
            
            match = MediaMatch(
                metadata=metadata,
                status="matched",
                posters={PosterType.POSTER: poster_info}
            )
            
            # Mock HTTP response that always fails
            def mock_urlopen_side_effect(request):
                raise Exception("Persistent network error")
            
            with patch('media_manager.poster_downloader.urlopen', side_effect=mock_urlopen_side_effect):
                # Create downloader with limited retries
                cache_dir = Path(temp_dir) / "cache"
                downloader = PosterDownloader(cache_dir=cache_dir, max_retries=2)
                
                with patch('time.sleep'):  # Skip actual sleep
                    result = downloader.download_poster(poster_info, media_file)
                
                assert not result
                assert poster_info.download_status == DownloadStatus.FAILED
                assert poster_info.retry_count == 2
                assert "Persistent network error" in poster_info.error_message

    def test_worker_progress_tracking(self) -> None:
        """Test that worker correctly tracks download progress."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple matches
            matches = []
            for i in range(3):
                media_file = Path(temp_dir) / f"Movie{i}.mkv"
                media_file.write_bytes(b"fake video data")
                
                metadata = VideoMetadata(
                    path=media_file,
                    title=f"Movie{i}",
                    media_type="movie"
                )
                
                poster_info = PosterInfo(
                    poster_type=PosterType.POSTER,
                    url=f"https://example.com/poster{i}.jpg"
                )
                
                match = MediaMatch(
                    metadata=metadata,
                    status="matched",
                    posters={PosterType.POSTER: poster_info}
                )
                matches.append(match)
            
            # Mock HTTP responses
            def mock_urlopen_side_effect(request):
                mock_response = Mock()
                mock_response.headers = {'content-type': 'image/jpeg', 'content-length': '1024'}
                mock_response.read.side_effect = [b"image data", b""]
                return mock_response.__enter__.return_value
            
            with patch('media_manager.poster_downloader.urlopen', side_effect=mock_urlopen_side_effect):
                # Create worker
                cache_dir = Path(temp_dir) / "cache"
                downloader = PosterDownloader(cache_dir=cache_dir)
                worker = PosterDownloadWorker(matches, [PosterType.POSTER])
                worker.poster_downloader = downloader
                
                # Track progress signals
                progress_signals = []
                
                def on_progress(current, total):
                    progress_signals.append((current, total))
                
                worker.signals.progress.connect(on_progress)
                
                # Run the worker
                worker.run()
                
                # Verify progress tracking
                assert len(progress_signals) == 3
                assert progress_signals[0] == (1, 3)  # First poster
                assert progress_signals[1] == (2, 3)  # Second poster
                assert progress_signals[2] == (3, 3)  # Third poster (complete)