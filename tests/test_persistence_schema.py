"""Tests for database persistence schema and repositories."""

import pytest
from datetime import datetime
from pathlib import Path

from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from media_manager.persistence.database import DatabaseService, init_database_service
from media_manager.persistence.models import (
    Library,
    MediaItem,
    MediaFile,
    ExternalId,
    Artwork,
    Subtitle,
    Trailer,
    Person,
    Credit,
    Company,
    Tag,
    Collection,
    Favorite,
    HistoryEvent,
    JobRun,
)
from media_manager.persistence.repositories import Repository, UnitOfWork, transactional_context


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
    import media_manager.persistence.database as db_module
    db_module._database_service = db_service

    session = Session(engine)

    yield db_service, session

    session.close()
    engine.dispose()
    db_module._database_service = None


class TestTableCreation:
    """Test that all tables are created correctly."""

    def test_all_tables_created(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Verify all required tables are created."""
        db_service, session = in_memory_db

        # Get all table names
        inspector_tables = set(SQLModel.metadata.tables.keys())

        expected_tables = {
            "library",
            "mediaitem",
            "mediafile",
            "externalid",
            "artwork",
            "subtitle",
            "trailer",
            "person",
            "credit",
            "company",
            "tag",
            "mediaitemtag",
            "collection",
            "mediaitemcollection",
            "favorite",
            "historyevent",
            "jobrun",
        }

        assert expected_tables.issubset(inspector_tables), f"Missing tables: {expected_tables - inspector_tables}"


class TestLibraryCRUD:
    """Test Library CRUD operations."""

    def test_create_library(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating a library."""
        db_service, session = in_memory_db

        library = Library(
            name="Test Library",
            path="/test/path",
            media_type="movie",
            description="Test library for movies"
        )

        session.add(library)
        session.commit()

        # Verify creation
        assert library.id is not None
        assert library.name == "Test Library"
        assert library.path == "/test/path"
        assert library.media_type == "movie"

    def test_read_library(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test reading a library."""
        db_service, session = in_memory_db

        # Create
        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()
        library_id = library.id

        # Clear session to force fresh read
        session.expunge_all()

        # Read
        from sqlmodel import select
        read_lib = session.exec(select(Library).where(Library.id == library_id)).first()
        assert read_lib is not None
        assert read_lib.name == "Test"

    def test_update_library(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test updating a library."""
        db_service, session = in_memory_db

        # Create
        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        # Update
        library.name = "Updated"
        session.add(library)
        session.commit()

        # Verify
        assert library.name == "Updated"

    def test_delete_library(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test deleting a library."""
        db_service, session = in_memory_db

        # Create
        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()
        library_id = library.id

        # Delete
        session.delete(library)
        session.commit()

        # Verify
        from sqlmodel import select
        read_lib = session.exec(select(Library).where(Library.id == library_id)).first()
        assert read_lib is None


class TestMediaItemCRUD:
    """Test MediaItem CRUD operations."""

    def test_create_media_item(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating a media item."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(
            library_id=library.id,
            title="Test Movie",
            media_type="movie",
            year=2023,
            runtime=120,
        )

        session.add(item)
        session.commit()

        assert item.id is not None
        assert item.title == "Test Movie"
        assert item.year == 2023

    def test_create_tv_episode(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating a TV episode."""
        db_service, session = in_memory_db

        library = Library(name="TV", path="/tv", media_type="tv")
        session.add(library)
        session.commit()

        episode = MediaItem(
            library_id=library.id,
            title="Pilot",
            media_type="tv",
            season=1,
            episode=1,
            runtime=45,
        )

        session.add(episode)
        session.commit()

        assert episode.season == 1
        assert episode.episode == 1


class TestMediaFileCRUD:
    """Test MediaFile CRUD operations."""

    def test_create_media_file(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating a media file."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(library_id=library.id, title="Test", media_type="movie")
        session.add(item)
        session.commit()

        media_file = MediaFile(
            media_item_id=item.id,
            path="/test/movie.mkv",
            filename="movie.mkv",
            file_size=1024000,
            duration=7200,
            container="matroska",
            video_codec="h264",
            audio_codec="aac",
            resolution="1920x1080",
        )

        session.add(media_file)
        session.commit()

        assert media_file.id is not None
        assert media_file.path == "/test/movie.mkv"
        assert media_file.file_size == 1024000


class TestExternalIdCRUD:
    """Test ExternalId CRUD operations."""

    def test_create_external_ids(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating external IDs."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(library_id=library.id, title="Test", media_type="movie")
        session.add(item)
        session.commit()

        # Add TMDB ID
        tmdb_id = ExternalId(
            media_item_id=item.id,
            source="tmdb",
            external_id="12345"
        )
        session.add(tmdb_id)

        # Add TVDB ID
        tvdb_id = ExternalId(
            media_item_id=item.id,
            source="tvdb",
            external_id="67890"
        )
        session.add(tvdb_id)

        session.commit()

        assert tmdb_id.id is not None
        assert tvdb_id.id is not None


class TestArtworkCRUD:
    """Test Artwork CRUD operations."""

    def test_create_artwork(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating artwork."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(library_id=library.id, title="Test", media_type="movie")
        session.add(item)
        session.commit()

        artwork = Artwork(
            media_item_id=item.id,
            artwork_type="poster",
            url="https://example.com/poster.jpg",
            local_path="/test/poster.jpg",
            size="medium",
            width=342,
            height=513,
            download_status="completed",
        )

        session.add(artwork)
        session.commit()

        assert artwork.id is not None
        assert artwork.artwork_type == "poster"
        assert artwork.download_status == "completed"


class TestSubtitleCRUD:
    """Test Subtitle CRUD operations."""

    def test_create_subtitles(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating subtitles."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(library_id=library.id, title="Test", media_type="movie")
        session.add(item)
        session.commit()

        # English subtitle
        en_sub = Subtitle(
            media_item_id=item.id,
            language="en",
            format="srt",
            provider="OpenSubtitles",
            url="https://example.com/en.srt",
            local_path="/test/movie.en.srt",
            download_status="completed",
        )
        session.add(en_sub)

        # Spanish subtitle
        es_sub = Subtitle(
            media_item_id=item.id,
            language="es",
            format="srt",
            download_status="pending",
        )
        session.add(es_sub)

        session.commit()

        assert en_sub.id is not None
        assert es_sub.id is not None


class TestPersonAndCreditCRUD:
    """Test Person and Credit CRUD operations."""

    def test_create_person_and_credits(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating persons and credits."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(library_id=library.id, title="Test", media_type="movie")
        session.add(item)
        session.commit()

        # Create person
        person = Person(
            name="Test Actor",
            external_id="12345",
            biography="A test actor"
        )
        session.add(person)
        session.commit()

        # Create credit
        credit = Credit(
            media_item_id=item.id,
            person_id=person.id,
            role="actor",
            character_name="Main Character",
            order=0,
        )
        session.add(credit)
        session.commit()

        assert credit.id is not None
        assert credit.person.name == "Test Actor"


class TestTagAndCollectionCRUD:
    """Test Tag and Collection CRUD operations."""

    def test_create_tags_and_collections(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating tags and collections."""
        db_service, session = in_memory_db

        library = Library(name="Test", path="/test", media_type="movie")
        session.add(library)
        session.commit()

        item = MediaItem(library_id=library.id, title="Test", media_type="movie")
        session.add(item)
        session.commit()

        # Create tag
        tag = Tag(name="Favorite", color="#FF0000")
        session.add(tag)
        session.commit()

        # Create collection
        collection = Collection(name="Best Movies", description="My favorite movies")
        session.add(collection)
        session.commit()

        assert tag.id is not None
        assert collection.id is not None


class TestRepository:
    """Test Repository CRUD helpers."""

    def test_repository_create(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test repository create operation."""
        db_service, session = in_memory_db

        repo = Repository(session, Library)
        library = Library(name="Test", path="/test", media_type="movie")
        created = repo.create(library)

        assert created.id is not None

    def test_repository_read(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test repository read operation."""
        db_service, session = in_memory_db

        repo = Repository(session, Library)
        library = Library(name="Test", path="/test", media_type="movie")
        created = repo.create(library)
        session.commit()

        read = repo.read(created.id)
        assert read is not None
        assert read.name == "Test"

    def test_repository_filter_by(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test repository filter_by operation."""
        db_service, session = in_memory_db

        repo = Repository(session, Library)

        lib1 = Library(name="Movies", path="/movies", media_type="movie")
        lib2 = Library(name="TV Shows", path="/tv", media_type="tv")

        repo.create(lib1)
        repo.create(lib2)
        session.commit()

        movies = repo.filter_by(media_type="movie")
        assert len(movies) == 1
        assert movies[0].name == "Movies"

    def test_repository_count(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test repository count operation."""
        db_service, session = in_memory_db

        repo = Repository(session, Library)

        repo.create(Library(name="Lib1", path="/lib1", media_type="movie"))
        repo.create(Library(name="Lib2", path="/lib2", media_type="movie"))
        session.commit()

        count = repo.count()
        assert count == 2


class TestUnitOfWork:
    """Test Unit of Work pattern."""

    def test_unit_of_work_commit(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test Unit of Work commit."""
        db_service, session = in_memory_db

        with transactional_context() as uow:
            lib_repo = uow.get_repository(Library)
            library = Library(name="Test", path="/test", media_type="movie")
            lib_repo.create(library)

        # Session should be closed after context, verify in new session
        from sqlmodel import select
        session2 = db_service.get_session()
        count = len(session2.exec(select(Library)).all())
        assert count == 1
        session2.close()

    def test_unit_of_work_rollback_on_error(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test Unit of Work rollback on error."""
        db_service, session = in_memory_db

        try:
            with transactional_context() as uow:
                lib_repo = uow.get_repository(Library)
                library = Library(name="Test", path="/test", media_type="movie")
                lib_repo.create(library)
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify rollback
        from sqlmodel import select
        session2 = db_service.get_session()
        count = len(session2.exec(select(Library)).all())
        assert count == 0
        session2.close()


class TestDatabaseService:
    """Test DatabaseService initialization."""

    def test_database_service_creation(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test creating a database service."""
        db_service, _ = in_memory_db

        assert db_service.database_url == "sqlite://"
        assert db_service._engine is not None

    def test_get_session(self, in_memory_db: tuple[DatabaseService, Session]) -> None:
        """Test getting a session from database service."""
        db_service, _ = in_memory_db

        session1 = db_service.get_session()
        session2 = db_service.get_session()

        assert session1 is not None
        assert session2 is not None
        assert session1 is not session2

        session1.close()
        session2.close()
