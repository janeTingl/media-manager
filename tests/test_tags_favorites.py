"""Tests for tags, favorites, and collections functionality."""

import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool

from src.media_manager.persistence.models import (
    Library,
    MediaItem,
    Tag,
    Collection,
    Favorite,
    MediaItemTag,
    MediaItemCollection,
)
from src.media_manager.persistence.repositories import Repository, UnitOfWork
from src.media_manager.search_service import SearchService


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(test_db):
    """Create a test session."""
    with Session(test_db) as session:
        yield session


@pytest.fixture
def library(session):
    """Create a test library."""
    lib = Library(
        name="Test Library",
        path="/test/path",
        media_type="mixed",
    )
    session.add(lib)
    session.commit()
    session.refresh(lib)
    return lib


@pytest.fixture
def media_item(session, library):
    """Create a test media item."""
    item = MediaItem(
        library_id=library.id,
        title="Test Movie",
        media_type="movie",
        year=2023,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


class TestTagManagement:
    """Test tag creation and management."""

    def test_create_tag(self, session):
        """Test creating a tag."""
        tag = Tag(name="Action", color="#FF0000")
        session.add(tag)
        session.commit()
        session.refresh(tag)

        assert tag.id is not None
        assert tag.name == "Action"
        assert tag.color == "#FF0000"

    def test_tag_unique_constraint(self, session):
        """Test that tag names are unique."""
        tag1 = Tag(name="Action")
        session.add(tag1)
        session.commit()

        tag2 = Tag(name="Action")
        session.add(tag2)

        with pytest.raises(Exception):  # Integrity error
            session.commit()

    def test_add_tag_to_media_item(self, session, media_item):
        """Test adding a tag to a media item."""
        tag = Tag(name="Favorite")
        session.add(tag)
        session.flush()

        media_item.tags.append(tag)
        session.commit()
        session.refresh(media_item)

        assert len(media_item.tags) == 1
        assert media_item.tags[0].name == "Favorite"

    def test_add_multiple_tags_to_media_item(self, session, media_item):
        """Test adding multiple tags to a media item."""
        tags = [
            Tag(name="Action"),
            Tag(name="Adventure"),
            Tag(name="Thriller"),
        ]
        session.add_all(tags)
        session.flush()

        for tag in tags:
            media_item.tags.append(tag)

        session.commit()
        session.refresh(media_item)

        assert len(media_item.tags) == 3
        tag_names = {t.name for t in media_item.tags}
        assert tag_names == {"Action", "Adventure", "Thriller"}

    def test_remove_tag_from_media_item(self, session, media_item):
        """Test removing a tag from a media item."""
        tags = [Tag(name="Tag1"), Tag(name="Tag2")]
        session.add_all(tags)
        session.flush()

        for tag in tags:
            media_item.tags.append(tag)

        session.commit()
        session.refresh(media_item)

        # Remove first tag
        media_item.tags.pop(0)
        session.commit()
        session.refresh(media_item)

        assert len(media_item.tags) == 1
        assert media_item.tags[0].name == "Tag2"

    def test_get_all_tags(self, session):
        """Test retrieving all tags."""
        tags = [Tag(name=f"Tag{i}") for i in range(5)]
        session.add_all(tags)
        session.commit()

        stmt = select(Tag).order_by(Tag.name)
        result = session.exec(stmt).all()

        assert len(result) == 5

    def test_tag_repository_crud(self, session):
        """Test tag CRUD operations via repository."""
        repo = Repository(session, Tag)

        # Create
        tag = Tag(name="TestTag", color="#00FF00")
        created = repo.create(tag)
        assert created.id is not None

        # Read
        read_tag = repo.read(created.id)
        assert read_tag is not None
        assert read_tag.name == "TestTag"

        # Update
        read_tag.color = "#0000FF"
        updated = repo.update(read_tag)
        assert updated.color == "#0000FF"

        # Delete
        deleted = repo.delete(created.id)
        assert deleted is True

        # Verify deletion
        deleted_tag = repo.read(created.id)
        assert deleted_tag is None


class TestCollectionManagement:
    """Test collection creation and management."""

    def test_create_collection(self, session):
        """Test creating a collection."""
        collection = Collection(
            name="Watchlist",
            description="Movies to watch",
        )
        session.add(collection)
        session.commit()
        session.refresh(collection)

        assert collection.id is not None
        assert collection.name == "Watchlist"
        assert collection.description == "Movies to watch"

    def test_collection_unique_name(self, session):
        """Test that collection names are unique."""
        col1 = Collection(name="Kids")
        session.add(col1)
        session.commit()

        col2 = Collection(name="Kids")
        session.add(col2)

        with pytest.raises(Exception):  # Integrity error
            session.commit()

    def test_add_media_item_to_collection(self, session, media_item):
        """Test adding a media item to a collection."""
        collection = Collection(name="Watchlist")
        session.add(collection)
        session.flush()

        media_item.collections.append(collection)
        session.commit()
        session.refresh(media_item)

        assert len(media_item.collections) == 1
        assert media_item.collections[0].name == "Watchlist"

    def test_add_media_item_to_multiple_collections(self, session, media_item):
        """Test adding a media item to multiple collections."""
        collections = [
            Collection(name="Watchlist"),
            Collection(name="Favorites"),
            Collection(name="Kids"),
        ]
        session.add_all(collections)
        session.flush()

        for collection in collections:
            media_item.collections.append(collection)

        session.commit()
        session.refresh(media_item)

        assert len(media_item.collections) == 3
        collection_names = {c.name for c in media_item.collections}
        assert collection_names == {"Watchlist", "Favorites", "Kids"}

    def test_get_items_in_collection(self, session, library):
        """Test retrieving items in a collection."""
        collection = Collection(name="Kids")
        session.add(collection)
        session.flush()

        items = [
            MediaItem(library_id=library.id, title=f"Movie{i}", media_type="movie")
            for i in range(3)
        ]
        session.add_all(items)
        session.flush()

        for item in items:
            item.collections.append(collection)

        session.commit()
        session.refresh(collection)

        assert len(collection.media_items) == 3

    def test_collection_repository_crud(self, session):
        """Test collection CRUD operations via repository."""
        repo = Repository(session, Collection)

        # Create
        collection = Collection(name="TestCollection", description="Test")
        created = repo.create(collection)
        assert created.id is not None

        # Read
        read_collection = repo.read(created.id)
        assert read_collection is not None
        assert read_collection.name == "TestCollection"

        # Update
        read_collection.description = "Updated"
        updated = repo.update(read_collection)
        assert updated.description == "Updated"

        # Delete
        deleted = repo.delete(created.id)
        assert deleted is True


class TestFavoriteManagement:
    """Test favorite marking functionality."""

    def test_mark_as_favorite(self, session, media_item):
        """Test marking a media item as favorite."""
        favorite = Favorite(media_item_id=media_item.id)
        session.add(favorite)
        session.commit()
        session.refresh(favorite)

        assert favorite.id is not None
        assert favorite.media_item_id == media_item.id
        assert favorite.notes is None

    def test_mark_as_favorite_with_notes(self, session, media_item):
        """Test marking a media item as favorite with notes."""
        favorite = Favorite(
            media_item_id=media_item.id,
            notes="Great movie!",
        )
        session.add(favorite)
        session.commit()
        session.refresh(favorite)

        assert favorite.notes == "Great movie!"

    def test_favorite_unique_constraint(self, session, media_item):
        """Test that a media item can only be favorited once."""
        fav1 = Favorite(media_item_id=media_item.id)
        session.add(fav1)
        session.commit()

        fav2 = Favorite(media_item_id=media_item.id)
        session.add(fav2)

        with pytest.raises(Exception):  # Integrity error
            session.commit()

    def test_unmark_favorite(self, session, media_item):
        """Test unmarking a media item as favorite."""
        favorite = Favorite(media_item_id=media_item.id)
        session.add(favorite)
        session.commit()

        stmt = select(Favorite).where(Favorite.media_item_id == media_item.id)
        fav = session.exec(stmt).first()

        session.delete(fav)
        session.commit()

        stmt = select(Favorite).where(Favorite.media_item_id == media_item.id)
        result = session.exec(stmt).first()
        assert result is None

    def test_update_favorite_notes(self, session, media_item):
        """Test updating favorite notes."""
        favorite = Favorite(media_item_id=media_item.id, notes="Original notes")
        session.add(favorite)
        session.commit()
        session.refresh(favorite)

        favorite.notes = "Updated notes"
        session.add(favorite)
        session.commit()
        session.refresh(favorite)

        assert favorite.notes == "Updated notes"

    def test_get_all_favorites(self, session, library):
        """Test retrieving all favorite items."""
        items = [
            MediaItem(library_id=library.id, title=f"Movie{i}", media_type="movie")
            for i in range(3)
        ]
        session.add_all(items)
        session.flush()

        for item in items:
            favorite = Favorite(media_item_id=item.id)
            session.add(favorite)

        session.commit()

        stmt = select(Favorite)
        favorites = session.exec(stmt).all()

        assert len(favorites) == 3

    def test_favorite_repository_crud(self, session, media_item):
        """Test favorite CRUD operations via repository."""
        repo = Repository(session, Favorite)

        # Create
        favorite = Favorite(media_item_id=media_item.id, notes="Test")
        created = repo.create(favorite)
        assert created.id is not None

        # Read
        read_favorite = repo.read(created.id)
        assert read_favorite is not None
        assert read_favorite.media_item_id == media_item.id

        # Update
        read_favorite.notes = "Updated"
        updated = repo.update(read_favorite)
        assert updated.notes == "Updated"

        # Delete
        deleted = repo.delete(created.id)
        assert deleted is True


class TestTagsWithSearchService:
    """Test tags with search service."""

    def test_search_by_tag(self, test_db):
        """Test searching media items by tag."""
        # This would need proper initialization of the database service
        # For now, we're testing the basic structure
        with Session(test_db) as session:
            # Create test data
            lib = Library(name="Test", path="/test", media_type="mixed")
            session.add(lib)
            session.flush()

            tag = Tag(name="ActionTag")
            session.add(tag)
            session.flush()

            item1 = MediaItem(
                library_id=lib.id,
                title="Action Movie",
                media_type="movie",
            )
            item1.tags.append(tag)
            session.add(item1)
            session.flush()

            item2 = MediaItem(
                library_id=lib.id,
                title="Comedy Movie",
                media_type="movie",
            )
            session.add(item2)
            session.commit()

            # Search for items with the tag
            stmt = select(MediaItem).where(
                MediaItem.id.in_(
                    select(MediaItemTag.media_item_id).where(
                        MediaItemTag.tag_id == tag.id
                    )
                )
            )
            results = session.exec(stmt).all()

            assert len(results) == 1
            assert results[0].title == "Action Movie"


class TestComplexScenarios:
    """Test complex scenarios combining tags, collections, and favorites."""

    def test_media_item_with_tags_collections_and_favorite(self, session, library):
        """Test a media item with tags, collections, and favorite status."""
        # Create data
        item = MediaItem(library_id=library.id, title="Test Movie", media_type="movie")
        session.add(item)
        session.flush()

        tags = [Tag(name="Action"), Tag(name="Thriller")]
        session.add_all(tags)
        session.flush()

        collections = [Collection(name="Watchlist"), Collection(name="Favorites")]
        session.add_all(collections)
        session.flush()

        favorite = Favorite(media_item_id=item.id)
        session.add(favorite)
        session.flush()

        # Associate
        for tag in tags:
            item.tags.append(tag)
        for collection in collections:
            item.collections.append(collection)

        session.commit()
        session.refresh(item)

        # Verify
        assert len(item.tags) == 2
        assert len(item.collections) == 2
        assert len(item.favorites) == 1

    def test_batch_tag_assignment(self, session, library):
        """Test batch assigning tags to multiple items."""
        items = [
            MediaItem(library_id=library.id, title=f"Movie{i}", media_type="movie")
            for i in range(5)
        ]
        session.add_all(items)
        session.flush()

        tag = Tag(name="Batch Tag")
        session.add(tag)
        session.flush()

        for item in items:
            item.tags.append(tag)

        session.commit()

        # Verify
        stmt = select(MediaItem).where(
            MediaItem.id.in_(
                select(MediaItemTag.media_item_id).where(MediaItemTag.tag_id == tag.id)
            )
        )
        results = session.exec(stmt).all()

        assert len(results) == 5

    def test_persistence_across_sessions(self, test_db, library):
        """Test that tags/collections/favorites persist across sessions."""
        # First session - create data
        with Session(test_db) as session:
            item = MediaItem(
                library_id=library.id,
                title="Persistent Movie",
                media_type="movie",
            )
            session.add(item)
            session.flush()

            tag = Tag(name="PersistentTag")
            session.add(tag)
            session.flush()

            item.tags.append(tag)

            favorite = Favorite(media_item_id=item.id)
            session.add(favorite)

            session.commit()
            item_id = item.id

        # Second session - read data
        with Session(test_db) as session:
            stmt = select(MediaItem).where(MediaItem.id == item_id)
            item = session.exec(stmt).first()

            assert item is not None
            assert len(item.tags) == 1
            assert item.tags[0].name == "PersistentTag"

            stmt = select(Favorite).where(Favorite.media_item_id == item.id)
            favorite = session.exec(stmt).first()

            assert favorite is not None
