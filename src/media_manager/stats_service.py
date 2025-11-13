"""Analytics service for querying and caching media statistics."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from .logging import get_logger
from .persistence.database import get_database_service
from .persistence.models import (
    Credit,
    HistoryEvent,
    Library,
    MediaFile,
    MediaItem,
    Person,
    Tag,
)

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class CacheEntry:
    """A cache entry with TTL support."""

    def __init__(self, data: Any, ttl_seconds: int = 300) -> None:
        """Initialize cache entry.

        Args:
            data: The cached data
            ttl_seconds: Time to live in seconds (default: 5 minutes)
        """
        self.data = data
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl_seconds


class StatsService:
    """Service for analytics and statistics with caching."""

    def __init__(self, cache_ttl: int = 300) -> None:
        """Initialize stats service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 5 minutes)
        """
        self._db_service = get_database_service()
        self._cache: dict[str, CacheEntry] = {}
        self._cache_ttl = cache_ttl
        self._logger = logger

    def _get_cache_key(
        self,
        method: str,
        library_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tag_id: Optional[int] = None,
    ) -> str:
        """Generate cache key."""
        parts = [method]
        if library_id is not None:
            parts.append(f"lib_{library_id}")
        if start_date is not None:
            parts.append(f"start_{start_date.isoformat()}")
        if end_date is not None:
            parts.append(f"end_{end_date.isoformat()}")
        if tag_id is not None:
            parts.append(f"tag_{tag_id}")
        return "|".join(parts)

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.data
            else:
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any) -> None:
        """Set cache value."""
        self._cache[key] = CacheEntry(data, self._cache_ttl)

    def clear_cache(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._logger.debug("Cache cleared")

    def get_item_counts(
        self,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
    ) -> dict[str, int]:
        """Get item counts by type and library.

        Args:
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)

        Returns:
            Dictionary with counts: {"total": int, "movies": int, "tv": int}
        """
        cache_key = self._get_cache_key(
            "item_counts", library_id=library_id, tag_id=tag_id
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            # Total items
            total_stmt = select(func.count(MediaItem.id))
            if library_id is not None:
                total_stmt = total_stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                total_stmt = total_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
            total = session.exec(total_stmt).scalar() or 0

            # Movies
            movies_stmt = select(func.count(MediaItem.id)).where(
                MediaItem.media_type == "movie"
            )
            if library_id is not None:
                movies_stmt = movies_stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                movies_stmt = movies_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
            movies = session.exec(movies_stmt).scalar() or 0

            # TV Shows
            tv_stmt = select(func.count(MediaItem.id)).where(
                MediaItem.media_type == "tv"
            )
            if library_id is not None:
                tv_stmt = tv_stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                tv_stmt = tv_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
            tv = session.exec(tv_stmt).scalar() or 0

            result = {"total": total, "movies": movies, "tv": tv}
            self._set_cache(cache_key, result)
            return result

    def get_counts_by_library(self) -> dict[int, dict[str, int]]:
        """Get item counts grouped by library.

        Returns:
            Dictionary with library_id -> {"total": int, "movies": int, "tv": int}
        """
        cache_key = self._get_cache_key("counts_by_library")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            # Get all libraries with their item counts
            result = {}
            libraries = session.exec(select(Library)).all()
            for lib in libraries:
                counts_stmt = select(func.count(MediaItem.id)).where(
                    MediaItem.library_id == lib.id
                )
                total = session.exec(counts_stmt).scalar() or 0

                movies_stmt = select(func.count(MediaItem.id)).where(
                    (MediaItem.library_id == lib.id)
                    & (MediaItem.media_type == "movie")
                )
                movies = session.exec(movies_stmt).scalar() or 0

                tv_stmt = select(func.count(MediaItem.id)).where(
                    (MediaItem.library_id == lib.id) & (MediaItem.media_type == "tv")
                )
                tv = session.exec(tv_stmt).scalar() or 0

                result[lib.id] = {"total": total, "movies": movies, "tv": tv}

            self._set_cache(cache_key, result)
            return result

    def get_total_runtime(
        self,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
    ) -> int:
        """Get total runtime in minutes for all items.

        Args:
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)

        Returns:
            Total runtime in minutes
        """
        cache_key = self._get_cache_key(
            "total_runtime", library_id=library_id, tag_id=tag_id
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            stmt = select(func.coalesce(func.sum(MediaItem.runtime), 0))
            if library_id is not None:
                stmt = stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                stmt = stmt.join(MediaItem.tags).where(Tag.id == tag_id)
            result = session.exec(stmt).scalar() or 0
            self._set_cache(cache_key, result)
            return result

    def get_storage_usage(
        self,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
    ) -> int:
        """Get total storage usage in bytes.

        Args:
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)

        Returns:
            Total storage in bytes
        """
        cache_key = self._get_cache_key(
            "storage_usage", library_id=library_id, tag_id=tag_id
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            stmt = select(func.coalesce(func.sum(MediaFile.file_size), 0)).select_from(
                MediaFile
            )
            if library_id is not None:
                stmt = stmt.join(MediaItem).where(MediaItem.library_id == library_id)
            if tag_id is not None:
                stmt = (
                    stmt.join(MediaItem)
                    .join(MediaItem.tags)
                    .where(Tag.id == tag_id)
                )
            result = session.exec(stmt).scalar() or 0
            self._set_cache(cache_key, result)
            return result

    def get_top_directors(
        self,
        limit: int = 10,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get top directors by number of items.

        Args:
            limit: Maximum number of results
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)

        Returns:
            List of dicts with {"name": str, "count": int}
        """
        cache_key = self._get_cache_key(
            "top_directors", library_id=library_id, tag_id=tag_id
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            stmt = (
                select(Person.name, func.count(Credit.id).label("count"))
                .select_from(Credit)
                .join(Person)
                .join(MediaItem)
                .where(Credit.role == "director")
                .group_by(Person.name)
                .order_by(func.count(Credit.id).desc())
                .limit(limit)
            )
            if library_id is not None:
                stmt = stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                stmt = stmt.join(MediaItem.tags).where(Tag.id == tag_id)

            results = session.exec(stmt).all()
            result = [{"name": name, "count": count} for name, count in results]
            self._set_cache(cache_key, result)
            return result

    def get_top_actors(
        self,
        limit: int = 10,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get top actors by number of items.

        Args:
            limit: Maximum number of results
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)

        Returns:
            List of dicts with {"name": str, "count": int}
        """
        cache_key = self._get_cache_key(
            "top_actors", library_id=library_id, tag_id=tag_id
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            stmt = (
                select(Person.name, func.count(Credit.id).label("count"))
                .select_from(Credit)
                .join(Person)
                .join(MediaItem)
                .where(Credit.role == "actor")
                .group_by(Person.name)
                .order_by(func.count(Credit.id).desc())
                .limit(limit)
            )
            if library_id is not None:
                stmt = stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                stmt = stmt.join(MediaItem.tags).where(Tag.id == tag_id)

            results = session.exec(stmt).all()
            result = [{"name": name, "count": count} for name, count in results]
            self._set_cache(cache_key, result)
            return result

    def get_recent_activity(
        self,
        limit: int = 20,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        days_back: int = 30,
    ) -> list[dict[str, Any]]:
        """Get recent activity events.

        Args:
            limit: Maximum number of results
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)
            days_back: Number of days to look back (default: 30)

        Returns:
            List of dicts with activity info
        """
        # Note: We don't cache recent activity to keep it fresh
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        with self._db_service.get_session() as session:
            stmt = (
                select(HistoryEvent.id, HistoryEvent.event_type, HistoryEvent.timestamp, MediaItem.title, MediaItem.id)
                .select_from(HistoryEvent)
                .join(MediaItem)
                .where(HistoryEvent.timestamp >= cutoff_date)
                .order_by(HistoryEvent.timestamp.desc())
                .limit(limit)
            )
            if library_id is not None:
                stmt = stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                stmt = stmt.join(MediaItem.tags).where(Tag.id == tag_id)

            results = session.exec(stmt).all()
            result = [
                {
                    "id": event_id,
                    "type": event_type,
                    "timestamp": timestamp.isoformat(),
                    "title": title,
                    "media_item_id": media_item_id,
                }
                for event_id, event_type, timestamp, title, media_item_id in results
            ]
            return result

    def get_completion_stats(
        self,
        library_id: Optional[int] = None,
        tag_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Get completion statistics (items with metadata).

        Args:
            library_id: Filter by library ID (optional)
            tag_id: Filter by tag ID (optional)

        Returns:
            Dictionary with completion stats
        """
        cache_key = self._get_cache_key(
            "completion_stats", library_id=library_id, tag_id=tag_id
        )
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        with self._db_service.get_session() as session:
            # Total items
            total_stmt = select(func.count(MediaItem.id))
            if library_id is not None:
                total_stmt = total_stmt.where(MediaItem.library_id == library_id)
            if tag_id is not None:
                total_stmt = total_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
            total = session.exec(total_stmt).scalar() or 0

            # Items with description
            with_desc_stmt = select(func.count(MediaItem.id)).where(
                MediaItem.description.is_not(None)
            )
            if library_id is not None:
                with_desc_stmt = with_desc_stmt.where(
                    MediaItem.library_id == library_id
                )
            if tag_id is not None:
                with_desc_stmt = (
                    with_desc_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
                )
            with_desc = session.exec(with_desc_stmt).scalar() or 0

            # Items with rating
            with_rating_stmt = select(func.count(MediaItem.id)).where(
                MediaItem.rating.is_not(None)
            )
            if library_id is not None:
                with_rating_stmt = with_rating_stmt.where(
                    MediaItem.library_id == library_id
                )
            if tag_id is not None:
                with_rating_stmt = (
                    with_rating_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
                )
            with_rating = session.exec(with_rating_stmt).scalar() or 0

            # Items with runtime
            with_runtime_stmt = select(func.count(MediaItem.id)).where(
                MediaItem.runtime.is_not(None)
            )
            if library_id is not None:
                with_runtime_stmt = with_runtime_stmt.where(
                    MediaItem.library_id == library_id
                )
            if tag_id is not None:
                with_runtime_stmt = (
                    with_runtime_stmt.join(MediaItem.tags).where(Tag.id == tag_id)
                )
            with_runtime = session.exec(with_runtime_stmt).scalar() or 0

            result = {
                "total": total,
                "with_description": with_desc,
                "with_rating": with_rating,
                "with_runtime": with_runtime,
                "description_completion": (with_desc / total * 100) if total > 0 else 0,
                "rating_completion": (with_rating / total * 100) if total > 0 else 0,
                "runtime_completion": (with_runtime / total * 100) if total > 0 else 0,
            }
            self._set_cache(cache_key, result)
            return result
