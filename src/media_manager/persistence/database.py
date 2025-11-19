"""Database service for managing SQLite connections and migrations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session, create_engine as sm_create_engine

from media_manager.logging import get_logger

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class DatabaseService:
    """Service for managing database connections and operations."""

    def __init__(
        self,
        database_url: str,
        auto_migrate: bool = True,
        alembic_ini_path: Optional[Path] = None,
    ) -> None:
        """Initialize database service.

        Args:
            database_url: SQLAlchemy database URL
            auto_migrate: Whether to automatically run migrations on init
            alembic_ini_path: Optional path to the Alembic configuration file
        """
        self.database_url = database_url
        self.auto_migrate = auto_migrate
        default_alembic_path = Path(__file__).parent / "alembic.ini"
        self.alembic_ini_path = Path(alembic_ini_path) if alembic_ini_path else default_alembic_path
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = sm_create_engine(
                self.database_url,
                echo=False,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {},
            )
        return self._engine

    def create_all(self) -> None:
        """Create all database tables."""
        try:
            SQLModel.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def run_migrations(self) -> None:
        """Run Alembic migrations or fall back to direct table creation when unavailable."""
        alembic_ini = self.alembic_ini_path

        if not alembic_ini.exists():
            logger.warning(
                "Alembic configuration not found at %s. Creating tables using SQLModel metadata instead of running migrations.",
                alembic_ini,
            )
            self.create_all()
            return

        try:
            from alembic.config import Config
            from alembic.command import upgrade

            config = Config(str(alembic_ini))
            config.set_main_option("sqlalchemy.url", self.database_url)

            upgrade(config, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.warning(f"Migration encountered issue: {e}")

    def initialize(self) -> None:
        """Initialize the database."""
        try:
            # First try to run migrations if auto_migrate is enabled
            if self.auto_migrate:
                self.run_migrations()
            else:
                # If migrations are disabled, create all tables directly
                self.create_all()

            logger.info(f"Database initialized: {self.database_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_session(self) -> Session:
        """Create a new database session."""
        return Session(self.engine)

    def close(self) -> None:
        """Close the database engine."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            logger.info("Database engine closed")


# Global database service instance
_database_service: Optional[DatabaseService] = None


def init_database_service(database_url: Optional[str] = None, auto_migrate: bool = True) -> DatabaseService:
    """Initialize the global database service.

    Args:
        database_url: SQLAlchemy database URL. If None, defaults to ~/.media-manager/media_manager.db
        auto_migrate: Whether to automatically run migrations

    Returns:
        Initialized DatabaseService instance
    """
    global _database_service

    if database_url is None:
        db_dir = Path.home() / ".media-manager"
        db_dir.mkdir(parents=True, exist_ok=True)
        database_url = f"sqlite:///{db_dir / 'media_manager.db'}"

    _database_service = DatabaseService(database_url, auto_migrate)
    _database_service.initialize()

    return _database_service


def get_database_service() -> DatabaseService:
    """Get the global database service instance.

    Returns:
        Global DatabaseService instance

    Raises:
        RuntimeError: If database service has not been initialized
    """
    if _database_service is None:
        raise RuntimeError(
            "Database service not initialized. Call init_database_service() first."
        )
    return _database_service
