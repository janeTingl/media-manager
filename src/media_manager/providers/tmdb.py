"""TMDB (The Movie Database) provider client."""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

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


class TMDBClient(BaseProviderClient):
    """TMDB API client."""

    BASE_URL = "https://api.themoviedb.org/3"

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests."""
        return {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json"
        }

    def _get_api_key(self) -> str:
        """Get TMDB API key from settings."""
        api_key = self.settings.get_tmdb_api_key()
        if not api_key:
            raise APIError("TMDB API key not configured")
        return api_key

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _parse_images(self, data: Dict[str, Any]) -> ImageUrls:
        """Parse image URLs from TMDB data."""
        base_url = "https://image.tmdb.org/t/p/original"
        return ImageUrls(
            poster=f"{base_url}{data.get('poster_path')}" if data.get('poster_path') else None,
            backdrop=f"{base_url}{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
            logo=f"{base_url}{data.get('logo_path')}" if data.get('logo_path') else None,
            thumbnail=f"{base_url}{data.get('poster_path')}" if data.get('poster_path') else None
        )

    def _parse_metadata(self, data: Dict[str, Any]) -> MediaMetadata:
        """Parse metadata from TMDB data."""
        return MediaMetadata(
            language=data.get('original_language'),
            country=data.get('production_countries', [{}])[0].get('iso_3166_1') if data.get('production_countries') else None,
            genres=[genre['name'] for genre in data.get('genres', [])],
            rating=data.get('vote_average'),
            vote_count=data.get('vote_count'),
            popularity=data.get('popularity')
        )

    def _parse_movie(self, data: Dict[str, Any]) -> Movie:
        """Parse TMDB movie data to Movie model."""
        return Movie(
            id=str(data['id']),
            title=data['title'],
            original_title=data.get('original_title'),
            overview=data.get('overview'),
            release_date=self._parse_date(data.get('release_date')),
            runtime_minutes=data.get('runtime'),
            images=self._parse_images(data),
            metadata=self._parse_metadata(data),
            external_ids={
                'tmdb': str(data['id']),
                'imdb': data.get('imdb_id')
            },
            raw_data=data
        )

    def _parse_tv_show(self, data: Dict[str, Any]) -> TVShow:
        """Parse TMDB TV show data to TVShow model."""
        return TVShow(
            id=str(data['id']),
            title=data['name'],
            original_title=data.get('original_name'),
            overview=data.get('overview'),
            first_air_date=self._parse_date(data.get('first_air_date')),
            last_air_date=self._parse_date(data.get('last_air_date')),
            status=data.get('status'),
            number_of_seasons=data.get('number_of_seasons'),
            number_of_episodes=data.get('number_of_episodes'),
            images=self._parse_images(data),
            metadata=self._parse_metadata(data),
            external_ids={
                'tmdb': str(data['id']),
                'imdb': data.get('external_ids', {}).get('imdb_id'),
                'tvdb': str(data.get('external_ids', {}).get('tvdb_id')) if data.get('external_ids', {}).get('tvdb_id') is not None else None
            },
            raw_data=data
        )

    def _parse_season(self, data: Dict[str, Any], tv_show_id: str) -> Season:
        """Parse TMDB season data to Season model."""
        return Season(
            id=str(data['id']),
            tv_show_id=tv_show_id,
            season_number=data['season_number'],
            title=data.get('name'),
            overview=data.get('overview'),
            air_date=self._parse_date(data.get('air_date')),
            episode_count=data.get('episode_count'),
            images=self._parse_images(data),
            metadata=self._parse_metadata(data),
            external_ids={'tmdb': str(data['id'])},
            raw_data=data
        )

    def _parse_episode(self, data: Dict[str, Any], tv_show_id: str, season_id: str) -> Episode:
        """Parse TMDB episode data to Episode model."""
        return Episode(
            id=str(data['id']),
            tv_show_id=tv_show_id,
            season_id=season_id,
            season_number=data['season_number'],
            episode_number=data['episode_number'],
            title=data.get('name'),
            overview=data.get('overview'),
            air_date=self._parse_date(data.get('air_date')),
            runtime_minutes=data.get('runtime'),
            images=self._parse_images(data),
            metadata=self._parse_metadata(data),
            external_ids={'tmdb': str(data['id'])},
            raw_data=data
        )

    async def search_movie(self, query: str, year: Optional[int] = None) -> List[Movie]:
        """Search for movies."""
        params = {
            "query": query,
            "include_adult": False
        }
        if year:
            params["year"] = year

        data = await self._make_request("GET", f"{self.BASE_URL}/search/movie", params=params)

        movies = []
        for item in data.get("results", []):
            movies.append(self._parse_movie(item))

        return movies

    async def search_tv_show(self, query: str, year: Optional[int] = None) -> List[TVShow]:
        """Search for TV shows."""
        params = {
            "query": query,
            "include_adult": False
        }
        if year:
            params["first_air_date_year"] = year

        data = await self._make_request("GET", f"{self.BASE_URL}/search/tv", params=params)

        shows = []
        for item in data.get("results", []):
            shows.append(self._parse_tv_show(item))

        return shows

    async def get_movie_details(self, movie_id: str) -> Movie:
        """Get detailed movie information."""
        data = await self._make_request("GET", f"{self.BASE_URL}/movie/{movie_id}", params={"append_to_response": "credits,images"})
        return self._parse_movie(data)

    async def get_tv_show_details(self, tv_show_id: str) -> TVShow:
        """Get detailed TV show information."""
        data = await self._make_request("GET", f"{self.BASE_URL}/tv/{tv_show_id}", params={"append_to_response": "credits,images,external_ids"})
        return self._parse_tv_show(data)

    async def get_season_details(self, tv_show_id: str, season_number: int) -> Season:
        """Get season details."""
        data = await self._make_request("GET", f"{self.BASE_URL}/tv/{tv_show_id}/season/{season_number}")
        return self._parse_season(data, tv_show_id)

    async def get_episode_details(self, tv_show_id: str, season_number: int, episode_number: int) -> Episode:
        """Get episode details."""
        data = await self._make_request("GET", f"{self.BASE_URL}/tv/{tv_show_id}/season/{season_number}/episode/{episode_number}")
        season_data = await self._make_request("GET", f"{self.BASE_URL}/tv/{tv_show_id}/season/{season_number}")
        season_id = str(season_data['id'])
        return self._parse_episode(data, tv_show_id, season_id)
