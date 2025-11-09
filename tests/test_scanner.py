"""Tests for the media scanner."""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.media_manager.models import MediaType
from src.media_manager.scanner import MediaScanner


class TestMediaScanner:
    """Test cases for MediaScanner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scanner = MediaScanner()

    def test_detect_tv_episode_s01e02_format(self):
        """Test detecting TV episode in S01E02 format."""
        file_path = Path("Test.Show.S01E02.1080p.mkv")
        metadata = self.scanner.parse_filename(file_path)

        assert metadata is not None
        assert metadata.title == "Test Show"
        assert metadata.media_type == MediaType.TV_EPISODE
        assert metadata.season == 1
        assert metadata.episode == 2

    def test_detect_tv_episode_1x02_format(self):
        """Test detecting TV episode in 1x02 format."""
        file_path = Path("Test.Show.1x02.HDTV.mkv")
        metadata = self.scanner.parse_filename(file_path)

        assert metadata is not None
        assert metadata.title == "Test Show"
        assert metadata.media_type == MediaType.TV_EPISODE
        assert metadata.season == 1
        assert metadata.episode == 2

    def test_detect_tv_episode_season_episode_format(self):
        """Test detecting TV episode in 'Season 1 Episode 2' format."""
        file_path = Path("Test.Show.Season.1.Episode.2.mkv")
        metadata = self.scanner.parse_filename(file_path)

        assert metadata is not None
        assert metadata.title == "Test Show"
        assert metadata.media_type == MediaType.TV_EPISODE
        assert metadata.season == 1
        assert metadata.episode == 2

    def test_detect_movie_with_year(self):
        """Test detecting movie with year."""
        file_path = Path("Test.Movie.2023.1080p.mkv")
        metadata = self.scanner.parse_filename(file_path)

        assert metadata is not None
        assert metadata.title == "Test Movie"
        assert metadata.media_type == MediaType.MOVIE
        assert metadata.year == 2023

    def test_detect_movie_without_year(self):
        """Test detecting movie without year."""
        file_path = Path("Test.Movie.mkv")
        metadata = self.scanner.parse_filename(file_path)

        assert metadata is not None
        assert metadata.title == "Test Movie"
        assert metadata.media_type == MediaType.MOVIE
        assert metadata.year is None

    def test_clean_title_removes_quality_indicators(self):
        """Test title cleaning removes quality indicators."""
        dirty_title = "Test Movie 1080p BluRay x264"
        clean_title = self.scanner._clean_title(dirty_title)

        assert "1080p" not in clean_title
        assert "BluRay" not in clean_title
        assert "x264" not in clean_title
        assert "Test Movie" in clean_title

    def test_clean_title_removes_years(self):
        """Test title cleaning removes years."""
        dirty_title = "Test Movie 2023"
        clean_title = self.scanner._clean_title(dirty_title)

        assert "2023" not in clean_title
        assert "Test Movie" in clean_title

    def test_clean_title_handles_separators(self):
        """Test title cleaning handles various separators."""
        dirty_title = "Test.Movie.With.Dots"
        clean_title = self.scanner._clean_title(dirty_title)

        assert clean_title == "Test Movie With Dots"

    def test_extract_year_valid_range(self):
        """Test extracting year in valid range."""
        assert self.scanner._extract_year("Movie 2023") == 2023
        assert self.scanner._extract_year("Movie 1999") == 1999
        assert self.scanner._extract_year("Movie 2099") == 2099

    def test_extract_year_invalid_range(self):
        """Test extracting year in invalid range."""
        assert self.scanner._extract_year("Movie 1800") is None
        assert self.scanner._extract_year("Movie 3000") is None

    def test_scan_directory_with_temp_files(self):
        """Test scanning directory with temporary files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "movie1.mkv").touch()
            (temp_path / "show.s01e01.mkv").touch()
            (temp_path / "not_video.txt").touch()

            # Create subdirectory with video
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "movie2.mp4").touch()

            # Scan directory
            media_files = self.scanner.scan_directory(temp_path)

            assert len(media_files) == 3  # Should find 3 video files

            titles = [m.title for m in media_files]
            assert "movie1" in titles
            assert "show" in titles
            assert "movie2" in titles

    def test_scan_directory_non_recursive(self):
        """Test scanning directory non-recursively."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "movie1.mkv").touch()

            # Create subdirectory with video
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "movie2.mp4").touch()

            # Scan directory non-recursively
            media_files = self.scanner.scan_directory(temp_path, recursive=False)

            assert len(media_files) == 1  # Should only find 1 video file
            assert media_files[0].title == "movie1"

    def test_should_ignore_hidden_files(self):
        """Test ignoring hidden files."""
        hidden_file = Path(".hidden_movie.mkv")
        assert self.scanner._should_ignore_file(hidden_file)

    def test_should_ignore_ignored_directories(self):
        """Test ignoring files in ignored directories."""
        ignored_file = Path("node_modules/movie.mkv")
        assert self.scanner._should_ignore_file(ignored_file)

    def test_video_extensions(self):
        """Test video extension detection."""
        valid_extensions = [".mkv", ".mp4", ".avi", ".mov"]

        for ext in valid_extensions:
            assert ext in self.scanner.video_extensions

    def test_parse_filename_with_complex_naming(self):
        """Test parsing filename with complex naming pattern."""
        file_path = Path("My.Awesome.Show.S02E05.2023.1080p.WEB-DL.x264-GROUP.mkv")
        metadata = self.scanner.parse_filename(file_path)

        assert metadata is not None
        assert metadata.title == "My Awesome Show"
        assert metadata.media_type == MediaType.TV_EPISODE
        assert metadata.season == 2
        assert metadata.episode == 5
        assert metadata.year == 2023

    def test_scan_nonexistent_directory(self):
        """Test scanning non-existent directory."""
        nonexistent = Path("/nonexistent/directory")
        media_files = self.scanner.scan_directory(nonexistent)

        assert media_files == []

    def test_scan_multiple_directories(self):
        """Test scanning multiple directories."""
        with TemporaryDirectory() as temp1, TemporaryDirectory() as temp2:
            temp1_path = Path(temp1)
            temp2_path = Path(temp2)

            # Create test files
            (temp1_path / "movie1.mkv").touch()
            (temp2_path / "movie2.mkv").touch()

            # Scan both directories
            media_files = self.scanner.scan_multiple_directories(
                [temp1_path, temp2_path]
            )

            assert len(media_files) == 2
            titles = [m.title for m in media_files]
            assert "movie1" in titles
            assert "movie2" in titles
