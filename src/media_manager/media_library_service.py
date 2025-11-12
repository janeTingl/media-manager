"""Media library service for coordinating persistence operations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .logging import get_logger
from .models import (
    DownloadStatus,
    MediaMatch,
    PosterInfo,
    PosterType,
    SubtitleInfo,
    SubtitleLanguage,
    VideoMetadata,
)
from .persistence.database import get_database_service
from .persistence.models import (
    Artwork,
    ExternalId,
    HistoryEvent,
    Library,
    MediaFile,
    MediaItem,
    Subtitle as DBSubtitle,
)
from .persistence.repositories import transactional_context

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class MediaLibraryService:
    """Service for coordinating media library persistence operations."""

    def __init__(self) -> None:
        """Initialize the media library service."""
        self._logger = logger

    def create_or_get_library(self, name: str, path: str, media_type: str) -> Library:
        """Create or get a library by path."""
        with transactional_context() as uow:
            repo = uow.get_repository(Library)
            
            # Try to find existing library by path
            existing = repo.filter_by(path=path)
            if existing:
                library = existing[0]
                # Refresh the library within the current session context
                return uow.session.merge(library)
            
            # Create new library
            library = Library(name=name, path=path, media_type=media_type)
            library = repo.create(library)
            # Return a fresh instance that's bound to the session
            return uow.session.merge(library)

    def create_media_item_from_scan(self, library_id: int, metadata: VideoMetadata) -> MediaItem:
        """Create a media item from scanned metadata."""
        with transactional_context() as uow:
            # Create media item
            media_item = MediaItem(
                library_id=library_id,
                title=metadata.title,
                media_type=metadata.media_type.value,
                year=metadata.year,
                season=metadata.season,
                episode=metadata.episode,
            )
            media_item = uow.get_repository(MediaItem).create(media_item)

            # Create media file
            media_file = MediaFile(
                media_item_id=media_item.id,
                path=str(metadata.path),
                filename=metadata.path.name,
                file_size=metadata.path.stat().st_size if metadata.path.exists() else 0,
            )
            uow.get_repository(MediaFile).create(media_file)

            # Create history event
            self._create_history_event(
                uow, media_item.id, "added", f"Scanned from {metadata.path}"
            )

            # Return a fresh instance bound to the session
            return uow.session.merge(media_item)

    def update_media_item_from_match(self, media_item_id: int, match: MediaMatch) -> MediaItem:
        """Update media item with match information."""
        with transactional_context() as uow:
            media_repo = uow.get_repository(MediaItem)
            media_item = media_repo.read(media_item_id)
            
            if not media_item:
                raise ValueError(f"Media item not found: {media_item_id}")

            # Update basic fields
            media_item.title = match.matched_title or match.metadata.title
            media_item.year = match.matched_year or match.metadata.year
            media_item.description = match.overview
            media_item.runtime = match.runtime
            media_item.aired_date = match.aired_date
            media_item.updated_at = media_item.updated_at  # Will be auto-updated
            media_repo.update(media_item)

            # Update external IDs
            if match.external_id and match.source:
                external_repo = uow.get_repository(ExternalId)
                
                # Remove existing IDs from same source
                existing = external_repo.filter_by(
                    media_item_id=media_item_id, source=match.source
                )
                for ext in existing:
                    external_repo.delete(ext.id)
                
                # Add new external ID
                external_id = ExternalId(
                    media_item_id=media_item_id,
                    source=match.source,
                    external_id=match.external_id,
                )
                external_repo.create(external_id)

            # Update artwork
            self._update_artwork(uow, media_item_id, match.posters)

            # Update subtitles
            self._update_subtitles(uow, media_item_id, match.subtitles)

            # Create history event
            self._create_history_event(
                uow, media_item_id, "modified", f"Matched with {match.source}"
            )

            return media_item

    def update_media_file_path(self, media_item_id: int, old_path: str, new_path: Path) -> None:
        """Update media file path after post-processing."""
        with transactional_context() as uow:
            file_repo = uow.get_repository(MediaFile)
            
            # Find media file by old path
            files = file_repo.filter_by(media_item_id=media_item_id, path=old_path)
            if not files:
                self._logger.warning(f"Media file not found for path: {old_path}")
                return
            
            media_file = files[0]
            media_file.path = str(new_path)
            media_file.filename = new_path.name
            if new_path.exists():
                media_file.file_size = new_path.stat().st_size
            file_repo.update(media_file)

            # Create history event
            self._create_history_event(
                uow, media_item_id, "modified", f"Moved to {new_path}"
            )

    def update_artwork_download_status(
        self, media_item_id: int, poster_type: PosterType, local_path: Optional[Path], status: DownloadStatus
    ) -> None:
        """Update artwork download status and local path."""
        with transactional_context() as uow:
            artwork_repo = uow.get_repository(Artwork)
            
            # Find artwork by type
            artworks = artwork_repo.filter_by(
                media_item_id=media_item_id, artwork_type=poster_type.value
            )
            
            if artworks:
                artwork = artworks[0]
                artwork.local_path = str(local_path) if local_path else None
                artwork.download_status = status.value
                artwork_repo.update(artwork)
            else:
                # Create new artwork record if it doesn't exist
                artwork = Artwork(
                    media_item_id=media_item_id,
                    artwork_type=poster_type.value,
                    local_path=str(local_path) if local_path else None,
                    download_status=status.value,
                    size="medium",  # Default size
                )
                artwork_repo.create(artwork)

    def update_subtitle_download_status(
        self, media_item_id: int, language: SubtitleLanguage, local_path: Optional[Path], status: DownloadStatus
    ) -> None:
        """Update subtitle download status and local path."""
        with transactional_context() as uow:
            subtitle_repo = uow.get_repository(DBSubtitle)
            
            # Find subtitle by language
            subtitles = subtitle_repo.filter_by(
                media_item_id=media_item_id, language=language.value
            )
            
            if subtitles:
                subtitle = subtitles[0]
                subtitle.local_path = str(local_path) if local_path else None
                subtitle.download_status = status.value
                if local_path and local_path.exists():
                    subtitle.file_size = local_path.stat().st_size
                subtitle_repo.update(subtitle)

    def get_media_item_by_path(self, path: str) -> Optional[MediaItem]:
        """Get media item by file path."""
        with transactional_context() as uow:
            file_repo = uow.get_repository(MediaFile)
            files = file_repo.filter_by(path=path)
            
            if files:
                media_file = files[0]
                media_repo = uow.get_repository(MediaItem)
                media_item = media_repo.read(media_file.media_item_id)
                # Return a fresh instance bound to session
                return uow.session.merge(media_item) if media_item else None
            
            return None

    def _update_artwork(self, uow, media_item_id: int, posters: dict[PosterType, PosterInfo]) -> None:
        """Update artwork information."""
        artwork_repo = uow.get_repository(Artwork)
        
        for poster_type, poster_info in posters.items():
            # Find existing artwork
            existing = artwork_repo.filter_by(
                media_item_id=media_item_id, artwork_type=poster_type.value
            )
            
            if existing:
                artwork = existing[0]
                artwork.url = poster_info.url
                artwork.download_status = poster_info.download_status.value
                artwork_repo.update(artwork)
            else:
                # Create new artwork
                artwork = Artwork(
                    media_item_id=media_item_id,
                    artwork_type=poster_type.value,
                    url=poster_info.url,
                    download_status=poster_info.download_status.value,
                    size="medium",  # Default size
                )
                artwork_repo.create(artwork)

    def _update_subtitles(self, uow, media_item_id: int, subtitles: dict[SubtitleLanguage, SubtitleInfo]) -> None:
        """Update subtitle information."""
        subtitle_repo = uow.get_repository(DBSubtitle)
        
        for language, subtitle_info in subtitles.items():
            # Find existing subtitle
            existing = subtitle_repo.filter_by(
                media_item_id=media_item_id, language=language.value
            )
            
            if existing:
                subtitle = existing[0]
                subtitle.url = subtitle_info.url
                subtitle.provider = subtitle_info.provider
                subtitle.subtitle_id = subtitle_info.subtitle_id
                subtitle.download_status = subtitle_info.download_status.value
                subtitle_repo.update(subtitle)
            else:
                # Create new subtitle
                subtitle = DBSubtitle(
                    media_item_id=media_item_id,
                    language=language.value,
                    format=subtitle_info.format.value,
                    url=subtitle_info.url,
                    provider=subtitle_info.provider,
                    subtitle_id=subtitle_info.subtitle_id,
                    download_status=subtitle_info.download_status.value,
                )
                subtitle_repo.create(subtitle)

    def _create_history_event(self, uow, media_item_id: int, event_type: str, event_data: str) -> None:
        """Create a history event."""
        history_repo = uow.get_repository(HistoryEvent)
        history_event = HistoryEvent(
            media_item_id=media_item_id,
            event_type=event_type,
            event_data=event_data,
        )
        history_repo.create(history_event)


# Global service instance
_media_library_service: Optional[MediaLibraryService] = None


def get_media_library_service() -> MediaLibraryService:
    """Get the global media library service instance."""
    global _media_library_service
    
    if _media_library_service is None:
        _media_library_service = MediaLibraryService()
    
    return _media_library_service