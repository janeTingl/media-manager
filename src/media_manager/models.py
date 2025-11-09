"""Data models for media files and metadata."""

from enum import Enum
from pathlib import Path
from typing import Dict, Optional


class MediaType(Enum):
    """Media type enumeration."""

    MOVIE = "movie"
    TV_EPISODE = "tv_episode"


class VideoMetadata:
    """Metadata for a video file."""

    def __init__(
        self,
        file_path: Path,
        title: str,
        media_type: MediaType,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
        extension: Optional[str] = None,
    ) -> None:
        self.file_path = file_path
        self.title = title
        self.media_type = media_type
        self.year = year
        self.season = season
        self.episode = episode
        self.extension = extension or file_path.suffix.lower()
        self.original_path = file_path

    def to_dict(self) -> Dict[str, Optional[object]]:
        """Convert metadata to dictionary for template rendering."""
        return {
            "title": self.title,
            "year": self.year,
            "season": self.season,
            "episode": self.episode,
            "extension": self.extension,
            "media_type": self.media_type.value,
            "original_name": self.file_path.stem,
            "original_path": str(self.file_path),
        }

    def __repr__(self) -> str:
        return (
            f"VideoMetadata(title='{self.title}', media_type={self.media_type.value}, "
            f"year={self.year}, season={self.season}, episode={self.episode})"
        )


class RenameOperation:
    """Represents a single rename operation."""

    def __init__(
        self,
        source_path: Path,
        target_path: Path,
        metadata: VideoMetadata,
    ) -> None:
        self.source_path = source_path
        self.target_path = target_path
        self.metadata = metadata
        self.executed = False

    def __repr__(self) -> str:
        return f"RenameOperation('{self.source_path}' -> '{self.target_path}')"
