"""Match manager for coordinating scan queue and match resolution workflows."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from .library_postprocessor import PostProcessingOptions, PostProcessingSummary
from .logging import get_logger
from .media_library_service import get_media_library_service
from .models import MediaMatch, PosterType, SearchRequest, SearchResult, SubtitleLanguage, VideoMetadata
from .persistence.models import MediaItem
from .services import get_service_registry
from .workers import WorkerManager


class MatchManager(QObject):
    """Manages the match resolution workflow and coordinates components."""

    # Signals
    matches_updated = Signal(list)  # List[MediaMatch]
    match_selected = Signal(object)  # MediaMatch
    status_changed = Signal(str)  # status message

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._media_library_service = get_media_library_service()

        # Get worker manager from service registry or create one
        service_registry = get_service_registry()
        if not service_registry.has(WorkerManager):
            service_registry.register(WorkerManager, lambda: WorkerManager())

        self._worker_manager = service_registry.get(WorkerManager)

        self._matches: list[MediaMatch] = []
        self._current_match: MediaMatch | None = None

    def add_metadata(self, metadata_list: list[VideoMetadata]) -> None:
        """Add metadata items to be matched."""
        for metadata in metadata_list:
            # Try to find existing media item in database
            media_item = self._media_library_service.get_media_item_by_path(str(metadata.path))
            
            match = MediaMatch(metadata=metadata)
            if media_item:
                match.media_item_id = media_item.id
                match.library_id = media_item.library_id
                match.sync_status = "synced"
            
            self._matches.append(match)

        self.matches_updated.emit(list(self._matches))
        self.status_changed.emit(f"Added {len(metadata_list)} items to queue")

    def add_media_items(self, media_items: list[MediaItem]) -> None:
        """Add media items from database to be matched."""
        for media_item in media_items:
            # Convert MediaItem back to VideoMetadata for matching
            from .models import MediaType, VideoMetadata
            from pathlib import Path
            
            # Get the media file to extract path
            with self._media_library_service._logger:
                from .persistence.repositories import transactional_context
                with transactional_context() as uow:
                    file_repo = uow.get_repository(MediaItem)
                    # This is a simplified approach - in practice, we'd need to reconstruct
                    # the VideoMetadata from the MediaItem and associated MediaFile
                    pass
            
            # For now, create a basic metadata object
            metadata = VideoMetadata(
                path=Path(f"/placeholder/path/{media_item.title}"),
                title=media_item.title,
                media_type=MediaType(media_item.media_type),
                year=media_item.year,
                season=media_item.season,
                episode=media_item.episode,
            )
            
            match = MediaMatch(
                metadata=metadata,
                media_item_id=media_item.id,
                library_id=media_item.library_id,
                sync_status="synced"
            )
            self._matches.append(match)

        self.matches_updated.emit(list(self._matches))
        self.status_changed.emit(f"Added {len(media_items)} items from database")

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
        """Update a match in the collection and sync to database."""
        for i, existing_match in enumerate(self._matches):
            if existing_match.metadata.path == match.metadata.path:
                self._matches[i] = match
                break

        # Sync to database if we have a media_item_id
        if match.media_item_id and match.is_matched():
            try:
                self._media_library_service.update_media_item_from_match(match.media_item_id, match)
                match.sync_status = "synced"
            except Exception as exc:
                self._logger.error(f"Failed to sync match to database: {exc}")
                match.sync_status = "error"

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

    def get_matches(self) -> list[MediaMatch]:
        """Get all matches."""
        return list(self._matches)

    def get_pending_count(self) -> int:
        """Get the count of pending matches."""
        return len([m for m in self._matches if m.needs_review()])

    def get_matched_count(self) -> int:
        """Get the count of matched items."""
        return len([m for m in self._matches if m.is_matched()])

    def download_posters(self, match: MediaMatch, poster_types: list[PosterType]) -> None:
        """Download posters for a specific match."""
        worker = self._worker_manager.start_poster_download_worker([match], poster_types)

        # Connect signals
        worker.signals.poster_downloaded.connect(self._on_poster_downloaded)
        worker.signals.poster_failed.connect(self._on_poster_failed)
        worker.signals.progress.connect(self._on_poster_progress)
        worker.signals.finished.connect(self._on_poster_download_finished)

        self.status_changed.emit(f"Downloading posters for {match.metadata.title}...")

    def download_all_posters(self, poster_types: list[PosterType]) -> None:
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

    def download_subtitles(self, match: MediaMatch, languages: list[SubtitleLanguage]) -> None:
        """Download subtitles for a specific match."""
        worker = self._worker_manager.start_subtitle_download_worker([match], languages)

        # Connect signals
        worker.signals.subtitle_downloaded.connect(self._on_subtitle_downloaded)
        worker.signals.subtitle_failed.connect(self._on_subtitle_failed)
        worker.signals.progress.connect(self._on_subtitle_progress)
        worker.signals.finished.connect(self._on_subtitle_download_finished)

        self.status_changed.emit(f"Downloading subtitles for {match.metadata.title}...")

    def download_all_subtitles(self, languages: list[SubtitleLanguage]) -> None:
        """Download subtitles for all matched items."""
        matched_matches = [m for m in self._matches if m.is_matched()]
        if not matched_matches:
            self.status_changed.emit("No matched items to download subtitles for")
            return

        worker = self._worker_manager.start_subtitle_download_worker(matched_matches, languages)

        # Connect signals
        worker.signals.subtitle_downloaded.connect(self._on_subtitle_downloaded)
        worker.signals.subtitle_failed.connect(self._on_subtitle_failed)
        worker.signals.progress.connect(self._on_subtitle_progress)
        worker.signals.finished.connect(self._on_subtitle_download_finished)

        self.status_changed.emit(f"Downloading subtitles for {len(matched_matches)} items...")

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
    def _on_search_completed(self, results: list[SearchResult]) -> None:
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
        # Update database with poster download status
        if match.media_item_id:
            try:
                self._media_library_service.update_artwork_download_status(
                    match.media_item_id, 
                    poster_info.poster_type, 
                    poster_info.local_path, 
                    poster_info.download_status
                )
            except Exception as exc:
                self._logger.error(f"Failed to update poster download status: {exc}")
        
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
        # Update database with new file location
        if match.media_item_id:
            try:
                self._media_library_service.update_media_file_path(
                    match.media_item_id, str(source), target
                )
            except Exception as exc:
                self._logger.error(f"Failed to update file path in database: {exc}")
        
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

    @Slot(object, object)
    def _on_subtitle_downloaded(self, match: MediaMatch, subtitle_info) -> None:
        """Handle successful subtitle download."""
        # Update database with subtitle download status
        if match.media_item_id:
            try:
                self._media_library_service.update_subtitle_download_status(
                    match.media_item_id,
                    subtitle_info.language,
                    subtitle_info.local_path,
                    subtitle_info.download_status
                )
            except Exception as exc:
                self._logger.error(f"Failed to update subtitle download status: {exc}")
        
        self.update_match(match)
        self.status_changed.emit(f"Downloaded {subtitle_info.language.value} subtitle for {match.metadata.title}")

    @Slot(object, str)
    def _on_subtitle_failed(self, match: MediaMatch, error: str) -> None:
        """Handle subtitle download failure."""
        self.update_match(match)
        self.status_changed.emit(f"Failed to download subtitle for {match.metadata.title}: {error}")

    @Slot(int, int)
    def _on_subtitle_progress(self, current: int, total: int) -> None:
        """Handle subtitle download progress."""
        self.status_changed.emit(f"Downloaded {current}/{total} subtitles")

    @Slot()
    def _on_subtitle_download_finished(self) -> None:
        """Handle subtitle download completion."""
        self.status_changed.emit("Subtitle download complete")
