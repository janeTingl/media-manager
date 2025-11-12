"""TMDB (The Movie Database) provider implementation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..logging import get_logger
from .base import BaseProvider, ProviderError, ProviderResult


class TMDBProvider(BaseProvider):
    """Provider for TMDB API."""

    API_BASE = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p"
    CACHE_DIR = Path.home() / ".media-manager" / "tmdb_cache"

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize TMDB provider.

        Args:
            api_key: TMDB API key. If None, ProviderError will be raised on API calls.
        """
        super().__init__(api_key)
        self._logger = get_logger().get_logger(__name__)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def _api_call(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make an API call to TMDB.

        Args:
            endpoint: API endpoint (without base URL)
            params: Optional query parameters

        Returns:
            Parsed JSON response

        Raises:
            ProviderError: If API key is not set or API call fails
        """
        if not self.api_key:
            raise ProviderError("TMDB API key is not configured")

        if params is None:
            params = {}

        params["api_key"] = self.api_key

        try:
            response = requests.get(
                f"{self.API_BASE}{endpoint}",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            self._logger.error(f"TMDB API error: {exc}")
            raise ProviderError(f"TMDB API call failed: {exc}") from exc

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
                import json
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
            import json
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            self._logger.debug(f"Failed to save cache: {exc}")

    def search_movie(self, title: str, year: int | None = None) -> list[ProviderResult]:
        """Search for a movie by title and optional year.

        Args:
            title: Movie title to search for
            year: Optional release year for disambiguation

        Returns:
            List of ProviderResult objects
        """
        cache_key = f"movie_search:{title}:{year}"
        cached = self._load_from_cache(cache_key)
        if cached:
            return self._parse_search_results(cached, "movie")

        try:
            params = {"query": title, "include_adult": False}
            if year:
                params["year"] = year

            response = self._api_call("/search/movie", params)
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
            year: Optional release year for disambiguation

        Returns:
            List of ProviderResult objects
        """
        cache_key = f"tv_search:{title}:{year}"
        cached = self._load_from_cache(cache_key)
        if cached:
            return self._parse_search_results(cached, "tv")

        try:
            params = {"query": title, "include_adult": False}
            if year:
                params["first_air_date_year"] = year

            response = self._api_call("/search/tv", params)
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
            external_id: TMDB movie ID

        Returns:
            ProviderResult with complete metadata
        """
        cache_key = f"movie_details:{external_id}"
        cached = self._load_from_cache(cache_key)
        if cached:
            return self._parse_movie_details(cached)

        try:
            response = self._api_call(f"/movie/{external_id}", {"append_to_response": "credits,videos,images"})
            self._save_to_cache(cache_key, response)
            return self._parse_movie_details(response)
        except ProviderError:
            raise
        except Exception as exc:
            self._logger.error(f"Failed to get movie details: {exc}")
            raise ProviderError(f"Failed to get movie details: {exc}") from exc

    def get_tv_details(self, external_id: str, season: int | None = None, episode: int | None = None) -> ProviderResult:
        """Get full details for a TV series or episode.

        Args:
            external_id: TMDB series ID
            season: Optional season number
            episode: Optional episode number

        Returns:
            ProviderResult with complete metadata
        """
        if season is not None and episode is not None:
            cache_key = f"tv_episode_details:{external_id}:{season}:{episode}"
            cached = self._load_from_cache(cache_key)
            if cached:
                return self._parse_tv_details(cached)

            try:
                response = self._api_call(
                    f"/tv/{external_id}/season/{season}/episode/{episode}",
                    {"append_to_response": "credits,videos"},
                )
                self._save_to_cache(cache_key, response)
                return self._parse_tv_details(response)
            except ProviderError:
                raise
            except Exception as exc:
                self._logger.error(f"Failed to get TV episode details: {exc}")
                raise ProviderError(f"Failed to get TV episode details: {exc}") from exc
        else:
            cache_key = f"tv_details:{external_id}"
            cached = self._load_from_cache(cache_key)
            if cached:
                return self._parse_tv_details(cached)

            try:
                response = self._api_call(
                    f"/tv/{external_id}",
                    {"append_to_response": "credits,videos,images"},
                )
                self._save_to_cache(cache_key, response)
                return self._parse_tv_details(response)
            except ProviderError:
                raise
            except Exception as exc:
                self._logger.error(f"Failed to get TV details: {exc}")
                raise ProviderError(f"Failed to get TV details: {exc}") from exc

    def get_cast(self, external_id: str, media_type: str) -> list[str]:
        """Get cast list for a movie or TV series.

        Args:
            external_id: TMDB ID
            media_type: "movie" or "tv"

        Returns:
            List of actor names
        """
        try:
            endpoint = f"/{media_type}/{external_id}"
            response = self._api_call(endpoint, {"append_to_response": "credits"})
            credits = response.get("credits", {})
            cast_list = credits.get("cast", [])
            return [person["name"] for person in cast_list[:10]]  # Top 10 cast members
        except Exception as exc:
            self._logger.warning(f"Failed to get cast: {exc}")
            return []

    def get_trailers(self, external_id: str, media_type: str) -> list[str]:
        """Get trailer URLs for a movie or TV series.

        Args:
            external_id: TMDB ID
            media_type: "movie" or "tv"

        Returns:
            List of trailer URLs
        """
        try:
            endpoint = f"/{media_type}/{external_id}"
            response = self._api_call(endpoint, {"append_to_response": "videos"})
            videos = response.get("videos", {})
            results = videos.get("results", [])
            trailers = []
            for video in results:
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    video_id = video.get("key")
                    if video_id:
                        trailers.append(f"https://www.youtube.com/watch?v={video_id}")
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
        for item in response.get("results", []):
            if not item.get("id"):
                continue

            if media_type == "movie":
                title = item.get("title", "")
                year = None
                if item.get("release_date"):
                    year = int(item["release_date"][:4])
                poster_url = None
                if item.get("poster_path"):
                    poster_url = f"{self.IMAGE_BASE}/w342{item['poster_path']}"
                fanart_url = None
                if item.get("backdrop_path"):
                    fanart_url = f"{self.IMAGE_BASE}/w1280{item['backdrop_path']}"
            else:  # TV
                title = item.get("name", "")
                year = None
                if item.get("first_air_date"):
                    year = int(item["first_air_date"][:4])
                poster_url = None
                if item.get("poster_path"):
                    poster_url = f"{self.IMAGE_BASE}/w342{item['poster_path']}"
                fanart_url = None
                if item.get("backdrop_path"):
                    fanart_url = f"{self.IMAGE_BASE}/w1280{item['backdrop_path']}"

            confidence = (item.get("popularity", 0) / 100.0) * 0.5 + 0.5
            confidence = min(1.0, max(0.0, confidence))

            result = ProviderResult(
                provider_name="TMDB",
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

    def _parse_movie_details(self, response: dict[str, Any]) -> ProviderResult:
        """Parse movie details from API response.

        Args:
            response: API response

        Returns:
            ProviderResult with complete metadata
        """
        cast_list = []
        if "credits" in response and "cast" in response["credits"]:
            cast_list = [person["name"] for person in response["credits"]["cast"][:10]]

        trailers = []
        if "videos" in response and "results" in response["videos"]:
            for video in response["videos"]["results"]:
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    video_id = video.get("key")
                    if video_id:
                        trailers.append(f"https://www.youtube.com/watch?v={video_id}")

        companies = []
        for company in response.get("production_companies", [])[:5]:
            if company.get("name"):
                companies.append(company["name"])

        poster_url = None
        if response.get("poster_path"):
            poster_url = f"{self.IMAGE_BASE}/w342{response['poster_path']}"
        fanart_url = None
        if response.get("backdrop_path"):
            fanart_url = f"{self.IMAGE_BASE}/w1280{response['backdrop_path']}"

        year = None
        if response.get("release_date"):
            year = int(response["release_date"][:4])

        genres = [g["name"] for g in response.get("genres", [])]

        return ProviderResult(
            provider_name="TMDB",
            external_id=str(response["id"]),
            title=response.get("title", ""),
            year=year,
            overview=response.get("overview"),
            confidence=1.0,
            runtime=response.get("runtime"),
            aired_date=response.get("release_date"),
            cast=cast_list,
            genres=genres,
            poster_url=poster_url,
            fanart_url=fanart_url,
            trailers=trailers,
            companies=companies,
            metadata={"original_title": response.get("original_title")},
        )

    def _parse_tv_details(self, response: dict[str, Any]) -> ProviderResult:
        """Parse TV series details from API response.

        Args:
            response: API response

        Returns:
            ProviderResult with complete metadata
        """
        cast_list = []
        if "credits" in response and "cast" in response["credits"]:
            cast_list = [person["name"] for person in response["credits"]["cast"][:10]]

        trailers = []
        if "videos" in response and "results" in response["videos"]:
            for video in response["videos"]["results"]:
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    video_id = video.get("key")
                    if video_id:
                        trailers.append(f"https://www.youtube.com/watch?v={video_id}")

        companies = []
        for company in response.get("production_companies", [])[:5]:
            if company.get("name"):
                companies.append(company["name"])

        poster_url = None
        if response.get("poster_path"):
            poster_url = f"{self.IMAGE_BASE}/w342{response['poster_path']}"
        fanart_url = None
        if response.get("backdrop_path"):
            fanart_url = f"{self.IMAGE_BASE}/w1280{response['backdrop_path']}"

        year = None
        if response.get("first_air_date"):
            year = int(response["first_air_date"][:4])

        # Get runtime from first season if available
        runtime = None
        if response.get("episode_run_time"):
            runtime = response["episode_run_time"][0] if response["episode_run_time"] else None

        genres = [g["name"] for g in response.get("genres", [])]

        # Get aired date from first season if this is season/episode query
        aired_date = response.get("first_air_date")
        if "air_date" in response:
            aired_date = response["air_date"]

        return ProviderResult(
            provider_name="TMDB",
            external_id=str(response["id"]),
            title=response.get("name", response.get("title", "")),
            year=year,
            overview=response.get("overview"),
            confidence=1.0,
            runtime=runtime,
            aired_date=aired_date,
            cast=cast_list,
            genres=genres,
            poster_url=poster_url,
            fanart_url=fanart_url,
            trailers=trailers,
            companies=companies,
            metadata={"original_name": response.get("original_name")},
        )
