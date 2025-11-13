from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, Optional
from uuid import uuid4

from sqlalchemy.orm import selectinload
from sqlmodel import select

from .logging import get_logger
from .models import MatchStatus, MediaMatch, MediaType, VideoMetadata
from .persistence.models import HistoryEvent, Library, MediaItem, Tag
from .persistence.repositories import transactional_context
from .providers.adapter import ProviderAdapter
from .providers.tmdb import TMDBProvider
from .providers.tvdb import TVDBProvider
from .renamer import RenamingEngine
from .settings import SettingsManager, get_settings


@dataclass
class BatchOperationConfig:
    """Configuration for batch operations."""

    rename: bool = False
    move_library_id: int | None = None
    delete_files: bool = False
    tags_to_add: list[str] = field(default_factory=list)
    override_genres: str | None = None
    override_rating: float | None = None
    resync_providers: bool = False
    cleanup_empty_dirs: bool = True


@dataclass
class BatchOperationSummary:
    """Summary information about executed batch operations."""

    total: int = 0
    processed: int = 0
    renamed: int = 0
    moved: int = 0
    deleted: int = 0
    tags_applied: int = 0
    metadata_updated: int = 0
    resynced: int = 0
    errors: list[str] = field(default_factory=list)

    def to_message(self) -> str:
        """Return a human-readable message describing the summary."""
        parts: list[str] = []
        parts.append(f"{self.processed}/{self.total} items processed")
        if self.renamed:
            parts.append(f"{self.renamed} renamed")
        if self.moved:
            parts.append(f"{self.moved} moved")
        if self.deleted:
            parts.append(f"{self.deleted} files deleted")
        if self.tags_applied:
            parts.append(f"tags applied to {self.tags_applied}")
        if self.metadata_updated:
            parts.append(f"metadata updated for {self.metadata_updated}")
        if self.resynced:
            parts.append(f"provider re-sync on {self.resynced}")
        if self.errors:
            parts.append(f"errors: {len(self.errors)}")
        return ", ".join(parts)


@dataclass
class _FileMoveRecord:
    source: Path
    target: Path


@dataclass
class _DeleteBackupRecord:
    original: Path
    backup: Path


