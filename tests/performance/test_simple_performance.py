"""Simple performance test to validate setup."""

import os
import pytest
from pathlib import Path

# Set environment variable to avoid Qt issues
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.media_manager.persistence.database import DatabaseService
from src.media_manager.persistence.repositories import MediaItemRepository
from src.media_manager.persistence.models import Library, MediaItem

from .data_factories import SyntheticDataFactory


@pytest.fixture
def simple_db(tmp_path: Path) -> DatabaseService:
    """Create a simple temporary database for testing."""
    db_path = tmp_path / "simple.db"
    db_service = DatabaseService(f"sqlite:///{db_path}")
    db_service.create_all()
    return db_service


@pytest.mark.benchmark
def test_simple_search_performance(benchmark, simple_db: DatabaseService) -> None:
    """Simple benchmark test to validate setup."""
    repository = MediaItemRepository(database_service=simple_db)
    
    # Create a simple library
    with simple_db.get_session() as session:
        factory = SyntheticDataFactory(session)
        library = factory.create_synthetic_library(
            item_count=100,  # Small dataset for testing
            library_name="Simple Test Library",
            with_tags=False,
            with_collections=False,
            with_favorites=False,
            with_credits=False,
        )
    
    # Benchmark simple search
    result = benchmark(
        repository.search,
        "Adventure",
        limit=10
    )
    assert len(result) >= 0  # Should not error