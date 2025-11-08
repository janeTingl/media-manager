"""Data models for media entities."""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from enum import Enum


class MediaType(Enum):
    """Media type enumeration."""
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    SEASON = "season"
    EPISODE = "episode"


@dataclass
class ImageUrls:
    """Container for image URLs."""
    poster: Optional[str] = None
    backdrop: Optional[str] = None
    logo: Optional[str] = None
    thumbnail: Optional[str] = None


@dataclass
class MediaMetadata:
    """Common metadata for media entities."""
    language: Optional[str] = None
    country: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    vote_count: Optional[int] = None
    popularity: Optional[float] = None


@dataclass
class Movie:
    """Movie data model."""
    id: str
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[date] = None
    runtime_minutes: Optional[int] = None
    images: ImageUrls = field(default_factory=ImageUrls)
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    external_ids: Dict[str, str] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TVShow:
    """TV Show data model."""
    id: str
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    first_air_date: Optional[date] = None
    last_air_date: Optional[date] = None
    status: Optional[str] = None
    number_of_seasons: Optional[int] = None
    number_of_episodes: Optional[int] = None
    images: ImageUrls = field(default_factory=ImageUrls)
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    external_ids: Dict[str, str] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Season:
    """Season data model."""
    id: str
    tv_show_id: str
    season_number: int
    title: Optional[str] = None
    overview: Optional[str] = None
    air_date: Optional[date] = None
    episode_count: Optional[int] = None
    images: ImageUrls = field(default_factory=ImageUrls)
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    external_ids: Dict[str, str] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Episode:
    """Episode data model."""
    id: str
    tv_show_id: str
    season_id: str
    season_number: int
    episode_number: int
    title: Optional[str] = None
    overview: Optional[str] = None
    air_date: Optional[date] = None
    runtime_minutes: Optional[int] = None
    images: ImageUrls = field(default_factory=ImageUrls)
    metadata: MediaMetadata = field(default_factory=MediaMetadata)
    external_ids: Dict[str, str] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Search result with fuzzy matching score."""
    media_type: MediaType
    item: Movie | TVShow | Season | Episode
    score: float
    provider: str