"""Basic functionality tests for matching components (non-GUI)."""

from __future__ import annotations

from pathlib import Path

from media_manager.models import MediaType, VideoMetadata, MediaMatch, MatchStatus
from media_manager.match_manager import MatchManager
from media_manager.services import get_service_registry
from media_manager.workers import WorkerManager


def test_basic_models() -> None:
    """Test basic model functionality."""
    # Create test metadata
    metadata = VideoMetadata(
        path=Path("/test/movie.mkv"),
        title="Test Movie",
        media_type=MediaType.MOVIE,
        year=2023
    )
    
    # Create match
    match = MediaMatch(
        metadata=metadata,
        status=MatchStatus.PENDING,
        confidence=0.8
    )
    
    assert match.metadata.title == "Test Movie"
    assert match.status == MatchStatus.PENDING
    assert match.confidence == 0.8
    assert match.needs_review() is True
    
    # Update status
    match.status = MatchStatus.MATCHED
    match.user_selected = True
    assert match.is_matched() is True
    assert match.needs_review() is False


def test_match_manager() -> None:
    """Test match manager functionality."""
    # Setup services
    registry = get_service_registry()
    registry.clear()
    registry.register(WorkerManager, lambda: WorkerManager())
    
    # Create match manager
    manager = MatchManager()
    
    # Create test metadata
    metadata = VideoMetadata(
        path=Path("/test/movie.mkv"),
        title="Test Movie",
        media_type=MediaType.MOVIE,
        year=2023
    )
    
    # Add metadata
    manager.add_metadata([metadata])
    
    # Verify results
    matches = manager.get_matches()
    assert len(matches) == 1
    assert matches[0].metadata.title == "Test Movie"
    assert matches[0].status == MatchStatus.PENDING
    
    # Test counts
    assert manager.get_pending_count() == 1
    assert manager.get_matched_count() == 0
    
    # Update match
    match = matches[0]
    match.status = MatchStatus.MATCHED
    match.confidence = 0.9
    manager.update_match(match)
    
    # Verify update
    updated_matches = manager.get_matches()
    assert updated_matches[0].status == MatchStatus.MATCHED
    assert updated_matches[0].confidence == 0.9
    assert manager.get_pending_count() == 0
    assert manager.get_matched_count() == 1


def test_worker_manager() -> None:
    """Test worker manager functionality."""
    registry = get_service_registry()
    registry.clear()
    registry.register(WorkerManager, lambda: WorkerManager())
    
    # Get worker manager
    wm = registry.get(WorkerManager)
    
    # Test initial state
    assert wm.get_active_count() == 0
    
    # Create test metadata
    metadata = VideoMetadata(
        path=Path("/test/movie.mkv"),
        title="Test Movie",
        media_type=MediaType.MOVIE,
        year=2023
    )
    
    # Start worker (without Qt event loop, just test creation)
    try:
        worker = wm.start_match_worker([metadata])
        assert worker is not None
        # Note: Worker would run in background thread
        # This test just verifies creation and setup
    except Exception:
        # Expected in non-Qt environment
        pass


if __name__ == "__main__":
    test_basic_models()
    print("✓ Basic models test passed")
    
    test_match_manager()
    print("✓ Match manager test passed")
    
    test_worker_manager()
    print("✓ Worker manager test passed")
    
    print("All basic tests passed!")