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


class PosterType(str, Enum):
    """Types of poster artwork."""

    POSTER = "poster"
    FANART = "fanart"
    BANNER = "banner"
    THUMBNAIL = "thumbnail"


class PosterSize(str, Enum):
    """Standard poster sizes."""

    SMALL = "small"  # ~w154
    MEDIUM = "medium"  # ~w342
    LARGE = "large"  # ~w500
    ORIGINAL = "original"  # ~w1280


class DownloadStatus(str, Enum):
    """Status of poster/subtitle download."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SubtitleLanguage(str, Enum):
    """Supported subtitle languages."""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"


class SubtitleFormat(str, Enum):
    """Supported subtitle formats."""

    SRT = "srt"
    ASS = "ass"
    SUB = "sub"
    VTT = "vtt"
    SSA = "ssa"


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
class PosterInfo:
    """Information about a poster download."""

    poster_type: PosterType
    url: Optional[str] = None
    local_path: Optional[Path] = None
    size: PosterSize = PosterSize.MEDIUM
    download_status: DownloadStatus = DownloadStatus.PENDING
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def is_downloaded(self) -> bool:
        """Return True if the poster has been successfully downloaded."""
        return self.download_status == DownloadStatus.COMPLETED and self.local_path and self.local_path.exists()

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the poster info."""
        return {
            "poster_type": self.poster_type.value,
            "url": self.url,
            "local_path": str(self.local_path) if self.local_path else None,
            "size": self.size.value,
            "download_status": self.download_status.value,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


@dataclass
class SubtitleInfo:
    """Information about a subtitle download."""

    language: SubtitleLanguage
    format: SubtitleFormat = SubtitleFormat.SRT
    url: Optional[str] = None
    local_path: Optional[Path] = None
    download_status: DownloadStatus = DownloadStatus.PENDING
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    provider: Optional[str] = None
    subtitle_id: Optional[str] = None

    def is_downloaded(self) -> bool:
        """Return True if the subtitle has been successfully downloaded."""
        return self.download_status == DownloadStatus.COMPLETED and self.local_path and self.local_path.exists()

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation of the subtitle info."""
        return {
            "language": self.language.value,
            "format": self.format.value,
            "url": self.url,
            "local_path": str(self.local_path) if self.local_path else None,
            "download_status": self.download_status.value,
            "file_size": self.file_size,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "provider": self.provider,
            "subtitle_id": self.subtitle_id,
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
    posters: Dict[PosterType, PosterInfo] = None
    subtitles: Dict[SubtitleLanguage, SubtitleInfo] = None

    def __post_init__(self) -> None:
        """Initialize posters and subtitles dicts if not provided."""
        if self.posters is None:
            self.posters = {}
        if self.subtitles is None:
            self.subtitles = {}

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
            "posters": {ptype.value: info.as_dict() for ptype, info in self.posters.items()},
            "subtitles": {lang.value: info.as_dict() for lang, info in self.subtitles.items()},
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
    poster_urls: Dict[PosterType, str] = None

    def __post_init__(self) -> None:
        """Initialize poster_urls dict if not provided."""
        if self.poster_urls is None:
            self.poster_urls = {}
        # For backward compatibility, populate poster_urls if poster_url is set
        if self.poster_url and PosterType.POSTER not in self.poster_urls:
            self.poster_urls[PosterType.POSTER] = self.poster_url
