"""Tests for the renaming engine."""

from pathlib import Path

import pytest

from src.media_manager.models import MediaType, VideoMetadata
from src.media_manager.renaming_engine import RenamingEngine


class TestRenamingEngine:
    """Test cases for RenamingEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RenamingEngine()

    def test_render_movie_template(self):
        """Test rendering movie template."""
        metadata = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        template = "Movies/{title} ({year})/{title} ({year}){extension}"
        result = self.engine.render_template(template, metadata)

        expected = Path("Movies/Test Movie (2023)/Test Movie (2023).mkv")
        assert result == expected

    def test_render_tv_template(self):
        """Test rendering TV episode template."""
        metadata = VideoMetadata(
            file_path=Path("/test/episode.mkv"),
            title="Test Show",
            media_type=MediaType.TV_EPISODE,
            year=2023,
            season=1,
            episode=2,
        )

        template = "TV/{title}/Season {season02}/{title} - {s00e00}{extension}"
        result = self.engine.render_template(template, metadata)

        expected = Path("TV/Test Show/Season 01/Test Show - S01E02.mkv")
        assert result == expected

    def test_render_tv_template_with_xee_format(self):
        """Test rendering TV template with xEE format."""
        metadata = VideoMetadata(
            file_path=Path("/test/episode.mkv"),
            title="Test Show",
            media_type=MediaType.TV_EPISODE,
            season=2,
            episode=5,
        )

        template = "TV/{title}/Season {season02}/{title} - {sxee}{extension}"
        result = self.engine.render_template(template, metadata)

        expected = Path("TV/Test Show/Season 02/Test Show - 2x5.mkv")
        assert result == expected

    def test_render_template_with_base_dir(self):
        """Test rendering template with base directory."""
        metadata = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        template = "Movies/{title} ({year})/{title} ({year}){extension}"
        base_dir = Path("/media")
        result = self.engine.render_template(template, metadata, base_dir)

        expected = Path("/media/Movies/Test Movie (2023)/Test Movie (2023).mkv")
        assert result == expected

    def test_clean_path_removes_invalid_chars(self):
        """Test path cleaning removes invalid characters."""
        dirty_path = "Movies/<>:Movie|?* (2023)/Movie: (2023).mkv"
        cleaned = self.engine._clean_path(dirty_path)

        assert "<" not in cleaned
        assert ">" not in cleaned
        assert ":" not in cleaned
        assert "|" not in cleaned
        assert "?" not in cleaned
        assert "*" not in cleaned

    def test_clean_path_handles_empty_segments(self):
        """Test path cleaning handles empty segments."""
        dirty_path = "Movies//Movie///(2023)//.mkv"
        cleaned = self.engine._clean_path(dirty_path)

        assert "//" not in cleaned
        assert cleaned == "Movies/Movie/(2023)/.mkv"

    def test_render_template_invalid_placeholder(self):
        """Test rendering template with invalid placeholder."""
        metadata = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        template = "Movies/{invalid_placeholder}/{title}{extension}"

        with pytest.raises(ValueError, match="Invalid placeholder"):
            self.engine.render_template(template, metadata)

    def test_preview_renames_mixed_media(self):
        """Test previewing renames for mixed media types."""
        movie = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        episode = VideoMetadata(
            file_path=Path("/test/episode.mkv"),
            title="Test Show",
            media_type=MediaType.TV_EPISODE,
            season=1,
            episode=2,
        )

        movie_template = "Movies/{title} ({year})/{title} ({year}){extension}"
        tv_template = "TV/{title}/Season {season02}/{title} - {s00e00}{extension}"

        operations = self.engine.preview_renames(
            [movie, episode], movie_template, tv_template
        )

        assert len(operations) == 2
        assert operations[0].target_path == Path(
            "Movies/Test Movie (2023)/Test Movie (2023).mkv"
        )
        assert operations[1].target_path == Path(
            "TV/Test Show/Season 01/Test Show - S01E02.mkv"
        )

    def test_preview_renames_preserves_extension(self):
        """Test preview preserves original extension when template doesn't specify."""
        metadata = VideoMetadata(
            file_path=Path("/test/movie.MP4"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023,
        )

        template = "Movies/{title} ({year})"  # No extension in template
        operations = self.engine.preview_renames([metadata], template, template)

        assert operations[0].target_path.suffix == ".mp4"

    def test_get_default_templates(self):
        """Test getting default templates."""
        templates = self.engine.get_default_templates()

        assert "movie" in templates
        assert "tv_episode" in templates
        assert "{title}" in templates["movie"]
        assert "{year}" in templates["movie"]
        assert "{season02}" in templates["tv_episode"]
        assert "{s00e00}" in templates["tv_episode"]

    def test_render_template_missing_optional_fields(self):
        """Test rendering template with missing optional fields."""
        metadata = VideoMetadata(
            file_path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            # No year
        )

        template = "Movies/{title}{extension}"
        result = self.engine.render_template(template, metadata)

        expected = Path("Movies/Test Movie.mkv")
        assert result == expected