class BatchOperationsService:
    """Service responsible for executing batch operations on media items."""

    def __init__(
        self,
        settings: SettingsManager | None = None,
        renamer: RenamingEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._renamer = renamer or RenamingEngine(self._settings)
        self._logger = get_logger().get_logger(__name__)

    def perform(
        self,
        items: Iterable[MediaItem | int],
        config: BatchOperationConfig,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> BatchOperationSummary:
        """Execute configured operations for the provided media items."""

        item_ids = self._normalize_item_ids(items)
        summary = BatchOperationSummary(total=len(item_ids))

        if summary.total == 0:
            return summary

        file_moves: list[_FileMoveRecord] = []
        delete_backups: list[_DeleteBackupRecord] = []
        cleanup_dirs: set[Path] = set()
        tags_cache: dict[str, Tag] = {}
        adapter: ProviderAdapter | None = (
            self._create_provider_adapter() if config.resync_providers else None
        )

        try:
            with transactional_context() as uow:
                session = uow.session

                target_library: Library | None = None
                if config.move_library_id is not None:
                    target_library = self._get_library(session, config.move_library_id)
                    if target_library is None:
                        raise ValueError("Target library not found")

                for index, item_id in enumerate(item_ids, start=1):
                    item = self._load_media_item(session, item_id)
                    if item is None:
                        raise ValueError(f"Media item {item_id} not found")

                    actions: list[str] = []
                    renamed_flag = False
                    moved_flag = False
                    deleted_count = 0
                    tags_added: list[str] = []
                    metadata_changed = False
                    resynced = False

                    # Ensure current library is loaded when needed
                    source_library = item.library
                    if (config.rename or config.move_library_id is not None) and source_library is None:
                        raise ValueError("Media item is not associated with a library")

                    if config.rename or config.move_library_id is not None:
                        rename_result = self._apply_rename_and_move(
                            item=item,
                            target_library=target_library,
                            config=config,
                            file_moves=file_moves,
                            cleanup_dirs=cleanup_dirs,
                        )
                        renamed_flag = rename_result[0]
                        moved_flag = rename_result[1]
                        if renamed_flag:
                            actions.append("renamed using templates")
                        if moved_flag:
                            destination = target_library.name if target_library else (item.library.name if item.library else "library")
                            actions.append(f"moved to library '{destination}'")

                    if config.delete_files:
                        deleted_count = self._delete_files(
                            session=session,
                            item=item,
                            delete_backups=delete_backups,
                            cleanup_dirs=cleanup_dirs,
                        )
                        if deleted_count:
                            actions.append(f"deleted {deleted_count} file(s)")

                    if config.tags_to_add:
                        tags_added = self._apply_tags(
                            session=session,
                            item=item,
                            tag_names=config.tags_to_add,
                            cache=tags_cache,
                        )
                        if tags_added:
                            actions.append(f"tags added: {', '.join(tags_added)}")

                    if config.override_genres is not None or config.override_rating is not None:
                        metadata_changed = self._apply_metadata_overrides(item, config)
                        if metadata_changed:
                            actions.append("metadata overrides applied")

                    if adapter is not None:
                        resynced = self._resync_from_providers(item, adapter)
                        if resynced:
                            actions.append("provider metadata refreshed")

                    if any((renamed_flag, moved_flag, deleted_count, tags_added, metadata_changed, resynced)):
                        item.updated_at = datetime.utcnow()
                        summary.processed += 1
                        if renamed_flag:
                            summary.renamed += 1
                        if moved_flag:
                            summary.moved += 1
                        if deleted_count:
                            summary.deleted += deleted_count
                        if tags_added:
                            summary.tags_applied += 1
                        if metadata_changed:
                            summary.metadata_updated += 1
                        if resynced:
                            summary.resynced += 1

                        history_event = HistoryEvent(
                            media_item_id=item.id,
                            event_type="batch_operation",
                            event_data=json.dumps(
                                {
                                    "actions": actions,
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            ),
                            timestamp=datetime.utcnow(),
                        )
                        session.add(history_event)

                    message = ", ".join(actions) if actions else "no changes"
                    if progress_callback is not None:
                        try:
                            progress_callback(index, summary.total, message)
                        except Exception:  # pragma: no cover - defensive
                            self._logger.warning("Progress callback raised an exception", exc_info=True)

                session.flush()
        except Exception as exc:
            self._rollback_file_moves(file_moves)
            self._restore_delete_backups(delete_backups)
            summary.errors.append(str(exc))
            self._logger.error("Batch operations failed: %s", exc)
            raise
        else:
            self._finalize_delete_backups(delete_backups)
            if config.cleanup_empty_dirs and cleanup_dirs:
                self._cleanup_directories(cleanup_dirs)

        return summary

    def _normalize_item_ids(self, items: Iterable[MediaItem | int]) -> list[int]:
        ids: list[int] = []
        for entry in items:
            if isinstance(entry, MediaItem):
                if entry.id is not None:
                    ids.append(int(entry.id))
            else:
                ids.append(int(entry))
        # Preserve order but drop duplicates
        seen: set[int] = set()
        ordered: list[int] = []
        for item_id in ids:
            if item_id not in seen:
                seen.add(item_id)
                ordered.append(item_id)
        return ordered

    def _create_provider_adapter(self) -> ProviderAdapter:
        providers = []
        enabled = self._settings.get_enabled_providers()

        if "TMDB" in enabled:
            tmdb_key = self._settings.get_tmdb_api_key()
            if tmdb_key:
                providers.append(TMDBProvider(tmdb_key))
            else:
                self._logger.warning("TMDB provider enabled but API key missing")

        if "TVDB" in enabled:
            tvdb_key = self._settings.get_tvdb_api_key()
            if tvdb_key:
                providers.append(TVDBProvider(tvdb_key))
            else:
                self._logger.warning("TVDB provider enabled but API key missing")

        return ProviderAdapter(providers if providers else None)

    def _load_media_item(self, session, item_id: int) -> MediaItem | None:
        stmt = (
            select(MediaItem)
            .where(MediaItem.id == item_id)
            .options(
                selectinload(MediaItem.files),
                selectinload(MediaItem.tags),
                selectinload(MediaItem.library),
                selectinload(MediaItem.external_ids),
            )
        )
        return session.exec(stmt).first()

    def _get_library(self, session, library_id: int) -> Library | None:
        stmt = select(Library).where(Library.id == library_id)
        return session.exec(stmt).first()

    def _apply_rename_and_move(
        self,
        item: MediaItem,
        target_library: Library | None,
        config: BatchOperationConfig,
        file_moves: list[_FileMoveRecord],
        cleanup_dirs: set[Path],
    ) -> tuple[bool, bool]:
        renamed = False
        moved = False

        if not item.files:
            return renamed, moved

        source_library = item.library
        if source_library is None:
            raise ValueError("Media item missing source library information")

        source_root = Path(source_library.path)
        destination_library = target_library or source_library
        destination_root = Path(destination_library.path)
        destination_root.mkdir(parents=True, exist_ok=True)

        for media_file in item.files:
            current_path = Path(media_file.path)
            if not current_path.exists():
                raise FileNotFoundError(f"Source file not found: {current_path}")

            if config.rename:
                relative_target = self._build_template_path(item, current_path)
            else:
                relative_target = self._relative_to_library(current_path, source_root)

            target_path = destination_root / relative_target
            target_path = self._ensure_unique_target(current_path, target_path)

            if current_path == target_path:
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_path), str(target_path))
            file_moves.append(_FileMoveRecord(source=current_path, target=target_path))

            media_file.path = str(target_path)
            media_file.filename = target_path.name
            media_file.updated_at = datetime.utcnow()

            cleanup_dirs.add(current_path.parent)

            if config.rename:
                renamed = True
            if target_library is not None and source_library.id != target_library.id:
                moved = True

        if target_library is not None and source_library.id != target_library.id:
            item.library_id = target_library.id
            item.library = target_library

        return renamed, moved

    def _build_template_path(self, item: MediaItem, file_path: Path) -> Path:
        metadata = self._build_metadata(item, file_path)
        match = MediaMatch(
            metadata=metadata,
            status=MatchStatus.MATCHED,
            matched_title=item.title,
            matched_year=item.year,
        )
        return self._renamer.build_relative_path(match)

    def _build_metadata(self, item: MediaItem, file_path: Path) -> VideoMetadata:
        media_type_value = item.media_type
        if isinstance(media_type_value, MediaType):
            media_type_enum = media_type_value
        else:
            media_type_enum = MediaType(media_type_value)
        metadata = VideoMetadata(
            path=file_path,
            title=item.title or file_path.stem,
            media_type=media_type_enum,
            year=item.year,
            season=item.season,
            episode=item.episode,
        )
        return metadata

    def _relative_to_library(self, file_path: Path, library_root: Path) -> Path:
        try:
            return file_path.relative_to(library_root)
        except ValueError:
            # Fallback to filename only if outside library root
            return Path(file_path.name)

    def _ensure_unique_target(self, source: Path, target: Path) -> Path:
        if target.exists() and target != source:
            return self._renamer.suggest_unique(target)
        return target

    def _delete_files(
        self,
        session,
        item: MediaItem,
        delete_backups: list[_DeleteBackupRecord],
        cleanup_dirs: set[Path],
    ) -> int:
        deleted = 0
        for media_file in list(item.files):
            file_path = Path(media_file.path)
            backup_path = file_path
            if file_path.exists():
                backup_path = file_path.parent / f".__mm_deleted_{uuid4().hex}{file_path.suffix}"
                shutil.move(str(file_path), str(backup_path))
                delete_backups.append(
                    _DeleteBackupRecord(original=file_path, backup=backup_path)
                )
                cleanup_dirs.add(file_path.parent)
            session.delete(media_file)
            item.files.remove(media_file)
            deleted += 1
        return deleted

    def _apply_tags(
        self,
        session,
        item: MediaItem,
        tag_names: Iterable[str],
        cache: dict[str, Tag],
    ) -> list[str]:
        applied: list[str] = []
        for raw_name in tag_names:
            name = raw_name.strip()
            if not name:
                continue
            tag = cache.get(name)
            if tag is None:
                stmt = select(Tag).where(Tag.name == name)
                tag = session.exec(stmt).first()
                if tag is None:
                    tag = Tag(name=name)
                    session.add(tag)
                    session.flush()
                cache[name] = tag
            if tag not in item.tags:
                item.tags.append(tag)
                applied.append(name)
        return applied

    def _apply_metadata_overrides(
        self,
        item: MediaItem,
        config: BatchOperationConfig,
    ) -> bool:
        changed = False
        if config.override_genres is not None:
            new_genres = config.override_genres.strip() or None
            if item.genres != new_genres:
                item.genres = new_genres
                changed = True
        if config.override_rating is not None:
            if config.override_rating <= 0:
                if item.rating is not None:
                    item.rating = None
                    changed = True
            elif item.rating != float(config.override_rating):
                item.rating = float(config.override_rating)
                changed = True
        return changed

    def _resync_from_providers(self, item: MediaItem, adapter: ProviderAdapter) -> bool:
        if not item.files:
            return False

        # Use the first file as reference
        file_path = Path(item.files[0].path)
        metadata = self._build_metadata(item, file_path)
        match = adapter.search_and_match(metadata, fallback_to_mock=True)

        updated = False
        if match.matched_title and match.matched_title != item.title:
            item.title = match.matched_title
            updated = True
        if match.matched_year and match.matched_year != item.year:
            item.year = match.matched_year
            updated = True
        if match.overview and match.overview != item.description:
            item.description = match.overview
            updated = True
        if match.runtime and match.runtime != item.runtime:
            item.runtime = match.runtime
            updated = True
        if match.aired_date and match.aired_date != item.aired_date:
            item.aired_date = match.aired_date
            updated = True
        return updated

    def _rollback_file_moves(self, file_moves: list[_FileMoveRecord]) -> None:
        for record in reversed(file_moves):
            try:
                if record.target.exists():
                    record.target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(record.target), str(record.source))
            except Exception:  # pragma: no cover - best effort rollback
                self._logger.error(
                    "Failed to rollback move %s -> %s",
                    record.target,
                    record.source,
                    exc_info=True,
                )

    def _restore_delete_backups(self, delete_backups: list[_DeleteBackupRecord]) -> None:
        for backup in reversed(delete_backups):
            try:
                if backup.backup.exists():
                    backup.original.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(backup.backup), str(backup.original))
            except Exception:  # pragma: no cover - best effort rollback
                self._logger.error(
                    "Failed to restore backup %s -> %s",
                    backup.backup,
                    backup.original,
                    exc_info=True,
                )

    def _finalize_delete_backups(self, delete_backups: list[_DeleteBackupRecord]) -> None:
        for backup in delete_backups:
            try:
                if backup.backup.exists():
                    if backup.backup.is_file():
                        backup.backup.unlink()
                    else:
                        shutil.rmtree(backup.backup)
            except Exception:  # pragma: no cover - best effort cleanup
                self._logger.warning(
                    "Failed to remove backup %s", backup.backup, exc_info=True
                )

    def _cleanup_directories(self, directories: Iterable[Path]) -> None:
        unique_dirs = sorted({Path(d) for d in directories}, key=lambda p: len(p.parts), reverse=True)
        for directory in unique_dirs:
            current = directory
            while True:
                if not current.exists():
                    break
                try:
                    if any(current.iterdir()):
                        break
                except OSError:
                    break
                try:
                    current.rmdir()
                except OSError:
                    break
                if current.parent == current:
                    break
                current = current.parent
