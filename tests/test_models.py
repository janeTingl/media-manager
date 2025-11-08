"""Tests for media models."""

import pytest
from datetime import date

from media_manager.models import (
    Movie,
    TVShow,
    Season,
    Episode,
    ImageUrls,
    MediaMetadata,
    SearchResult,
    MediaType,
)


class TestImageUrls:
    """Test ImageUrls model."""
    
    def test_image_urls_creation(self):
        """Test creating ImageUrls with various URLs."""
        images = ImageUrls(
            poster="https://example.com/poster.jpg",
            backdrop="https://example.com/backdrop.jpg",
            logo="https://example.com/logo.png",
            thumbnail="https://example.com/thumb.jpg"
        )
        
        assert images.poster == "https://example.com/poster.jpg"
        assert images.backdrop == "https://example.com/backdrop.jpg"
        assert images.logo == "https://example.com/logo.png"
        assert images.thumbnail == "https://example.com/thumb.jpg"
    
    def test_image_urls_defaults(self):
        """Test ImageUrls with default values."""
        images = ImageUrls()
        
        assert images.poster is None
        assert images.backdrop is None
        assert images.logo is None
        assert images.thumbnail is None


class TestMediaMetadata:
    """Test MediaMetadata model."""
    
    def test_metadata_creation(self):
        """Test creating MediaMetadata with full data."""
        metadata = MediaMetadata(
            language="en",
            country="US",
            genres=["Action", "Drama"],
            keywords=["hero", "marvel"],
            rating=8.5,
            vote_count=1000,
            popularity=75.2
        )
        
        assert metadata.language == "en"
        assert metadata.country == "US"
        assert metadata.genres == ["Action", "Drama"]
        assert metadata.keywords == ["hero", "marvel"]
        assert metadata.rating == 8.5
        assert metadata.vote_count == 1000
        assert metadata.popularity == 75.2
    
    def test_metadata_defaults(self):
        """Test MediaMetadata with default values."""
        metadata = MediaMetadata()
        
        assert metadata.language is None
        assert metadata.country is None
        assert metadata.genres == []
        assert metadata.keywords == []
        assert metadata.rating is None
        assert metadata.vote_count is None
        assert metadata.popularity is None


class TestMovie:
    """Test Movie model."""
    
    def test_movie_creation(self):
        """Test creating Movie with full data."""
        images = ImageUrls(poster="https://example.com/poster.jpg")
        metadata = MediaMetadata(rating=8.5, genres=["Drama"])
        
        movie = Movie(
            id="550",
            title="Fight Club",
            original_title="Fight Club",
            overview="An insomniac office worker...",
            release_date=date(1999, 10, 15),
            runtime_minutes=139,
            images=images,
            metadata=metadata,
            external_ids={"tmdb": "550", "imdb": "tt0137523"},
            raw_data={"test": "data"}
        )
        
        assert movie.id == "550"
        assert movie.title == "Fight Club"
        assert movie.original_title == "Fight Club"
        assert movie.overview == "An insomniac office worker..."
        assert movie.release_date == date(1999, 10, 15)
        assert movie.runtime_minutes == 139
        assert movie.images.poster == "https://example.com/poster.jpg"
        assert movie.metadata.rating == 8.5
        assert movie.metadata.genres == ["Drama"]
        assert movie.external_ids["tmdb"] == "550"
        assert movie.external_ids["imdb"] == "tt0137523"
        assert movie.raw_data == {"test": "data"}
    
    def test_movie_defaults(self):
        """Test Movie with minimal required data."""
        movie = Movie(id="123", title="Test Movie")
        
        assert movie.id == "123"
        assert movie.title == "Test Movie"
        assert movie.original_title is None
        assert movie.overview is None
        assert movie.release_date is None
        assert movie.runtime_minutes is None
        assert isinstance(movie.images, ImageUrls)
        assert isinstance(movie.metadata, MediaMetadata)
        assert movie.external_ids == {}
        assert movie.raw_data == {}


