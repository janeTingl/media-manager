"""Matching performance benchmarks."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.media_manager.persistence.database import DatabaseService
from src.media_manager.persistence.repositories import MediaItemRepository
from src.media_manager.providers.tmdb import TMDbProvider
from src.media_manager.providers.base import BaseProvider

from .data_factories import SyntheticDataFactory
from .conftest import perf_thresholds


@pytest.fixture
def mock_tmdb_provider():
    """Create a mock TMDB provider for testing."""
    provider = Mock(spec=TMDbProvider)
    
    # Mock search results
    mock_search_result = {
        'results': [
            {
                'id': 12345,
                'title': 'Test Movie',
                'release_date': '2020-01-01',
                'overview': 'Test description',
                'vote_average': 7.5,
                'poster_path': '/poster.jpg',
                'backdrop_path': '/backdrop.jpg'
            }
        ]
    }
    
    provider.search_movies = AsyncMock(return_value=mock_search_result)
    provider.search_tv = AsyncMock(return_value=mock_search_result)
    provider.get_movie_details = AsyncMock(return_value=mock_search_result['results'][0])
    provider.get_tv_details = AsyncMock(return_value=mock_search_result['results'][0])
    
    return provider


@pytest.fixture
def matching_library(benchmark_db: DatabaseService) -> int:
    """Create a library for matching benchmarks."""
    with benchmark_db.get_session() as session:
        factory = SyntheticDataFactory(session)
        library = factory.create_synthetic_library(
            item_count=1000,
            library_name="Matching Test Library",
            with_tags=False,  # Faster creation
            with_collections=False,
            with_favorites=False,
            with_credits=False,
        )
        return library.id


@pytest.mark.benchmark
def test_single_movie_matching_performance(
    benchmark, mock_tmdb_provider, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Benchmark single movie matching performance."""
    from src.media_manager.scanner import Scanner
    
    # Create scanner with mock provider
    scanner = Scanner(benchmark_db)
    scanner.providers = {'tmdb': mock_tmdb_provider}
    
    # Get a media item to match
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        item = session.exec(select(MediaItem).limit(1)).first()
        assert item is not None
        
        # Benchmark matching
        async def match_item():
            return await scanner._match_media_item(item)
        
        # Run async benchmark
        import asyncio
        result = benchmark(
            asyncio.run,
            match_item()
        )
        
        assert result is not None


