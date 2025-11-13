"""Search service for composing complex SQL queries."""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlmodel import Session, select, and_, or_, func, col
from sqlalchemy.orm import selectinload

from .logging import get_logger
from .persistence.database import get_database_service
from .persistence.models import (
    MediaItem,
    MediaFile,
    Credit,
    Person,
    Tag,
    MediaItemTag,
    Collection,
    MediaItemCollection,
    Artwork,
    ExternalId,
    SavedSearch,
)
from .search_criteria import SearchCriteria

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class SearchService:
    """Service for advanced media search with complex filtering."""

    def __init__(self) -> None:
        """Initialize search service."""
        self._db_service = get_database_service()
        self._logger = logger

    def search(self, criteria: SearchCriteria) -> Tuple[List[MediaItem], int]:
        """
        Search media items with given criteria.

        Args:
            criteria: Search criteria

        Returns:
            Tuple of (list of matching items, total count)
        """
        with self._db_service.get_session() as session:
            # Build the base query
            query = self._build_query(session, criteria)

            # Count total results
            count_query = select(func.count()).select_from(query.subquery())
            total_count = session.exec(count_query).one()

            # Apply sorting
            query = self._apply_sorting(query, criteria)

            # Apply pagination
            offset = criteria.page * criteria.page_size
            query = query.offset(offset).limit(criteria.page_size)

            # Execute query
            results = session.exec(query).all()

            # Detach from session to avoid lazy loading issues
            session.expunge_all()

            return list(results), total_count

    def _build_query(self, session: Session, criteria: SearchCriteria):
        """Build the base query with all filters applied."""
        # Start with base query including eager loading
        query = select(MediaItem).options(
            selectinload(MediaItem.files),
            selectinload(MediaItem.artworks),
            selectinload(MediaItem.credits).selectinload(Credit.person),
            selectinload(MediaItem.library),
            selectinload(MediaItem.tags),
            selectinload(MediaItem.collections),
        )

        conditions = []

        # Media type filter
        if criteria.media_type:
            conditions.append(MediaItem.media_type == criteria.media_type)

        # Library filter
        if criteria.library_id:
            conditions.append(MediaItem.library_id == criteria.library_id)

        # Text search (title or description)
        if criteria.text_query:
            text = f"%{criteria.text_query}%"
            conditions.append(
                or_(
                    MediaItem.title.ilike(text),
                    MediaItem.description.ilike(text),
                )
            )

        # Year range
        if criteria.year_min is not None:
            conditions.append(MediaItem.year >= criteria.year_min)
        if criteria.year_max is not None:
            conditions.append(MediaItem.year <= criteria.year_max)

        # Rating range
        if criteria.rating_min is not None:
            conditions.append(MediaItem.rating >= criteria.rating_min)
        if criteria.rating_max is not None:
            conditions.append(MediaItem.rating <= criteria.rating_max)

        # Runtime range
        if criteria.runtime_min is not None:
            conditions.append(MediaItem.runtime >= criteria.runtime_min)
        if criteria.runtime_max is not None:
            conditions.append(MediaItem.runtime <= criteria.runtime_max)

        # Tags filter (items must have ALL specified tags)
        if criteria.tags:
            for tag_id in criteria.tags:
                subquery = (
                    select(MediaItemTag.media_item_id)
                    .where(MediaItemTag.tag_id == tag_id)
                )
                conditions.append(MediaItem.id.in_(subquery))

        # People filter (items must have ANY of the specified people)
        if criteria.people:
            subquery = (
                select(Credit.media_item_id)
                .where(Credit.person_id.in_(criteria.people))
            )
            conditions.append(MediaItem.id.in_(subquery))

        # Collections filter (items must be in ANY of the specified collections)
        if criteria.collections:
            subquery = (
                select(MediaItemCollection.media_item_id)
                .where(MediaItemCollection.collection_id.in_(criteria.collections))
            )
            conditions.append(MediaItem.id.in_(subquery))

        # Quick filters
        if criteria.quick_filter:
            quick_conditions = self._apply_quick_filter(
                session, criteria.quick_filter
            )
            if quick_conditions is not None:
                conditions.append(quick_conditions)

        # Apply all conditions
        if conditions:
            query = query.where(and_(*conditions))

        return query

    def _apply_quick_filter(self, session: Session, quick_filter: str):
        """Apply quick filter shortcuts."""
        if quick_filter == "unmatched":
            # Items without external IDs
            subquery = select(ExternalId.media_item_id).distinct()
            return MediaItem.id.notin_(subquery)

        elif quick_filter == "recent":
            # Items added in the last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            return MediaItem.created_at >= seven_days_ago

        elif quick_filter == "no_poster":
            # Items without poster artwork
            subquery = (
                select(Artwork.media_item_id)
                .where(Artwork.artwork_type == "poster")
                .distinct()
            )
            return MediaItem.id.notin_(subquery)

        elif quick_filter == "high_rated":
            # Items with rating >= 8.0
            return MediaItem.rating >= 8.0

        elif quick_filter == "favorites":
            # Items marked as favorites
            from .persistence.models import Favorite
            subquery = select(Favorite.media_item_id)
            return MediaItem.id.in_(subquery)

        return None

    def _apply_sorting(self, query, criteria: SearchCriteria):
        """Apply sorting to the query."""
        sort_field = MediaItem.title  # Default

        if criteria.sort_by == "year":
            sort_field = MediaItem.year
        elif criteria.sort_by == "rating":
            sort_field = MediaItem.rating
        elif criteria.sort_by == "added":
            sort_field = MediaItem.created_at
        elif criteria.sort_by == "runtime":
            sort_field = MediaItem.runtime

        if criteria.sort_order == "desc":
            sort_field = sort_field.desc()

        return query.order_by(sort_field)

    def get_available_tags(self) -> List[Tag]:
        """Get all available tags for filtering."""
        with self._db_service.get_session() as session:
            statement = select(Tag).order_by(Tag.name)
            return list(session.exec(statement).all())

    def get_available_people(self, limit: int = 100) -> List[Person]:
        """Get available people (actors, directors, etc.) for filtering."""
        with self._db_service.get_session() as session:
            statement = select(Person).order_by(Person.name).limit(limit)
            return list(session.exec(statement).all())

    def get_available_collections(self) -> List[Collection]:
        """Get all available collections for filtering."""
        with self._db_service.get_session() as session:
            statement = select(Collection).order_by(Collection.name)
            return list(session.exec(statement).all())

    def save_search(self, name: str, criteria: SearchCriteria, description: Optional[str] = None) -> SavedSearch:
        """Save search criteria for later use."""
        with self._db_service.get_session() as session:
            saved_search = SavedSearch(
                name=name,
                description=description,
                criteria=json.dumps(criteria.to_dict()),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(saved_search)
            session.commit()
            session.refresh(saved_search)
            return saved_search

    def load_search(self, search_id: int) -> Optional[Tuple[SavedSearch, SearchCriteria]]:
        """Load a saved search by ID."""
        with self._db_service.get_session() as session:
            statement = select(SavedSearch).where(SavedSearch.id == search_id)
            saved_search = session.exec(statement).first()
            if saved_search:
                criteria_dict = json.loads(saved_search.criteria)
                criteria = SearchCriteria.from_dict(criteria_dict)
                return saved_search, criteria
            return None

    def get_saved_searches(self) -> List[SavedSearch]:
        """Get all saved searches."""
        with self._db_service.get_session() as session:
            statement = select(SavedSearch).order_by(SavedSearch.name)
            return list(session.exec(statement).all())

    def delete_saved_search(self, search_id: int) -> bool:
        """Delete a saved search."""
        with self._db_service.get_session() as session:
            statement = select(SavedSearch).where(SavedSearch.id == search_id)
            saved_search = session.exec(statement).first()
            if saved_search:
                session.delete(saved_search)
                session.commit()
                return True
            return False

    def update_saved_search(self, search_id: int, name: Optional[str] = None, 
                           criteria: Optional[SearchCriteria] = None,
                           description: Optional[str] = None) -> Optional[SavedSearch]:
        """Update an existing saved search."""
        with self._db_service.get_session() as session:
            statement = select(SavedSearch).where(SavedSearch.id == search_id)
            saved_search = session.exec(statement).first()
            if saved_search:
                if name is not None:
                    saved_search.name = name
                if criteria is not None:
                    saved_search.criteria = json.dumps(criteria.to_dict())
                if description is not None:
                    saved_search.description = description
                saved_search.updated_at = datetime.utcnow()
                session.add(saved_search)
                session.commit()
                session.refresh(saved_search)
                return saved_search
            return None
