"""TheTVDB provider client."""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from media_manager.models import (
    Episode,
    ImageUrls,
    MediaMetadata,
    Movie,
    Season,
    TVShow,
)

from .base import APIError, BaseProviderClient

logger = logging.getLogger(__name__)


class TheTVDBClient(BaseProviderClient):
    """TheTVDB API client."""

    BASE_URL = "https://api4.thetvdb.com/v4"

    def __init__(self, settings, cache_ttl_seconds: int = 3600):
        super().__init__(settings, cache_ttl_seconds)
        self._auth_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        if self._auth_token and (not self._token_expires or self._token_expires > datetime.now()):
            return {
                "Authorization": f"Bearer {self._auth_token}",
                "Content-Type": "application/json"
            }
        return {
            "Content-Type": "application/json"
        }

    def _get_api_key(self) -> str:
        """Get TheTVDB API key from settings."""
        api_key = self.settings.get_thetvdb_api_key()
        if not api_key:
            raise APIError("TheTVDB API key not configured")
        return api_key

    async def _ensure_auth(self) -> None:
        """Ensure we have a valid authentication token."""
        if self._auth_token and (not self._token_expires or self._token_expires > datetime.now()):
            return

        # Authenticate using a temporary client without auth headers
        auth_data = {
            "apikey": self._get_api_key()
        }

        try:
            temp_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={"Content-Type": "application/json"},
                follow_redirects=True
            )

            response = await temp_client.post(f"{self.BASE_URL}/login", json=auth_data)
            response.raise_for_status()
            await temp_client.aclose()

            auth_response = await response.json()
            self._auth_token = auth_response.get("data", {}).get("token")

            if not self._auth_token:
                raise APIError("Failed to obtain authentication token")

            # Token expires after 24 hours
            self._token_expires = datetime.now() + timedelta(hours=24)

        except Exception as e:
            raise APIError(f"Authentication failed: {str(e)}") from e

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized with auth headers."""
        if self._client is None:
            await self._ensure_auth()
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=self._get_headers(),
                follow_redirects=True
            )

    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with authentication."""
        await self._ensure_auth()
        return await super()._make_request(method, url, params, use_cache, **kwargs)

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            # TheTVDB uses various date formats
            for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except ValueError:
            return None

    async def _parse_images(self, data: Dict[str, Any]) -> ImageUrls:
        """Parse image URLs from TheTVDB data."""
        # TheTVDB image URLs need to be constructed with base URL
        base_url = "https://artworks.thetvdb.com"

        # TheTVDB has different image structure
        images = data.get('image', {}) or data.get('images', {})

        return ImageUrls(
            poster=f"{base_url}{images.get('poster')}" if images.get('poster') else None,
            backdrop=f"{base_url}{images.get('background')}" if images.get('background') else None,
            logo=f"{base_url}{images.get('logo')}" if images.get('logo') else None,
            thumbnail=f"{base_url}{images.get('poster')}" if images.get('poster') else None
        )

    def _parse_metadata(self, data: Dict[str, Any]) -> MediaMetadata:
        """Parse metadata from TheTVDB data."""
        return MediaMetadata(
            language=data.get('language'),
            country=data.get('country'),
            genres=data.get('genres', {}).get('names', []) if isinstance(data.get('genres'), dict) else data.get('genres', []),
            keywords=data.get('tags', []),
            rating=data.get('score'),
            vote_count=data.get('votes'),
            popularity=data.get('popularity')
        )

    def _parse_movie(self, data: Dict[str, Any]) -> Movie:
        """Parse TheTVDB movie data to Movie model."""
        # TheTVDB movie structure
        movie_data = data.get('data', data)

        return Movie(
            id=str(movie_data['id']),
            title=movie_data['name'],
            original_title=movie_data.get('original_name'),
            overview=movie_data.get('overview'),
            release_date=self._parse_date(movie_data.get('first_air')),
            runtime_minutes=movie_data.get('runtime'),
            images=self._parse_images(movie_data),
            metadata=self._parse_metadata(movie_data),
            external_ids={
                'tvdb': str(movie_data['id']),
                'imdb': movie_data.get('imdb_id')
            },
            raw_data=data
        )

    def _parse_tv_show(self, data: Dict[str, Any]) -> TVShow:
        """Parse TheTVDB TV show data to TVShow model."""
        show_data = data.get('data', data)

        return TVShow(
            id=str(show_data['id']),
            title=show_data['name'],
            original_title=show_data.get('original_name'),
            overview=show_data.get('overview'),
            first_air_date=self._parse_date(show_data.get('first_air')),
            last_air_date=self._parse_date(show_data.get('last_air')),
            status=show_data.get('status', {}).get('name') if isinstance(show_data.get('status'), dict) else show_data.get('status'),
            number_of_seasons=show_data.get('seasons_count'),
            number_of_episodes=show_data.get('episodes_count'),
            images=self._parse_images(show_data),
            metadata=self._parse_metadata(show_data),
            external_ids={
                'tvdb': str(show_data['id']),
                'imdb': show_data.get('imdb_id'),
                'tmdb': str(show_data.get('tmdb_id')) if show_data.get('tmdb_id') else None
            },
            raw_data=data
        )

    def _parse_season(self, data: Dict[str, Any], tv_show_id: str) -> Season:
        """Parse TheTVDB season data to Season model."""
        season_data = data.get('data', data)

        return Season(
            id=str(season_data['id']),
            tv_show_id=tv_show_id,
            season_number=season_data['number'],
            title=season_data.get('name'),
            overview=season_data.get('overview'),
            air_date=self._parse_date(season_data.get('first_air')),
            episode_count=season_data.get('episodes_count'),
            images=self._parse_images(season_data),
            metadata=self._parse_metadata(season_data),
            external_ids={'tvdb': str(season_data['id'])},
            raw_data=data
        )

    def _parse_episode(self, data: Dict[str, Any], tv_show_id: str, season_id: str) -> Episode:
        """Parse TheTVDB episode data to Episode model."""
        episode_data = data.get('data', data)

        return Episode(
            id=str(episode_data['id']),
            tv_show_id=tv_show_id,
            season_id=season_id,
            season_number=episode_data['season_number'],
            episode_number=episode_data['number'],
            title=episode_data.get('name'),
            overview=episode_data.get('overview'),
            air_date=self._parse_date(episode_data.get('first_air')),
            runtime_minutes=episode_data.get('runtime'),
            images=self._parse_images(episode_data),
            metadata=self._parse_metadata(episode_data),
            external_ids={'tvdb': str(episode_data['id'])},
            raw_data=data
        )

    async def search_movie(self, query: str, year: Optional[int] = None) -> List[Movie]:
        """Search for movies."""
        params = {
            "query": query,
            "type": "movie"
        }
        if year:
            params["year"] = year

        data = await self._make_request("GET", f"{self.BASE_URL}/search", params=params)

        movies = []
        for item in data.get("data", {}).get("results", []):
            if item.get('type') == 'movie':
                movies.append(self._parse_movie(item))

        return movies

    async def search_tv_show(self, query: str, year: Optional[int] = None) -> List[TVShow]:
        """Search for TV shows."""
        params = {
            "query": query,
            "type": "series"
        }
        if year:
            params["year"] = year

        data = await self._make_request("GET", f"{self.BASE_URL}/search", params=params)

        shows = []
        for item in data.get("data", {}).get("results", []):
            if item.get('type') == 'series':
                shows.append(self._parse_tv_show(item))

        return shows

    async def get_movie_details(self, movie_id: str) -> Movie:
        """Get detailed movie information."""
        data = await self._make_request("GET", f"{self.BASE_URL}/movies/{movie_id}/extended")
        return self._parse_movie(data)

    async def get_tv_show_details(self, tv_show_id: str) -> TVShow:
        """Get detailed TV show information."""
        data = await self._make_request("GET", f"{self.BASE_URL}/series/{tv_show_id}/extended")
        return self._parse_tv_show(data)

    async def get_season_details(self, tv_show_id: str, season_number: int) -> Season:
        """Get season details."""
        # First get all seasons to find the season ID
        seasons_data = await self._make_request("GET", f"{self.BASE_URL}/series/{tv_show_id}/seasons")

        season_id = None
        for season in seasons_data.get("data", {}).get("seasons", []):
            if season.get("number") == season_number:
                season_id = season.get("id")
                break

        if not season_id:
            raise APIError(f"Season {season_number} not found for TV show {tv_show_id}")

        data = await self._make_request("GET", f"{self.BASE_URL}/seasons/{season_id}/extended")
        return self._parse_season(data, tv_show_id)

    async def get_episode_details(self, tv_show_id: str, season_number: int, episode_number: int) -> Episode:
        """Get episode details."""
        # First get the season to find the season ID
        season_data = await self.get_season_details(tv_show_id, season_number)
        season_id = season_data.id

        # Get all episodes in the season
        episodes_data = await self._make_request("GET", f"{self.BASE_URL}/seasons/{season_id}/episodes/extended")

        episode_data = None
        for episode in episodes_data.get("data", {}).get("episodes", []):
            if episode.get("number") == episode_number:
                episode_data = episode
                break

        if not episode_data:
            raise APIError(f"Episode {episode_number} not found in season {season_number} of TV show {tv_show_id}")

        return self._parse_episode({"data": episode_data}, tv_show_id, season_id)
