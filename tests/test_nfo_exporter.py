"""Tests for NFO exporter functionality."""

import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from src.media_manager.models import MatchStatus, MediaMatch, MediaType, VideoMetadata
from src.media_manager.nfo_exporter import NFOExporter


class TestNFOExporter:
    """Test cases for NFOExporter."""

    def test_exporter_initialization(self) -> None:
        """Test NFOExporter initialization."""
        exporter = NFOExporter()
        assert exporter is not None

    def test_export_movie_nfo(self) -> None:
        """Test exporting a movie NFO file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "test_movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Test Movie",
                media_type=MediaType.MOVIE,
                year=2023,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Test Movie",
                matched_year=2023,
                external_id="12345",
                source="tmdb",
                overview="A test movie",
                runtime=120,
                aired_date="2023-01-01",
                cast=["Actor 1", "Actor 2"],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.exists()
            assert nfo_path.name == "test_movie.nfo"
            assert nfo_path.suffix == ".nfo"

    def test_export_episode_nfo(self) -> None:
        """Test exporting a TV episode NFO file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "test_episode.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Test Episode",
                media_type=MediaType.TV,
                season=1,
                episode=1,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Test Episode",
                external_id="54321",
                source="tvdb",
                overview="A test episode",
                runtime=45,
                aired_date="2023-01-15",
                cast=["Actor A", "Actor B"],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.exists()
            assert nfo_path.name == "test_episode.nfo"

    def test_export_nfo_with_subfolder(self) -> None:
        """Test exporting NFO to a target subfolder."""
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
                external_id="111",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match, target_subfolder="metadata")

            assert nfo_path.exists()
            assert nfo_path.parent.name == "metadata"

    def test_export_nfo_custom_path(self) -> None:
        """Test exporting NFO to a custom output path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "media" / "movie.mkv"
            media_file.parent.mkdir(parents=True, exist_ok=True)
            media_file.touch()

            output_path = temp_path / "output"
            output_path.mkdir(parents=True, exist_ok=True)

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
            nfo_path = exporter.export_nfo(match, output_path=output_path)

            assert nfo_path.exists()
            assert nfo_path.parent == output_path

    def test_export_unmatched_nfo_raises_error(self) -> None:
        """Test that exporting unmatched media raises an error."""
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
                status=MatchStatus.PENDING,
            )

            exporter = NFOExporter()
            with pytest.raises(
                ValueError, match="Cannot export NFO for unmatched media"
            ):
                exporter.export_nfo(match)

    def test_nfo_utf8_encoding(self) -> None:
        """Test that NFO files are properly encoded in UTF-8."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Movie with UTF-8",
                media_type=MediaType.MOVIE,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Tëst Möviè with Spëcíål Çhärs",
                overview="Übung macht den Meister",
                cast=["François", "José", "李明"],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            # Read back and verify
            with open(nfo_path, encoding="utf-8") as f:
                content = f.read()
                assert "Tëst Möviè with Spëcíål Çhärs" in content
                assert "Übung macht den Meister" in content
                assert "José" in content
                assert "李明" in content

    def test_generated_xml_valid(self) -> None:
        """Test that generated XML is valid."""
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
                matched_year=2023,
                external_id="123",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            assert exporter.validate_nfo(nfo_path)

    def test_movie_nfo_content(self) -> None:
        """Test that movie NFO contains expected elements."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Movie",
                media_type=MediaType.MOVIE,
                year=2023,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Test Movie",
                matched_year=2023,
                external_id="12345",
                source="tmdb",
                overview="This is a test movie",
                runtime=120,
                aired_date="2023-06-15",
                cast=["John Doe", "Jane Smith"],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()

            assert root.tag == "movie"
            assert root.find("title").text == "Test Movie"
            assert root.find("originaltitle").text == "Test Movie"
            assert root.find("year").text == "2023"
            assert root.find("runtime").text == "120"
            assert root.find("plot").text == "This is a test movie"
            assert root.find("aired").text == "2023-06-15"
            assert root.find("tmdbid").text == "12345"

            actors = root.findall("actor")
            assert len(actors) == 2
            assert actors[0].find("name").text == "John Doe"
            assert actors[1].find("name").text == "Jane Smith"

    def test_episode_nfo_content(self) -> None:
        """Test that episode NFO contains expected elements."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "episode.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Episode",
                media_type=MediaType.TV,
                season=2,
                episode=5,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Test Episode",
                external_id="54321",
                source="tvdb",
                overview="This is a test episode",
                runtime=45,
                aired_date="2023-03-20",
                cast=["Actor A"],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()

            assert root.tag == "episodedetails"
            assert root.find("title").text == "Test Episode"
            assert root.find("season").text == "2"
            assert root.find("episode").text == "5"
            assert root.find("runtime").text == "45"
            assert root.find("plot").text == "This is a test episode"
            assert root.find("aired").text == "2023-03-20"
            assert root.find("tvdbid").text == "54321"

            actors = root.findall("actor")
            assert len(actors) == 1
            assert actors[0].find("name").text == "Actor A"

    def test_nfo_with_missing_optional_fields(self) -> None:
        """Test NFO generation with minimal metadata."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Minimal Movie",
                media_type=MediaType.MOVIE,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Minimal Movie",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            assert exporter.validate_nfo(nfo_path)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            assert root.find("title").text == "Minimal Movie"

    def test_validate_nfo_invalid_file(self) -> None:
        """Test validation of invalid XML file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            invalid_nfo = temp_path / "invalid.nfo"
            invalid_nfo.write_text("This is not valid XML <unclosed>")

            exporter = NFOExporter()
            assert not exporter.validate_nfo(invalid_nfo)

    def test_read_nfo_file(self) -> None:
        """Test reading and parsing an NFO file."""
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
                matched_year=2023,
                overview="A test movie",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            nfo_dict = exporter.read_nfo(nfo_path)
            assert nfo_dict["_tag"] == "movie"
            assert nfo_dict["title"]["_text"] == "Test Movie"


