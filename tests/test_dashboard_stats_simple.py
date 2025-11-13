"""Simple tests for dashboard statistics (no Qt dependency)."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.media_manager.persistence.database import DatabaseService
from src.media_manager.persistence.models import (
    Credit,
    HistoryEvent,
    Library,
    MediaFile,
    MediaItem,
    MediaItemTag,
    Person,
    Tag,
)
from src.media_manager.stats_service import StatsService


@pytest.fixture
def in_memory_db() -> tuple[DatabaseService, Session]:
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    db_service = DatabaseService("sqlite://", auto_migrate=False)
    db_service._engine = engine

    import src.media_manager.persistence.database as db_module
    db_module._database_service = db_service

    session = Session(engine)

    yield db_service, session

    session.close()
    engine.dispose()
    db_module._database_service = None


@pytest.fixture
def session(in_memory_db: tuple[DatabaseService, Session]) -> Session:
    """Get session from in-memory database."""
    _, session = in_memory_db
    return session


@pytest.fixture
def seeded_data(session: Session) -> dict:
    """Create seeded data for testing."""
    # Create library
    lib = Library(
        name="Test Library",
        path="/test/library",
        media_type="mixed",
        is_active=True,
    )
    session.add(lib)
    session.flush()

    # Create persons
    director = Person(name="Christopher Nolan")
    actor = Person(name="Leonardo DiCaprio")
    session.add_all([director, actor])
    session.flush()

    # Create movies
    movies = []
    for i in range(3):
        movie = MediaItem(
            library_id=lib.id,
            title=f"Movie {i+1}",
            media_type="movie",
            year=2020 + i,
            runtime=120 + i * 10,
            rating=8.0 + i * 0.2,
            description=f"Description for movie {i+1}",
        )
        movies.append(movie)
        session.add(movie)
    session.flush()

    # Create TV shows
    tv_shows = []
    for i in range(2):
        tv = MediaItem(
            library_id=lib.id,
            title=f"TV Show {i+1}",
            media_type="tv",
            year=2021 + i,
            runtime=60 + i * 5,
        )
        tv_shows.append(tv)
        session.add(tv)
    session.flush()

    # Add files
    for i, movie in enumerate(movies):
        mf = MediaFile(
            media_item_id=movie.id,
            path=f"/path/to/movie{i}.mkv",
            filename=f"movie{i}.mkv",
            file_size=1000000000,  # 1GB each
        )
        session.add(mf)
    session.flush()

    # Add credits
    credit1 = Credit(
        media_item_id=movies[0].id, person_id=director.id, role="director"
    )
    credit2 = Credit(
        media_item_id=movies[0].id, person_id=actor.id, role="actor"
    )
    session.add_all([credit1, credit2])
    session.flush()

    session.commit()

    return {"library": lib, "movies": movies, "tv_shows": tv_shows}


class TestStatsService:
    """Tests for StatsService without Qt dependencies."""

    def test_item_counts(self, seeded_data: dict) -> None:
        """Test item counting."""
        stats = StatsService()
        lib = seeded_data["library"]

        counts = stats.get_item_counts(library_id=lib.id)

        assert counts["total"] == 5  # 3 movies + 2 TV shows
        assert counts["movies"] == 3
        assert counts["tv"] == 2

    def test_runtime_calculation(self, seeded_data: dict) -> None:
        """Test runtime calculation."""
        stats = StatsService()
        lib = seeded_data["library"]

        runtime = stats.get_total_runtime(library_id=lib.id)

        # Movies: 120 + 130 + 140 = 390
        # TV: 60 + 65 = 125
        # Total: 515
        assert runtime == 515

    def test_storage_usage(self, seeded_data: dict) -> None:
        """Test storage calculation."""
        stats = StatsService()
        lib = seeded_data["library"]

        storage = stats.get_storage_usage(library_id=lib.id)

        # 3 movies × 1GB = 3GB
        expected = 3 * 1000000000
        assert storage == expected

    def test_top_directors(self, seeded_data: dict) -> None:
        """Test top directors list."""
        stats = StatsService()
        lib = seeded_data["library"]

        directors = stats.get_top_directors(limit=10, library_id=lib.id)

        assert len(directors) == 1
        assert directors[0]["name"] == "Christopher Nolan"
        assert directors[0]["count"] == 1

    def test_cache_functionality(self, seeded_data: dict) -> None:
        """Test caching works."""
        stats = StatsService(cache_ttl=3600)
        lib = seeded_data["library"]

        # First call caches
        counts1 = stats.get_item_counts(library_id=lib.id)
        cache_size1 = len(stats._cache)

        # Second call uses cache
        counts2 = stats.get_item_counts(library_id=lib.id)
        cache_size2 = len(stats._cache)

        assert counts1 == counts2
        assert cache_size1 > 0
        assert cache_size2 == cache_size1

    def test_cache_clear(self, seeded_data: dict) -> None:
        """Test manual cache clear."""
        stats = StatsService()
        lib = seeded_data["library"]

        # Cache something
        stats.get_item_counts(library_id=lib.id)
        assert len(stats._cache) > 0

        # Clear cache
        stats.clear_cache()
        assert len(stats._cache) == 0

    def test_completion_stats(self, seeded_data: dict) -> None:
        """Test completion statistics."""
        stats = StatsService()
        lib = seeded_data["library"]

        completion = stats.get_completion_stats(library_id=lib.id)

        assert completion["total"] == 5
        assert completion["with_description"] == 3  # Only movies have descriptions
        assert completion["description_completion"] == 60.0  # 3/5

    def test_all_item_counts(self, seeded_data: dict, session: Session) -> None:
        """Test getting all item counts across all libraries."""
        stats = StatsService()

        # Should include data from seeded_data library
        counts = stats.get_item_counts()

        assert counts["total"] >= 5
        assert counts["movies"] >= 3
        assert counts["tv"] >= 2

    def test_counts_by_library(self, seeded_data: dict) -> None:
        """Test counts grouped by library."""
        stats = StatsService()
        lib = seeded_data["library"]

        counts_by_lib = stats.get_counts_by_library()

        assert lib.id in counts_by_lib
        assert counts_by_lib[lib.id]["total"] == 5
        assert counts_by_lib[lib.id]["movies"] == 3
        assert counts_by_lib[lib.id]["tv"] == 2
