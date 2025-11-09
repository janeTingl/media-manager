"""Tests for the filesystem scanner and filename parsing."""

from __future__ import annotations

from pathlib import Path

from media_manager.models import MediaType
from media_manager.scanner import ScanConfig, Scanner


def _touch_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestScanner:
    """Tests for the Scanner class."""

    def test_scanner_detects_movies_and_tv(self, tmp_path: Path) -> None:
        library = tmp_path / "library"

        _touch_file(library / "Movies" / "The.Matrix.1999.1080p.mkv")
        _touch_file(library / "Movies" / "Avatar (2009).mp4")
        _touch_file(library / "TV" / "Breaking.Bad.S01E01.720p.mkv")
        _touch_file(library / "TV" / "The.Office.US.2x03.mkv")
        _touch_file(
            library
            / "TV"
            / "Strange.Show.Season.3.Episode.5.WEBRip.mp4"
        )
        _touch_file(library / "node_modules" / "ignore_me.mkv")
        _touch_file(library / "Extras" / "note.txt")

        scanner = Scanner()
        config = ScanConfig(root_paths=[library])
        results = scanner.scan(config)

        assert len(results) == 5

        metadata_by_name = {metadata.path.name: metadata for metadata in results}

        matrix = metadata_by_name[
            "The.Matrix.1999.1080p.mkv"
        ]
        assert matrix.media_type is MediaType.MOVIE
        assert matrix.title == "The Matrix"
        assert matrix.year == 1999
        assert matrix.season is None
        assert matrix.episode is None

        avatar = metadata_by_name[
            "Avatar (2009).mp4"
        ]
        assert avatar.media_type is MediaType.MOVIE
        assert avatar.title == "Avatar"
        assert avatar.year == 2009

        breaking_bad = metadata_by_name[
            "Breaking.Bad.S01E01.720p.mkv"
        ]
        assert breaking_bad.media_type is MediaType.TV
        assert breaking_bad.title == "Breaking Bad"
        assert breaking_bad.season == 1
        assert breaking_bad.episode == 1

        office = metadata_by_name[
            "The.Office.US.2x03.mkv"
        ]
        assert office.media_type is MediaType.TV
        assert office.title == "The Office US"
        assert office.season == 2
        assert office.episode == 3

        strange_show = metadata_by_name[
            "Strange.Show.Season.3.Episode.5.WEBRip.mp4"
        ]
        assert strange_show.media_type is MediaType.TV
        assert strange_show.title == "Strange Show"
        assert strange_show.season == 3
        assert strange_show.episode == 5

    def test_scanner_respects_ignored_extensions(self, tmp_path: Path) -> None:
        _touch_file(tmp_path / "movie.mkv")
        _touch_file(tmp_path / "episode.mp4")

        scanner = Scanner()
        config = ScanConfig(root_paths=[tmp_path], ignored_extensions=[".mkv"])
        results = scanner.scan(config)

        assert len(results) == 1
        assert results[0].path.name == "episode.mp4"

    def test_scanner_handles_missing_roots(self, tmp_path: Path) -> None:
        missing_root = tmp_path / "does_not_exist"
        existing_root = tmp_path / "existing"
        _touch_file(existing_root / "Movie.Title.2020.mkv")

        scanner = Scanner()
        config = ScanConfig(root_paths=[missing_root, existing_root])
        results = list(scanner.iter_video_files(config))

        assert len(results) == 1
        assert results[0].name == "Movie.Title.2020.mkv"
