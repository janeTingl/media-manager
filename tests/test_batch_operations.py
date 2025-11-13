from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlmodel import select

from src.media_manager.batch_operations_service import (
    BatchOperationConfig,
    BatchOperationsService,
)
from src.media_manager.persistence.database import get_database_service, init_database_service
from src.media_manager.persistence.models import HistoryEvent, Library, MediaFile, MediaItem


@pytest.fixture
def temp_db(tmp_path):
    """Return a temporary database URL."""
    db_path = tmp_path / "test.db"
    return f"sqlite:///{db_path}"


def _create_library(session, name: str, path: Path, media_type: str = "movie") -> Library:
    library = Library(name=name, path=str(path), media_type=media_type)
    session.add(library)
    session.commit()
    session.refresh(library)
    return library


def test_batch_rename_uses_templates_and_updates_db(temp_db, temp_settings, tmp_path):
    """Batch rename should move files according to templates and persist changes."""
    init_database_service(temp_db, auto_migrate=False)
    service = BatchOperationsService(settings=temp_settings)

    library_path = tmp_path / "library"
    library_path.mkdir()

    db_service = get_database_service()
    with db_service.get_session() as session:
        library = _create_library(session, "Movies", library_path)

        original_path = library_path / "Example.Movie.2020.mkv"
        original_path.write_text("content")

        item = MediaItem(
            title="Example Movie",
            media_type="movie",
            library_id=library.id,
            year=2020,
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        media_file = MediaFile(
            media_item_id=item.id,
            path=str(original_path),
            filename=original_path.name,
            file_size=1024,
        )
        session.add(media_file)
        session.commit()
        item_id = item.id

    summary = service.perform([item_id], BatchOperationConfig(rename=True))

    expected_path = library_path / "Example Movie (2020)" / "Example Movie (2020).mkv"
    assert expected_path.exists()
    assert not original_path.exists()

    with db_service.get_session() as session:
        db_item = session.get(MediaItem, item_id)
        assert db_item is not None
        file_stmt = select(MediaFile).where(MediaFile.media_item_id == item_id)
        files = session.exec(file_stmt).all()
        assert len(files) == 1
        assert Path(files[0].path) == expected_path

        history_stmt = select(HistoryEvent).where(HistoryEvent.media_item_id == item_id)
        history_events = session.exec(history_stmt).all()
        assert len(history_events) == 1
        history_data = json.loads(history_events[0].event_data)
        assert any("renamed" in action for action in history_data.get("actions", []))

    assert summary.total == 1
    assert summary.processed == 1
    assert summary.renamed == 1
    assert summary.moved == 0
    assert summary.errors == []


def test_batch_move_updates_library_and_paths(temp_db, temp_settings, tmp_path):
    """Moving items should relocate files and update the library assignment."""
    init_database_service(temp_db, auto_migrate=False)
    service = BatchOperationsService(settings=temp_settings)

    source_path = tmp_path / "source"
    dest_path = tmp_path / "destination"
    source_path.mkdir()
    dest_path.mkdir()

    db_service = get_database_service()
    with db_service.get_session() as session:
        source_library = _create_library(session, "Source", source_path)
        dest_library = _create_library(session, "Destination", dest_path)

        original_path = source_path / "Move.Me.mkv"
        original_path.write_text("content")

        item = MediaItem(
            title="Move Me",
            media_type="movie",
            library_id=source_library.id,
            year=2021,
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        media_file = MediaFile(
            media_item_id=item.id,
            path=str(original_path),
            filename=original_path.name,
            file_size=2048,
        )
        session.add(media_file)
        session.commit()
        item_id = item.id
        dest_library_id = dest_library.id

    summary = service.perform(
        [item_id],
        BatchOperationConfig(move_library_id=dest_library_id),
    )

    expected_path = dest_path / "Move.Me.mkv"
    assert expected_path.exists()
    assert not original_path.exists()

    with db_service.get_session() as session:
        db_item = session.get(MediaItem, item_id)
        assert db_item is not None
        assert db_item.library_id == dest_library_id

        file_stmt = select(MediaFile).where(MediaFile.media_item_id == item_id)
        files = session.exec(file_stmt).all()
        assert len(files) == 1
        assert Path(files[0].path) == expected_path

        history_stmt = select(HistoryEvent).where(HistoryEvent.media_item_id == item_id)
        history_events = session.exec(history_stmt).all()
        assert len(history_events) == 1
        history_data = json.loads(history_events[0].event_data)
        assert any("moved" in action for action in history_data.get("actions", []))

    assert summary.total == 1
    assert summary.processed == 1
    assert summary.moved == 1
    assert summary.errors == []
