"""Integration tests for the scan-to-match workflow."""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from src.media_manager.main_window import MainWindow
from src.media_manager.match_manager import MatchManager
from src.media_manager.models import MediaType, VideoMetadata
from src.media_manager.scan_engine import ScanEngine
from src.media_manager.scanner import ScanConfig
from src.media_manager.services import get_service_registry, ServiceRegistry
from src.media_manager.workers import WorkerManager


def _touch_file(path: Path) -> None:
    """Create a test file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _setup_test_services() -> ServiceRegistry:
    """Setup test services."""
    registry = get_service_registry()
    registry.clear()
    
    # Register worker manager
    registry.register(WorkerManager, lambda: WorkerManager())
    
    return registry


class TestMatchIntegration:
    """Integration tests for the match workflow."""

    def test_scan_to_match_workflow(self, qapp, tmp_path: Path) -> None:
        """Test the complete scan-to-match workflow."""
        # Setup test services
        _setup_test_services()
        
        # Create test files
        library = tmp_path / "library"
        _touch_file(library / "Movies" / "Inception.2010.1080p.mkv")
        _touch_file(library / "TV" / "Dark.S02E03.1080p.mkv")
        _touch_file(library / "Movies" / "The.Matrix.1999.BluRay.mkv")

        # Create scan engine and perform scan
        engine = ScanEngine()
        config = ScanConfig(root_paths=[library])
        scan_results = engine.scan(config)

        assert len(scan_results) == 3

        # Create match manager
        match_manager = MatchManager()
        matches_spy = QSignalSpy(match_manager.matches_updated)
        status_spy = QSignalSpy(match_manager.status_changed)

        # Add scan results to match manager
        match_manager.add_metadata(scan_results)

        # Verify signals were emitted
        assert len(matches_spy) == 1
        matches = matches_spy[0][0]
        assert len(matches) == 3

        # Verify all items are pending initially
        pending_count = match_manager.get_pending_count()
        assert pending_count == 3
        assert match_manager.get_matched_count() == 0

        # Start matching process
        match_manager.start_matching()

        # Wait for matching to complete (simulate with a small delay)
        qapp.processEvents()
        
        # Verify status updates
        assert len(status_spy) > 0
        status_messages = [call[0][0] for call in status_spy]
        assert any("matching" in msg.lower() for msg in status_messages)

    def test_match_manager_signal_flow(self, qapp) -> None:
        """Test signal flow in match manager."""
        _setup_test_services()
        
        match_manager = MatchManager()
        matches_spy = QSignalSpy(match_manager.matches_updated)
        selected_spy = QSignalSpy(match_manager.match_selected)
        status_spy = QSignalSpy(match_manager.status_changed)

        # Create test metadata
        metadata = VideoMetadata(
            path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023
        )

        # Add metadata
        match_manager.add_metadata([metadata])

        # Verify signals
        assert len(matches_spy) == 1
        assert len(status_spy) == 1
        assert "Added 1 items" in status_spy[0][0]

        # Select match
        matches = matches_spy[0][0]
        match_manager.select_match(matches[0])

        # Verify selection signal
        assert len(selected_spy) == 1
        assert selected_spy[0][0].metadata.title == "Test Movie"

    def test_search_workflow(self, qapp) -> None:
        """Test the manual search workflow."""
        _setup_test_services()
        
        match_manager = MatchManager()
        
        # Create search request
        from src.media_manager.models import SearchRequest
        request = SearchRequest(
            query="Inception",
            media_type=MediaType.MOVIE,
            year=2010
        )

        # Perform search (this will use mock search)
        status_spy = QSignalSpy(match_manager.status_changed)
        match_manager.search_matches(request)

        # Process events to allow background worker to complete
        qapp.processEvents()

        # Verify search was initiated
        assert len(status_spy) > 0
        status_messages = [call[0][0] for call in status_spy]
        assert any("searching" in msg.lower() for msg in status_messages)

    def test_ui_integration(self, qapp) -> None:
        """Test UI component integration."""
        _setup_test_services()
        
        # Create main window
        from src.media_manager.settings import SettingsManager
        settings = SettingsManager()
        main_window = MainWindow(settings)

        # Create test metadata
        metadata = VideoMetadata(
            path=Path("/test/example.mkv"),
            title="Example Movie",
            media_type=MediaType.MOVIE,
            year=2023
        )

        # Add to scan queue
        main_window.add_scan_results([metadata])

        # Verify the matching tab was selected
        assert main_window.tab_widget.currentIndex() == 4  # Matching tab

        # Verify items were added to queue
        queue_matches = main_window.scan_queue_widget.get_matches()
        assert len(queue_matches) == 1
        assert queue_matches[0].metadata.title == "Example Movie"

    def test_match_status_updates(self, qapp) -> None:
        """Test match status updates throughout the workflow."""
        _setup_test_services()
        
        match_manager = MatchManager()
        matches_spy = QSignalSpy(match_manager.matches_updated)

        # Create test metadata
        metadata = VideoMetadata(
            path=Path("/test/movie.mkv"),
            title="Test Movie",
            media_type=MediaType.MOVIE,
            year=2023
        )

        # Add metadata
        match_manager.add_metadata([metadata])
        matches = matches_spy[0][0]
        match = matches[0]

        # Initially pending
        assert match.status.value == "pending"
        assert match.needs_review() is True

        # Update match to matched
        from src.media_manager.models import MatchStatus
        match.status = MatchStatus.MATCHED
        match.confidence = 0.9
        match_manager.update_match(match)

        # Verify update
        updated_matches = matches_spy[-1][0]
        updated_match = updated_matches[0]
        assert updated_match.status.value == "matched"
        assert updated_match.needs_review() is False

    def test_worker_manager_integration(self, qapp) -> None:
        """Test worker manager integration with matching."""
        _setup_test_services()
        
        registry = get_service_registry()
        worker_manager = registry.get(WorkerManager)

        # Create test metadata
        metadata_list = [
            VideoMetadata(
                path=Path(f"/test/movie_{i}.mkv"),
                title=f"Movie {i}",
                media_type=MediaType.MOVIE,
                year=2020 + i
            )
            for i in range(3)
        ]

        # Start match worker
        worker = worker_manager.start_match_worker(metadata_list)
        
        # Verify worker is active
        assert worker_manager.get_active_count() == 1

        # Wait for completion
        match_spy = QSignalSpy(worker.signals.match_found)
        finished_spy = QSignalSpy(worker.signals.finished)
        
        # Process events
        qapp.processEvents()

        # Wait for signals (with timeout)
        finished_spy.wait(5000)  # 5 second timeout

        # Verify results
        assert len(match_spy) == 3
        assert len(finished_spy) >= 1

        # Verify worker is cleaned up
        assert worker_manager.get_active_count() == 0

    def test_error_handling(self, qapp) -> None:
        """Test error handling in the match workflow."""
        _setup_test_services()
        
        match_manager = MatchManager()
        status_spy = QSignalSpy(match_manager.status_changed)

        # Try to start matching with no items
        match_manager.start_matching()

        # Should emit appropriate status message
        assert len(status_spy) >= 1
        assert "no pending" in status_spy[-1][0].lower()

    def test_filter_functionality(self, qapp) -> None:
        """Test filtering functionality in scan queue."""
        _setup_test_services()
        
        from src.media_manager.settings import SettingsManager
        settings = SettingsManager()
        main_window = MainWindow(settings)

        # Create test metadata with different titles
        metadata_list = [
            VideoMetadata(
                path=Path("/test/inception.mkv"),
                title="Inception",
                media_type=MediaType.MOVIE,
                year=2010
            ),
            VideoMetadata(
                path=Path("/test/matrix.mkv"),
                title="The Matrix",
                media_type=MediaType.MOVIE,
                year=1999
            ),
            VideoMetadata(
                path=Path("/test/dark.mkv"),
                title="Dark",
                media_type=MediaType.TV,
                year=2017
            )
        ]

        # Add to queue
        main_window.add_scan_results(metadata_list)

        # Test filtering
        queue_widget = main_window.scan_queue_widget
        queue_widget.filter_edit.setText("Matrix")

        # Should filter to show only Matrix
        visible_count = 0
        for i in range(queue_widget.queue_list.count()):
            if not queue_widget.queue_list.item(i).isHidden():
                visible_count += 1

        assert visible_count == 1

        # Clear filter
        queue_widget.filter_edit.setText("")
        qapp.processEvents()

        # Should show all items
        visible_count = 0
        for i in range(queue_widget.queue_list.count()):
            if not queue_widget.queue_list.item(i).isHidden():
                visible_count += 1

        assert visible_count == 3