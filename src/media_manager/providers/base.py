"""Base provider client with common functionality."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from cachetools import TTLCache

from media_manager.models import Episode, Movie, Season, TVShow
from media_manager.settings import SettingsManager

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_second: float = 2.0, burst_size: int = 10):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(self.burst_size, self.tokens + time_passed * self.requests_per_second)
            self.last_update = now

            if self.tokens < 1:
                sleep_time = (1 - self.tokens) / self.requests_per_second
                await asyncio.sleep(sleep_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class APIError(ProviderError):
    """API-related error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(ProviderError):
    """Rate limit exceeded error."""
    pass


class AuthenticationError(ProviderError):
    """Authentication error."""
    pass


class BaseProviderClient(ABC):
    """Base class for provider clients."""

    def __init__(self, settings: SettingsManager, cache_ttl_seconds: int = 3600):
        self.settings = settings
        self.cache = TTLCache(maxsize=1000, ttl=cache_ttl_seconds)
        self.rate_limiter = RateLimiter()
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=self._get_headers(),
                follow_redirects=True
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        pass

    @abstractmethod
    def _get_api_key(self) -> str:
        """Get API key from settings."""
        pass

    def _get_cache_key(self, method: str, **kwargs: Any) -> str:
        """Generate cache key for request."""
        key_parts = [self.__class__.__name__, method] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return "|".join(key_parts)

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Make HTTP request with rate limiting, caching, and error handling."""
        await self._ensure_client()
        await self.rate_limiter.acquire()

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(method, url=url, params=params or {}, **kwargs)
            if cache_key in self.cache:
                logger.debug(f"Cache hit for {cache_key}")
                return self.cache[cache_key]

        try:
            logger.debug(f"Making {method} request to {url}")
            response = await self._client.request(method, url, params=params, **kwargs)
            response.raise_for_status()

            data: Dict[str, Any] = response.json()

            # Cache the response
            if use_cache:
                self.cache[cache_key] = data

            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(f"Rate limit exceeded: {e.response.text}") from e
            elif e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed: {e.response.text}") from e
            else:
                raise APIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    status_code=e.response.status_code,
                    response_data=e.response.json() if e.response.headers.get("content-type", "").startswith("application/json") else None
                ) from e
        except httpx.RequestError as e:
            raise ProviderError(f"Request failed: {str(e)}") from e
        except Exception as e:
            raise ProviderError(f"Unexpected error: {str(e)}") from e

    @abstractmethod
    async def search_movie(self, query: str, year: Optional[int] = None) -> List[Movie]:
        """Search for movies."""
        pass

    @abstractmethod
    async def search_tv_show(self, query: str, year: Optional[int] = None) -> List[TVShow]:
        """Search for TV shows."""
        pass

    @abstractmethod
    async def get_movie_details(self, movie_id: str) -> Movie:
        """Get detailed movie information."""
        pass

    @abstractmethod
    async def get_tv_show_details(self, tv_show_id: str) -> TVShow:
        """Get detailed TV show information."""
        pass

    @abstractmethod
    async def get_season_details(self, tv_show_id: str, season_number: int) -> Season:
        """Get season details."""
        pass

    @abstractmethod
    async def get_episode_details(self, tv_show_id: str, season_number: int, episode_number: int) -> Episode:
        """Get episode details."""
        pass
