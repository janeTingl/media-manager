"""Caching service for provider results with optional Redis/diskcache support."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from sqlmodel import Session, select

from .logging import get_logger
from .persistence.database import get_database_service
from .persistence.models import ProviderCache

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class CacheBackend:
    """Base interface for cache backends."""

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        raise NotImplementedError

    def set(self, key: str, value: str, ttl: int) -> None:
        """Set value in cache with TTL in seconds."""
        raise NotImplementedError

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all cache entries."""
        raise NotImplementedError


class RedisBackend(CacheBackend):
    """Redis cache backend."""

    def __init__(self, redis_client: Any) -> None:
        """Initialize Redis backend.

        Args:
            redis_client: Redis client instance
        """
        self.client = redis_client

    def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            value = self.client.get(key)
            return value.decode("utf-8") if value else None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: str, ttl: int) -> None:
        """Set value in Redis with TTL."""
        try:
            self.client.setex(key, ttl, value)
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def delete(self, key: str) -> None:
        """Delete value from Redis."""
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis clear error: {e}")


class DiskCacheBackend(CacheBackend):
    """Disk cache backend using diskcache library."""

    def __init__(self, cache_dir: str) -> None:
        """Initialize diskcache backend.

        Args:
            cache_dir: Directory for cache files
        """
        try:
            import diskcache
            self.cache = diskcache.Cache(cache_dir)
        except ImportError:
            logger.warning("diskcache not installed, disk caching disabled")
            self.cache = None

    def get(self, key: str) -> Optional[str]:
        """Get value from disk cache."""
        if not self.cache:
            return None
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Diskcache get error: {e}")
            return None

    def set(self, key: str, value: str, ttl: int) -> None:
        """Set value in disk cache with TTL."""
        if not self.cache:
            return
        try:
            self.cache.set(key, value, expire=ttl)
        except Exception as e:
            logger.error(f"Diskcache set error: {e}")

    def delete(self, key: str) -> None:
        """Delete value from disk cache."""
        if not self.cache:
            return
        try:
            self.cache.delete(key)
        except Exception as e:
            logger.error(f"Diskcache delete error: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        if not self.cache:
            return
        try:
            self.cache.clear()
        except Exception as e:
            logger.error(f"Diskcache clear error: {e}")


class CacheService:
    """Service for caching provider results with multiple backend support."""

    def __init__(
        self,
        backend: Optional[CacheBackend] = None,
        default_ttl: int = 3600,  # 1 hour default
        use_db_cache: bool = True,
    ) -> None:
        """Initialize cache service.

        Args:
            backend: Optional external cache backend (Redis or DiskCache)
            default_ttl: Default TTL in seconds
            use_db_cache: Whether to use database as cache layer
        """
        self.backend = backend
        self.default_ttl = default_ttl
        self.use_db_cache = use_db_cache
        self.db_service = get_database_service()

    def _generate_cache_key(
        self, provider_name: str, query_type: str, **params: Any
    ) -> str:
        """Generate cache key from query parameters.

        Args:
            provider_name: Provider name (tmdb, tvdb, etc.)
            query_type: Type of query (search_movie, get_details, etc.)
            **params: Query parameters

        Returns:
            Cache key hash
        """
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        key_string = f"{provider_name}:{query_type}:{sorted_params}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self, provider_name: str, query_type: str, **params: Any
    ) -> Optional[dict[str, Any]]:
        """Get cached result.

        Args:
            provider_name: Provider name
            query_type: Type of query
            **params: Query parameters

        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._generate_cache_key(provider_name, query_type, **params)

        # Try external backend first (Redis/DiskCache)
        if self.backend:
            try:
                cached_value = self.backend.get(cache_key)
                if cached_value:
                    logger.debug(f"Cache hit (backend): {cache_key}")
                    return json.loads(cached_value)
            except Exception as e:
                logger.warning(f"Backend cache error: {e}")

        # Fall back to database cache
        if self.use_db_cache:
            return self._get_from_db(cache_key)

        return None

    def _get_from_db(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Get cached result from database.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        try:
            with self.db_service.get_session() as session:
                statement = (
                    select(ProviderCache)
                    .where(ProviderCache.cache_key == cache_key)
                    .where(ProviderCache.expires_at > datetime.utcnow())
                )
                result = session.exec(statement).first()

                if result:
                    # Update hit count and last accessed
                    result.hit_count += 1
                    result.last_accessed = datetime.utcnow()
                    session.add(result)
                    session.commit()

                    logger.debug(f"Cache hit (DB): {cache_key}")
                    return json.loads(result.response_data)

                return None
        except Exception as e:
            logger.error(f"Database cache get error: {e}")
            return None

    def set(
        self,
        provider_name: str,
        query_type: str,
        response_data: dict[str, Any],
        ttl: Optional[int] = None,
        **params: Any,
    ) -> None:
        """Set cached result.

        Args:
            provider_name: Provider name
            query_type: Type of query
            response_data: Response data to cache
            ttl: TTL in seconds (uses default if None)
            **params: Query parameters
        """
        cache_key = self._generate_cache_key(provider_name, query_type, **params)
        ttl = ttl or self.default_ttl
        response_json = json.dumps(response_data)

        # Store in external backend if available
        if self.backend:
            try:
                self.backend.set(cache_key, response_json, ttl)
                logger.debug(f"Cache set (backend): {cache_key}")
            except Exception as e:
                logger.warning(f"Backend cache set error: {e}")

        # Store in database cache
        if self.use_db_cache:
            self._set_in_db(
                cache_key, provider_name, query_type, params, response_json, ttl
            )

    def _set_in_db(
        self,
        cache_key: str,
        provider_name: str,
        query_type: str,
        params: dict[str, Any],
        response_json: str,
        ttl: int,
    ) -> None:
        """Set cached result in database.

        Args:
            cache_key: Cache key
            provider_name: Provider name
            query_type: Type of query
            params: Query parameters
            response_json: Response JSON string
            ttl: TTL in seconds
        """
        try:
            with self.db_service.get_session() as session:
                # Check if entry exists
                statement = select(ProviderCache).where(
                    ProviderCache.cache_key == cache_key
                )
                existing = session.exec(statement).first()

                expires_at = datetime.utcnow() + timedelta(seconds=ttl)

                if existing:
                    # Update existing entry
                    existing.response_data = response_json
                    existing.expires_at = expires_at
                    existing.last_accessed = datetime.utcnow()
                    session.add(existing)
                else:
                    # Create new entry
                    cache_entry = ProviderCache(
                        cache_key=cache_key,
                        provider_name=provider_name,
                        query_type=query_type,
                        query_params=json.dumps(params),
                        response_data=response_json,
                        expires_at=expires_at,
                    )
                    session.add(cache_entry)

                session.commit()
                logger.debug(f"Cache set (DB): {cache_key}")
        except Exception as e:
            logger.error(f"Database cache set error: {e}")

    def delete(self, provider_name: str, query_type: str, **params: Any) -> None:
        """Delete cached result.

        Args:
            provider_name: Provider name
            query_type: Type of query
            **params: Query parameters
        """
        cache_key = self._generate_cache_key(provider_name, query_type, **params)

        if self.backend:
            try:
                self.backend.delete(cache_key)
            except Exception as e:
                logger.warning(f"Backend cache delete error: {e}")

        if self.use_db_cache:
            try:
                with self.db_service.get_session() as session:
                    statement = select(ProviderCache).where(
                        ProviderCache.cache_key == cache_key
                    )
                    result = session.exec(statement).first()
                    if result:
                        session.delete(result)
                        session.commit()
            except Exception as e:
                logger.error(f"Database cache delete error: {e}")

    def clear_expired(self) -> int:
        """Clear expired cache entries from database.

        Returns:
            Number of entries cleared
        """
        if not self.use_db_cache:
            return 0

        try:
            with self.db_service.get_session() as session:
                statement = select(ProviderCache).where(
                    ProviderCache.expires_at < datetime.utcnow()
                )
                expired_entries = session.exec(statement).all()
                count = len(expired_entries)

                for entry in expired_entries:
                    session.delete(entry)

                session.commit()
                logger.info(f"Cleared {count} expired cache entries")
                return count
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0

    def clear_all(self) -> None:
        """Clear all cache entries."""
        if self.backend:
            try:
                self.backend.clear()
            except Exception as e:
                logger.warning(f"Backend cache clear error: {e}")

        if self.use_db_cache:
            try:
                with self.db_service.get_session() as session:
                    statement = select(ProviderCache)
                    entries = session.exec(statement).all()
                    for entry in entries:
                        session.delete(entry)
                    session.commit()
                    logger.info("Cleared all database cache entries")
            except Exception as e:
                logger.error(f"Error clearing database cache: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.use_db_cache:
            return {}

        try:
            with self.db_service.get_session() as session:
                all_entries = session.exec(select(ProviderCache)).all()
                now = datetime.utcnow()
                expired = sum(1 for e in all_entries if e.expires_at < now)
                total_hits = sum(e.hit_count for e in all_entries)

                return {
                    "total_entries": len(all_entries),
                    "expired_entries": expired,
                    "active_entries": len(all_entries) - expired,
                    "total_hits": total_hits,
                }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create the global cache service instance.

    Returns:
        Cache service instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def initialize_cache_service(
    backend: Optional[CacheBackend] = None,
    default_ttl: int = 3600,
    use_db_cache: bool = True,
) -> CacheService:
    """Initialize the global cache service with custom configuration.

    Args:
        backend: Optional external cache backend
        default_ttl: Default TTL in seconds
        use_db_cache: Whether to use database cache

    Returns:
        Initialized cache service
    """
    global _cache_service
    _cache_service = CacheService(backend, default_ttl, use_db_cache)
    return _cache_service
