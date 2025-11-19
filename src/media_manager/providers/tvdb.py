"""TVDB (TheTVDB) provider implementation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from media_manager.logging import get_logger
from .base import BaseProvider, ProviderError, ProviderResult


class TVDBProvider(BaseProvider):
    """Provider for TVDB API (v4)."""

    API_BASE = "https://api4.thetvdb.com/v4"
    CACHE_DIR = Path.home() / ".media-manager" / "tvdb_cache"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize TVDB provider.

        Args:
            api_key: TVDB API key. If None, ProviderError will be raised on API calls.
        """
        super().__init__(api_key)
        self._logger = get_logger().get_logger(__name__)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._token: str | None = None

    def _authenticate(self) -> None:
        """Authenticate and get token for TVDB API v4."""
        if not self.api_key:
            raise ProviderError("TVDB API key is not configured")

        cache_key = "tvdb_token"
        cache_path = self.CACHE_DIR / f"{hashlib.md5(cache_key.encode()).hexdigest()}.json"

        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._token = data.get("token")
                    if self._token:
                        return
            except Exception as exc:
                self._logger.debug(f"Failed to load token cache: {exc}")

        try:
            response = requests.post(
                f"{self.API_BASE}/login",
                json={"apikey": self.api_key},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            self._token = data.get("data", {}).get("token")

            if self._token:
                try:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump({"token": self._token}, f)
                except Exception as exc:
                    self._logger.debug(f"Failed to cache token: {exc}")
        except requests.RequestException as exc:
            self._logger.error(f"TVDB authentication failed: {exc}")
            raise ProviderError(f"TVDB authentication failed: {exc}") from exc

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, TimeoutError)),
    )
    def _api_call(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an API call to TVDB.

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            Parsed JSON response

        Raises:
            ProviderError: If not authenticated or API call fails
        """
        if not self._token:
            self._authenticate()

        headers = {
            "Authorization": f"Bearer {self._token}",
        }

        try:
            response = requests.get(
                f"{self.API_BASE}{endpoint}",
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            self._logger.error(f"TVDB API error: {exc}")
            raise ProviderError(f"TVDB API call failed: {exc}") from exc

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key.

        Args:
            key: Cache key (any string)

        Returns:
            Path to cache file
        """
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.CACHE_DIR / f"{hash_key}.json"

    def _load_from_cache(self, key: str) -> dict[str, Any] | None:
        """Load data from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as exc:
                self._logger.debug(f"Failed to load cache: {exc}")
        return None

    def _save_to_cache(self, key: str, data: dict[str, Any]) -> None:
        """Save data to cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            self._logger.debug(f"Failed to save cache: {exc}")

    def search_movie(self, title: str, year: int | None = None) -> list[ProviderResult]:
        """Search for a movie by title and optional year.

        TVDB v4 focuses on TV content, so this will return limited results.

        Args:
            title: Movie title to search for
            year: Optional release year (ignored for TVDB)

        Returns:
            List of ProviderResult objects
        """
        cache_key = f"movie_search:{title}:{year}"
        cached = self._load_from_cache(cache_key)
        if cached:
            return self._parse_search_results(cached, "movie")

        try:
            params = {"query": title, "type": "movie"}
            response = self._api_call("/search", params)
            self._save_to_cache(cache_key, response)
            return self._parse_search_results(response, "movie")
        except ProviderError:
            raise
        except Exception as exc:
            self._logger.error(f"Failed to search movie: {exc}")
            raise ProviderError(f"Failed to search movie: {exc}") from exc

    def search_tv(self, title: str, year: int | None = None) -> list[ProviderResult]:
        """Search for a TV series by title and optional year.

        Args:
            title: TV series title to search for
            year: Optional release year (ignored for TVDB v4)

        Returns:
            List of ProviderResult objects
        """
        cache_key = f"tv_search:{title}:{year}"
        cached = self._load_from_cache(cache_key)
        if cached:
            return self._parse_search_results(cached, "tv")

        try:
            params = {"query": title, "type": "series"}
            response = self._api_call("/search", params)
            self._save_to_cache(cache_key, response)
            return self._parse_search_results(response, "tv")
        except ProviderError:
            raise
        except Exception as exc:
            self._logger.error(f"Failed to search TV series: {exc}")
            raise ProviderError(f"Failed to search TV series: {exc}") from exc

    def get_movie_details(self, external_id: str) -> ProviderResult:
        """Get full details for a movie.

        Args:
            external_id: TVDB movie ID

        Returns:
            ProviderResult with complete metadata
        """
        cache_key = f"movie_details:{external_id}"
        cached = self._load_from_cache(cache_key)
        if cached:
            return self._parse_details(cached, "movie")

        try:
            response = self._api_call(f"/movies/{external_id}", {"extended": "full"})
            self._save_to_cache(cache_key, response)
            return self._parse_details(response, "movie")
        except ProviderError:
            raise
        except Exception as exc:
            self._logger.error(f"Failed to get movie details: {exc}")
            raise ProviderError(f"Failed to get movie details: {exc}") from exc

    def get_tv_details(self, external_id: str, season: int | None = None, episode: int | None = None) -> ProviderResult:
        """Get full details for a TV series or episode.

        Args:
            external_id: TVDB series ID
            season: Optional season number
            episode: Optional episode number

        Returns:
            ProviderResult with complete metadata
        """
        if season is not None and episode is not None:
            cache_key = f"tv_episode_details:{external_id}:{season}:{episode}"
            cached = self._load_from_cache(cache_key)
            if cached:
                return self._parse_details(cached, "tv")

            try:
                response = self._api_call(f"/series/{external_id}/episodes/default/{season}/{episode}")
                self._save_to_cache(cache_key, response)
                return self._parse_details(response, "tv")
            except ProviderError:
                raise
            except Exception as exc:
                self._logger.error(f"Failed to get TV episode details: {exc}")
                raise ProviderError(f"Failed to get TV episode details: {exc}") from exc
        else:
            cache_key = f"tv_details:{external_id}"
            cached = self._load_from_cache(cache_key)
            if cached:
                return self._parse_details(cached, "tv")

            try:
                response = self._api_call(f"/series/{external_id}", {"extended": "full"})
                self._save_to_cache(cache_key, response)
                return self._parse_details(response, "tv")
            except ProviderError:
                raise
            except Exception as exc:
                self._logger.error(f"Failed to get TV details: {exc}")
                raise ProviderError(f"Failed to get TV details: {exc}") from exc

    def get_cast(self, external_id: str, media_type: str) -> list[str]:
        """Get cast list for a movie or TV series.

        Args:
            external_id: TVDB ID
            media_type: "movie" or "tv"

        Returns:
            List of actor names
        """
        try:
            endpoint_type = "movies" if media_type == "movie" else "series"
            response = self._api_call(f"/{endpoint_type}/{external_id}", {"extended": "full"})
            cast_list = []

            # Extract actors from characters
            if media_type == "tv":
                characters = response.get("data", {}).get("characters", [])
            else:
                characters = response.get("data", {}).get("characters", [])

            for character in characters[:10]:
                if character.get("personName"):
                    cast_list.append(character["personName"])

            return cast_list
        except Exception as exc:
            self._logger.warning(f"Failed to get cast: {exc}")
            return []

    def get_trailers(self, external_id: str, media_type: str) -> list[str]:
        """Get trailer URLs for a movie or TV series.

        Args:
            external_id: TVDB ID
            media_type: "movie" or "tv"

        Returns:
            List of trailer URLs
        """
        try:
            endpoint_type = "movies" if media_type == "movie" else "series"
            response = self._api_call(f"/{endpoint_type}/{external_id}")
            trailers = []

            data = response.get("data", {})
            if isinstance(data, dict):
                # TVDB doesn't have direct trailer URLs in API v4
                # This would need to be enhanced with additional API calls
                pass

            return trailers
        except Exception as exc:
            self._logger.warning(f"Failed to get trailers: {exc}")
            return []

    def _parse_search_results(self, response: dict[str, Any], media_type: str) -> list[ProviderResult]:
        """Parse search results from API response.

        Args:
            response: API response
            media_type: "movie" or "tv"

        Returns:
            List of ProviderResult objects
        """
        results = []
        for item in response.get("data", []):
            if not item.get("id"):
                continue

            title = item.get("name", item.get("title", ""))
            year = None

            # Try to extract year from first_air_date or year field
            if item.get("first_air_date"):
                year = int(item["first_air_date"][:4])
            elif item.get("year"):
                year = item["year"]

            poster_url = None
            if item.get("image_url"):
                poster_url = item["image_url"]

            fanart_url = None
            if item.get("thumbnail"):
                fanart_url = item["thumbnail"]

            # TVDB search results have limited rating, use default confidence
            confidence = 0.8

            result = ProviderResult(
                provider_name="TVDB",
                external_id=str(item["id"]),
                title=title,
                year=year,
                overview=item.get("overview"),
                confidence=confidence,
                poster_url=poster_url,
                fanart_url=fanart_url,
            )
            results.append(result)

        return results

    def _parse_details(self, response: dict[str, Any], media_type: str) -> ProviderResult:
        """Parse details from API response.

        Args:
            response: API response
            media_type: "movie" or "tv"

        Returns:
            ProviderResult with complete metadata
        """
        data = response.get("data", {})

        title = data.get("name", data.get("title", ""))
        year = None

        if data.get("first_air_date"):
            year = int(data["first_air_date"][:4])
        elif data.get("year"):
            year = data["year"]

        cast_list = []
        if "characters" in data:
            for character in data["characters"][:10]:
                if character.get("personName"):
                    cast_list.append(character["personName"])

        poster_url = None
        if data.get("image"):
            poster_url = data["image"]

        fanart_url = None
        if data.get("thumbnail"):
            fanart_url = data["thumbnail"]

        aired_date = data.get("first_air_date") or data.get("date") or data.get("air_date")

        companies = []
        if media_type == "tv" and "companies" in data:
            for company in data["companies"][:5]:
                if isinstance(company, dict) and company.get("name"):
                    companies.append(company["name"])
                elif isinstance(company, str):
                    companies.append(company)

        genres = []
        if "genres" in data:
            for genre in data["genres"]:
                if isinstance(genre, dict) and genre.get("name"):
                    genres.append(genre["name"])
                elif isinstance(genre, str):
                    genres.append(genre)

        runtime = data.get("runtime") or data.get("episode_runtime")

        return ProviderResult(
            provider_name="TVDB",
            external_id=str(data["id"]),
            title=title,
            year=year,
            overview=data.get("overview"),
            confidence=1.0,
            runtime=runtime,
            aired_date=aired_date,
            cast=cast_list,
            genres=genres,
            poster_url=poster_url,
            fanart_url=fanart_url,
            trailers=[],
            companies=companies,
            metadata={"original_name": data.get("original_name", "")},
        )
