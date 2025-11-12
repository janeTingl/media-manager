"""Persistence layer for media manager."""

from .database import DatabaseService, get_database_service, init_database_service
from .models import (
    Artwork,
    Collection,
    Company,
    Credit,
    ExternalId,
    Favorite,
    HistoryEvent,
    JobRun,
    Library,
    MediaFile,
    MediaItem,
    Person,
    Subtitle,
    Tag,
    Trailer,
)
from .repositories import Repository, RepositoryManager, UnitOfWork

__all__ = [
    "DatabaseService",
    "get_database_service",
    "init_database_service",
    "Library",
    "MediaItem",
    "MediaFile",
    "ExternalId",
    "Artwork",
    "Subtitle",
    "Trailer",
    "Person",
    "Credit",
    "Company",
    "Tag",
    "Collection",
    "Favorite",
    "HistoryEvent",
    "JobRun",
    "Repository",
    "RepositoryManager",
    "UnitOfWork",
]
