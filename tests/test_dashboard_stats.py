"""Tests for dashboard statistics and analytics service."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from src.media_manager.persistence.database import DatabaseService, init_database_service
from src.media_manager.persistence.models import (
    Credit,
    HistoryEvent,
    Library,
    MediaFile,
    MediaItem,
    Person,
    Tag,
    MediaItemTag,
)
from src.media_manager.stats_service import StatsService


@pytest.fixture
def in_memory_db() -> tuple[DatabaseService, Session]:
    """Create an in-memory SQLite database for testing."""
    # Create in-memory SQLite engine
    engine = create_engine(
        "sqlite://",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    SQLModel.metadata.create_all(engine)

    # Create database service with in-memory engine
    db_service = DatabaseService("sqlite://", auto_migrate=False)
    db_service._engine = engine

    # Initialize the global database service for transactional_context() usage
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
def test_library(session: Session) -> Library:
    """Create test library."""
    lib = Library(
        name="Test Library",
        path="/test/library",
        media_type="mixed",
        is_active=True,
    )
    session.add(lib)
    session.flush()
    return lib


@pytest.fixture
def test_tag(session: Session) -> Tag:
    """Create test tag."""
    tag = Tag(name="Action", color="#ff0000")
    session.add(tag)
    session.flush()
    return tag


@pytest.fixture
def seeded_data(session: Session, test_library: Library, test_tag: Tag) -> dict:
    """Create seeded data for testing."""
    # Create persons
    director1 = Person(name="Christopher Nolan")
    director2 = Person(name="Quentin Tarantino")
    actor1 = Person(name="Leonardo DiCaprio")
    actor2 = Person(name="Brad Pitt")
    session.add_all([director1, director2, actor1, actor2])
    session.flush()

    # Create movies
    movies = []
    movie_titles = [
        ("Inception", 2010, 148),
        ("The Dark Knight", 2008, 152),
        ("Pulp Fiction", 1994, 154),
        ("Django Unchained", 2012, 165),
        ("Avatar", 2009, 162),
    ]

    for i, (title, year, runtime) in enumerate(movie_titles):
        movie = MediaItem(
            library_id=test_library.id,
            title=title,
            media_type="movie",
            year=year,
            runtime=runtime,
            rating=8.0 + (i * 0.1),
            description=f"Description for {title}",
        )
        movies.append(movie)
        session.add(movie)
    session.flush()

    # Create TV shows
    tv_shows = []
    tv_titles = [
        ("Breaking Bad", 2008, 47),
        ("Game of Thrones", 2011, 60),
    ]

    for i, (title, year, runtime) in enumerate(tv_titles):
        tv = MediaItem(
            library_id=test_library.id,
            title=title,
            media_type="tv",
            year=year,
            runtime=runtime,
            rating=9.0 + (i * 0.1),
        )
        tv_shows.append(tv)
        session.add(tv)
    session.flush()

    # Add credits
    # Inception - Nolan (director), DiCaprio (actor)
    credit1 = Credit(
        media_item_id=movies[0].id, person_id=director1.id, role="director"
    )
    credit2 = Credit(
        media_item_id=movies[0].id, person_id=actor1.id, role="actor"
    )
    # The Dark Knight - Nolan (director)
    credit3 = Credit(
        media_item_id=movies[1].id, person_id=director1.id, role="director"
    )
    # Pulp Fiction - Tarantino (director)
    credit4 = Credit(
        media_item_id=movies[2].id, person_id=director2.id, role="director"
    )
    credit5 = Credit(
        media_item_id=movies[2].id, person_id=actor2.id, role="actor"
    )
    # Django Unchained - Tarantino (director), DiCaprio (actor)
    credit6 = Credit(
        media_item_id=movies[3].id, person_id=director2.id, role="director"
    )
    credit7 = Credit(
        media_item_id=movies[3].id, person_id=actor1.id, role="actor"
    )

    session.add_all([credit1, credit2, credit3, credit4, credit5, credit6, credit7])
    session.flush()

    # Add files
    for i, movie in enumerate(movies):
        file_size = (i + 1) * 1000000000  # 1GB, 2GB, etc.
        mf = MediaFile(
            media_item_id=movie.id,
            path=f"/path/to/movie{i}.mkv",
            filename=f"movie{i}.mkv",
            file_size=file_size,
        )
        session.add(mf)
    session.flush()

    # Add history events
    now = datetime.utcnow()
    for i, movie in enumerate(movies):
        event = HistoryEvent(
            media_item_id=movie.id,
            event_type="watched" if i % 2 == 0 else "added",
            timestamp=now - timedelta(days=i),
        )
        session.add(event)
    session.flush()

    # Tag first movie
    tag_link = MediaItemTag(media_item_id=movies[0].id, tag_id=test_tag.id)
    session.add(tag_link)
    session.flush()

    session.commit()

    return {
        "library": test_library,
        "movies": movies,
        "tv_shows": tv_shows,
        "directors": [director1, director2],
        "actors": [actor1, actor2],
        "tag": test_tag,
    }


class TestStatsServiceCounting:
    """Test item counting functionality."""

    def test_get_item_counts_all(self, seeded_data: dict) -> None:
        """Test getting total item counts."""
        stats = StatsService()
        counts = stats.get_item_counts()

        assert counts["total"] == 7  # 5 movies + 2 TV shows
        assert counts["movies"] == 5
        assert counts["tv"] == 2

    def test_get_item_counts_by_library(self, seeded_data: dict) -> None:
        """Test getting item counts filtered by library."""
        lib = seeded_data["library"]
        stats = StatsService()
        counts = stats.get_item_counts(library_id=lib.id)

        assert counts["total"] == 7
        assert counts["movies"] == 5
        assert counts["tv"] == 2

    def test_get_counts_by_library(self, seeded_data: dict) -> None:
        """Test getting counts grouped by library."""
        lib = seeded_data["library"]
        stats = StatsService()
        counts_by_lib = stats.get_counts_by_library()

        assert lib.id in counts_by_lib
        assert counts_by_lib[lib.id]["total"] == 7
        assert counts_by_lib[lib.id]["movies"] == 5
        assert counts_by_lib[lib.id]["tv"] == 2


class TestStatsServiceAggregations:
    """Test aggregation statistics."""

    def test_get_total_runtime(self, seeded_data: dict) -> None:
        """Test total runtime calculation."""
        lib = seeded_data["library"]
        stats = StatsService()
        runtime = stats.get_total_runtime(library_id=lib.id)

        # 5 movies: 148 + 152 + 154 + 165 + 162 = 781 minutes
        # 2 TV shows: 47 + 60 = 107 minutes
        # Total: 888 minutes
        assert runtime == 888

    def test_get_storage_usage(self, seeded_data: dict) -> None:
        """Test storage usage calculation."""
        lib = seeded_data["library"]
        stats = StatsService()
        storage = stats.get_storage_usage(library_id=lib.id)

        # 1GB + 2GB + 3GB + 4GB + 5GB = 15GB
        expected = 15 * 1000000000
        assert storage == expected

    def test_get_storage_usage_all(self, seeded_data: dict) -> None:
        """Test storage usage for all libraries."""
        stats = StatsService()
        storage = stats.get_storage_usage()

        # 1GB + 2GB + 3GB + 4GB + 5GB = 15GB
        expected = 15 * 1000000000
        assert storage == expected


class TestStatsServiceTopLists:
    """Test top lists (directors, actors)."""

    def test_get_top_directors(self, seeded_data: dict) -> None:
        """Test getting top directors."""
        lib = seeded_data["library"]
        stats = StatsService()
        directors = stats.get_top_directors(limit=10, library_id=lib.id)

        # Nolan appears in 2 movies, Tarantino in 2 movies
        assert len(directors) == 2
        assert directors[0]["name"] in ["Christopher Nolan", "Quentin Tarantino"]
        assert directors[0]["count"] == 2
        assert directors[1]["name"] in ["Christopher Nolan", "Quentin Tarantino"]
        assert directors[1]["count"] == 2

    def test_get_top_actors(self, seeded_data: dict) -> None:
        """Test getting top actors."""
        lib = seeded_data["library"]
        stats = StatsService()
        actors = stats.get_top_actors(limit=10, library_id=lib.id)

        # DiCaprio appears in 2 movies, Pitt in 1 movie
        assert len(actors) == 2
        assert actors[0]["name"] == "Leonardo DiCaprio"
        assert actors[0]["count"] == 2
        assert actors[1]["name"] == "Brad Pitt"
        assert actors[1]["count"] == 1

    def test_get_top_directors_limit(self, seeded_data: dict) -> None:
        """Test top directors with limit."""
        lib = seeded_data["library"]
        stats = StatsService()
        directors = stats.get_top_directors(limit=1, library_id=lib.id)

        assert len(directors) == 1


class TestStatsServiceActivityAndCompletion:
    """Test activity and completion statistics."""

    def test_get_recent_activity(self, seeded_data: dict) -> None:
        """Test getting recent activity."""
        lib = seeded_data["library"]
        stats = StatsService()
        activity = stats.get_recent_activity(limit=20, library_id=lib.id)

        assert len(activity) > 0
        assert "type" in activity[0]
        assert "timestamp" in activity[0]
        assert "title" in activity[0]

    def test_get_recent_activity_filters(self, seeded_data: dict) -> None:
        """Test recent activity with filters."""
        lib = seeded_data["library"]
        stats = StatsService()
        activity = stats.get_recent_activity(
            limit=20, library_id=lib.id, days_back=5
        )

        assert len(activity) > 0

    def test_get_completion_stats(self, seeded_data: dict) -> None:
        """Test completion statistics."""
        lib = seeded_data["library"]
        stats = StatsService()
        completion = stats.get_completion_stats(library_id=lib.id)

        assert completion["total"] == 7
        assert completion["with_description"] == 5  # Only movies have descriptions
        assert completion["description_completion"] == 5 / 7 * 100
        assert 0 <= completion["rating_completion"] <= 100


class TestStatsServiceCaching:
    """Test caching functionality."""

    def test_cache_expiration(self, seeded_data: dict) -> None:
        """Test cache expiration."""
        stats = StatsService(cache_ttl=1)  # 1 second TTL
        lib = seeded_data["library"]

        # First call should cache
        counts1 = stats.get_item_counts(library_id=lib.id)
        assert counts1["total"] == 7

        # Immediate call should return cached
        counts2 = stats.get_item_counts(library_id=lib.id)
        assert counts2["total"] == 7

        # Wait for cache to expire
        import time

        time.sleep(1.1)

        # Should fetch fresh data
        counts3 = stats.get_item_counts(library_id=lib.id)
        assert counts3["total"] == 7

    def test_clear_cache(self, seeded_data: dict) -> None:
        """Test manual cache clearing."""
        stats = StatsService()
        lib = seeded_data["library"]

        # Cache some data
        counts1 = stats.get_item_counts(library_id=lib.id)

        # Clear cache
        stats.clear_cache()

        # Should still work (data fetched fresh)
        counts2 = stats.get_item_counts(library_id=lib.id)
        assert counts2["total"] == 7


class TestStatsServiceTagFiltering:
    """Test filtering by tags."""

    def test_get_item_counts_by_tag(
        self, seeded_data: dict, session: Session
    ) -> None:
        """Test getting counts filtered by tag."""
        tag = seeded_data["tag"]
        stats = StatsService()
        counts = stats.get_item_counts(tag_id=tag.id)

        # Only first movie is tagged
        assert counts["total"] == 1
        assert counts["movies"] == 1
        assert counts["tv"] == 0

    def test_get_runtime_by_tag(self, seeded_data: dict) -> None:
        """Test runtime filtered by tag."""
        tag = seeded_data["tag"]
        movie = seeded_data["movies"][0]
        stats = StatsService()
        runtime = stats.get_total_runtime(tag_id=tag.id)

        # Only first movie (Inception, 148 minutes)
        assert runtime == 148
