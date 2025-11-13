"""Service for managing person (actor/director) data with provider integration."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from .logging import get_logger
from .persistence.database import get_database_service
from .persistence.models import Person, Credit, MediaItem
from .providers.tmdb import TMDBProvider
from .settings import get_tmdb_api_key


@dataclass
class PersonDetails:
    """Detailed person information."""
    
    id: int
    name: str
    biography: Optional[str] = None
    birthday: Optional[str] = None
    deathday: Optional[str] = None
    image_url: Optional[str] = None
    external_id: Optional[str] = None
    place_of_birth: Optional[str] = None
    known_for_department: Optional[str] = None
    filmography: List[FilmographyEntry] = None
    
    def __post_init__(self) -> None:
        if self.filmography is None:
            self.filmography = []


@dataclass
class FilmographyEntry:
    """Single filmography entry linking person to media item."""
    
    media_item_id: int
    media_item_title: str
    media_type: str
    year: Optional[int]
    role: str  # "actor", "director", "writer", etc.
    character_name: Optional[str] = None
    order: int = 0
    rating: Optional[float] = None
    poster_url: Optional[str] = None


class PersonService:
    """Service for managing person data with caching and provider integration."""
    
    CACHE_DIR = Path.home() / ".media-manager" / "person_cache"
    CACHE_TTL_DAYS = 30
    
    def __init__(self) -> None:
        """Initialize person service."""
        self._logger = get_logger().get_logger(__name__)
        self._db_service = get_database_service()
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize TMDB provider if API key available
        api_key = get_tmdb_api_key()
        self._tmdb_provider = TMDBProvider(api_key) if api_key else None
    
    def get_person_by_id(self, person_id: int, force_refresh: bool = False) -> Optional[PersonDetails]:
        """Get person details by database ID.
        
        Args:
            person_id: Database person ID
            force_refresh: Force refresh from provider even if cached
            
        Returns:
            PersonDetails or None if not found
        """
        with self._db_service.get_session() as session:
            # Get person from database
            statement = (
                select(Person)
                .where(Person.id == person_id)
                .options(selectinload(Person.credits).selectinload(Credit.media_item))
            )
            person = session.exec(statement).first()
            
            if not person:
                return None
            
            # Check if we need to refresh from provider
            needs_refresh = force_refresh or self._needs_refresh(person)
            
            if needs_refresh and person.external_id and self._tmdb_provider:
                self._refresh_person_from_provider(person, session)
            
            # Build person details
            return self._build_person_details(person)
    
    def get_person_by_name(self, name: str, force_refresh: bool = False) -> Optional[PersonDetails]:
        """Get person details by name.
        
        Args:
            name: Person name
            force_refresh: Force refresh from provider
            
        Returns:
            PersonDetails or None if not found
        """
        with self._db_service.get_session() as session:
            statement = (
                select(Person)
                .where(Person.name == name)
                .options(selectinload(Person.credits).selectinload(Credit.media_item))
            )
            person = session.exec(statement).first()
            
            if not person:
                return None
            
            # Check if we need to refresh from provider
            needs_refresh = force_refresh or self._needs_refresh(person)
            
            if needs_refresh and person.external_id and self._tmdb_provider:
                self._refresh_person_from_provider(person, session)
            
            return self._build_person_details(person)
    
    def search_person(self, query: str) -> List[PersonDetails]:
        """Search for persons by name.
        
        Args:
            query: Search query
            
        Returns:
            List of PersonDetails matching the query
        """
        with self._db_service.get_session() as session:
            statement = (
                select(Person)
                .where(Person.name.ilike(f"%{query}%"))
                .options(selectinload(Person.credits).selectinload(Credit.media_item))
                .limit(50)
            )
            persons = session.exec(statement).all()
            
            return [self._build_person_details(person) for person in persons]
    
    def get_headshot_path(self, person_id: int) -> Optional[Path]:
        """Get local path to cached headshot image.
        
        Args:
            person_id: Database person ID
            
        Returns:
            Path to cached headshot or None
        """
        with self._db_service.get_session() as session:
            person = session.get(Person, person_id)
            if not person or not person.image_url:
                return None
            
            # Generate cache path from image URL
            url_hash = hashlib.md5(person.image_url.encode()).hexdigest()
            cache_path = self.CACHE_DIR / f"{url_hash}.jpg"
            
            return cache_path if cache_path.exists() else None
    
    def download_headshot(self, person_id: int, force_download: bool = False) -> Optional[Path]:
        """Download and cache person headshot.
        
        Args:
            person_id: Database person ID
            force_download: Force re-download even if cached
            
        Returns:
            Path to cached headshot or None
        """
        with self._db_service.get_session() as session:
            person = session.get(Person, person_id)
            if not person or not person.image_url:
                return None
            
            # Generate cache path
            url_hash = hashlib.md5(person.image_url.encode()).hexdigest()
            cache_path = self.CACHE_DIR / f"{url_hash}.jpg"
            
            # Return cached if exists and not forcing
            if cache_path.exists() and not force_download:
                return cache_path
            
            # Download image
            try:
                import requests
                response = requests.get(person.image_url, timeout=10)
                response.raise_for_status()
                
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                
                self._logger.info(f"Downloaded headshot for {person.name}: {cache_path}")
                return cache_path
                
            except Exception as exc:
                self._logger.error(f"Failed to download headshot: {exc}")
                return None
    
    def _needs_refresh(self, person: Person) -> bool:
        """Check if person data needs refresh from provider.
        
        Args:
            person: Person entity
            
        Returns:
            True if refresh needed
        """
        # Check if data is stale (older than TTL)
        if person.updated_at:
            age = datetime.utcnow() - person.updated_at
            if age > timedelta(days=self.CACHE_TTL_DAYS):
                return True
        
        # Check if essential data is missing
        if not person.biography and person.external_id:
            return True
        
        return False
    
    def _refresh_person_from_provider(self, person: Person, session: Session) -> None:
        """Refresh person data from provider.
        
        Args:
            person: Person entity to refresh
            session: Database session
        """
        if not self._tmdb_provider or not person.external_id:
            return
        
        try:
            # Check cache first
            cache_key = f"person_{person.external_id}"
            cached_data = self._load_from_cache(cache_key)
            
            if not cached_data:
                # Fetch from TMDB API
                endpoint = f"/person/{person.external_id}"
                response = self._tmdb_provider._api_call(endpoint)
                
                # Save to cache
                self._save_to_cache(cache_key, response)
                cached_data = response
            
            # Update person entity
            person.biography = cached_data.get("biography")
            person.birthday = cached_data.get("birthday")
            person.deathday = cached_data.get("deathday")
            person.updated_at = datetime.utcnow()
            
            # Update image URL if present
            if cached_data.get("profile_path"):
                person.image_url = f"{self._tmdb_provider.IMAGE_BASE}/w342{cached_data['profile_path']}"
            
            session.add(person)
            session.commit()
            
            self._logger.info(f"Refreshed person data for {person.name}")
            
        except Exception as exc:
            self._logger.error(f"Failed to refresh person from provider: {exc}")
    
    def _build_person_details(self, person: Person) -> PersonDetails:
        """Build PersonDetails from Person entity.
        
        Args:
            person: Person entity
            
        Returns:
            PersonDetails with filmography
        """
        # Build filmography from credits
        filmography = []
        for credit in sorted(person.credits, key=lambda c: (c.media_item.year or 0, c.order), reverse=True):
            if credit.media_item:
                # Get poster URL from artworks
                poster_url = None
                for artwork in credit.media_item.artworks:
                    if artwork.artwork_type == "poster" and artwork.url:
                        poster_url = artwork.url
                        break
                
                entry = FilmographyEntry(
                    media_item_id=credit.media_item.id,
                    media_item_title=credit.media_item.title,
                    media_type=credit.media_item.media_type,
                    year=credit.media_item.year,
                    role=credit.role,
                    character_name=credit.character_name,
                    order=credit.order,
                    rating=credit.media_item.rating,
                    poster_url=poster_url
                )
                filmography.append(entry)
        
        return PersonDetails(
            id=person.id,
            name=person.name,
            biography=person.biography,
            birthday=person.birthday,
            deathday=person.deathday,
            image_url=person.image_url,
            external_id=person.external_id,
            filmography=filmography
        )
    
    def _load_from_cache(self, key: str) -> Optional[dict]:
        """Load data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None
        """
        cache_path = self.CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Check if cache is stale
                    cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
                    age = datetime.utcnow() - cached_at
                    if age > timedelta(days=self.CACHE_TTL_DAYS):
                        return None
                    
                    return data.get("data")
            except Exception as exc:
                self._logger.debug(f"Failed to load cache: {exc}")
        return None
    
    def _save_to_cache(self, key: str, data: dict) -> None:
        """Save data to cache.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        cache_path = self.CACHE_DIR / f"{hashlib.md5(key.encode()).hexdigest()}.json"
        try:
            cache_data = {
                "_cached_at": datetime.utcnow().isoformat(),
                "data": data
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            self._logger.debug(f"Failed to save cache: {exc}")
