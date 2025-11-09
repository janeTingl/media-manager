"""Tests for the poster downloader functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest
from requests import Response

from media_manager.models import DownloadStatus, PosterInfo, PosterType, PosterSize
from media_manager.poster_downloader import PosterDownloader


class TestPosterDownloader:
    """Test cases for PosterDownloader."""

    def test_init_default_cache_dir(self) -> None:
        """Test PosterDownloader initialization with default cache directory."""
        downloader = PosterDownloader()
        expected_cache_dir = Path.home() / ".media-manager" / "poster-cache"
        assert downloader._cache_dir == expected_cache_dir

    def test_init_custom_cache_dir(self) -> None:
        """Test PosterDownloader initialization with custom cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_cache = Path(temp_dir) / "custom_cache"
            downloader = PosterDownloader(cache_dir=custom_cache)
            assert downloader._cache_dir == custom_cache
            assert custom_cache.exists()

    def test_get_poster_path_movie_poster(self) -> None:
        """Test getting poster path for movie poster."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "MovieName (2023).mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloader = PosterDownloader()
            poster_path = downloader.get_poster_path(media_path, PosterType.POSTER)
            
            expected = media_path.parent / "MovieName (2023)-poster.jpg"
            assert poster_path == expected

    def test_get_poster_path_tv_fanart(self) -> None:
        """Test getting poster path for TV fanart."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "ShowName" / "S01E01.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            downloader = PosterDownloader()
            poster_path = downloader.get_poster_path(media_path, PosterType.FANART)
            
            expected = media_path.parent / "S01E01-fanart.jpg"
            assert poster_path == expected

    def test_get_poster_path_no_media_dir(self) -> None:
        """Test getting poster path when media directory doesn't exist."""
        media_path = Path("/nonexistent/path/Movie.mkv")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            poster_path = downloader.get_poster_path(media_path, PosterType.POSTER)
            
            # Should fall back to cache directory
            assert poster_path.parent == downloader._cache_dir
            assert poster_path.name == "Movie-poster.jpg"

    def test_download_poster_no_url(self) -> None:
        """Test downloading poster with no URL."""
        poster_info = PosterInfo(poster_type=PosterType.POSTER)
        media_path = Path("/test/movie.mkv")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            result = downloader.download_poster(poster_info, media_path)
            
            assert not result
            assert poster_info.download_status == DownloadStatus.FAILED
            assert poster_info.error_message == "No URL provided"

    def test_download_poster_already_exists(self) -> None:
        """Test downloading poster when file already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create existing poster file
            poster_path = media_path.parent / "movie-poster.jpg"
            poster_path.write_bytes(b"fake image data")
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg"
            )
            
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            result = downloader.download_poster(poster_info, media_path)
            
            assert result
            assert poster_info.download_status == DownloadStatus.COMPLETED
            assert poster_info.local_path == poster_path
            assert poster_info.file_size == len(b"fake image data")

    @patch('media_manager.poster_downloader.urlopen')
    def test_download_poster_success(self, mock_urlopen) -> None:
        """Test successful poster download."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.headers = {
            'content-type': 'image/jpeg',
            'content-length': '1024'
        }
        mock_response.read.side_effect = [b'image data', b'']  # First call returns data, second returns empty
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg"
            )
            
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            result = downloader.download_poster(poster_info, media_path)
            
            assert result
            assert poster_info.download_status == DownloadStatus.COMPLETED
            assert poster_info.local_path is not None
            assert poster_info.local_path.exists()
            assert poster_info.file_size == 1024

    @patch('media_manager.poster_downloader.urlopen')
    def test_download_poster_invalid_content_type(self, mock_urlopen) -> None:
        """Test downloading poster with invalid content type."""
        # Mock HTTP response with HTML content
        mock_response = Mock()
        mock_response.headers = {
            'content-type': 'text/html',
        }
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg"
            )
            
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            result = downloader.download_poster(poster_info, media_path)
            
            assert not result
            assert poster_info.download_status == DownloadStatus.FAILED
            assert "Invalid content type" in poster_info.error_message

    @patch('media_manager.poster_downloader.urlopen')
    def test_download_poster_with_retries(self, mock_urlopen) -> None:
        """Test poster download with retries."""
        # Mock HTTP response that fails first two times, succeeds on third
        mock_response_fail = Mock()
        mock_response_fail.headers = {'content-type': 'image/jpeg'}
        mock_response_fail.read.side_effect = Exception("Network error")
        
        mock_response_success = Mock()
        mock_response_success.headers = {
            'content-type': 'image/jpeg',
            'content-length': '512'
        }
        mock_response_success.read.side_effect = [b'image data', b'']
        
        # First two calls fail, third succeeds
        mock_urlopen.side_effect = [
            mock_response_fail.__enter__.return_value,
            mock_response_fail.__enter__.return_value,
            mock_response_success.__enter__.return_value
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg"
            )
            
            downloader = PosterDownloader(cache_dir=Path(temp_dir), max_retries=2)
            with patch('time.sleep'):  # Skip actual sleep during tests
                result = downloader.download_poster(poster_info, media_path)
            
            assert result
            assert poster_info.download_status == DownloadStatus.COMPLETED
            assert poster_info.retry_count == 2  # Should have retried twice

    @patch('media_manager.poster_downloader.urlopen')
    def test_download_poster_max_retries_exceeded(self, mock_urlopen) -> None:
        """Test poster download when max retries are exceeded."""
        # Mock HTTP response that always fails
        mock_response = Mock()
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.read.side_effect = Exception("Persistent network error")
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            media_path = Path(temp_dir) / "movie.mkv"
            media_path.parent.mkdir(parents=True, exist_ok=True)
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg"
            )
            
            downloader = PosterDownloader(cache_dir=Path(temp_dir), max_retries=2)
            with patch('time.sleep'):  # Skip actual sleep during tests
                result = downloader.download_poster(poster_info, media_path)
            
            assert not result
            assert poster_info.download_status == DownloadStatus.FAILED
            assert poster_info.retry_count == 2

    def test_get_cached_path(self) -> None:
        """Test getting cached path for URL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            
            url = "https://example.com/poster.jpg"
            cached_path = downloader._get_cached_path(url)
            
            assert cached_path.parent == downloader._cache_dir
            assert cached_path.suffix == ".jpg"
            # Should be consistent for the same URL
            cached_path2 = downloader._get_cached_path(url)
            assert cached_path == cached_path2

    def test_get_cached_path_different_extensions(self) -> None:
        """Test getting cached path for URLs with different extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            
            jpg_url = "https://example.com/poster.jpg"
            png_url = "https://example.com/poster.png"
            no_ext_url = "https://example.com/poster"
            
            jpg_path = downloader._get_cached_path(jpg_url)
            png_path = downloader._get_cached_path(png_url)
            no_ext_path = downloader._get_cached_path(no_ext_url)
            
            assert jpg_path.suffix == ".jpg"
            assert png_path.suffix == ".png"
            assert no_ext_path.suffix == ".jpg"  # Default extension

    def test_clear_cache(self) -> None:
        """Test clearing the cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            
            # Create some cache files
            (downloader._cache_dir / "file1.jpg").write_bytes(b"data1")
            (downloader._cache_dir / "file2.png").write_bytes(b"data2")
            
            assert len(list(downloader._cache_dir.iterdir())) == 2
            
            downloader.clear_cache()
            
            assert len(list(downloader._cache_dir.iterdir())) == 0

    def test_get_cache_size(self) -> None:
        """Test getting cache size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            
            # Empty cache
            assert downloader.get_cache_size() == 0
            
            # Add some files
            (downloader._cache_dir / "file1.jpg").write_bytes(b"data1")  # 5 bytes
            (downloader._cache_dir / "file2.jpg").write_bytes(b"data2")  # 5 bytes
            
            assert downloader.get_cache_size() == 10

    def test_is_downloading(self) -> None:
        """Test checking if poster is currently downloading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = PosterDownloader(cache_dir=Path(temp_dir))
            
            poster_info = PosterInfo(
                poster_type=PosterType.POSTER,
                url="https://example.com/poster.jpg"
            )
            
            # Initially not downloading
            assert not downloader.is_downloading(poster_info)
            
            # Add to downloading set
            poster_id = downloader._get_poster_id(poster_info)
            downloader._downloading.add(poster_id)
            
            assert downloader.is_downloading(poster_info)
            
            # Remove from downloading set
            downloader._downloading.remove(poster_id)
            assert not downloader.is_downloading(poster_info)

    def test_get_poster_id(self) -> None:
        """Test generating poster ID."""
        downloader = PosterDownloader()
        
        # With URL
        poster_info_with_url = PosterInfo(
            poster_type=PosterType.POSTER,
            url="https://example.com/poster.jpg"
        )
        poster_id = downloader._get_poster_id(poster_info_with_url)
        assert len(poster_id) == 16  # MD5 hash truncated to 16 chars
        
        # Consistent ID for same URL
        poster_id2 = downloader._get_poster_id(poster_info_with_url)
        assert poster_id == poster_id2
        
        # Different ID for different URL
        poster_info_diff_url = PosterInfo(
            poster_type=PosterType.POSTER,
            url="https://example.com/different.jpg"
        )
        poster_id3 = downloader._get_poster_id(poster_info_diff_url)
        assert poster_id != poster_id3
        
        # Without URL
        poster_info_no_url = PosterInfo(poster_type=PosterType.POSTER)
        poster_id4 = downloader._get_poster_id(poster_info_no_url)
        assert "poster" in poster_id4