class TestNFOExporterWithMultipleCast:
    """Test NFO export with various cast configurations."""

    def test_empty_cast(self) -> None:
        """Test NFO with empty cast list."""
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
                cast=[],
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            actors = root.findall("actor")
            assert len(actors) == 0

    def test_large_cast(self) -> None:
        """Test NFO with many cast members."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mkv"
            media_file.touch()

            cast = [f"Actor {i}" for i in range(50)]

            metadata = VideoMetadata(
                path=media_file,
                title="Movie",
                media_type=MediaType.MOVIE,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Movie",
                cast=cast,
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            actors = root.findall("actor")
            assert len(actors) == 50


class TestNFOExporterSourceHandling:
    """Test NFO export with different source IDs."""

    def test_tmdb_id(self) -> None:
        """Test NFO with TMDB source."""
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
                external_id="123456",
                source="tmdb",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            assert root.find("tmdbid").text == "123456"

    def test_tvdb_id(self) -> None:
        """Test NFO with TVDB source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "episode.mkv"
            media_file.touch()

            metadata = VideoMetadata(
                path=media_file,
                title="Episode",
                media_type=MediaType.TV,
            )

            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.MATCHED,
                matched_title="Episode",
                external_id="654321",
                source="tvdb",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            assert root.find("tvdbid").text == "654321"

    def test_generic_id(self) -> None:
        """Test NFO with generic source."""
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
                external_id="999",
                source="other",
            )

            exporter = NFOExporter()
            nfo_path = exporter.export_nfo(match)

            tree = ET.parse(nfo_path)
            root = tree.getroot()
            assert root.find("id").text == "999"


class TestNFOExporterFilenameHandling:
    """Test NFO filename generation with various media files."""

    def test_mkv_file(self) -> None:
        """Test NFO generated for MKV file."""
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
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.name == "movie.nfo"

    def test_mp4_file(self) -> None:
        """Test NFO generated for MP4 file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "movie.mp4"
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
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.name == "movie.nfo"

    def test_complex_filename(self) -> None:
        """Test NFO with complex media filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            media_file = temp_path / "Movie.2023.1080p.BluRay.mkv"
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
            nfo_path = exporter.export_nfo(match)

            assert nfo_path.name == "Movie.2023.1080p.BluRay.nfo"
