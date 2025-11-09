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


class MatchStatus(str, Enum):
    """Status of match resolution for a media item."""

    PENDING = "pending"
    MATCHED = "matched"
    MANUAL = "manual"
    SKIPPED = "skipped"


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


@dataclass
class MediaMatch:
    """Match information for a media item."""

    metadata: VideoMetadata
    status: MatchStatus = MatchStatus.PENDING
    confidence: Optional[float] = None
    matched_title: Optional[str] = None
    matched_year: Optional[int] = None
    external_id: Optional[str] = None
    source: Optional[str] = None
    poster_url: Optional[str] = None
    overview: Optional[str] = None
    user_selected: bool = False

    def is_matched(self) -> bool:
        """Return True if the item has been matched (automatically or manually)."""
        return self.status in (MatchStatus.MATCHED, MatchStatus.MANUAL)

    def needs_review(self) -> bool:
        """Return True if the item needs user review."""
        return self.status == MatchStatus.PENDING or (
            self.status == MatchStatus.MATCHED and (self.confidence or 0) < 0.8
        )

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the match."""
        result = self.metadata.as_dict()
        result.update({
            "status": self.status.value,
            "confidence": self.confidence,
            "matched_title": self.matched_title,
            "matched_year": self.matched_year,
            "external_id": self.external_id,
            "source": self.source,
            "poster_url": self.poster_url,
            "overview": self.overview,
            "user_selected": self.user_selected,
        })
        return result


@dataclass
class SearchRequest:
    """Request for searching media matches."""

    query: str
    media_type: MediaType
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None


@dataclass
class SearchResult:
    """Result from a media search."""

    title: str
    year: Optional[int] = None
    external_id: Optional[str] = None
    source: Optional[str] = None
    poster_url: Optional[str] = None
    overview: Optional[str] = None
    confidence: float = 0.0
