"""UI performance benchmarks."""

import pytest
from unittest.mock import Mock, patch

from src.media_manager.persistence.database import DatabaseService
from src.media_manager.persistence.repositories import MediaItemRepository
from src.media_manager.search_results_model import SearchResultsModel
from src.media_manager.media_views import MediaItemModel

from .data_factories import SyntheticDataFactory
from .conftest import perf_thresholds


@pytest.fixture
def large_ui_library(benchmark_db: DatabaseService) -> int:
    """Create a large library for UI benchmarking."""
    with benchmark_db.get_session() as session:
        factory = SyntheticDataFactory(session)
        library = factory.create_synthetic_library(
            item_count=2000,  # Smaller for UI tests
            library_name="UI Performance Library",
            with_tags=True,
            with_collections=True,
            with_favorites=True,
            with_credits=True,
        )
        return library.id


@pytest.fixture
def media_repository(benchmark_db: DatabaseService) -> MediaItemRepository:
    """Create media item repository for testing."""
    return MediaItemRepository(benchmark_db)


@pytest.mark.benchmark
def test_ui_model_initial_load_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark UI model initial loading."""
    # Mock the database service to use our test database
    media_repository._db_service = media_repository._db_service
    
    # Benchmark initial model loading (first page)
    results = benchmark(
        media_repository.get_by_library,
        large_ui_library,
        limit=100,
        offset=0,
        lazy_load=True
    )
    
    assert len(results) == 100


@pytest.mark.benchmark
def test_ui_model_fetch_more_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark UI model fetchMore functionality."""
    media_repository._db_service = media_repository._db_service
    
    # Benchmark fetching next page
    next_page = benchmark(
        media_repository.get_by_library,
        large_ui_library,
        limit=100,
        offset=100,
        lazy_load=True
    )
    
    assert len(next_page) == 100


@pytest.mark.benchmark
def test_ui_model_eager_loading_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark UI model with eager loading."""
    media_repository._db_service = media_repository._db_service
    
    # Benchmark eager loading (with all relationships)
    results = benchmark(
        media_repository.get_by_library,
        large_ui_library,
        limit=50,
        offset=0,
        lazy_load=False
    )
    
    assert len(results) == 50


@pytest.mark.benchmark
def test_ui_search_model_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark search model performance."""
    media_repository._db_service = media_repository._db_service
    
    # Benchmark search with results
    search_results = benchmark(
        media_repository.search,
        "Adventure",
        limit=100
    )
    
    assert isinstance(search_results, list)


@pytest.mark.benchmark
def test_ui_filter_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark UI filtering performance."""
    media_repository._db_service = media_repository._db_service
    
    # Benchmark filtering by year
    filtered_results = benchmark(
        media_repository.get_by_library,
        large_ui_library,
        limit=100,
        offset=0,
        filters={"year": 2020}
    )
    
    assert isinstance(filtered_results, list)


@pytest.mark.benchmark
def test_ui_pagination_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark UI pagination performance."""
    media_repository._db_service = media_repository._db_service
    
    # Benchmark multiple pagination operations
    def paginate_multiple_pages():
        results = []
        for page in range(5):  # Load 5 pages
            page_results = media_repository.get_by_library(
                large_ui_library,
                limit=50,
                offset=page * 50,
                lazy_load=True
            )
            results.extend(page_results)
        return results
    
    all_results = benchmark(paginate_multiple_pages)
    assert len(all_results) == 250  # 5 pages * 50 items


