"""Tests for metadata validator (non-Qt)."""

import pytest

from src.media_manager.metadata_validator import MetadataValidator


class TestMetadataValidator:
    """Test cases for MetadataValidator."""

    def test_validate_valid_movie(self) -> None:
        """Test validation of valid movie metadata."""
        validator = MetadataValidator()
        data = {
            "title": "Test Movie",
            "year": 2020,
            "runtime": 120,
            "rating": 7.5,
        }
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_missing_title(self) -> None:
        """Test validation fails when title is missing."""
        validator = MetadataValidator()
        data = {
            "year": 2020,
            "runtime": 120,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("Title" in err for err in errors)

    def test_validate_empty_title(self) -> None:
        """Test validation fails when title is empty."""
        validator = MetadataValidator()
        data = {
            "title": "   ",
            "year": 2020,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_title_too_long(self) -> None:
        """Test validation fails when title is too long."""
        validator = MetadataValidator()
        data = {
            "title": "x" * 300,
            "year": 2020,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("exceed" in err for err in errors)

    def test_validate_invalid_year(self) -> None:
        """Test validation fails with invalid year."""
        validator = MetadataValidator()

        # Too old
        data = {"title": "Test", "year": 1700}
        is_valid, errors = validator.validate(data)
        assert not is_valid

        # Too new
        data = {"title": "Test", "year": 2200}
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_runtime(self) -> None:
        """Test validation fails with invalid runtime."""
        validator = MetadataValidator()

        # Negative runtime
        data = {"title": "Test", "year": 2020, "runtime": -10}
        is_valid, errors = validator.validate(data)
        assert not is_valid

        # Too large runtime
        data = {"title": "Test", "year": 2020, "runtime": 2000}
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_season(self) -> None:
        """Test validation fails with invalid season."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "season": 150,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_episode(self) -> None:
        """Test validation fails with invalid episode."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "episode": 2000,
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_invalid_aired_date(self) -> None:
        """Test validation fails with invalid aired date."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "aired_date": "2020/01/01",  # Wrong format
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_valid_aired_date(self) -> None:
        """Test validation passes with valid aired date."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": 2020,
            "aired_date": "2020-01-15",
        }
        is_valid, errors = validator.validate(data)
        assert is_valid

    def test_validate_invalid_rating(self) -> None:
        """Test validation fails with invalid rating."""
        validator = MetadataValidator()

        # Negative rating
        data = {"title": "Test", "year": 2020, "rating": -5}
        is_valid, errors = validator.validate(data)
        assert not is_valid

        # Too high rating
        data = {"title": "Test", "year": 2020, "rating": 150}
        is_valid, errors = validator.validate(data)
        assert not is_valid

    def test_validate_title_single(self) -> None:
        """Test single title validation."""
        validator = MetadataValidator()

        # Valid
        assert validator.validate_title("Test Movie") is None

        # Empty
        assert validator.validate_title("") is not None

        # Too long
        assert validator.validate_title("x" * 300) is not None

    def test_validate_year_single(self) -> None:
        """Test single year validation."""
        validator = MetadataValidator()

        # Valid
        assert validator.validate_year(2020) is None

        # Invalid
        assert validator.validate_year(1700) is not None
        assert validator.validate_year(2200) is not None

    def test_validate_runtime_single(self) -> None:
        """Test single runtime validation."""
        validator = MetadataValidator()

        # Valid
        assert validator.validate_runtime(120) is None
        assert validator.validate_runtime(0) is None

        # Invalid
        assert validator.validate_runtime(-10) is not None
        assert validator.validate_runtime(2000) is not None

    def test_validate_date_single(self) -> None:
        """Test single date validation."""
        validator = MetadataValidator()

        # Valid
        assert validator.validate_date("2020-01-15") is None
        assert validator.validate_date("") is None  # Empty is OK

        # Invalid
        assert validator.validate_date("2020/01/15") is not None
        assert validator.validate_date("01-15-2020") is not None

    def test_validate_valid_episode(self) -> None:
        """Test validation of valid episode metadata."""
        validator = MetadataValidator()
        data = {
            "title": "Test Episode",
            "year": 2020,
            "season": 2,
            "episode": 5,
            "aired_date": "2020-05-20",
            "runtime": 45,
        }
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0

    def test_validate_multiple_errors(self) -> None:
        """Test validation with multiple errors."""
        validator = MetadataValidator()
        data = {
            "title": "",  # Missing
            "year": 1700,  # Too old
            "runtime": 2000,  # Too high
        }
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert len(errors) > 1

    def test_validate_with_none_values(self) -> None:
        """Test validation with None values."""
        validator = MetadataValidator()
        data = {
            "title": "Test",
            "year": None,
            "runtime": None,
            "rating": None,
            "aired_date": None,
        }
        is_valid, errors = validator.validate(data)
        assert is_valid

    def test_validate_boundary_values(self) -> None:
        """Test validation at boundary values."""
        validator = MetadataValidator()

        # Minimum year
        data = {"title": "Test", "year": 1800}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Maximum year
        data = {"title": "Test", "year": 2100}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Minimum runtime
        data = {"title": "Test", "year": 2020, "runtime": 0}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Maximum runtime
        data = {"title": "Test", "year": 2020, "runtime": 1000}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Minimum season
        data = {"title": "Test", "year": 2020, "season": 0}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Maximum season
        data = {"title": "Test", "year": 2020, "season": 100}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Minimum episode
        data = {"title": "Test", "year": 2020, "episode": 0}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Maximum episode
        data = {"title": "Test", "year": 2020, "episode": 1000}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Minimum rating
        data = {"title": "Test", "year": 2020, "rating": 0}
        is_valid, errors = validator.validate(data)
        assert is_valid

        # Maximum rating
        data = {"title": "Test", "year": 2020, "rating": 100}
        is_valid, errors = validator.validate(data)
        assert is_valid
