"""Tests for search service and search criteria."""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine, SQLModel

from src.media_manager.search_service import SearchService
from src.media_manager.search_criteria import SearchCriteria
from src.media_manager.persistence.models import (
    MediaItem,
    Library,
    Tag,
    MediaItemTag,
    Person,
    Credit,
    Collection,
    MediaItemCollection,
    ExternalId,
    Artwork,
)
from src.media_manager.persistence.database import DatabaseService


@pytest.fixture
def db_service():
    """Create an in-memory database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    db_service = DatabaseService(":memory:")
    db_service._engine = engine
    
    yield db_service


@pytest.fixture
def sample_library(db_service):
    """Create a sample library."""
    with db_service.get_session() as session:
        library = Library(
            name="Test Library",
            path="/test/path",
            media_type="mixed",
        )
        session.add(library)
        session.commit()
        session.refresh(library)
        return library.id


@pytest.fixture
def sample_data(db_service, sample_library):
    """Create sample media items for testing."""
    with db_service.get_session() as session:
        # Create tags
        action_tag = Tag(name="Action")
        drama_tag = Tag(name="Drama")
        session.add(action_tag)
        session.add(drama_tag)
        session.commit()
        session.refresh(action_tag)
        session.refresh(drama_tag)
        
        # Create people
        actor1 = Person(name="John Doe")
        actor2 = Person(name="Jane Smith")
        session.add(actor1)
        session.add(actor2)
        session.commit()
        session.refresh(actor1)
        session.refresh(actor2)
        
        # Create collection
        collection = Collection(name="Test Collection")
        session.add(collection)
        session.commit()
        session.refresh(collection)
        
        # Create media items
        items = []
        
        # Movie 1 - High rated action movie with poster
        item1 = MediaItem(
            library_id=sample_library,
            title="The Dark Knight",
            media_type="movie",
            year=2008,
            rating=9.0,
            runtime=152,
            description="Batman fights the Joker",
        )
        session.add(item1)
        session.commit()
        session.refresh(item1)
        
        # Add tag
        tag_link1 = MediaItemTag(media_item_id=item1.id, tag_id=action_tag.id)
        session.add(tag_link1)
        
        # Add credit
        credit1 = Credit(
            media_item_id=item1.id,
            person_id=actor1.id,
            role="actor",
            character_name="Batman",
        )
        session.add(credit1)
        
        # Add external ID (matched)
        ext_id1 = ExternalId(
            media_item_id=item1.id,
            source="tmdb",
            external_id="155",
        )
        session.add(ext_id1)
        
        # Add poster
        poster1 = Artwork(
            media_item_id=item1.id,
            artwork_type="poster",
            url="http://example.com/poster1.jpg",
            size="large",
            download_status="completed",
        )
        session.add(poster1)
        
        items.append(item1)
        
        # Movie 2 - Low rated drama without poster
        item2 = MediaItem(
            library_id=sample_library,
            title="Boring Movie",
            media_type="movie",
            year=2020,
            rating=5.5,
            runtime=90,
            description="A very boring movie",
        )
        session.add(item2)
        session.commit()
        session.refresh(item2)
        
        # Add tag
        tag_link2 = MediaItemTag(media_item_id=item2.id, tag_id=drama_tag.id)
        session.add(tag_link2)
        
        # Add credit
        credit2 = Credit(
            media_item_id=item2.id,
            person_id=actor2.id,
            role="actor",
        )
        session.add(credit2)
        
        items.append(item2)
        
        # TV Show - Recent, no external ID (unmatched)
        item3 = MediaItem(
            library_id=sample_library,
            title="Great TV Show",
            media_type="tv",
            year=2023,
            rating=8.5,
            runtime=45,
            description="An amazing TV series",
            created_at=datetime.utcnow() - timedelta(days=3),
        )
        session.add(item3)
        session.commit()
        session.refresh(item3)
        
        # Add to collection
        coll_link = MediaItemCollection(
            media_item_id=item3.id,
            collection_id=collection.id,
        )
        session.add(coll_link)
        
        items.append(item3)
        
        # Old movie
        item4 = MediaItem(
            library_id=sample_library,
            title="Classic Film",
            media_type="movie",
            year=1975,
            rating=7.0,
            runtime=120,
        )
        session.add(item4)
        session.commit()
        session.refresh(item4)
        items.append(item4)
        
        session.commit()
        
        return {
            "items": items,
            "tags": [action_tag, drama_tag],
            "people": [actor1, actor2],
            "collection": collection,
        }


class TestSearchCriteria:
    """Tests for SearchCriteria class."""
    
    def test_default_criteria(self):
        """Test default search criteria."""
        criteria = SearchCriteria()
        assert criteria.text_query == ""
        assert criteria.media_type is None
        assert criteria.year_min is None
        assert criteria.is_empty()
    
    def test_to_dict(self):
        """Test converting criteria to dict."""
        criteria = SearchCriteria(
            text_query="test",
            media_type="movie",
            year_min=2000,
            year_max=2020,
        )
        data = criteria.to_dict()
        assert data["text_query"] == "test"
        assert data["media_type"] == "movie"
        assert data["year_min"] == 2000
        assert data["year_max"] == 2020
    
    def test_from_dict(self):
        """Test creating criteria from dict."""
        data = {
            "text_query": "test",
            "media_type": "tv",
            "rating_min": 8.0,
        }
        criteria = SearchCriteria.from_dict(data)
        assert criteria.text_query == "test"
        assert criteria.media_type == "tv"
        assert criteria.rating_min == 8.0
    
    def test_is_empty(self):
        """Test is_empty method."""
        criteria = SearchCriteria()
        assert criteria.is_empty()
        
        criteria.text_query = "test"
        assert not criteria.is_empty()


class TestSearchService:
    """Tests for SearchService class."""
    
    def test_basic_search(self, db_service, sample_data):
        """Test basic search without filters."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria()
        results, total = service.search(criteria)
        
        assert total == 4
        assert len(results) == 4
    
    def test_text_search(self, db_service, sample_data):
        """Test text search."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(text_query="Dark Knight")
        results, total = service.search(criteria)
        
        assert total == 1
        assert results[0].title == "The Dark Knight"
    
    def test_media_type_filter(self, db_service, sample_data):
        """Test media type filtering."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(media_type="movie")
        results, total = service.search(criteria)
        
        assert total == 3
        assert all(item.media_type == "movie" for item in results)
        
        criteria = SearchCriteria(media_type="tv")
        results, total = service.search(criteria)
        
        assert total == 1
        assert results[0].media_type == "tv"
    
    def test_year_range_filter(self, db_service, sample_data):
        """Test year range filtering."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(year_min=2000, year_max=2020)
        results, total = service.search(criteria)
        
        assert total == 2
        assert all(2000 <= item.year <= 2020 for item in results)
    
    def test_rating_range_filter(self, db_service, sample_data):
        """Test rating range filtering."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(rating_min=8.0)
        results, total = service.search(criteria)
        
        assert total == 2
        assert all(item.rating >= 8.0 for item in results)
    
    def test_runtime_range_filter(self, db_service, sample_data):
        """Test runtime range filtering."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(runtime_min=100, runtime_max=160)
        results, total = service.search(criteria)
        
        assert total == 2
        assert all(100 <= item.runtime <= 160 for item in results)
    
    def test_tags_filter(self, db_service, sample_data):
        """Test filtering by tags."""
        service = SearchService()
        service._db_service = db_service
        
        action_tag = sample_data["tags"][0]
        criteria = SearchCriteria(tags=[action_tag.id])
        results, total = service.search(criteria)
        
        assert total == 1
        assert results[0].title == "The Dark Knight"
    
    def test_people_filter(self, db_service, sample_data):
        """Test filtering by people."""
        service = SearchService()
        service._db_service = db_service
        
        actor1 = sample_data["people"][0]
        criteria = SearchCriteria(people=[actor1.id])
        results, total = service.search(criteria)
        
        assert total == 1
        assert results[0].title == "The Dark Knight"
    
    def test_collections_filter(self, db_service, sample_data):
        """Test filtering by collections."""
        service = SearchService()
        service._db_service = db_service
        
        collection = sample_data["collection"]
        criteria = SearchCriteria(collections=[collection.id])
        results, total = service.search(criteria)
        
        assert total == 1
        assert results[0].title == "Great TV Show"
    
    def test_quick_filter_unmatched(self, db_service, sample_data):
        """Test unmatched quick filter."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(quick_filter="unmatched")
        results, total = service.search(criteria)
        
        # Should return 3 items (all except the one with external_id)
        assert total == 3
        assert all(item.title != "The Dark Knight" for item in results)
    
    def test_quick_filter_recent(self, db_service, sample_data):
        """Test recent quick filter."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(quick_filter="recent")
        results, total = service.search(criteria)
        
        # Should return 1 item (created in last 7 days)
        assert total == 1
        assert results[0].title == "Great TV Show"
    
    def test_quick_filter_no_poster(self, db_service, sample_data):
        """Test no_poster quick filter."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(quick_filter="no_poster")
        results, total = service.search(criteria)
        
        # Should return 3 items (all except the one with poster)
        assert total == 3
        assert all(item.title != "The Dark Knight" for item in results)
    
    def test_quick_filter_high_rated(self, db_service, sample_data):
        """Test high_rated quick filter."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(quick_filter="high_rated")
        results, total = service.search(criteria)
        
        assert total == 2
        assert all(item.rating >= 8.0 for item in results)
    
    def test_complex_filter_combination(self, db_service, sample_data):
        """Test combining multiple filters."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(
            media_type="movie",
            year_min=2000,
            rating_min=8.0,
        )
        results, total = service.search(criteria)
        
        assert total == 1
        assert results[0].title == "The Dark Knight"
    
    def test_sorting(self, db_service, sample_data):
        """Test sorting results."""
        service = SearchService()
        service._db_service = db_service
        
        # Sort by year ascending
        criteria = SearchCriteria(sort_by="year", sort_order="asc")
        results, total = service.search(criteria)
        
        assert results[0].year == 1975
        assert results[-1].year == 2023
        
        # Sort by year descending
        criteria = SearchCriteria(sort_by="year", sort_order="desc")
        results, total = service.search(criteria)
        
        assert results[0].year == 2023
        assert results[-1].year == 1975
        
        # Sort by rating
        criteria = SearchCriteria(sort_by="rating", sort_order="desc")
        results, total = service.search(criteria)
        
        assert results[0].rating == 9.0
    
    def test_pagination(self, db_service, sample_data):
        """Test pagination."""
        service = SearchService()
        service._db_service = db_service
        
        # First page
        criteria = SearchCriteria(page=0, page_size=2)
        results, total = service.search(criteria)
        
        assert total == 4
        assert len(results) == 2
        
        # Second page
        criteria = SearchCriteria(page=1, page_size=2)
        results, total = service.search(criteria)
        
        assert total == 4
        assert len(results) == 2
        
        # Last page
        criteria = SearchCriteria(page=2, page_size=2)
        results, total = service.search(criteria)
        
        assert total == 4
        assert len(results) == 0  # No items on third page
    
    def test_empty_results(self, db_service, sample_data):
        """Test search with no results."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(text_query="NonexistentMovie")
        results, total = service.search(criteria)
        
        assert total == 0
        assert len(results) == 0
    
    def test_save_and_load_search(self, db_service, sample_data):
        """Test saving and loading searches."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(
            text_query="test",
            media_type="movie",
            year_min=2000,
        )
        
        # Save search
        saved = service.save_search("My Search", criteria, "Test description")
        assert saved.id is not None
        assert saved.name == "My Search"
        
        # Load search
        result = service.load_search(saved.id)
        assert result is not None
        loaded_search, loaded_criteria = result
        assert loaded_search.name == "My Search"
        assert loaded_criteria.text_query == "test"
        assert loaded_criteria.media_type == "movie"
        assert loaded_criteria.year_min == 2000
    
    def test_get_saved_searches(self, db_service, sample_data):
        """Test getting all saved searches."""
        service = SearchService()
        service._db_service = db_service
        
        # Save multiple searches
        criteria1 = SearchCriteria(text_query="test1")
        criteria2 = SearchCriteria(text_query="test2")
        
        service.save_search("Search 1", criteria1)
        service.save_search("Search 2", criteria2)
        
        # Get all
        searches = service.get_saved_searches()
        assert len(searches) >= 2
    
    def test_delete_saved_search(self, db_service, sample_data):
        """Test deleting saved search."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(text_query="test")
        saved = service.save_search("To Delete", criteria)
        
        # Delete
        result = service.delete_saved_search(saved.id)
        assert result is True
        
        # Verify deleted
        loaded = service.load_search(saved.id)
        assert loaded is None
    
    def test_update_saved_search(self, db_service, sample_data):
        """Test updating saved search."""
        service = SearchService()
        service._db_service = db_service
        
        criteria = SearchCriteria(text_query="original")
        saved = service.save_search("Original", criteria)
        
        # Update
        new_criteria = SearchCriteria(text_query="updated")
        updated = service.update_saved_search(
            saved.id,
            name="Updated",
            criteria=new_criteria,
        )
        
        assert updated is not None
        assert updated.name == "Updated"
        
        # Verify update
        result = service.load_search(saved.id)
        assert result is not None
        _, loaded_criteria = result
        assert loaded_criteria.text_query == "updated"
