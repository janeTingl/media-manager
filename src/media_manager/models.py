"""Data models for the media manager scanning engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class MediaType(str, Enum):
    """Types of media that can be detected by the scanner."""

    MOVIE = "movie"
    TV = "tv"


@dataclass
class VideoMetadata:
    """Metadata extracted from a video file name."""

    path: Path
    title: str
    media_type: MediaType
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None

    def is_movie(self) -> bool:
        """Return True if the metadata represents a movie."""
        return self.media_type is MediaType.MOVIE

    def is_episode(self) -> bool:
        """Return True if the metadata represents a TV episode."""
        return self.media_type is MediaType.TV

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the metadata."""
        return {
            "path": str(self.path),
            "title": self.title,
            "media_type": self.media_type.value,
            "year": self.year,
            "season": self.season,
            "episode": self.episode,
        }
