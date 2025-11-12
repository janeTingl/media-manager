"""Scanning engine coordinating filesystem discovery and enrichment."""

from __future__ import annotations

from typing import Callable, Sequence

from PySide6.QtCore import QObject, Signal

from .logging import get_logger
from .media_library_service import get_media_library_service
from .models import VideoMetadata
from .persistence.models import MediaItem
from .scanner import ScanConfig, Scanner


class ScanEngine(QObject):
    """High-level scanning engine that coordinates filesystem discovery."""

    scan_started = Signal(str)
    scan_progress = Signal(int, int, str)
    scan_completed = Signal(object)
    enrichment_task_created = Signal(object)
    scan_error = Signal(str)

    def __init__(
        self,
        scanner: Scanner | None = None,
        library_id: int | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._scanner = scanner or Scanner()
        self._logger = get_logger().get_logger(__name__)
        self._results: list[VideoMetadata] = []
        self._media_items: list[MediaItem] = []
        self._library_id = library_id
        self._media_library_service = get_media_library_service()
        self._callbacks: list[Callable[[VideoMetadata], None]] = []

    def scan(self, config: ScanConfig) -> list[MediaItem]:
        """Perform a scan with the provided configuration."""
        self._results = []
        self._media_items = []

        valid_roots = [root for root in config.root_paths if root.exists()]
        for root in config.root_paths:
            if root.exists():
                self.scan_started.emit(str(root))
            else:
                message = f"Scan root does not exist: {root}"
                self._logger.warning(message)
                self.scan_error.emit(message)

        if not valid_roots:
            self.scan_completed.emit([])
            return []

        effective_config = config.with_roots(valid_roots)
        video_paths = list(self._scanner.iter_video_files(effective_config))
        total = len(video_paths)

        for index, path in enumerate(video_paths, start=1):
            metadata = self._scanner.parse_video(path)
            self._results.append(metadata)
            
            # Create media item in database if library_id is provided
            if self._library_id is not None:
                try:
                    media_item = self._media_library_service.create_media_item_from_scan(
                        self._library_id, metadata
                    )
                    self._media_items.append(media_item)
                except Exception as exc:
                    self._logger.error(f"Failed to create media item for {path}: {exc}")
                    # Continue scanning even if database creation fails
                    continue
            
            self.scan_progress.emit(index, total, str(path))
            self.enrichment_task_created.emit(metadata)
            self._dispatch_enrichment_callbacks(metadata)

        self.scan_completed.emit(list(self._media_items))
        return list(self._media_items)

    def register_enrichment_callback(
        self, callback: Callable[[VideoMetadata], None]
    ) -> None:
        """Register a callback invoked for every discovered item."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_enrichment_callback(
        self, callback: Callable[[VideoMetadata], None]
    ) -> None:
        """Remove a previously registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def clear_results(self) -> None:
        """Clear cached scan results."""
        self._results = []
        self._media_items = []

    def get_results(self) -> list[VideoMetadata]:
        """Return the cached scan results."""
        return list(self._results)

    def get_media_items(self) -> list[MediaItem]:
        """Return the cached media items with database IDs."""
        return list(self._media_items)

    def get_results_by_paths(self, paths: Sequence[str]) -> list[VideoMetadata]:
        """Return cached results filtered by file path."""
        lookup = {metadata.path.as_posix(): metadata for metadata in self._results}
        return [lookup[path] for path in paths if path in lookup]

    def _dispatch_enrichment_callbacks(self, metadata: VideoMetadata) -> None:
        for callback in list(self._callbacks):
            try:
                callback(metadata)
            except Exception as exc:  # pragma: no cover - safeguard logging
                self._logger.error(
                    "Enrichment callback failed for %s: %s",
                    metadata.path,
                    exc,
                )
