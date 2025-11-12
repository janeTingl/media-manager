"""Validator for media metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class MetadataValidator:
    """Validates media metadata."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.errors: List[str] = []

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate metadata dictionary.

        Args:
            data: Metadata dictionary to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        self.errors = []

        self._validate_title(data.get("title"))
        self._validate_year(data.get("year"))
        self._validate_runtime(data.get("runtime"))
        self._validate_season(data.get("season"))
        self._validate_episode(data.get("episode"))
        self._validate_aired_date(data.get("aired_date"))
        self._validate_rating(data.get("rating"))

        return len(self.errors) == 0, self.errors

    def _validate_title(self, title: Optional[str]) -> None:
        """Validate title field."""
        if not title or not title.strip():
            self.errors.append("Title is required")
        elif len(title) > 255:
            self.errors.append("Title must not exceed 255 characters")

    def _validate_year(self, year: Optional[int]) -> None:
        """Validate year field."""
        if year is not None:
            if not isinstance(year, int):
                self.errors.append("Year must be an integer")
            elif year < 1800 or year > 2100:
                self.errors.append("Year must be between 1800 and 2100")

    def _validate_runtime(self, runtime: Optional[int]) -> None:
        """Validate runtime field."""
        if runtime is not None:
            if not isinstance(runtime, int):
                self.errors.append("Runtime must be an integer")
            elif runtime < 0 or runtime > 1000:
                self.errors.append("Runtime must be between 0 and 1000 minutes")

    def _validate_season(self, season: Optional[int]) -> None:
        """Validate season field."""
        if season is not None:
            if not isinstance(season, int):
                self.errors.append("Season must be an integer")
            elif season < 0 or season > 100:
                self.errors.append("Season must be between 0 and 100")

    def _validate_episode(self, episode: Optional[int]) -> None:
        """Validate episode field."""
        if episode is not None:
            if not isinstance(episode, int):
                self.errors.append("Episode must be an integer")
            elif episode < 0 or episode > 1000:
                self.errors.append("Episode must be between 0 and 1000")

    def _validate_aired_date(self, aired_date: Optional[str]) -> None:
        """Validate aired date field."""
        if aired_date and aired_date.strip():
            if not self._is_valid_date(aired_date):
                self.errors.append("Aired date must be in YYYY-MM-DD format")

    def _validate_rating(self, rating: Optional[float]) -> None:
        """Validate rating field."""
        if rating is not None:
            if not isinstance(rating, (int, float)):
                self.errors.append("Rating must be a number")
            elif rating < 0 or rating > 100:
                self.errors.append("Rating must be between 0 and 100")

    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is in valid format.

        Args:
            date_str: Date string to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_title(self, title: str) -> Optional[str]:
        """Validate a single title.

        Args:
            title: Title to validate

        Returns:
            Error message or None if valid
        """
        if not title or not title.strip():
            return "Title is required"
        if len(title) > 255:
            return "Title must not exceed 255 characters"
        return None

    def validate_year(self, year: int) -> Optional[str]:
        """Validate a single year.

        Args:
            year: Year to validate

        Returns:
            Error message or None if valid
        """
        if year < 1800 or year > 2100:
            return "Year must be between 1800 and 2100"
        return None

    def validate_runtime(self, runtime: int) -> Optional[str]:
        """Validate a single runtime value.

        Args:
            runtime: Runtime to validate (in minutes)

        Returns:
            Error message or None if valid
        """
        if runtime < 0 or runtime > 1000:
            return "Runtime must be between 0 and 1000 minutes"
        return None

    def validate_date(self, date_str: str) -> Optional[str]:
        """Validate a single date string.

        Args:
            date_str: Date string to validate

        Returns:
            Error message or None if valid
        """
        if not date_str.strip():
            return None
        if not self._is_valid_date(date_str):
            return "Date must be in YYYY-MM-DD format"
        return None
