"""SQLModel database schema for media manager persistence."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    pass


# Association tables for many-to-many relationships
class MediaItemTag(SQLModel, table=True):
    """Association between media items and tags."""

    media_item_id: Optional[int] = Field(
        default=None, foreign_key="mediaitem.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class MediaItemCollection(SQLModel, table=True):
    """Association between media items and collections."""

    media_item_id: Optional[int] = Field(
        default=None, foreign_key="mediaitem.id", primary_key=True
    )
    collection_id: Optional[int] = Field(
        default=None, foreign_key="collection.id", primary_key=True
    )


class Library(SQLModel, table=True):
    """User library containing media items."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    path: str = Field(unique=True, index=True)
    media_type: str = Field(index=True)  # "movie", "tv", or "mixed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    is_active: bool = Field(default=True, index=True)
    scan_roots: Optional[str] = None  # JSON array of paths to scan
    default_destination: Optional[str] = None  # Default path for processed files
    color: Optional[str] = None  # UI color for library identification

    # Relationships
    media_items: list["MediaItem"] = Relationship(back_populates="library")
    job_runs: list["JobRun"] = Relationship(back_populates="library")


class MediaItem(SQLModel, table=True):
    """Media item (movie or TV show) in a library."""

    id: Optional[int] = Field(default=None, primary_key=True)
    library_id: int = Field(foreign_key="library.id", index=True)
    title: str = Field(index=True)
    media_type: str = Field(index=True)  # "movie" or "tv"
    year: Optional[int] = Field(index=True)
    description: Optional[str] = None
    runtime: Optional[int] = None
    aired_date: Optional[str] = None
    rating: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # For TV episodes
    season: Optional[int] = Field(index=True)
    episode: Optional[int] = Field(index=True)

    # Relationships
    library: Library = Relationship(back_populates="media_items")
    files: list["MediaFile"] = Relationship(back_populates="media_item")
    external_ids: list["ExternalId"] = Relationship(back_populates="media_item")
    artworks: list["Artwork"] = Relationship(back_populates="media_item")
    subtitles: list["Subtitle"] = Relationship(back_populates="media_item")
    trailers: list["Trailer"] = Relationship(back_populates="media_item")
    credits: list["Credit"] = Relationship(back_populates="media_item")
    tags: list["Tag"] = Relationship(
        back_populates="media_items", link_model=MediaItemTag
    )
    collections: list["Collection"] = Relationship(
        back_populates="media_items", link_model=MediaItemCollection
    )
    favorites: list["Favorite"] = Relationship(back_populates="media_item")
    history_events: list["HistoryEvent"] = Relationship(back_populates="media_item")


class MediaFile(SQLModel, table=True):
    """Physical file associated with a media item."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    path: str = Field(unique=True, index=True)
    filename: str
    file_size: int
    duration: Optional[int] = None
    container: Optional[str] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    media_item: MediaItem = Relationship(back_populates="files")


class ExternalId(SQLModel, table=True):
    """External IDs (TMDB, TVDB, IMDB, etc.) for a media item."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    source: str = Field(index=True)  # "tmdb", "tvdb", "imdb"
    external_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    media_item: MediaItem = Relationship(back_populates="external_ids")


class Artwork(SQLModel, table=True):
    """Artwork (posters, fanart, banners, etc.) for a media item."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    artwork_type: str = Field(index=True)  # "poster", "fanart", "banner", "thumbnail"
    url: Optional[str] = None
    local_path: Optional[str] = None
    size: str = Field(index=True)  # "small", "medium", "large", "original"
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    download_status: str = Field(index=True)  # "pending", "downloading", "completed", "failed", "skipped"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    downloaded_at: Optional[datetime] = None

    # Relationships
    media_item: MediaItem = Relationship(back_populates="artworks")


class Subtitle(SQLModel, table=True):
    """Subtitle file for a media item."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    language: str = Field(index=True)  # ISO 639-1 code
    format: str  # "srt", "ass", "sub", "vtt", "ssa"
    provider: Optional[str] = None
    subtitle_id: Optional[str] = None
    url: Optional[str] = None
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    download_status: str = Field(index=True)  # "pending", "downloading", "completed", "failed", "skipped"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    downloaded_at: Optional[datetime] = None

    # Relationships
    media_item: MediaItem = Relationship(back_populates="subtitles")


class Trailer(SQLModel, table=True):
    """Trailer video link for a media item."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    name: str
    url: str
    language: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    media_item: MediaItem = Relationship(back_populates="trailers")


class Person(SQLModel, table=True):
    """Person (actor, director, writer, etc.) involved in media."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    external_id: Optional[str] = None
    biography: Optional[str] = None
    birthday: Optional[str] = None
    deathday: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    credits: list["Credit"] = Relationship(back_populates="person")


class Credit(SQLModel, table=True):
    """Credit for a person in a media item (actor, director, writer, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    person_id: int = Field(foreign_key="person.id", index=True)
    role: str = Field(index=True)  # "actor", "director", "writer", etc.
    character_name: Optional[str] = None
    order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    media_item: MediaItem = Relationship(back_populates="credits")
    person: Person = Relationship(back_populates="credits")


class Company(SQLModel, table=True):
    """Production/distribution company involved in media."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    external_id: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Tag(SQLModel, table=True):
    """User-defined tags for organizing media."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    color: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    media_items: list[MediaItem] = Relationship(
        back_populates="tags", link_model=MediaItemTag
    )


class Collection(SQLModel, table=True):
    """User-defined collections of media items."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    media_items: list[MediaItem] = Relationship(
        back_populates="collections", link_model=MediaItemCollection
    )


class Favorite(SQLModel, table=True):
    """User favorite marking for a media item."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True, unique=True)
    favorited_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

    # Relationships
    media_item: MediaItem = Relationship(back_populates="favorites")


class HistoryEvent(SQLModel, table=True):
    """User interaction history (watched, added, modified, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    media_item_id: int = Field(foreign_key="mediaitem.id", index=True)
    event_type: str = Field(index=True)  # "watched", "added", "modified", "viewed"
    event_data: Optional[str] = None  # JSON data
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    media_item: MediaItem = Relationship(back_populates="history_events")


class JobRun(SQLModel, table=True):
    """Record of background job execution (scans, downloads, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    library_id: Optional[int] = Field(foreign_key="library.id", index=True)
    job_type: str = Field(index=True)  # "scan", "match", "download_poster", "download_subtitle"
    status: str = Field(index=True)  # "pending", "running", "completed", "failed"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    items_processed: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    error_message: Optional[str] = None

    # Relationships
    library: Optional[Library] = Relationship(back_populates="job_runs")
