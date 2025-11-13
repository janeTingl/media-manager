"""Performance benchmark tests for large libraries."""

import time
from datetime import datetime
from pathlib import Path
from typing import List

import pytest
from sqlmodel import Session, select

from media_manager.instrumentation import get_instrumentation, reset_instrumentation
from media_manager.persistence.database import DatabaseService
from media_manager.persistence.models import (
    Artwork,
    Credit,
    Library,
    MediaFile,
    MediaItem,
    Person,
)
from media_manager.persistence.repositories import MediaItemRepository


@pytest.fixture
def benchmark_db(tmp_path: Path) -> DatabaseService:
    """Create a temporary database for benchmarking."""
    db_path = tmp_path / "benchmark.db"
    db_service = DatabaseService(str(db_path))
    db_service.create_database()
    return db_service


def generate_synthetic_library(
    session: Session, library_id: int, item_count: int = 10000
) -> None:
    """Generate synthetic library data for benchmarking.

    Args:
        session: Database session
        library_id: Library ID
        item_count: Number of media items to generate
    """
    print(f"Generating {item_count} synthetic media items...")
    start_time = time.time()

    # Generate persons for credits
    persons = []
    for i in range(100):  # 100 persons
        person = Person(
            name=f"Person {i}",
            external_id=f"person_{i}",
            biography=f"Biography for person {i}",
        )
        session.add(person)
        persons.append(person)

    session.flush()

    # Generate media items in batches
    batch_size = 500
    for batch_start in range(0, item_count, batch_size):
        batch_items = []

        for i in range(batch_start, min(batch_start + batch_size, item_count)):
            # Create media item
            is_movie = i % 3 != 0  # 2/3 movies, 1/3 TV
            item = MediaItem(
                library_id=library_id,
                title=f"Media Item {i}",
                media_type="movie" if is_movie else "tv",
                year=1990 + (i % 34),  # Years from 1990-2024
                description=f"Description for media item {i}. " * 10,  # Long description
                genres='["Action", "Drama", "Comedy"]',
                runtime=90 + (i % 120),
                rating=5.0 + (i % 5),
                season=None if is_movie else ((i % 10) + 1),
                episode=None if is_movie else ((i % 20) + 1),
            )
            session.add(item)
            batch_items.append(item)

        session.flush()

        # Add files, artworks, and credits
        for item in batch_items:
            # Add media file
            file = MediaFile(
                media_item_id=item.id,
                path=f"/media/library/item_{item.id}.mp4",
                filename=f"item_{item.id}.mp4",
                file_size=1024 * 1024 * 1024 * 2,  # 2GB
                duration=5400,
                container="mp4",
                video_codec="h264",
                audio_codec="aac",
                resolution="1920x1080",
            )
            session.add(file)

            # Add artworks
            for artwork_type in ["poster", "fanart", "banner"]:
                artwork = Artwork(
                    media_item_id=item.id,
                    artwork_type=artwork_type,
                    url=f"https://example.com/{artwork_type}/{item.id}.jpg",
                    size="original",
                    download_status="completed",
                )
                session.add(artwork)

            # Add credits (5 per item)
            for j in range(5):
                person = persons[j % len(persons)]
                credit = Credit(
                    media_item_id=item.id,
                    person_id=person.id,
                    role="actor" if j < 3 else ("director" if j == 3 else "writer"),
                    character_name=f"Character {j}" if j < 3 else None,
                    order=j,
                )
                session.add(credit)

        session.commit()

        elapsed = time.time() - start_time
        progress = min(batch_start + batch_size, item_count)
        print(
            f"  Progress: {progress}/{item_count} ({progress * 100 // item_count}%) - "
            f"Elapsed: {elapsed:.1f}s"
        )

    total_time = time.time() - start_time
    print(f"Generated {item_count} items in {total_time:.2f}s")


@pytest.mark.benchmark
def test_benchmark_library_creation(benchmark_db: DatabaseService) -> None:
    """Benchmark: Create large synthetic library."""
    with benchmark_db.get_session() as session:
        # Create library
        library = Library(
            name="Benchmark Library",
            path="/benchmark/library",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)

        # Generate 10k items
        generate_synthetic_library(session, library.id, item_count=10000)

        # Verify count
        count_statement = select(MediaItem).where(MediaItem.library_id == library.id)
        items = session.exec(count_statement).all()
        assert len(items) == 10000


@pytest.mark.benchmark
def test_benchmark_search_performance(benchmark_db: DatabaseService) -> None:
    """Benchmark: Search performance on large library (<500ms target)."""
    reset_instrumentation()
    instrumentation = get_instrumentation()

    with benchmark_db.get_session() as session:
        # Create library with 10k items
        library = Library(
            name="Search Benchmark Library",
            path="/search/library",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)

        generate_synthetic_library(session, library.id, item_count=10000)

    # Benchmark various search patterns
    repository = MediaItemRepository()
    repository._db_service = benchmark_db

    # Test 1: Simple title search
    with instrumentation.timer("search.simple_title"):
        results = repository.search("Item 1", limit=100)
    assert len(results) > 0

    # Test 2: Search with year filter
    with instrumentation.timer("search.with_year"):
        with benchmark_db.get_session() as session:
            statement = (
                select(MediaItem)
                .where(MediaItem.title.ilike("%Item 5%"))
                .where(MediaItem.year == 2000)
                .limit(100)
            )
            results = session.exec(statement).all()

    # Test 3: Search by library
    with instrumentation.timer("search.by_library"):
        results = repository.get_by_library(library.id, limit=100, offset=0)
    assert len(results) == 100

    # Test 4: Pagination
    with instrumentation.timer("search.pagination"):
        page1 = repository.get_by_library(library.id, limit=50, offset=0)
        page2 = repository.get_by_library(library.id, limit=50, offset=50)
    assert len(page1) == 50
    assert len(page2) == 50

    # Export metrics
    metrics = instrumentation.get_all_metrics()
    print("\n=== Search Performance Metrics ===")
    for timer_name, timer_data in metrics["timers"].items():
        avg_time = timer_data["avg_time"]
        print(f"{timer_name}: {avg_time * 1000:.2f}ms (avg)")

        # Assert performance targets
        if "search" in timer_name:
            assert avg_time < 0.5, f"{timer_name} exceeded 500ms target: {avg_time * 1000:.2f}ms"


