"""Tests for the scan engine coordinating filesystem discovery."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtTest import QSignalSpy

from media_manager.models import MediaType, VideoMetadata
from media_manager.scan_engine import ScanEngine
from media_manager.scanner import ScanConfig


def _touch_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestScanEngine:
    """Tests for the ScanEngine class."""

    def test_scan_engine_emits_signals_and_callbacks(
        self, qapp, tmp_path: Path
    ) -> None:
        library = tmp_path / "library"
        _touch_file(library / "Movies" / "Inception.2010.1080p.mkv")
        _touch_file(library / "TV" / "Dark.S02E03.1080p.mkv")

        engine = ScanEngine()
        started_spy = QSignalSpy(engine.scan_started)
        progress_spy = QSignalSpy(engine.scan_progress)
        completed_spy = QSignalSpy(engine.scan_completed)
        error_spy = QSignalSpy(engine.scan_error)
        task_spy = QSignalSpy(engine.enrichment_task_created)

        callbacks: List[VideoMetadata] = []

        def capture_callback(metadata: VideoMetadata) -> None:
            callbacks.append(metadata)

        engine.register_enrichment_callback(capture_callback)

        config = ScanConfig(root_paths=[library])
        results = engine.scan(config)

        assert len(results) == 2
        assert len(started_spy) == 1
        assert started_spy[0][0] == str(library)
        assert len(progress_spy) == len(results)
        assert len(task_spy) == len(results)
        assert len(error_spy) == 0
        assert len(completed_spy) == 1
        completed_payload = completed_spy[0][0]
        assert isinstance(completed_payload, list)
        assert len(completed_payload) == 2
        assert len(callbacks) == 2

        movies = [
            metadata
            for metadata in results
            if metadata.media_type is MediaType.MOVIE
        ]
        shows = [
            metadata
            for metadata in results
            if metadata.media_type is MediaType.TV
        ]

        assert len(movies) == 1
        assert movies[0].title == "Inception"
        assert movies[0].year == 2010

        assert len(shows) == 1
        assert shows[0].title == "Dark"
        assert shows[0].season == 2
        assert shows[0].episode == 3

        copied_results = engine.get_results()
        assert copied_results != []
        assert len(copied_results) == len(results)

        selected = engine.get_results_by_paths([results[0].path.as_posix()])
        assert len(selected) == 1
        assert selected[0].path == results[0].path

        engine.clear_results()
        assert engine.get_results() == []

    def test_scan_engine_handles_missing_root(self, qapp, tmp_path: Path) -> None:
        missing_root = tmp_path / "missing"

        engine = ScanEngine()
        started_spy = QSignalSpy(engine.scan_started)
        error_spy = QSignalSpy(engine.scan_error)
        completed_spy = QSignalSpy(engine.scan_completed)

        config = ScanConfig(root_paths=[missing_root])
        results = engine.scan(config)

        assert results == []
        assert len(started_spy) == 0
        assert len(error_spy) == 1
        assert len(completed_spy) == 1
        assert completed_spy[0][0] == []
