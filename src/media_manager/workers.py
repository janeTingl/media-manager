"""Background workers for async operations in the media manager."""

from __future__ import annotations

import time
from typing import List, Optional

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from .logging import get_logger
from .models import (
    MatchStatus,
    MediaMatch,
    SearchRequest,
    SearchResult,
    VideoMetadata,
)


class MatchWorkerSignals(QObject):
    """Signals for the match worker."""

    match_found = Signal(object)  # MediaMatch
    match_failed = Signal(str, str)  # path, error
    progress = Signal(int, int)  # current, total
    finished = Signal()


class MatchWorker(QRunnable):
    """Worker for finding matches in background threads."""

    def __init__(self, metadata_list: List[VideoMetadata]) -> None:
        super().__init__()
        self.metadata_list = metadata_list
        self.signals = MatchWorkerSignals()
        self._logger = get_logger().get_logger(__name__)
        self._should_stop = False

    @Slot()
    def run(self) -> None:
        """Run the matching process."""
        total = len(self.metadata_list)

        for index, metadata in enumerate(self.metadata_list, start=1):
            if self._should_stop:
                break

            try:
                # Simulate network/disk operation
                time.sleep(0.1)  # Simulate processing time

                # Mock matching logic - in real implementation this would call
                # external APIs like TMDB, TVDB, etc.
                match = self._create_mock_match(metadata)

                self.signals.match_found.emit(match)
                self.signals.progress.emit(index, total)

            except Exception as exc:
                error_msg = f"Failed to match {metadata.path}: {exc}"
                self._logger.error(error_msg)
                self.signals.match_failed.emit(str(metadata.path), str(exc))

        self.signals.finished.emit()

    def stop(self) -> None:
        """Stop the worker."""
        self._should_stop = True

    def _create_mock_match(self, metadata: VideoMetadata) -> MediaMatch:
        """Create a mock match for demonstration."""
        # Simulate different confidence levels based on title clarity
        base_confidence = 0.9

        # Reduce confidence for generic titles
        generic_titles = ["movie", "video", "test", "sample"]
        if metadata.title.lower() in generic_titles:
            base_confidence = 0.3
        elif len(metadata.title) < 3:
            base_confidence = 0.5
        elif metadata.year is None:
            base_confidence = 0.7

        # Create mock match data
        match = MediaMatch(
            metadata=metadata,
            status=MatchStatus.MATCHED if base_confidence > 0.6 else MatchStatus.PENDING,
            confidence=base_confidence,
            matched_title=metadata.title,
            matched_year=metadata.year,
            external_id=f"mock_{hash(str(metadata.path)) % 10000}",
            source="MockAPI",
            poster_url=f"https://example.com/poster/{hash(str(metadata.path))}.jpg",
            overview=f"This is a mock overview for {metadata.title}. "
                    f"A great {metadata.media_type.value} from {metadata.year or 'unknown'}."
        )

        return match


class SearchWorkerSignals(QObject):
    """Signals for the search worker."""

    search_completed = Signal(list)  # List[SearchResult]
    search_failed = Signal(str)  # error


class SearchWorker(QRunnable):
    """Worker for searching media matches in background."""

    def __init__(self, request: SearchRequest) -> None:
        super().__init__()
        self.request = request
        self.signals = SearchWorkerSignals()
        self._logger = get_logger().get_logger(__name__)

    @Slot()
    def run(self) -> None:
        """Run the search process."""
        try:
            # Simulate network operation
            time.sleep(0.5)

            # Mock search results
            results = self._create_mock_results()

            self.signals.search_completed.emit(results)

        except Exception as exc:
            error_msg = f"Search failed: {exc}"
            self._logger.error(error_msg)
            self.signals.search_failed.emit(error_msg)

    def _create_mock_results(self) -> List[SearchResult]:
        """Create mock search results."""
        results = []

        # Generate 3-5 mock results
        base_query = self.request.query.lower()

        for i in range(3):
            confidence = 0.9 - (i * 0.1)  # Decreasing confidence
            year = self.request.year or (2020 + i)

            result = SearchResult(
                title=f"{self.request.query.title()} ({i + 1})",
                year=year,
                external_id=f"search_{hash(base_query + str(i)) % 10000}",
                source="MockSearchAPI",
                poster_url=f"https://example.com/search/{hash(base_query + str(i))}.jpg",
                overview=f"This is search result {i + 1} for '{self.request.query}'. "
                        f"A matching {self.request.media_type.value} from {year}.",
                confidence=confidence
            )
            results.append(result)

        return results


class WorkerManager(QObject):
    """Manages background workers and thread pools."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._thread_pool = QThreadPool()
        self._logger = get_logger().get_logger(__name__)
        self._active_workers: List[QRunnable] = []

    def start_match_worker(self, metadata_list: List[VideoMetadata]) -> MatchWorker:
        """Start a match worker and return it."""
        worker = MatchWorker(metadata_list)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        # Connect finished signal to cleanup
        worker.signals.finished.connect(
            lambda: self._cleanup_worker(worker)
        )

        self._logger.info(f"Started match worker for {len(metadata_list)} items")
        return worker

    def start_search_worker(self, request: SearchRequest) -> SearchWorker:
        """Start a search worker and return it."""
        worker = SearchWorker(request)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        # Connect finished signal to cleanup
        worker.signals.search_completed.connect(
            lambda: self._cleanup_worker(worker)
        )
        worker.signals.search_failed.connect(
            lambda: self._cleanup_worker(worker)
        )

        self._logger.info(f"Started search worker for '{request.query}'")
        return worker

    def stop_all_workers(self) -> None:
        """Stop all active workers."""
        for worker in self._active_workers:
            if hasattr(worker, 'stop'):
                worker.stop()

        self._thread_pool.clear()
        self._logger.info("Stopped all background workers")

    def _cleanup_worker(self, worker: QRunnable) -> None:
        """Remove worker from active list when finished."""
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        self._logger.debug(f"Cleaned up worker: {type(worker).__name__}")

    def get_active_count(self) -> int:
        """Get the number of active workers."""
        return len(self._active_workers)
