"""Repository pattern implementations for database access."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from ..logging import get_logger
from .database import get_database_service
from .models import Library, MediaItem, MediaFile, Artwork, Credit, Person

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)

T = TypeVar("T")


class Repository(Generic[T]):
    """Generic repository for CRUD operations on SQLModel entities."""

    def __init__(self, session: Session, entity_type: Type[T]) -> None:
        """Initialize repository.

        Args:
            session: SQLModel session
            entity_type: The entity type this repository manages
        """
        self.session = session
        self.entity_type = entity_type

    def create(self, entity: T) -> T:
        """Create and persist a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID
        """
        try:
            self.session.add(entity)
            self.session.flush()
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Failed to create {self.entity_type.__name__}: {e}")
            raise

    def read(self, entity_id: int) -> Optional[T]:
        """Read an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity or None if not found
        """
        try:
            statement = select(self.entity_type).where(
                self.entity_type.id == entity_id
            )
            return self.session.exec(statement).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to read {self.entity_type.__name__} with ID {entity_id}: {e}")
            raise

    def read_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Read multiple entities with pagination.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        try:
            statement = select(self.entity_type).offset(skip).limit(limit)
            return self.session.exec(statement).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to read all {self.entity_type.__name__}: {e}")
            raise

    def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Updated entity
        """
        try:
            self.session.add(entity)
            self.session.flush()
            return entity
        except SQLAlchemyError as e:
            logger.error(f"Failed to update {self.entity_type.__name__}: {e}")
            raise

    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        try:
            entity = self.read(entity_id)
            if entity is None:
                return False
            self.session.delete(entity)
            self.session.flush()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete {self.entity_type.__name__} with ID {entity_id}: {e}")
            raise

    def filter_by(self, **kwargs: Any) -> List[T]:
        """Filter entities by attributes.

        Args:
            **kwargs: Filter conditions

        Returns:
            List of matching entities
        """
        try:
            statement = select(self.entity_type)
            for key, value in kwargs.items():
                if hasattr(self.entity_type, key):
                    statement = statement.where(
                        getattr(self.entity_type, key) == value
                    )
            return self.session.exec(statement).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to filter {self.entity_type.__name__}: {e}")
            raise

    def count(self) -> int:
        """Count total entities.

        Returns:
            Total number of entities
        """
        try:
            statement = select(self.entity_type)
            return len(self.session.exec(statement).all())
        except SQLAlchemyError as e:
            logger.error(f"Failed to count {self.entity_type.__name__}: {e}")
            raise


class RepositoryManager:
    """Manager for multiple repositories."""

    def __init__(self, session: Session) -> None:
        """Initialize repository manager.

        Args:
            session: SQLModel session
        """
        self.session = session
        self._repositories: dict[Type[T], Repository[T]] = {}

    def get_repository(self, entity_type: Type[T]) -> Repository[T]:
        """Get or create a repository for an entity type.

        Args:
            entity_type: The entity type

        Returns:
            Repository instance
        """
        if entity_type not in self._repositories:
            self._repositories[entity_type] = Repository(self.session, entity_type)
        return self._repositories[entity_type]


class UnitOfWork:
    """Unit of Work pattern for transactional database operations."""

    def __init__(self, session: Optional[Session] = None) -> None:
        """Initialize Unit of Work.

        Args:
            session: SQLModel session. If None, creates a new one from the database service.
        """
        if session is None:
            db_service = get_database_service()
            session = db_service.get_session()

        self.session = session
        self.repository_manager = RepositoryManager(session)

    def get_repository(self, entity_type: Type[T]) -> Repository[T]:
        """Get a repository for an entity type.

        Args:
            entity_type: The entity type

        Returns:
            Repository instance
        """
        return self.repository_manager.get_repository(entity_type)

    def commit(self) -> None:
        """Commit the transaction."""
        try:
            self.session.commit()
            logger.debug("Transaction committed")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to commit transaction: {e}")
            raise

    def rollback(self) -> None:
        """Rollback the transaction."""
        try:
            self.session.rollback()
            logger.debug("Transaction rolled back")
        except SQLAlchemyError as e:
            logger.error(f"Failed to rollback transaction: {e}")
            raise

    def close(self) -> None:
        """Close the session."""
        try:
            self.session.close()
            logger.debug("Session closed")
        except SQLAlchemyError as e:
            logger.error(f"Failed to close session: {e}")
            raise

    def __enter__(self) -> UnitOfWork:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        try:
            if exc_type is not None:
                self.rollback()
            else:
                try:
                    self.commit()
                except SQLAlchemyError:
                    self.rollback()
                    raise
        finally:
            self.close()


class MediaItemRepository:
    """Repository for MediaItem operations."""
    
    def __init__(self) -> None:
        """Initialize the media item repository."""
        self._logger = logger
        self._db_service = get_database_service()
    
    def get_all(self) -> List[MediaItem]:
        """Get all media items with their relationships."""
        with self._db_service.get_session() as session:
            statement = (
                select(MediaItem)
                .options(
                    selectinload(MediaItem.files),
                    selectinload(MediaItem.artworks),
                    selectinload(MediaItem.credits).selectinload(Credit.person),
                    selectinload(MediaItem.library)
                )
                .order_by(MediaItem.title)
            )
            result = session.exec(statement)
            return list(result.all())
    
    def get_by_library(self, library_id: int) -> List[MediaItem]:
        """Get media items by library ID."""
        with self._db_service.get_session() as session:
            statement = (
                select(MediaItem)
                .where(MediaItem.library_id == library_id)
                .options(
                    selectinload(MediaItem.files),
                    selectinload(MediaItem.artworks),
                    selectinload(MediaItem.credits).selectinload(Credit.person),
                    selectinload(MediaItem.library)
                )
                .order_by(MediaItem.title)
            )
            result = session.exec(statement)
            return list(result.all())
    
    def get_by_id(self, item_id: int) -> Optional[MediaItem]:
        """Get media item by ID."""
        with self._db_service.get_session() as session:
            statement = (
                select(MediaItem)
                .where(MediaItem.id == item_id)
                .options(
                    selectinload(MediaItem.files),
                    selectinload(MediaItem.artworks),
                    selectinload(MediaItem.credits).selectinload(Credit.person),
                    selectinload(MediaItem.library)
                )
            )
            result = session.exec(statement)
            return result.first()
    
    def search(self, query: str, limit: int = 100) -> List[MediaItem]:
        """Search media items by title or description."""
        with self._db_service.get_session() as session:
            statement = (
                select(MediaItem)
                .where(
                    (MediaItem.title.ilike(f"%{query}%")) |
                    (MediaItem.description.ilike(f"%{query}%"))
                )
                .options(
                    selectinload(MediaItem.files),
                    selectinload(MediaItem.artworks),
                    selectinload(MediaItem.credits).selectinload(Credit.person),
                    selectinload(MediaItem.library)
                )
                .order_by(MediaItem.title)
                .limit(limit)
            )
            result = session.exec(statement)
            return list(result.all())


@contextmanager
def transactional_context() -> Generator[UnitOfWork, None, None]:
    """Context manager for transactional operations.

    Yields:
        UnitOfWork instance
    """
    uow = UnitOfWork()
    try:
        yield uow
    except Exception:
        uow.rollback()
        raise
    else:
        uow.commit()
    finally:
        uow.close()
