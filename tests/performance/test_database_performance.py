"""Database performance benchmarks using pytest-benchmark."""

import os
import pytest
from pathlib import Path
from sqlmodel import Session, select

# Set environment variable to avoid Qt issues in performance tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.media_manager.persistence.database import DatabaseService
from src.media_manager.persistence.repositories import MediaItemRepository
from src.media_manager.persistence.models import (
    Library,
    MediaItem,
    Person,
    Credit,
)

from .data_factories import SyntheticDataFactory
from .conftest import perf_thresholds


@pytest.fixture
def benchmark_db(tmp_path: Path) -> DatabaseService:
    """Create a temporary database for benchmarking."""
    db_path = tmp_path / "benchmark.db"
    db_service = DatabaseService(f"sqlite:///{db_path}")
    db_service.create_all()
    return db_service


@pytest.fixture
def large_library(benchmark_db: DatabaseService) -> Library:
    """Create a large library for benchmarking."""
    with benchmark_db.get_session() as session:
        factory = SyntheticDataFactory(session)
        library = factory.create_synthetic_library(
            item_count=5000,
            library_name="Performance Benchmark Library",
            with_tags=True,
            with_collections=True,
            with_favorites=True,
            with_credits=True,
        )
        return library


@pytest.mark.benchmark
def test_database_search_performance(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark database search queries."""
    # Initialize repository with test database
    repository = MediaItemRepository(database_service=benchmark_db)
    
    # Benchmark simple title search
    result = benchmark(
        repository.search,
        "Adventure",
        limit=100
    )
    assert len(result) > 0


@pytest.mark.benchmark
def test_database_search_by_year(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark search with year filter."""
    repository = MediaItemRepository(database_service=benchmark_db)
    
    with benchmark_db.get_session() as session:
        statement = (
            select(MediaItem)
            .where(MediaItem.title.ilike("%Adventure%"))
            .where(MediaItem.year == 2020)
            .limit(100)
        )
        result = benchmark(session.exec, statement)
        items = result.all()
        assert isinstance(items, list)


@pytest.mark.benchmark
def test_database_pagination_performance(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark database pagination."""
    repository = MediaItemRepository(database_service=benchmark_db)
    
    # Benchmark first page
    page1 = benchmark(
        repository.get_by_library,
        large_library.id,
        limit=50,
        offset=0
    )
    assert len(page1) == 50


@pytest.mark.benchmark
def test_database_count_performance(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark count queries."""
    repository = MediaItemRepository(database_service=benchmark_db)
    
    # Benchmark count all
    count = benchmark(repository.count_all)
    assert count == 5000


@pytest.mark.benchmark
def test_database_count_by_library(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark count by library."""
    repository = MediaItemRepository(database_service=benchmark_db)
    
    # Benchmark count by library
    count = benchmark(
        repository.count_by_library,
        large_library.id
    )
    assert count == 5000


@pytest.mark.benchmark
def test_person_join_query_performance(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark queries with person joins."""
    with benchmark_db.get_session() as session:
        # Find first person
        person = session.exec(select(Person).limit(1)).first()
        assert person is not None
        
        # Benchmark query for media items by person
        statement = (
            select(MediaItem)
            .join(Credit)
            .where(Credit.person_id == person.id)
            .limit(100)
        )
        result = benchmark(session.exec, statement)
        items = result.all()
        assert len(items) > 0


@pytest.mark.benchmark
def test_complex_filter_query(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Benchmark complex filter queries."""
    with benchmark_db.get_session() as session:
        # Complex query with multiple conditions
        statement = (
            select(MediaItem)
            .where(MediaItem.year.between(2010, 2020))
            .where(MediaItem.rating >= 7.0)
            .where(MediaItem.media_type == "movie")
            .limit(100)
        )
        result = benchmark(session.exec, statement)
        items = result.all()
        assert isinstance(items, list)


@pytest.mark.benchmark
def test_bulk_insert_performance(
    benchmark, benchmark_db: DatabaseService
) -> None:
    """Benchmark bulk insert operations."""
    with benchmark_db.get_session() as session:
        # Create library
        library = Library(
            name="Bulk Insert Test Library",
            path="/test/bulk_insert",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)
        
        # Benchmark bulk insert of 100 items
        def bulk_insert():
            items = []
            for i in range(100):
                item = MediaItem(
                    library_id=library.id,
                    title=f"Bulk Item {i}",
                    media_type="movie",
                    year=2020 + i,
                    description=f"Description for bulk item {i}",
                )
                items.append(item)
            
            session.add_all(items)
            session.commit()
        
        benchmark(bulk_insert)
        
        # Verify count
        count = session.exec(
            select(MediaItem).where(MediaItem.library_id == library.id)
        ).all()
        assert len(count) == 100


# Performance regression tests
@pytest.mark.benchmark
def test_search_performance_regression(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Test search performance doesn't regress beyond threshold."""
    repository = MediaItemRepository()
    repository._db_service = benchmark_db
    thresholds = perf_thresholds()
    
    # Run benchmark and check against threshold
    result = benchmark.pedantic(
        repository.search,
        args=("Adventure",),
        kwargs={"limit": 100},
        iterations=5,
        warmup_rounds=2,
    )
    
    # Check that the minimum time is below threshold
    assert result.min < thresholds["db_search_max_time"], (
        f"Search performance regression: {result.min:.3f}s > "
        f"{thresholds['db_search_max_time']}s"
    )


@pytest.mark.benchmark
def test_pagination_performance_regression(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Test pagination performance doesn't regress."""
    repository = MediaItemRepository()
    repository._db_service = benchmark_db
    thresholds = perf_thresholds()
    
    result = benchmark.pedantic(
        repository.get_by_library,
        args=(large_library.id,),
        kwargs={"limit": 50, "offset": 0},
        iterations=10,
        warmup_rounds=3,
    )
    
    assert result.min < thresholds["ui_initial_load_max_time"], (
        f"Pagination performance regression: {result.min:.3f}s > "
        f"{thresholds['ui_initial_load_max_time']}s"
    )


@pytest.mark.benchmark
def test_count_performance_regression(
    benchmark, large_library: Library, benchmark_db: DatabaseService
) -> None:
    """Test count query performance doesn't regress."""
    repository = MediaItemRepository()
    repository._db_service = benchmark_db
    thresholds = perf_thresholds()
    
    result = benchmark.pedantic(
        repository.count_by_library,
        args=(large_library.id,),
        iterations=20,
        warmup_rounds=5,
    )
    
    assert result.min < thresholds["db_count_max_time"], (
        f"Count performance regression: {result.min:.3f}s > "
        f"{thresholds['db_count_max_time']}s"
    )