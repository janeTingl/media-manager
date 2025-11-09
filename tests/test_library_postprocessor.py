"""Tests for the library post-processing module."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_manager.library_postprocessor import (
    ConflictResolution,
    LibraryPostProcessor,
    PostProcessingError,
    PostProcessingOptions,
)
from media_manager.models import MatchStatus, MediaMatch, MediaType, VideoMetadata


def _create_movie_match(path: Path, title: str = "Example Movie", year: int = 2021) -> MediaMatch:
    metadata = VideoMetadata(
        path=path,
        title=title,
        media_type=MediaType.MOVIE,
        year=year,
    )
    return MediaMatch(
        metadata=metadata,
        status=MatchStatus.MATCHED,
        matched_title=title,
        matched_year=year,
    )


def _create_tv_match(path: Path, title: str = "Example Show", season: int = 1, episode: int = 2) -> MediaMatch:
    metadata = VideoMetadata(
        path=path,
        title=title,
        media_type=MediaType.TV,
        season=season,
        episode=episode,
    )
    return MediaMatch(
        metadata=metadata,
        status=MatchStatus.MATCHED,
        matched_title=title,
    )


def test_library_postprocessor_moves_movie(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging" / "nested"
    staging_dir.mkdir(parents=True)
    movie_file = staging_dir / "Example.Movie.2021.mkv"
    movie_file.write_text("content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    match = _create_movie_match(movie_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions(conflict_resolution=ConflictResolution.RENAME)
    summary = processor.process([match], options)

    expected_path = library_root / "Movie" / "Example Movie (2021)" / "Example Movie (2021).mkv"
    assert expected_path.exists()
    assert not movie_file.exists()
    assert match.metadata.path == expected_path
    assert len(summary.processed) == 1
    # Ensure intermediate directories were cleaned up
    assert not staging_dir.exists()


def test_library_postprocessor_dry_run(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    movie_file = staging_dir / "Example.Movie.2021.mkv"
    movie_file.write_text("content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    match = _create_movie_match(movie_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions(dry_run=True)
    summary = processor.process([match], options)

    expected_path = library_root / "Movie" / "Example Movie (2021)" / "Example Movie (2021).mkv"
    assert not expected_path.exists()
    assert movie_file.exists()
    assert match.metadata.path == movie_file
    assert len(summary.processed) == 1
    assert summary.processed[0].action == "planned-move"


def test_library_postprocessor_conflict_skip(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    movie_file = staging_dir / "Example.Movie.2021.mkv"
    movie_file.write_text("content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    existing_path = library_root / "Movie" / "Example Movie (2021)" / "Example Movie (2021).mkv"
    existing_path.parent.mkdir(parents=True)
    existing_path.write_text("existing")

    match = _create_movie_match(movie_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions(conflict_resolution=ConflictResolution.SKIP)
    summary = processor.process([match], options)

    assert movie_file.exists()
    assert existing_path.exists()
    assert len(summary.skipped) == 1
    assert match.metadata.path == movie_file


def test_library_postprocessor_conflict_overwrite(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    movie_file = staging_dir / "Example.Movie.2021.mkv"
    movie_file.write_text("new content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    target_path = library_root / "Movie" / "Example Movie (2021)" / "Example Movie (2021).mkv"
    target_path.parent.mkdir(parents=True)
    target_path.write_text("old content")

    match = _create_movie_match(movie_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions(conflict_resolution=ConflictResolution.OVERWRITE)
    summary = processor.process([match], options)

    assert target_path.exists()
    assert target_path.read_text() == "new content"
    assert not movie_file.exists()
    assert len(summary.processed) == 1
    assert summary.processed[0].target == target_path


def test_library_postprocessor_conflict_rename(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    movie_file = staging_dir / "Example.Movie.2021.mkv"
    movie_file.write_text("content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    base_folder = library_root / "Movie" / "Example Movie (2021)"
    base_folder.mkdir(parents=True)
    existing_path = base_folder / "Example Movie (2021).mkv"
    existing_path.write_text("existing")

    match = _create_movie_match(movie_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions(conflict_resolution=ConflictResolution.RENAME)
    summary = processor.process([match], options)

    assert existing_path.exists()
    assert len(summary.processed) == 1
    new_path = summary.processed[0].target
    assert new_path is not None
    assert new_path != existing_path
    assert new_path.exists()
    assert not movie_file.exists()
    assert "Example Movie (2021)" in new_path.name
    assert "(1)" in new_path.stem


def test_library_postprocessor_copy_mode(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    movie_file = staging_dir / "Example.Movie.2021.mkv"
    movie_file.write_text("content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    match = _create_movie_match(movie_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions(copy_mode=True)
    summary = processor.process([match], options)

    expected_path = library_root / "Movie" / "Example Movie (2021)" / "Example Movie (2021).mkv"
    assert expected_path.exists()
    assert expected_path.read_text() == "content"
    assert movie_file.exists()
    assert match.metadata.path == expected_path
    assert len(summary.processed) == 1
    assert summary.processed[0].action == "copied"


def test_library_postprocessor_tv_episode(tmp_path: Path, temp_settings) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    episode_file = staging_dir / "Example.Show.S01E02.mkv"
    episode_file.write_text("content")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("tv", str(library_root / "TV"))

    match = _create_tv_match(episode_file)

    processor = LibraryPostProcessor(settings=temp_settings)
    options = PostProcessingOptions()
    summary = processor.process([match], options)

    expected_path = library_root / "TV" / "Example Show" / "Season 01" / "Example Show - S01E02.mkv"
    assert expected_path.exists()
    assert not episode_file.exists()
    assert match.metadata.path == expected_path
    assert len(summary.processed) == 1


def test_library_postprocessor_rollback_on_error(tmp_path: Path, temp_settings, monkeypatch) -> None:
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    first_file = staging_dir / "Example.Movie.2021.mkv"
    second_file = staging_dir / "Example.Movie.2022.mkv"
    first_file.write_text("first")
    second_file.write_text("second")

    library_root = tmp_path / "library"
    temp_settings.set_target_folder("movie", str(library_root / "Movie"))

    first_match = _create_movie_match(first_file, year=2021)
    second_match = _create_movie_match(second_file, year=2022)

    processor = LibraryPostProcessor(settings=temp_settings)

    from media_manager import library_postprocessor as lp_module

    original_move = lp_module.shutil.move

    call_count = {"count": 0}

    def failing_move(src, dst, *args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 2:
            raise OSError("Simulated failure")
        return original_move(src, dst, *args, **kwargs)

    monkeypatch.setattr(lp_module.shutil, "move", failing_move)

    options = PostProcessingOptions()

    with pytest.raises(PostProcessingError) as excinfo:
        processor.process([first_match, second_match], options)

    summary = excinfo.value.summary
    assert len(summary.processed) == 0

    # Ensure original files still exist and no target files were left behind
    assert first_file.exists()
    assert second_file.exists()

    expected_first = (
        library_root / "Movie" / "Example Movie (2021)" / "Example Movie (2021).mkv"
    )
    expected_second = (
        library_root / "Movie" / "Example Movie (2022)" / "Example Movie (2022).mkv"
    )
    assert not expected_first.exists()
    assert not expected_second.exists()

