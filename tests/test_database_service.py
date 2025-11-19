"""Tests for the database service behavior."""

from media_manager.persistence.database import DatabaseService


def test_run_migrations_creates_tables_when_alembic_missing(tmp_path, monkeypatch) -> None:
    """Fallback to SQLModel metadata table creation when Alembic config is missing."""
    db_path = tmp_path / "fallback.db"
    service = DatabaseService(
        f"sqlite:///{db_path}",
        alembic_ini_path=tmp_path / "missing" / "alembic.ini",
    )

    create_all_called = False

    def fake_create_all(self) -> None:
        nonlocal create_all_called
        create_all_called = True

    monkeypatch.setattr(DatabaseService, "create_all", fake_create_all)

    service.run_migrations()

    assert create_all_called is True
