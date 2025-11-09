"""Library post-processing module for organizing finalized media files."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable
from uuid import uuid4

from .logging import get_logger
from .models import MediaMatch, MediaType
from .renamer import RenamingEngine
from .settings import SettingsManager, get_settings

_LOGGER = get_logger().get_logger(__name__)


class ConflictResolution(str, Enum):
    """Strategies for handling conflicts when a target file already exists."""

    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"


class OperationType(str, Enum):
    """Types of filesystem operations performed during post processing."""

    MOVE = "move"
    COPY = "copy"


@dataclass
class PostProcessingOptions:
    """User-configurable options for the post-processing run."""

    dry_run: bool = False
    copy_mode: bool = False
    conflict_resolution: ConflictResolution = ConflictResolution.RENAME
    cleanup_empty_dirs: bool = True


@dataclass
class PostProcessingItemResult:
    """Result information for a single processed media item."""

    match: MediaMatch
    source: Path
    target: Path | None
    action: str
    message: str | None = None


@dataclass
class PostProcessingSummary:
    """Aggregate summary for a post-processing session."""

    processed: list[PostProcessingItemResult] = field(default_factory=list)
    skipped: list[PostProcessingItemResult] = field(default_factory=list)
    failed: list[PostProcessingItemResult] = field(default_factory=list)


class ProcessingEventType(str, Enum):
    """Types of progress events emitted during processing."""

    PROCESSED = "processed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class ProcessingEvent:
    """Event emitted for UI updates during processing."""

    type: ProcessingEventType
    match: MediaMatch
    source: Path
    target: Path | None
    message: str | None = None


class PostProcessingError(Exception):
    """Raised when post processing fails and the operation is rolled back."""

    def __init__(
        self, message: str, match: MediaMatch | None, summary: PostProcessingSummary
    ) -> None:
        super().__init__(message)
        self.match = match
        self.summary = summary


@dataclass
class _OperationRecord:
    """Internal record of a filesystem operation for rollback."""

    operation: OperationType
    source: Path
    target: Path


@dataclass
class _OverwriteBackup:
    """Tracks a backup file created during overwrite conflict resolution."""

    original_path: Path
    backup_path: Path


class LibraryPostProcessor:
    """Apply rename templates and organize files into the media library tree."""

    def __init__(
        self,
        settings: SettingsManager | None = None,
        renamer: RenamingEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._renamer = renamer or RenamingEngine(self._settings)
        self._default_root = self._settings.get("library_root")
        if self._default_root:
            self._default_root = Path(self._default_root)
        else:
            self._default_root = Path.home() / "MediaLibrary"

    def process(
        self,
        matches: Iterable[MediaMatch],
        options: PostProcessingOptions,
        progress_callback: Callable[[int, int], None] | None = None,
        event_callback: Callable[[ProcessingEvent], None] | None = None,
    ) -> PostProcessingSummary:
        """Process matched items and move/copy them into the library."""

        matched_items = [match for match in matches if match.is_matched()]
        summary = PostProcessingSummary()

        total = len(matched_items)
        if total == 0:
            return summary

        operations: list[_OperationRecord] = []
        backups: list[_OverwriteBackup] = []
        cleanup_dirs: set[Path] = set()

        try:
            for index, match in enumerate(matched_items, start=1):
                if progress_callback:
                    progress_callback(index, total)

                source_path = match.metadata.path
                if not source_path.exists():
                    message = f"Source file not found: {source_path}"
                    failure = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=None,
                        action="failed",
                        message=message,
                    )
                    summary.failed.append(failure)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.FAILED,
                                match,
                                source_path,
                                None,
                                message,
                            )
                        )
                    raise PostProcessingError(message, match, summary)

                target_root = self._determine_target_root(match)
                relative_path = self._renamer.build_relative_path(match)
                target_path = target_root / relative_path

                if self._paths_are_identical(source_path, target_path):
                    message = "Source already resides in target location"
                    skipped = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=target_path,
                        action="skipped",
                        message=message,
                    )
                    summary.skipped.append(skipped)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.SKIPPED,
                                match,
                                source_path,
                                target_path,
                                message,
                            )
                        )
                    continue

                try:
                    conflict = self._handle_conflict(target_path, options.conflict_resolution)
                except Exception as exc:
                    message = f"Failed to prepare target path {target_path}: {exc}"
                    failure = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=target_path,
                        action="failed",
                        message=message,
                    )
                    summary.failed.append(failure)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.FAILED,
                                match,
                                source_path,
                                target_path,
                                message,
                            )
                        )
                    raise PostProcessingError(message, match, summary) from exc

                if conflict.reason:
                    skipped = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=target_path,
                        action="skipped",
                        message=conflict.reason,
                    )
                    summary.skipped.append(skipped)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.SKIPPED,
                                match,
                                source_path,
                                target_path,
                                conflict.reason,
                            )
                        )
                    continue

                final_target = conflict.target_path
                if final_target is None:
                    # Should not happen, but guard against it.
                    message = "Unable to determine target path"
                    failure = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=None,
                        action="failed",
                        message=message,
                    )
                    summary.failed.append(failure)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.FAILED,
                                match,
                                source_path,
                                None,
                                message,
                            )
                        )
                    raise PostProcessingError(message, match, summary)

                if options.dry_run:
                    result = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=final_target,
                        action="planned-copy" if options.copy_mode else "planned-move",
                        message="Dry run",
                    )
                    summary.processed.append(result)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.PROCESSED,
                                match,
                                source_path,
                                final_target,
                                result.message,
                            )
                        )
                    continue

                final_target.parent.mkdir(parents=True, exist_ok=True)

                backup_record = None
                if conflict.backup_path is not None:
                    backup_record = _OverwriteBackup(final_target, conflict.backup_path)
                    backups.append(backup_record)

                try:
                    if options.copy_mode:
                        shutil.copy2(source_path, final_target)
                        operations.append(
                            _OperationRecord(OperationType.COPY, source_path, final_target)
                        )
                    else:
                        shutil.move(source_path, final_target)
                        operations.append(
                            _OperationRecord(OperationType.MOVE, source_path, final_target)
                        )
                        if options.cleanup_empty_dirs:
                            cleanup_dirs.add(source_path.parent)
                except Exception as exc:
                    message = f"Failed to {'copy' if options.copy_mode else 'move'} {source_path}: {exc}"
                    failure = PostProcessingItemResult(
                        match=match,
                        source=source_path,
                        target=final_target,
                        action="failed",
                        message=message,
                    )
                    summary.failed.append(failure)
                    if event_callback:
                        event_callback(
                            ProcessingEvent(
                                ProcessingEventType.FAILED,
                                match,
                                source_path,
                                final_target,
                                message,
                            )
                        )
                    raise PostProcessingError(message, match, summary) from exc

                match.metadata.path = final_target

                result = PostProcessingItemResult(
                    match=match,
                    source=source_path,
                    target=final_target,
                    action="copied" if options.copy_mode else "moved",
                )
                summary.processed.append(result)
                if event_callback:
                    event_callback(
                        ProcessingEvent(
                            ProcessingEventType.PROCESSED,
                            match,
                            source_path,
                            final_target,
                            None,
                        )
                    )

            if not options.dry_run:
                self._remove_backups(backups)
                if options.cleanup_empty_dirs and cleanup_dirs:
                    self._cleanup_directories(cleanup_dirs)

        except PostProcessingError:
            # Rollback already recorded operations then re-raise
            if not options.dry_run:
                self._rollback_operations(operations, backups)
            summary.processed.clear()
            raise
        except Exception as exc:  # Unexpected failure
            if not options.dry_run:
                self._rollback_operations(operations, backups)
            summary.processed.clear()
            message = f"Unexpected post-processing failure: {exc}"
            raise PostProcessingError(message, None, summary) from exc

        return summary

    def _determine_target_root(self, match: MediaMatch) -> Path:
        metadata = match.metadata
        key = metadata.media_type.value

        configured = self._settings.get_target_folder(key)
        if not configured and metadata.media_type is MediaType.MOVIE:
            configured = self._settings.get_target_folder("movies")
        elif not configured and metadata.media_type is MediaType.TV:
            configured = self._settings.get_target_folder("tv") or self._settings.get_target_folder(
                "tv_shows"
            )

        if configured:
            return Path(configured)

        type_dir = "Movie" if metadata.media_type is MediaType.MOVIE else "TV"
        return self._default_root / type_dir

    def _handle_conflict(
        self, target_path: Path, resolution: ConflictResolution
    ) -> _ConflictResult:
        if not target_path.exists():
            return _ConflictResult(target_path)

        if resolution is ConflictResolution.SKIP:
            return _ConflictResult(target_path, reason="Target exists; skipped")

        if resolution is ConflictResolution.RENAME:
            new_target = self._renamer.suggest_unique(target_path)
            return _ConflictResult(new_target)

        if resolution is ConflictResolution.OVERWRITE:
            temp_name = target_path.parent / f".__mm_backup_{uuid4().hex}{target_path.suffix}"
            shutil.move(target_path, temp_name)
            return _ConflictResult(target_path, backup_path=temp_name)

        raise ValueError(f"Unsupported conflict resolution: {resolution}")

    def _paths_are_identical(self, source: Path, target: Path) -> bool:
        try:
            return source.resolve() == target.resolve()
        except OSError:
            return False

    def _rollback_operations(
        self,
        operations: list[_OperationRecord],
        backups: list[_OverwriteBackup],
    ) -> None:
        for record in reversed(operations):
            try:
                if record.operation is OperationType.MOVE:
                    if record.target.exists():
                        shutil.move(record.target, record.source)
                elif record.operation is OperationType.COPY:
                    if record.target.exists():
                        record.target.unlink()
            except Exception as exc:
                _LOGGER.error("Failed to rollback operation %s -> %s: %s", record.source, record.target, exc)

        for backup in reversed(backups):
            try:
                if backup.backup_path.exists():
                    shutil.move(backup.backup_path, backup.original_path)
            except Exception as exc:
                _LOGGER.error(
                    "Failed to restore backup %s -> %s: %s",
                    backup.backup_path,
                    backup.original_path,
                    exc,
                )

    def _remove_backups(self, backups: list[_OverwriteBackup]) -> None:
        for backup in backups:
            try:
                if backup.backup_path.exists():
                    if backup.backup_path.is_file():
                        backup.backup_path.unlink()
                    elif backup.backup_path.is_dir():
                        shutil.rmtree(backup.backup_path)
            except Exception as exc:
                _LOGGER.warning("Failed to remove backup file %s: %s", backup.backup_path, exc)

    def _cleanup_directories(self, directories: Iterable[Path]) -> None:
        unique_directories = sorted(
            {Path(d) for d in directories}, key=lambda p: len(p.parts), reverse=True
        )
        for directory in unique_directories:
            current = directory
            while current.exists():
                try:
                    is_empty = not any(current.iterdir())
                except OSError:
                    break

                if not is_empty:
                    break

                try:
                    current.rmdir()
                except OSError:
                    break

                if current.parent == current:
                    break
                current = current.parent


@dataclass
class _ConflictResult:
    target_path: Path | None
    backup_path: Path | None = None
    reason: str | None = None


__all__ = [
    "ConflictResolution",
    "LibraryPostProcessor",
    "PostProcessingError",
    "PostProcessingItemResult",
    "PostProcessingOptions",
    "PostProcessingSummary",
    "ProcessingEvent",
    "ProcessingEventType",
]
