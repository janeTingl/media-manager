"""Base provider interface for metadata lookups."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    """Exception raised by providers."""

    pass


@dataclass
class ProviderResult:
    """Result from a provider query."""

    provider_name: str
    external_id: str
    title: str
    year: int | None = None
    overview: str | None = None
    confidence: float = 1.0
    runtime: int | None = None
    aired_date: str | None = None
    cast: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    poster_url: str | None = None
    fanart_url: str | None = None
    banner_url: str | None = None
    thumbnail_url: str | None = None
    trailers: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider_name": self.provider_name,
            "external_id": self.external_id,
            "title": self.title,
            "year": self.year,
            "overview": self.overview,
            "confidence": self.confidence,
            "runtime": self.runtime,
            "aired_date": self.aired_date,
            "cast": self.cast,
            "genres": self.genres,
            "poster_url": self.poster_url,
            "fanart_url": self.fanart_url,
            "banner_url": self.banner_url,
            "thumbnail_url": self.thumbnail_url,
            "trailers": self.trailers,
            "companies": self.companies,
            "metadata": self.metadata,
        }


class BaseProvider(ABC):
    """Base class for metadata providers."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the provider."""
        self.api_key = api_key
        self.name = self.__class__.__name__

    @abstractmethod
    def search_movie(self, title: str, year: int | None = None) -> list[ProviderResult]:
        """Search for a movie by title and optional year.

        Args:
            title: Movie title to search for
            year: Optional release year for disambiguation

        Returns:
            List of ProviderResult objects with confidence scores

        Raises:
            ProviderError: If the API call fails or API key is missing
        """
        pass

    @abstractmethod
    def search_tv(
        self, title: str, year: int | None = None
    ) -> list[ProviderResult]:
        """Search for a TV series by title and optional year.

        Args:
            title: TV series title to search for
            year: Optional release year for disambiguation

        Returns:
            List of ProviderResult objects with confidence scores

        Raises:
            ProviderError: If the API call fails or API key is missing
        """
        pass

    @abstractmethod
    def get_movie_details(self, external_id: str) -> ProviderResult:
        """Get full details for a movie.

        Args:
            external_id: Provider-specific movie ID

        Returns:
            ProviderResult with complete metadata

        Raises:
            ProviderError: If the API call fails or ID is invalid
        """
        pass

    @abstractmethod
    def get_tv_details(self, external_id: str, season: int | None = None, episode: int | None = None) -> ProviderResult:
        """Get full details for a TV series or episode.

        Args:
            external_id: Provider-specific series ID
            season: Optional season number for episode-specific details
            episode: Optional episode number for episode-specific details

        Returns:
            ProviderResult with complete metadata

        Raises:
            ProviderError: If the API call fails or ID is invalid
        """
        pass

    @abstractmethod
    def get_cast(self, external_id: str, media_type: str) -> list[str]:
        """Get cast list for a movie or TV series.

        Args:
            external_id: Provider-specific ID
            media_type: "movie" or "tv"

        Returns:
            List of actor names

        Raises:
            ProviderError: If the API call fails
        """
        pass

    @abstractmethod
    def get_trailers(self, external_id: str, media_type: str) -> list[str]:
        """Get trailer URLs for a movie or TV series.

        Args:
            external_id: Provider-specific ID
            media_type: "movie" or "tv"

        Returns:
            List of trailer URLs

        Raises:
            ProviderError: If the API call fails
        """
        pass
