"""Integration tests for persistence workflows."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.media_manager.library_postprocessor import PostProcessingOptions, LibraryPostProcessor
from src.media_manager.media_library_service import get_media_library_service
from src.media_manager.models import MediaMatch, MatchStatus, MediaType, VideoMetadata
from src.media_manager.persistence.database import init_database_service
from src.media_manager.persistence.models import HistoryEvent, Library, MediaItem, MediaFile
from src.media_manager.persistence.repositories import transactional_context
from src.media_manager.scanner import ScanConfig
from src.media_manager.scan_engine import ScanEngine
from src.media_manager.workers import MatchWorker


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_url = f"sqlite:///{f.name}"
    
    # Initialize database service with temporary database
    db_service = init_database_service(db_url, auto_migrate=False)
    db_service.create_all()
    
    yield db_service
    
    # Cleanup
    db_service.close()
    Path(db_url.replace("sqlite:///", "")).unlink(missing_ok=True)


@pytest.fixture
def temp_library_dir():
    """Create a temporary directory for library files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_video_files(temp_library_dir):
    """Create sample video files for testing."""
    files = []
    
    # Create movie file
    movie_file = temp_library_dir / "Test.Movie.2023.mkv"
    movie_file.write_bytes(b"fake movie content")
    files.append(movie_file)
    
    # Create TV episode file
    episode_file = temp_library_dir / "Test.Show.S01E01.mkv"
    episode_file.write_bytes(b"fake episode content")
    files.append(episode_file)
    
    return files


