"""Service for managing production company data with provider integration."""

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
from .persistence.models import Company, MediaItem
from .providers.tmdb import TMDBProvider
from .settings import get_tmdb_api_key


@dataclass
class CompanyProduction:
    """Single production entry linking company to media item."""
    
    media_item_id: int
    media_item_title: str
    media_type: str
    year: Optional[int]
    rating: Optional[float] = None
    poster_url: Optional[str] = None


@dataclass
class CompanyDetails:
    """Detailed company information."""
    
    id: int
    name: str
    description: Optional[str] = None
    headquarters: Optional[str] = None
    homepage: Optional[str] = None
    logo_url: Optional[str] = None
    external_id: Optional[str] = None
    productions: List[CompanyProduction] = None
    
    def __post_init__(self) -> None:
        if self.productions is None:
            self.productions = []


class CompanyService:
    """Service for managing company data with caching and provider integration."""
    
    CACHE_DIR = Path.home() / ".media-manager" / "company_cache"
    CACHE_TTL_DAYS = 30
    
    def __init__(self) -> None:
        """Initialize company service."""
        self._logger = get_logger().get_logger(__name__)
        self._db_service = get_database_service()
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize TMDB provider if API key available
        api_key = get_tmdb_api_key()
        self._tmdb_provider = TMDBProvider(api_key) if api_key else None
    
    def get_company_by_id(self, company_id: int, force_refresh: bool = False) -> Optional[CompanyDetails]:
        """Get company details by database ID.
        
        Args:
            company_id: Database company ID
            force_refresh: Force refresh from provider even if cached
            
        Returns:
            CompanyDetails or None if not found
        """
        with self._db_service.get_session() as session:
            company = session.get(Company, company_id)
            
            if not company:
                return None
            
            # Check if we need to refresh from provider
            needs_refresh = force_refresh or self._needs_refresh(company)
            
            if needs_refresh and company.external_id and self._tmdb_provider:
                self._refresh_company_from_provider(company, session)
            
            # Build company details
            return self._build_company_details(company, session)
    
    def get_company_by_name(self, name: str, force_refresh: bool = False) -> Optional[CompanyDetails]:
        """Get company details by name.
        
        Args:
            name: Company name
            force_refresh: Force refresh from provider
            
        Returns:
            CompanyDetails or None if not found
        """
        with self._db_service.get_session() as session:
            statement = select(Company).where(Company.name == name)
            company = session.exec(statement).first()
            
            if not company:
                return None
            
            # Check if we need to refresh from provider
            needs_refresh = force_refresh or self._needs_refresh(company)
            
            if needs_refresh and company.external_id and self._tmdb_provider:
                self._refresh_company_from_provider(company, session)
            
            return self._build_company_details(company, session)
    
    def search_company(self, query: str) -> List[CompanyDetails]:
        """Search for companies by name.
        
        Args:
            query: Search query
            
        Returns:
            List of CompanyDetails matching the query
        """
        with self._db_service.get_session() as session:
            statement = (
                select(Company)
                .where(Company.name.ilike(f"%{query}%"))
                .limit(50)
            )
            companies = session.exec(statement).all()
            
            return [self._build_company_details(company, session) for company in companies]
    
    def get_logo_path(self, company_id: int) -> Optional[Path]:
        """Get local path to cached logo image.
        
        Args:
            company_id: Database company ID
            
        Returns:
            Path to cached logo or None
        """
        with self._db_service.get_session() as session:
            company = session.get(Company, company_id)
            if not company or not company.logo_url:
                return None
            
            # Generate cache path from logo URL
            url_hash = hashlib.md5(company.logo_url.encode()).hexdigest()
            cache_path = self.CACHE_DIR / f"{url_hash}.png"
            
            return cache_path if cache_path.exists() else None
    
    def download_logo(self, company_id: int, force_download: bool = False) -> Optional[Path]:
        """Download and cache company logo.
        
        Args:
            company_id: Database company ID
            force_download: Force re-download even if cached
            
        Returns:
            Path to cached logo or None
        """
        with self._db_service.get_session() as session:
            company = session.get(Company, company_id)
            if not company or not company.logo_url:
                return None
            
            # Generate cache path
            url_hash = hashlib.md5(company.logo_url.encode()).hexdigest()
            cache_path = self.CACHE_DIR / f"{url_hash}.png"
            
            # Return cached if exists and not forcing
            if cache_path.exists() and not force_download:
                return cache_path
            
            # Download image
            try:
                import requests
                response = requests.get(company.logo_url, timeout=10)
                response.raise_for_status()
                
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                
                self._logger.info(f"Downloaded logo for {company.name}: {cache_path}")
                return cache_path
                
            except Exception as exc:
                self._logger.error(f"Failed to download logo: {exc}")
                return None
    
    def _needs_refresh(self, company: Company) -> bool:
        """Check if company data needs refresh from provider.
        
        Args:
            company: Company entity
            
        Returns:
            True if refresh needed
        """
        # Check if data is stale (older than TTL)
        if company.created_at:
            age = datetime.utcnow() - company.created_at
            if age > timedelta(days=self.CACHE_TTL_DAYS):
                return True
        
        return False
    
    def _refresh_company_from_provider(self, company: Company, session: Session) -> None:
        """Refresh company data from provider.
        
        Args:
            company: Company entity to refresh
            session: Database session
        """
        if not self._tmdb_provider or not company.external_id:
            return
        
        try:
            # Check cache first
            cache_key = f"company_{company.external_id}"
            cached_data = self._load_from_cache(cache_key)
            
            if not cached_data:
                # Fetch from TMDB API
                endpoint = f"/company/{company.external_id}"
                response = self._tmdb_provider._api_call(endpoint)
                
                # Save to cache
                self._save_to_cache(cache_key, response)
                cached_data = response
            
            # Update company entity (TMDB API has limited company data)
            # We can store description in a future schema update
            
            # Update logo URL if present
            if cached_data.get("logo_path"):
                company.logo_url = f"{self._tmdb_provider.IMAGE_BASE}/w154{cached_data['logo_path']}"
            
            session.add(company)
            session.commit()
            
            self._logger.info(f"Refreshed company data for {company.name}")
            
        except Exception as exc:
            self._logger.error(f"Failed to refresh company from provider: {exc}")
    
    def _build_company_details(self, company: Company, session: Session) -> CompanyDetails:
        """Build CompanyDetails from Company entity.
        
        Args:
            company: Company entity
            session: Database session
            
        Returns:
            CompanyDetails with productions
        """
        # Find all media items that mention this company in metadata
        # Note: We need to search through provider metadata stored in ProviderResult
        # For now, we'll return empty productions list
        # In a full implementation, we would need a CompanyMediaItem junction table
        productions = []
        
        # Alternative: Search through media items for company name in description
        # This is a basic implementation and could be improved with proper relationships
        try:
            from sqlalchemy import or_
            statement = (
                select(MediaItem)
                .where(
                    or_(
                        MediaItem.description.ilike(f"%{company.name}%"),
                        MediaItem.title.ilike(f"%{company.name}%")
                    )
                )
                .options(selectinload(MediaItem.artworks))
                .limit(100)
            )
            media_items = session.exec(statement).all()
            
            for item in media_items:
                # Get poster URL from artworks
                poster_url = None
                for artwork in item.artworks:
                    if artwork.artwork_type == "poster" and artwork.url:
                        poster_url = artwork.url
                        break
                
                production = CompanyProduction(
                    media_item_id=item.id,
                    media_item_title=item.title,
                    media_type=item.media_type,
                    year=item.year,
                    rating=item.rating,
                    poster_url=poster_url
                )
                productions.append(production)
            
            # Sort by year, most recent first
            productions.sort(key=lambda p: (p.year or 0), reverse=True)
            
        except Exception as exc:
            self._logger.warning(f"Failed to load productions for company: {exc}")
        
        return CompanyDetails(
            id=company.id,
            name=company.name,
            logo_url=company.logo_url,
            external_id=company.external_id,
            productions=productions
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