class TestTVShow:
    """Test TVShow model."""
    
    def test_tv_show_creation(self):
        """Test creating TVShow with full data."""
        images = ImageUrls(poster="https://example.com/poster.jpg")
        metadata = MediaMetadata(rating=9.0, genres=["Crime", "Drama"])
        
        show = TVShow(
            id="1396",
            title="Breaking Bad",
            original_title="Breaking Bad",
            overview="A high school chemistry teacher...",
            first_air_date=date(2008, 1, 20),
            last_air_date=date(2013, 9, 29),
            status="Ended",
            number_of_seasons=5,
            number_of_episodes=62,
            images=images,
            metadata=metadata,
            external_ids={"tmdb": "1396", "imdb": "tt0903747"},
            raw_data={"test": "data"}
        )
        
        assert show.id == "1396"
        assert show.title == "Breaking Bad"
        assert show.first_air_date == date(2008, 1, 20)
        assert show.last_air_date == date(2013, 9, 29)
        assert show.status == "Ended"
        assert show.number_of_seasons == 5
        assert show.number_of_episodes == 62
        assert show.metadata.rating == 9.0
        assert show.external_ids["tmdb"] == "1396"
        assert show.external_ids["imdb"] == "tt0903747"


class TestSeason:
    """Test Season model."""
    
    def test_season_creation(self):
        """Test creating Season with full data."""
        images = ImageUrls(poster="https://example.com/season_poster.jpg")
        metadata = MediaMetadata(rating=8.8)
        
        season = Season(
            id="789",
            tv_show_id="1396",
            season_number=1,
            title="Season 1",
            overview="The first season...",
            air_date=date(2008, 1, 20),
            episode_count=7,
            images=images,
            metadata=metadata,
            external_ids={"tmdb": "789"},
            raw_data={"test": "data"}
        )
        
        assert season.id == "789"
        assert season.tv_show_id == "1396"
        assert season.season_number == 1
        assert season.title == "Season 1"
        assert season.overview == "The first season..."
        assert season.air_date == date(2008, 1, 20)
        assert season.episode_count == 7
        assert season.metadata.rating == 8.8
        assert season.external_ids["tmdb"] == "789"


class TestEpisode:
    """Test Episode model."""
    
    def test_episode_creation(self):
        """Test creating Episode with full data."""
        images = ImageUrls(thumbnail="https://example.com/ep_thumb.jpg")
        metadata = MediaMetadata(rating=8.5)
        
        episode = Episode(
            id="101",
            tv_show_id="1396",
            season_id="789",
            season_number=1,
            episode_number=1,
            title="Pilot",
            overview="Walter White is diagnosed with cancer...",
            air_date=date(2008, 1, 20),
            runtime_minutes=58,
            images=images,
            metadata=metadata,
            external_ids={"tmdb": "101"},
            raw_data={"test": "data"}
        )
        
        assert episode.id == "101"
        assert episode.tv_show_id == "1396"
        assert episode.season_id == "789"
        assert episode.season_number == 1
        assert episode.episode_number == 1
        assert episode.title == "Pilot"
        assert episode.overview == "Walter White is diagnosed with cancer..."
        assert episode.air_date == date(2008, 1, 20)
        assert episode.runtime_minutes == 58
        assert episode.metadata.rating == 8.5
        assert episode.external_ids["tmdb"] == "101"


class TestSearchResult:
    """Test SearchResult model."""
    
    def test_search_result_creation(self):
        """Test creating SearchResult."""
        movie = Movie(id="550", title="Fight Club")
        result = SearchResult(
            media_type=MediaType.MOVIE,
            item=movie,
            score=95.5,
            provider="tmdb"
        )
        
        assert result.media_type == MediaType.MOVIE
        assert result.item == movie
        assert result.score == 95.5
        assert result.provider == "tmdb"
    
    def test_search_result_with_tv_show(self):
        """Test SearchResult with TV show."""
        show = TVShow(id="1396", title="Breaking Bad")
        result = SearchResult(
            media_type=MediaType.TV_SHOW,
            item=show,
            score=88.2,
            provider="thetvdb"
        )
        
        assert result.media_type == MediaType.TV_SHOW
        assert result.item == show
        assert result.score == 88.2
        assert result.provider == "thetvdb"


class TestMediaType:
    """Test MediaType enum."""
    
    def test_media_type_values(self):
        """Test MediaType enum values."""
        assert MediaType.MOVIE.value == "movie"
        assert MediaType.TV_SHOW.value == "tv_show"
        assert MediaType.SEASON.value == "season"
        assert MediaType.EPISODE.value == "episode"
    
    def test_media_type_comparison(self):
        """Test MediaType comparison."""
        assert MediaType.MOVIE == MediaType.MOVIE
        assert MediaType.MOVIE != MediaType.TV_SHOW
        assert str(MediaType.MOVIE) == "MediaType.MOVIE"