@pytest.mark.benchmark
def test_batch_matching_performance(
    benchmark, mock_tmdb_provider, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Benchmark batch matching performance."""
    from src.media_manager.scanner import Scanner
    
    scanner = Scanner(benchmark_db)
    scanner.providers = {'tmdb': mock_tmdb_provider}
    
    # Get multiple items to match
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        items = session.exec(select(MediaItem).limit(10)).all()
        assert len(items) == 10
        
        # Benchmark batch matching
        async def match_batch():
            results = []
            for item in items:
                result = await scanner._match_media_item(item)
                results.append(result)
            return results
        
        import asyncio
        results = benchmark(
            asyncio.run,
            match_batch()
        )
        
        assert len(results) == 10


@pytest.mark.benchmark
def test_provider_search_performance(
    benchmark, mock_tmdb_provider
) -> None:
    """Benchmark provider search performance."""
    import asyncio
    
    # Benchmark provider search
    result = benchmark(
        asyncio.run,
        mock_tmdb_provider.search_movies("Test Movie", 2020)
    )
    
    assert 'results' in result


@pytest.mark.benchmark
def test_provider_details_fetch_performance(
    benchmark, mock_tmdb_provider
) -> None:
    """Benchmark provider details fetching."""
    import asyncio
    
    # Benchmark details fetching
    result = benchmark(
        asyncio.run,
        mock_tmdb_provider.get_movie_details(12345)
    )
    
    assert result is not None


@pytest.mark.benchmark
def test_matching_cache_performance(
    benchmark, mock_tmdb_provider, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Benchmark matching with cache."""
    from src.media_manager.scanner import Scanner
    
    scanner = Scanner(benchmark_db)
    scanner.providers = {'tmdb': mock_tmdb_provider}
    
    # Enable caching
    scanner.cache_enabled = True
    
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        item = session.exec(select(MediaItem).limit(1)).first()
        assert item is not None
        
        # First match (cache miss)
        async def first_match():
            return await scanner._match_media_item(item)
        
        import asyncio
        result1 = benchmark(
            asyncio.run,
            first_match()
        )
        
        # Second match (cache hit) - should be faster
        async def second_match():
            return await scanner._match_media_item(item)
        
        result2 = benchmark(
            asyncio.run,
            second_match()
        )
        
        assert result1 is not None
        assert result2 is not None


@pytest.mark.benchmark
def test_fuzzy_matching_performance(
    benchmark, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Benchmark fuzzy string matching performance."""
    import difflib
    
    # Get media items for testing
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        items = session.exec(select(MediaItem).limit(100)).all()
        titles = [item.title for item in items]
        
        # Test string for matching
        test_title = "Adventure Test"
        
        # Benchmark fuzzy matching
        def fuzzy_match():
            matches = []
            for title in titles:
                ratio = difflib.SequenceMatcher(None, test_title.lower(), title.lower()).ratio()
                if ratio > 0.6:  # Similarity threshold
                    matches.append((title, ratio))
            return sorted(matches, key=lambda x: x[1], reverse=True)
        
        matches = benchmark(fuzzy_match)
        assert isinstance(matches, list)


@pytest.mark.benchmark
def test_matching_with_various_titles(
    benchmark, mock_tmdb_provider
) -> None:
    """Benchmark matching with various title formats."""
    import asyncio
    
    # Various title formats to test
    test_titles = [
        "The Adventure Begins",
        "Adventure of the Lost City",
        "Journey to Adventure",
        "Adventure Time",
        "Amazing Adventure",
        "Ultimate Adventure",
        "Adventure Returns",
        "Adventure Forever",
        "Adventure Quest",
        "The Final Adventure"
    ]
    
    # Benchmark matching multiple titles
    async def match_multiple_titles():
        results = []
        for title in test_titles:
            result = await mock_tmdb_provider.search_movies(title, 2020)
            results.append(result)
        return results
    
    results = benchmark(
        asyncio.run,
        match_multiple_titles()
    )
    
    assert len(results) == len(test_titles)


@pytest.mark.benchmark
def test_matching_error_handling_performance(
    benchmark, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Benchmark matching error handling performance."""
    from src.media_manager.scanner import Scanner
    
    # Create provider that raises exceptions
    error_provider = Mock(spec=BaseProvider)
    error_provider.search_movies = AsyncMock(side_effect=Exception("Network error"))
    
    scanner = Scanner(benchmark_db)
    scanner.providers = {'tmdb': error_provider}
    
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        item = session.exec(select(MediaItem).limit(1)).first()
        assert item is not None
        
        # Benchmark error handling
        async def match_with_error():
            try:
                return await scanner._match_media_item(item)
            except Exception:
                return None
        
        import asyncio
        result = benchmark(
            asyncio.run,
            match_with_error()
        )
        
        # Should handle error gracefully
        assert result is None


# Performance regression tests
@pytest.mark.benchmark
def test_matching_performance_regression(
    benchmark, mock_tmdb_provider, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Test matching performance doesn't regress."""
    thresholds = perf_thresholds()
    
    from src.media_manager.scanner import Scanner
    scanner = Scanner(benchmark_db)
    scanner.providers = {'tmdb': mock_tmdb_provider}
    
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        item = session.exec(select(MediaItem).limit(1)).first()
        assert item is not None
        
        async def match_item():
            return await scanner._match_media_item(item)
        
        import asyncio
        
        result = benchmark.pedantic(
            lambda: asyncio.run(match_item()),
            iterations=5,
            warmup_rounds=2,
        )
        
        assert result.min < thresholds["match_max_time_per_item"], (
            f"Matching performance regression: {result.min:.3f}s > "
            f"{thresholds['match_max_time_per_item']}s"
        )


@pytest.mark.benchmark
def test_batch_matching_regression(
    benchmark, mock_tmdb_provider, matching_library: int, benchmark_db: DatabaseService
) -> None:
    """Test batch matching performance doesn't regress."""
    thresholds = perf_thresholds()
    
    from src.media_manager.scanner import Scanner
    scanner = Scanner(benchmark_db)
    scanner.providers = {'tmdb': mock_tmdb_provider}
    
    with benchmark_db.get_session() as session:
        from sqlmodel import select
        from src.media_manager.persistence.models import MediaItem
        
        items = session.exec(select(MediaItem).limit(10)).all()
        
        async def match_batch():
            results = []
            for item in items:
                result = await scanner._match_media_item(item)
                results.append(result)
            return results
        
        import asyncio
        
        result = benchmark.pedantic(
            lambda: asyncio.run(match_batch()),
            iterations=3,
            warmup_rounds=1,
        )
        
        # Calculate average time per item
        time_per_item = result.min / len(items)
        
        assert time_per_item < thresholds["match_max_time_per_item"], (
            f"Batch matching regression: {time_per_item:.3f}s per item > "
            f"{thresholds['match_max_time_per_item']}s per item"
        )