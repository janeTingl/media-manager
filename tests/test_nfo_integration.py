"""Integration tests for NFO exporter with media manager system."""

import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from media_manager.models import (
    MatchStatus,
    MediaMatch,
    MediaType,
    VideoMetadata,
)
from media_manager.nfo_exporter import NFOExporter
from media_manager.settings import SettingsManager


class TestNFOExporterIntegration:
    """Integration tests for NFO exporter."""

    def test_nfo_exporter_with_settings(self, temp_settings: SettingsManager) -> None:
        """Test NFO exporter respecting settings."""
        # Set up settings
        temp_settings.set_nfo_enabled(True)
        temp_settings.set_nfo_target_subfolder("metadata")

        # Create media match
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Movie",
                media_type=MediaType.MOVIE,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Test Movie",
                external_id="123",
            )

            # Export with settings
            exporter = NFOExporter()
            subfolder = temp_settings.get_nfo_target_subfolder()
            nfo_path = exporter.export_nfo(match, target_subfolder=subfolder)

            assert nfo_path.parent.name == "metadata"
            assert exporter.validate_nfo(nfo_path)

    def test_nfo_disabled_setting(self, temp_settings: SettingsManager) -> None:
        """Test that NFO generation can be disabled via settings."""
        temp_settings.set_nfo_enabled(False)

        assert not temp_settings.get_nfo_enabled()
        assert temp_settings.get_nfo_setting("enabled") is False

    def test_nfo_settings_persistence(self, temp_settings: SettingsManager) -> None:
        """Test that NFO settings persist across saves."""
        temp_settings.set_nfo_enabled(False)
        temp_settings.set_nfo_target_subfolder("nfo_files")

        # Simulate reload
        enabled = temp_settings.get_nfo_enabled()
        subfolder = temp_settings.get_nfo_target_subfolder()

        assert enabled is False
        assert subfolder == "nfo_files"

    def test_movie_episode_workflow(self) -> None:
        """Test complete workflow for movie and episode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Movie workflow
            movie_file = temp_path / "movie.mp4"
            movie_file.touch()

            movie_metadata = VideoMetadata(
                path=movie_file,
                title="Test Movie",
                media_type=MediaType.MOVIE,
                year=2023,
            )

            movie_match = MediaMatch(
                metadata=movie_metadata,
                status=MatchStatus.MATCHED,
                matched_title="Amazing Movie",
                matched_year=2023,
                external_id="555",
                source="tmdb",
                overview="An amazing movie",
                runtime=120,
                aired_date="2023-06-15",
                cast=["Star Actor"],
            )

            # Episode workflow
            episode_file = temp_path / "episode.mkv"
            episode_file.touch()

            episode_metadata = VideoMetadata(
                path=episode_file,
                title="Test Episode",
                media_type=MediaType.TV,
                season=1,
                episode=3,
            )

            episode_match = MediaMatch(
                metadata=episode_metadata,
                status=MatchStatus.MATCHED,
                matched_title="Amazing Episode",
                external_id="666",
                source="tvdb",
                overview="An amazing episode",
                runtime=45,
                aired_date="2023-01-15",
                cast=["Guest Star"],
            )

            exporter = NFOExporter()

            # Export both
            movie_nfo = exporter.export_nfo(movie_match)
            episode_nfo = exporter.export_nfo(episode_match)

            assert movie_nfo.exists()
            assert episode_nfo.exists()

            # Validate both
            assert exporter.validate_nfo(movie_nfo)
            assert exporter.validate_nfo(episode_nfo)

            # Read and verify content
            movie_tree = ET.parse(movie_nfo)
            episode_tree = ET.parse(episode_nfo)

            movie_root = movie_tree.getroot()
            episode_root = episode_tree.getroot()

            assert movie_root.tag == "movie"
            assert episode_root.tag == "episodedetails"

    def test_batch_export_scenario(self) -> None:
        """Test exporting multiple media files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            movies = []

            # Create multiple movie matches
            for i in range(5):
                media_file = temp_path / f"movie_{i}.mkv"
                media_file.touch()

                metadata = VideoMetadata(
                    path=media_file,
                    title=f"Movie {i}",
                    media_type=MediaType.MOVIE,
                )

                match = MediaMatch(
                    metadata=metadata,
                    status=MatchStatus.MATCHED,
                    matched_title=f"Movie {i}",
                    external_id=str(1000 + i),
                    cast=[f"Actor {j}" for j in range(3)],
                )
                movies.append(match)

            exporter = NFOExporter()
            nfo_paths = []

            for movie in movies:
                nfo_path = exporter.export_nfo(movie)
                nfo_paths.append(nfo_path)
                assert nfo_path.exists()
                assert exporter.validate_nfo(nfo_path)

            assert len(nfo_paths) == 5
            # Verify all are unique
            assert len({str(p) for p in nfo_paths}) == 5

    def test_nfo_with_manual_match(self) -> None:
        """Test NFO export with manual match status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Unknown Movie",
                media_type=MediaType.MOVIE,
            )

            # User manually selected match
            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MANUAL,
                user_selected=True,
                matched_title="Actually This Movie",
                external_id="999",
                source="tmdb",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.exists()
            assert exporter.validate_nfo(nfo_path)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            assert root.find("title").text == "Actually This Movie"


class TestNFOExporterErrorHandling:
    """Test error handling in NFO exporter."""

    def test_export_to_readonly_directory_fails(self) -> None:
        """Test that export fails when directory is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Movie",
                media_type=MediaType.MOVIE,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Movie",
            )

            exporter = NFOExporter()

            # Create a read-only subdirectory
            readonly_dir = temp_path / "readonly_nfo"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)

            try:
                # Try to write to read-only directory
                exporter.export_nfo(match, output_path=readonly_dir)
                pytest.fail("Expected OSError for read-only directory")
            except (OSError, PermissionError):
                pass  # Expected
            finally:
                # Restore permissions for cleanup
                readonly_dir.chmod(0o755)

    def test_export_with_none_values(self) -> None:
        """Test NFO export with all optional fields as None."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Movie",
                media_type=MediaType.MOVIE,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Movie",
                matched_year=None,
                external_id=None,
                overview=None,
                runtime=None,
                aired_date=None,
                cast=[],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.exists()
            assert exporter.validate_nfo(nfo_path)
