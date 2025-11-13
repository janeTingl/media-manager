"""Tests for the caching service."""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from media_manager.cache_service import (
    CacheService,
    DiskCacheBackend,
    get_cache_service,
    initialize_cache_service,
)
from media_manager.persistence.database import DatabaseService


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseService:
    """Create a test database."""
    db_path = tmp_path / "test_cache.db"
    db_service = DatabaseService(str(db_path))
    db_service.create_database()
    return db_service


@pytest.fixture
def cache_service(test_db: DatabaseService) -> CacheService:
    """Create a cache service for testing."""
    return CacheService(default_ttl=60, use_db_cache=True)


def test_cache_get_set(cache_service: CacheService) -> None:
    """Test basic cache get/set operations."""
    # Set a value
    cache_service.set(
        "tmdb",
        "search_movie",
        {"title": "Inception", "results": [{"id": 1, "title": "Inception"}]},
        title="Inception",
    )

    # Get the value
    result = cache_service.get("tmdb", "search_movie", title="Inception")
    assert result is not None
    assert result["title"] == "Inception"
    assert len(result["results"]) == 1


def test_cache_ttl_expiration(cache_service: CacheService) -> None:
    """Test that cache entries expire based on TTL."""
    # Set a value with 1 second TTL
    cache_service.set(
        "tmdb",
        "get_details",
        {"id": 123, "title": "Test Movie"},
        ttl=1,
        movie_id=123,
    )

    # Should be available immediately
    result = cache_service.get("tmdb", "get_details", movie_id=123)
    assert result is not None

    # Wait for expiration
    time.sleep(2)

    # Clear expired entries
    cleared = cache_service.clear_expired()
    assert cleared >= 1

    # Should be gone after expiration
    result = cache_service.get("tmdb", "get_details", movie_id=123)
    assert result is None


def test_cache_key_generation(cache_service: CacheService) -> None:
    """Test that cache keys are generated consistently."""
    # Same parameters should produce same key
    key1 = cache_service._generate_cache_key(
        "tmdb", "search_movie", title="Matrix", year=1999
    )
    key2 = cache_service._generate_cache_key(
        "tmdb", "search_movie", title="Matrix", year=1999
    )
    assert key1 == key2

    # Different parameters should produce different keys
    key3 = cache_service._generate_cache_key(
        "tmdb", "search_movie", title="Matrix", year=2003
    )
    assert key1 != key3

    # Parameter order shouldn't matter (sorted internally)
    key4 = cache_service._generate_cache_key(
        "tmdb", "search_movie", year=1999, title="Matrix"
    )
    assert key1 == key4


def test_cache_hit_count(cache_service: CacheService) -> None:
    """Test that cache hit count is tracked."""
    # Set a value
    cache_service.set(
        "tmdb",
        "search_movie",
        {"title": "Avatar", "results": []},
        title="Avatar",
    )

    # Access it multiple times
    for _ in range(5):
        result = cache_service.get("tmdb", "search_movie", title="Avatar")
        assert result is not None

    # Check stats
    stats = cache_service.get_stats()
    assert stats["total_hits"] >= 5


def test_cache_update_existing(cache_service: CacheService) -> None:
    """Test updating an existing cache entry."""
    # Set initial value
    cache_service.set(
        "tmdb",
        "get_details",
        {"id": 456, "title": "Old Title"},
        movie_id=456,
    )

    # Update with new value
    cache_service.set(
        "tmdb",
        "get_details",
        {"id": 456, "title": "New Title"},
        movie_id=456,
    )

    # Should have new value
    result = cache_service.get("tmdb", "get_details", movie_id=456)
    assert result is not None
    assert result["title"] == "New Title"


def test_cache_delete(cache_service: CacheService) -> None:
    """Test deleting cache entries."""
    # Set a value
    cache_service.set(
        "tvdb",
        "search_tv",
        {"title": "Breaking Bad", "results": []},
        title="Breaking Bad",
    )

    # Verify it exists
    result = cache_service.get("tvdb", "search_tv", title="Breaking Bad")
    assert result is not None

    # Delete it
    cache_service.delete("tvdb", "search_tv", title="Breaking Bad")

    # Should be gone
    result = cache_service.get("tvdb", "search_tv", title="Breaking Bad")
    assert result is None


def test_cache_stats(cache_service: CacheService) -> None:
    """Test cache statistics."""
    # Add some entries
    for i in range(10):
        cache_service.set(
            "tmdb",
            "search_movie",
            {"title": f"Movie {i}", "results": []},
            movie_id=i,
        )

    # Get stats
    stats = cache_service.get_stats()
    assert stats["total_entries"] >= 10
    assert stats["active_entries"] >= 10
    assert stats["expired_entries"] == 0


def test_cache_clear_all(cache_service: CacheService) -> None:
    """Test clearing all cache entries."""
    # Add some entries
    for i in range(5):
        cache_service.set(
            "tmdb",
            "search_movie",
            {"title": f"Movie {i}", "results": []},
            movie_id=i,
        )

    # Clear all
    cache_service.clear_all()

    # Check that they're gone
    stats = cache_service.get_stats()
    assert stats["total_entries"] == 0


def test_disk_cache_backend(tmp_path: Path) -> None:
    """Test disk cache backend."""
    cache_dir = tmp_path / "diskcache"

    # Skip if diskcache not installed
    try:
        import diskcache
    except ImportError:
        pytest.skip("diskcache not installed")

    backend = DiskCacheBackend(str(cache_dir))

    # Test set/get
    backend.set("test_key", "test_value", ttl=60)
    value = backend.get("test_key")
    assert value == "test_value"

    # Test delete
    backend.delete("test_key")
    value = backend.get("test_key")
    assert value is None

    # Test clear
    backend.set("key1", "value1", ttl=60)
    backend.set("key2", "value2", ttl=60)
    backend.clear()
    assert backend.get("key1") is None
    assert backend.get("key2") is None


def test_cache_service_with_backend(tmp_path: Path) -> None:
    """Test cache service with external backend."""
    try:
        import diskcache
    except ImportError:
        pytest.skip("diskcache not installed")

    cache_dir = tmp_path / "diskcache"
    backend = DiskCacheBackend(str(cache_dir))
    cache_service = CacheService(backend=backend, use_db_cache=False)

    # Set and get through service
    cache_service.set(
        "tmdb",
        "search_movie",
        {"title": "Interstellar", "results": []},
        title="Interstellar",
    )

    result = cache_service.get("tmdb", "search_movie", title="Interstellar")
    assert result is not None
    assert result["title"] == "Interstellar"


def test_global_cache_service() -> None:
    """Test global cache service singleton."""
    service1 = get_cache_service()
    service2 = get_cache_service()
    assert service1 is service2

    # Test initialization
    service3 = initialize_cache_service(default_ttl=120)
    assert service3.default_ttl == 120


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