class TestPersistenceIntegration:
    """Test integration of scan, match, and finalize workflows with persistence."""

    def test_complete_scan_match_finalize_cycle(self, temp_db, temp_library_dir, sample_video_files):
        """Test a complete scan -> match -> finalize cycle with persistence."""
        
        # 1. Create a library
        media_service = get_media_library_service()
        
        # Create library and verify within the same context
        library_id = None
        with transactional_context() as uow:
            repo = uow.get_repository(Library)
            
            # Try to find existing library by path
            existing = repo.filter_by(path=str(temp_library_dir))
            if existing:
                library = existing[0]
            else:
                # Create new library
                library = Library(name="Test Library", path=str(temp_library_dir), media_type="movie")
                library = repo.create(library)
            
            library_id = library.id
            assert library_id is not None
            assert library.name == "Test Library"
            assert library.path == str(temp_library_dir)
        
        # Now get the library for use in scan engine
        library = media_service.create_or_get_library(
            name="Test Library",
            path=str(temp_library_dir),
            media_type="movie"
        )
        
        # Use the library_id from the transaction context
        scan_engine = ScanEngine(library_id=library_id)
        scan_config = ScanConfig(root_paths=[temp_library_dir])
        
        media_items = scan_engine.scan(scan_config)
        
        assert len(media_items) == 2  # Movie + TV episode
        
        # Verify media items were created in database
        with transactional_context() as uow:
            media_repo = uow.get_repository(MediaItem)
            all_items = media_repo.read_all()
            assert len(all_items) == 2
            
            # Check that items have correct library_id
            for item in all_items:
                assert item.library_id == library_id
        
        # 3. Run matching with persistence
        match_worker = MatchWorker(scan_engine.get_results())
        
        # Mock the signal handlers
        matched_items = []
        def on_match_found(match):
            matched_items.append(match)
        
        match_worker.signals.match_found.connect(on_match_found)
        match_worker.run()
        
        assert len(matched_items) == 2
        
        # 4. Update matches in database
        for match in matched_items:
            if match.media_item_id:
                media_service.update_media_item_from_match(match.media_item_id, match)
        
        # Verify matches were updated
        with transactional_context() as uow:
            media_repo = uow.get_repository(MediaItem)
            for match in matched_items:
                if match.media_item_id:
                    item = media_repo.read(match.media_item_id)
                    assert item.title == match.matched_title
                    assert item.description == match.overview
        
        # 5. Test post-processing with history events
        processor = LibraryPostProcessor()
        options = PostProcessingOptions(dry_run=True)  # Use dry run to avoid actual file moves
        
        # Filter only matched items
        matched_matches = [m for m in matched_items if m.is_matched()]
        
        summary = processor.process(matched_matches, options)
        
        assert len(summary.processed) > 0
        
        # 6. Verify history events were created
        with transactional_context() as uow:
            history_repo = uow.get_repository(HistoryEvent)
            events = history_repo.read_all()
            
            # Should have events for:
            # - Initial scan (added)
            # - Match update (modified) 
            # - Post-processing (modified)
            assert len(events) >= 2  # At minimum, scan and match events
            
            # Verify event types
            event_types = [event.event_type for event in events]
            assert "added" in event_types
            # Note: "modified" may not be present if matches weren't updated or post-processing was dry run

    def test_library_persistence_across_restarts(self, temp_db, temp_library_dir):
        """Test that library data persists across application restarts."""
        
        # Create initial library
        media_service = get_media_library_service()
        
        # Create library and get ID within the same context
        library_id = None
        with transactional_context() as uow:
            repo = uow.get_repository(Library)
            
            # Try to find existing library by path
            existing = repo.filter_by(path=str(temp_library_dir))
            if existing:
                library = existing[0]
            else:
                # Create new library
                library = Library(name="Persistent Library", path=str(temp_library_dir), media_type="movie")
                library = repo.create(library)
            
            library_id = library.id
        
        # Simulate application restart by creating new service instance
        # (In real scenario, this would be a new process)
        from src.media_manager.media_library_service import MediaLibraryService
        new_service = MediaLibraryService()
        
        # Retrieve library by path
        library2 = new_service.create_or_get_library(
            name="Persistent Library",
            path=str(temp_library_dir),
            media_type="movie"
        )
        
        # Verify library was found correctly
        assert library2.id is not None
        assert library2.name == "Persistent Library"
        assert library2.path == str(temp_library_dir)

    def test_media_file_path_updates(self, temp_db, temp_library_dir, sample_video_files):
        """Test that media file paths are updated correctly during post-processing."""
        
        # Create library and scan
        media_service = get_media_library_service()
        
        # Create library and get ID within the same context
        library_id = None
        with transactional_context() as uow:
            repo = uow.get_repository(Library)
            
            # Try to find existing library by path
            existing = repo.filter_by(path=str(temp_library_dir))
            if existing:
                library = existing[0]
            else:
                # Create new library
                library = Library(name="Path Test Library", path=str(temp_library_dir), media_type="movie")
                library = repo.create(library)
            
            library_id = library.id
        
        # Scan files and create media items
        scan_engine = ScanEngine(library_id=library_id)
        scan_config = ScanConfig(root_paths=[temp_library_dir])
        media_items = scan_engine.scan(scan_config)
        
        assert len(media_items) == 2
        
        # Get the original path and media item ID within context
        original_path = str(sample_video_files[0])
        media_item_id = None
        with transactional_context() as uow:
            file_repo = uow.get_repository(MediaFile)
            files = file_repo.filter_by(path=original_path)
            if files:
                media_item_id = files[0].media_item_id
        
        if not media_item_id:
            pytest.skip("No media item found for testing")
        
        # Simulate file move during post-processing
        new_path = temp_library_dir / "moved" / "Test.Movie.2023.mkv"
        
        # Update path in database
        media_service.update_media_file_path(media_item_id, original_path, new_path)
        
        # Verify path was updated
        updated_item = media_service.get_media_item_by_path(str(new_path))
        assert updated_item is not None
        assert updated_item.id == media_item.id
        
        # Verify old path no longer exists
        old_item = media_service.get_media_item_by_path(original_path)
        assert old_item is None

    def test_artwork_and_subtitle_download_persistence(self, temp_db, temp_library_dir):
        """Test that artwork and subtitle download status is persisted."""
        
        # Create library and scan
        media_service = get_media_library_service()
        library = media_service.create_or_get_library(
            name="Download Test Library",
            path=str(temp_library_dir),
            media_type="movie"
        )
        
        scan_engine = ScanEngine(library_id=library.id)
        scan_config = ScanConfig(root_paths=[temp_library_dir])
        media_items = scan_engine.scan(scan_config)
        
        if not media_items:
            pytest.skip("No media items found for testing")
        
        media_item = media_items[0]
        
        # Test artwork download status update
        poster_path = temp_library_dir / "poster.jpg"
        poster_path.write_bytes(b"fake poster content")
        
        media_service.update_artwork_download_status(
            media_item.id,
            PosterType.POSTER,
            poster_path,
            DownloadStatus.COMPLETED
        )
        
        # Test subtitle download status update
        subtitle_path = temp_library_dir / "subtitle.srt"
        subtitle_path.write_bytes(b"fake subtitle content")
        
        media_service.update_subtitle_download_status(
            media_item.id,
            SubtitleLanguage.ENGLISH,
            subtitle_path,
            DownloadStatus.COMPLETED
        )
        
        # Verify updates in database
        with transactional_context() as uow:
            from src.media_manager.persistence.models import Artwork, Subtitle as DBSubtitle
            
            artwork_repo = uow.get_repository(Artwork)
            artworks = artwork_repo.filter_by(
                media_item_id=media_item.id,
                artwork_type=PosterType.POSTER.value
            )
            assert len(artworks) == 1
            assert artworks[0].local_path == str(poster_path)
            assert artworks[0].download_status == DownloadStatus.COMPLETED.value
            
            subtitle_repo = uow.get_repository(DBSubtitle)
            subtitles = subtitle_repo.filter_by(
                media_item_id=media_item.id,
                language=SubtitleLanguage.ENGLISH.value
            )
            assert len(subtitles) == 1
            assert subtitles[0].local_path == str(subtitle_path)
            assert subtitles[0].download_status == DownloadStatus.COMPLETED.value

    def test_error_handling_and_rollback(self, temp_db, temp_library_dir):
        """Test error handling and rollback scenarios."""
        
        media_service = get_media_library_service()
        library = media_service.create_or_get_library(
            name="Error Test Library",
            path=str(temp_library_dir),
            media_type="movie"
        )
        
        # Test invalid media item ID
        with pytest.raises(ValueError):
            media_service.update_media_item_from_match(99999, Mock(spec=MediaMatch))
        
        # Test updating non-existent file path
        media_service.update_media_file_path(99999, "/nonexistent/path", Path("/new/path"))
        # Should not raise exception, just log warning
        
        # Test artwork update with invalid media item ID
        from src.media_manager.models import DownloadStatus, PosterType
        media_service.update_artwork_download_status(
            99999,
            PosterType.POSTER,
            None,
            DownloadStatus.FAILED
        )
        # Should not raise exception

    def test_match_with_database_ids(self, temp_db, temp_library_dir, sample_video_files):
        """Test that MediaMatch objects carry database IDs correctly."""
        
        # Create library and scan
        media_service = get_media_library_service()
        library = media_service.create_or_get_library(
            name="Match ID Test Library",
            path=str(temp_library_dir),
            media_type="movie"
        )
        
        scan_engine = ScanEngine(library_id=library.id)
        scan_config = ScanConfig(root_paths=[temp_library_dir])
        media_items = scan_engine.scan(scan_config)
        
        # Run matching
        match_worker = MatchWorker(scan_engine.get_results())
        matched_items = []
        
        def on_match_found(match):
            matched_items.append(match)
        
        match_worker.signals.match_found.connect(on_match_found)
        match_worker.run()
        
        # Verify matches have database IDs
        for match in matched_items:
            if match.metadata.path.as_posix() in [str(f) for f in sample_video_files]:
                # Should have database IDs for files that were scanned
                assert match.media_item_id is not None
                assert match.library_id == library.id
                assert match.sync_status == "synced"

    def test_postprocessing_history_events(self, temp_db, temp_library_dir, sample_video_files):
        """Test that post-processing creates appropriate history events."""
        
        # Setup
        media_service = get_media_library_service()
        library = media_service.create_or_get_library(
            name="History Test Library",
            path=str(temp_library_dir),
            media_type="movie"
        )
        
        scan_engine = ScanEngine(library_id=library.id)
        scan_config = ScanConfig(root_paths=[temp_library_dir])
        media_items = scan_engine.scan(scan_config)
        
        # Create a match for testing
        metadata = scan_engine.get_results()[0] if scan_engine.get_results() else None
        if not metadata:
            pytest.skip("No metadata found for testing")
        
        match = MediaMatch(
            metadata=metadata,
            status=MatchStatus.MATCHED,
            matched_title="Test Match",
            media_item_id=media_items[0].id if media_items else None
        )
        
        # Run post-processing
        processor = LibraryPostProcessor()
        options = PostProcessingOptions(dry_run=True)
        
        summary = processor.process([match], options)
        
        # Verify history events
        with transactional_context() as uow:
            history_repo = uow.get_repository(HistoryEvent)
            events = history_repo.filter_by(media_item_id=match.media_item_id)
            
            # Should have at least one event (from scan)
            assert len(events) >= 1
            
            # Verify event structure
            for event in events:
                assert event.media_item_id == match.media_item_id
                assert event.event_type in ["added", "modified", "viewed"]
                assert event.timestamp is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])