@pytest.mark.benchmark
def test_ui_model_data_conversion_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark data conversion for UI models."""
    media_repository._db_service = media_repository._db_service
    
    # Get raw data
    raw_items = media_repository.get_by_library(
        large_ui_library,
        limit=100,
        offset=0,
        lazy_load=True
    )
    
    # Benchmark conversion to UI model format
    def convert_to_ui_model():
        ui_items = []
        for item in raw_items:
            ui_item = {
                'id': item.id,
                'title': item.title,
                'year': item.year,
                'media_type': item.media_type,
                'rating': item.rating,
                'runtime': item.runtime,
                'poster_url': None,  # Would be populated from artwork
            }
            ui_items.append(ui_item)
        return ui_items
    
    ui_items = benchmark(convert_to_ui_model)
    assert len(ui_items) == 100


@pytest.mark.benchmark
def test_ui_sorting_performance(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark UI sorting performance."""
    media_repository._db_service = media_repository._db_service
    
    # Benchmark sorting by different fields
    def sort_by_title():
        return media_repository.get_by_library(
            large_ui_library,
            limit=100,
            offset=0,
            order_by="title"
        )
    
    def sort_by_year():
        return media_repository.get_by_library(
            large_ui_library,
            limit=100,
            offset=0,
            order_by="year"
        )
    
    def sort_by_rating():
        return media_repository.get_by_library(
            large_ui_library,
            limit=100,
            offset=0,
            order_by="rating"
        )
    
    # Benchmark each sort operation
    title_sorted = benchmark(sort_by_title)
    year_sorted = benchmark(sort_by_year)
    rating_sorted = benchmark(sort_by_rating)
    
    assert len(title_sorted) == 100
    assert len(year_sorted) == 100
    assert len(rating_sorted) == 100


@pytest.mark.benchmark
def test_ui_model_memory_usage(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Benchmark memory usage of UI models."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    media_repository._db_service = media_repository._db_service
    
    # Load larger dataset
    def load_large_dataset():
        return media_repository.get_by_library(
            large_ui_library,
            limit=500,
            offset=0,
            lazy_load=False  # Load with relationships
        )
    
    large_dataset = benchmark(load_large_dataset)
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_used = final_memory - initial_memory
    
    # Check memory usage is reasonable
    thresholds = perf_thresholds()
    assert memory_used < thresholds["memory_max_usage_mb"], (
        f"UI model memory usage too high: {memory_used:.1f}MB > "
        f"{thresholds['memory_max_usage_mb']}MB"
    )


# Performance regression tests
@pytest.mark.benchmark
def test_ui_initial_load_regression(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Test UI initial load performance doesn't regress."""
    thresholds = perf_thresholds()
    
    media_repository._db_service = media_repository._db_service
    
    result = benchmark.pedantic(
        media_repository.get_by_library,
        args=(large_ui_library,),
        kwargs={"limit": 100, "offset": 0, "lazy_load": True},
        iterations=10,
        warmup_rounds=3,
    )
    
    assert result.min < thresholds["ui_initial_load_max_time"], (
        f"UI initial load regression: {result.min:.3f}s > "
        f"{thresholds['ui_initial_load_max_time']}s"
    )


@pytest.mark.benchmark
def test_ui_fetch_more_regression(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Test UI fetch more performance doesn't regress."""
    thresholds = perf_thresholds()
    
    media_repository._db_service = media_repository._db_service
    
    result = benchmark.pedantic(
        media_repository.get_by_library,
        args=(large_ui_library,),
        kwargs={"limit": 100, "offset": 100, "lazy_load": True},
        iterations=15,
        warmup_rounds=5,
    )
    
    assert result.min < thresholds["ui_fetch_more_max_time"], (
        f"UI fetch more regression: {result.min:.3f}s > "
        f"{thresholds['ui_fetch_more_max_time']}s"
    )


@pytest.mark.benchmark
def test_ui_filter_regression(
    benchmark, large_ui_library: int, media_repository: MediaItemRepository
) -> None:
    """Test UI filtering performance doesn't regress."""
    thresholds = perf_thresholds()
    
    media_repository._db_service = media_repository._db_service
    
    result = benchmark.pedantic(
        media_repository.get_by_library,
        args=(large_ui_library,),
        kwargs={"limit": 100, "offset": 0, "filters": {"year": 2020}},
        iterations=10,
        warmup_rounds=3,
    )
    
    assert result.min < thresholds["ui_filter_max_time"], (
        f"UI filter regression: {result.min:.3f}s > "
        f"{thresholds['ui_filter_max_time']}s"
    )