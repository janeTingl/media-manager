"""Match manager for coordinating scan queue and match resolution workflows."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot

from .library_postprocessor import PostProcessingOptions, PostProcessingSummary
from .logging import get_logger
from .models import MediaMatch, PosterType, SearchRequest, SearchResult, VideoMetadata
from .services import get_service_registry
from .workers import WorkerManager


class MatchManager(QObject):
    """Manages the match resolution workflow and coordinates components."""

    # Signals
    matches_updated = Signal(list)  # List[MediaMatch]
    match_selected = Signal(object)  # MediaMatch
    status_changed = Signal(str)  # status message

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)

        # Get worker manager from service registry or create one
        service_registry = get_service_registry()
        if not service_registry.has(WorkerManager):
            service_registry.register(WorkerManager, lambda: WorkerManager())

        self._worker_manager = service_registry.get(WorkerManager)

        self._matches: List[MediaMatch] = []
        self._current_match: Optional[MediaMatch] = None

    def add_metadata(self, metadata_list: List[VideoMetadata]) -> None:
        """Add metadata items to be matched."""
        for metadata in metadata_list:
            match = MediaMatch(metadata=metadata)
            self._matches.append(match)

        self.matches_updated.emit(list(self._matches))
        self.status_changed.emit(f"Added {len(metadata_list)} items to queue")

    def start_matching(self) -> None:
        """Start the matching process for pending items."""
        pending_matches = [m for m in self._matches if m.status.value == "pending"]
        if not pending_matches:
            self.status_changed.emit("No pending items to match")
            return

        # Extract metadata for worker
        pending_metadata = [m.metadata for m in pending_matches]

        # Start match worker
        worker = self._worker_manager.start_match_worker(pending_metadata)

        # Connect signals
        worker.signals.match_found.connect(self._on_match_found)
        worker.signals.match_failed.connect(self._on_match_failed)
        worker.signals.progress.connect(self._on_match_progress)
        worker.signals.finished.connect(self._on_matching_finished)

        self.status_changed.emit(f"Started matching {len(pending_metadata)} items")

    def search_matches(self, request: SearchRequest) -> None:
        """Perform a search for manual matching."""
        worker = self._worker_manager.start_search_worker(request)

        # Connect signals
        worker.signals.search_completed.connect(self._on_search_completed)
        worker.signals.search_failed.connect(self._on_search_failed)

        self.status_changed.emit(f"Searching for '{request.query}'...")

    def update_match(self, match: MediaMatch) -> None:
        """Update a match in the collection."""
        for i, existing_match in enumerate(self._matches):
            if existing_match.metadata.path == match.metadata.path:
                self._matches[i] = match
                break

        self.matches_updated.emit(list(self._matches))

        # Update current match if it's the same one
        if self._current_match and self._current_match.metadata.path == match.metadata.path:
            self._current_match = match
            self.match_selected.emit(match)

    def clear_all(self) -> None:
        """Clear all matches."""
        self._matches.clear()
        self._current_match = None
        self.matches_updated.emit([])
        self.status_changed.emit("Queue cleared")

    def select_match(self, match: MediaMatch) -> None:
        """Select a match for detailed view."""
        self._current_match = match
        self.match_selected.emit(match)

    def get_matches(self) -> List[MediaMatch]:
        """Get all matches."""
        return list(self._matches)

    def get_pending_count(self) -> int:
        """Get the count of pending matches."""
        return len([m for m in self._matches if m.needs_review()])

    def get_matched_count(self) -> int:
        """Get the count of matched items."""
        return len([m for m in self._matches if m.is_matched()])

    def download_posters(self, match: MediaMatch, poster_types: List[PosterType]) -> None:
        """Download posters for a specific match."""
        worker = self._worker_manager.start_poster_download_worker([match], poster_types)
        
        # Connect signals
        worker.signals.poster_downloaded.connect(self._on_poster_downloaded)
        worker.signals.poster_failed.connect(self._on_poster_failed)
        worker.signals.progress.connect(self._on_poster_progress)
        worker.signals.finished.connect(self._on_poster_download_finished)
        
        self.status_changed.emit(f"Downloading posters for {match.metadata.title}...")

    def download_all_posters(self, poster_types: List[PosterType]) -> None:
        """Download posters for all matched items."""
        matched_matches = [m for m in self._matches if m.is_matched()]
        if not matched_matches:
            self.status_changed.emit("No matched items to download posters for")
            return

        worker = self._worker_manager.start_poster_download_worker(matched_matches, poster_types)
        
        # Connect signals
        worker.signals.poster_downloaded.connect(self._on_poster_downloaded)
        worker.signals.poster_failed.connect(self._on_poster_failed)
        worker.signals.progress.connect(self._on_poster_progress)
        worker.signals.finished.connect(self._on_poster_download_finished)
        
        self.status_changed.emit(f"Downloading posters for {len(matched_matches)} items...")

    def finalize_library(self, options: PostProcessingOptions):
        """Finalize matched media items into the organized library."""
        matched_matches = [m for m in self._matches if m.is_matched()]
        if not matched_matches:
            self.status_changed.emit("No matched items ready for finalization")
            return None

        worker = self._worker_manager.start_post_processing_worker(matched_matches, options)

        worker.signals.item_processed.connect(self._on_finalize_processed)
        worker.signals.item_skipped.connect(self._on_finalize_skipped)
        worker.signals.item_failed.connect(self._on_finalize_failed)
        worker.signals.progress.connect(self._on_finalize_progress)
        worker.signals.finished.connect(self._on_finalize_finished)
        worker.signals.error.connect(self._on_finalize_error)

        self.status_changed.emit(f"Starting library finalization for {len(matched_matches)} items")
        return worker

    @Slot(object)
    def _on_match_found(self, match: MediaMatch) -> None:
        """Handle match found from worker."""
        self.update_match(match)

    @Slot(str, str)
    def _on_match_failed(self, path: str, error: str) -> None:
        """Handle match failure from worker."""
        self._logger.error(f"Match failed for {path}: {error}")
        self.status_changed.emit(f"Error matching {path}")

    @Slot(int, int)
    def _on_match_progress(self, current: int, total: int) -> None:
        """Handle matching progress."""
        self.status_changed.emit(f"Matched {current}/{total} items")

    @Slot()
    def _on_matching_finished(self) -> None:
        """Handle matching completion."""
        pending = self.get_pending_count()
        matched = self.get_matched_count()
        total = len(self._matches)

        if pending == 0:
            self.status_changed.emit(f"Matching complete: {matched}/{total} items matched")
        else:
            self.status_changed.emit(f"Matching complete: {matched} matched, {pending} need review")

    @Slot(list)
    def _on_search_completed(self, results: List[SearchResult]) -> None:
        """Handle search completion."""
        # This would be emitted as a signal for the UI to handle
        # For now, we'll just log it
        self.status_changed.emit(f"Found {len(results)} search results")
        # The actual search results would be handled by the UI component
        # that requested the search

    @Slot(str)
    def _on_search_failed(self, error: str) -> None:
        """Handle search failure."""
        self._logger.error(f"Search failed: {error}")
        self.status_changed.emit(f"Search failed: {error}")

    @Slot(object, object)
    def _on_poster_downloaded(self, match: MediaMatch, poster_info) -> None:
        """Handle successful poster download."""
        self.update_match(match)
        self.status_changed.emit(f"Downloaded {poster_info.poster_type.value} for {match.metadata.title}")

    @Slot(object, str)
    def _on_poster_failed(self, match: MediaMatch, error: str) -> None:
        """Handle poster download failure."""
        self.update_match(match)
        self.status_changed.emit(f"Failed to download poster for {match.metadata.title}: {error}")

    @Slot(int, int)
    def _on_poster_progress(self, current: int, total: int) -> None:
        """Handle poster download progress."""
        self.status_changed.emit(f"Downloaded {current}/{total} posters")

    @Slot()
    def _on_poster_download_finished(self) -> None:
        """Handle poster download completion."""
        self.status_changed.emit("Poster download complete")

    @Slot(object, object, object)
    def _on_finalize_processed(self, match: MediaMatch, source, target) -> None:
        """Handle a successfully finalized media item."""
        self.update_match(match)
        self.status_changed.emit(f"Finalized {match.metadata.title}")

    @Slot(object, object, str)
    def _on_finalize_skipped(self, match: MediaMatch, target, reason: str) -> None:
        """Handle a skipped media item during finalization."""
        self.status_changed.emit(f"Skipped {match.metadata.title}: {reason}")

    @Slot(object, str)
    def _on_finalize_failed(self, match: MediaMatch, message: str) -> None:
        """Handle a failed media item during finalization."""
        self.status_changed.emit(f"Failed to finalize {match.metadata.title}: {message}")

    @Slot(int, int)
    def _on_finalize_progress(self, current: int, total: int) -> None:
        """Handle finalization progress updates."""
        self.status_changed.emit(f"Finalizing {current}/{total} items")

    @Slot(object)
    def _on_finalize_finished(self, summary: PostProcessingSummary) -> None:
        """Handle completion of library finalization."""
        processed = len(summary.processed)
        skipped = len(summary.skipped)
        failed = len(summary.failed)
        message = f"Library finalization complete: {processed} processed"
        if skipped:
            message += f", {skipped} skipped"
        if failed:
            message += f", {failed} failed"
        self.status_changed.emit(message)

    @Slot(str)
    def _on_finalize_error(self, message: str) -> None:
        """Handle finalization error notifications."""
        self.status_changed.emit(f"Library finalization error: {message}")