@pytest.mark.benchmark
def test_benchmark_ui_loading(benchmark_db: DatabaseService) -> None:
    """Benchmark: UI list loading (<1s target)."""
    reset_instrumentation()
    instrumentation = get_instrumentation()

    with benchmark_db.get_session() as session:
        # Create library
        library = Library(
            name="UI Benchmark Library",
            path="/ui/library",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)

        generate_synthetic_library(session, library.id, item_count=10000)

    repository = MediaItemRepository()
    repository._db_service = benchmark_db

    # Test initial load (first page, lazy loading)
    with instrumentation.timer("ui.initial_load_lazy"):
        results = repository.get_by_library(
            library.id, limit=100, offset=0, lazy_load=True
        )
    assert len(results) == 100

    # Test initial load (first page, eager loading)
    with instrumentation.timer("ui.initial_load_eager"):
        results = repository.get_by_library(
            library.id, limit=100, offset=0, lazy_load=False
        )
    assert len(results) == 100

    # Test fetchMore pattern (load next page)
    with instrumentation.timer("ui.fetch_more"):
        next_page = repository.get_by_library(
            library.id, limit=100, offset=100, lazy_load=True
        )
    assert len(next_page) == 100

    # Export metrics
    metrics = instrumentation.get_all_metrics()
    print("\n=== UI Loading Performance Metrics ===")
    for timer_name, timer_data in metrics["timers"].items():
        avg_time = timer_data["avg_time"]
        print(f"{timer_name}: {avg_time * 1000:.2f}ms (avg)")

        # Assert performance targets
        if "ui.initial_load" in timer_name:
            assert avg_time < 1.0, f"{timer_name} exceeded 1s target: {avg_time * 1000:.2f}ms"
        elif "ui.fetch_more" in timer_name:
            assert avg_time < 0.5, f"{timer_name} exceeded 500ms target: {avg_time * 1000:.2f}ms"


@pytest.mark.benchmark
def test_benchmark_person_queries(benchmark_db: DatabaseService) -> None:
    """Benchmark: Person/credit queries with indexes."""
    reset_instrumentation()
    instrumentation = get_instrumentation()

    with benchmark_db.get_session() as session:
        # Create library
        library = Library(
            name="Person Benchmark Library",
            path="/person/library",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)

        generate_synthetic_library(session, library.id, item_count=10000)

        # Test: Find all movies with a specific person
        with instrumentation.timer("person.find_by_person"):
            person = session.exec(select(Person).limit(1)).first()
            if person:
                statement = (
                    select(MediaItem)
                    .join(Credit)
                    .where(Credit.person_id == person.id)
                    .limit(100)
                )
                results = session.exec(statement).all()
                assert len(results) > 0

        # Test: Find all actors in a media item
        with instrumentation.timer("person.find_by_media_and_role"):
            statement = (
                select(Person)
                .join(Credit)
                .where(Credit.media_item_id == 1)
                .where(Credit.role == "actor")
            )
            results = session.exec(statement).all()
            assert len(results) > 0

    # Export metrics
    metrics = instrumentation.get_all_metrics()
    print("\n=== Person Query Performance Metrics ===")
    for timer_name, timer_data in metrics["timers"].items():
        avg_time = timer_data["avg_time"]
        print(f"{timer_name}: {avg_time * 1000:.2f}ms (avg)")

        # Person queries should be fast with indexes
        assert avg_time < 0.1, f"{timer_name} exceeded 100ms target: {avg_time * 1000:.2f}ms"


@pytest.mark.benchmark
def test_benchmark_count_queries(benchmark_db: DatabaseService) -> None:
    """Benchmark: Count queries with large datasets."""
    reset_instrumentation()
    instrumentation = get_instrumentation()

    with benchmark_db.get_session() as session:
        # Create library
        library = Library(
            name="Count Benchmark Library",
            path="/count/library",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)

        generate_synthetic_library(session, library.id, item_count=10000)

    repository = MediaItemRepository()
    repository._db_service = benchmark_db

    # Test: Count all items
    with instrumentation.timer("count.all_items"):
        count = repository.count_all()
    assert count == 10000

    # Test: Count by library
    with instrumentation.timer("count.by_library"):
        count = repository.count_by_library(library.id)
    assert count == 10000

    # Export metrics
    metrics = instrumentation.get_all_metrics()
    print("\n=== Count Query Performance Metrics ===")
    for timer_name, timer_data in metrics["timers"].items():
        avg_time = timer_data["avg_time"]
        print(f"{timer_name}: {avg_time * 1000:.2f}ms (avg)")

        # Count queries should be very fast
        assert avg_time < 0.05, f"{timer_name} exceeded 50ms target: {avg_time * 1000:.2f}ms"


if __name__ == "__main__":
    # Run benchmarks with verbose output
    pytest.main([__file__, "-v", "-s", "-m", "benchmark"])
