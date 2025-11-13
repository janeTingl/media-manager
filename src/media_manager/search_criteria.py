"""Search criteria and filter definitions."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SearchCriteria:
    """Criteria for searching media items."""
    
    # Text search
    text_query: str = ""
    
    # Media type filter
    media_type: Optional[str] = None  # "movie", "tv", or None for all
    
    # Library filter
    library_id: Optional[int] = None
    
    # Year range
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    
    # Rating range (0-10)
    rating_min: Optional[float] = None
    rating_max: Optional[float] = None
    
    # Runtime range (in minutes)
    runtime_min: Optional[int] = None
    runtime_max: Optional[int] = None
    
    # Tags (list of tag IDs)
    tags: List[int] = field(default_factory=list)
    
    # People (list of person IDs - actors/directors/etc)
    people: List[int] = field(default_factory=list)
    
    # Collections (list of collection IDs)
    collections: List[int] = field(default_factory=list)
    
    # Quick filters
    quick_filter: Optional[str] = None  # "unmatched", "recent", "favorites", "no_poster", "high_rated"
    
    # Sorting
    sort_by: str = "title"  # "title", "year", "rating", "added", "runtime"
    sort_order: str = "asc"  # "asc" or "desc"
    
    # Pagination
    page_size: int = 50
    page: int = 0
    
    def to_dict(self) -> dict:
        """Convert criteria to dictionary for serialization."""
        return {
            "text_query": self.text_query,
            "media_type": self.media_type,
            "library_id": self.library_id,
            "year_min": self.year_min,
            "year_max": self.year_max,
            "rating_min": self.rating_min,
            "rating_max": self.rating_max,
            "runtime_min": self.runtime_min,
            "runtime_max": self.runtime_max,
            "tags": self.tags,
            "people": self.people,
            "collections": self.collections,
            "quick_filter": self.quick_filter,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "page_size": self.page_size,
            "page": self.page,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SearchCriteria":
        """Create criteria from dictionary."""
        return cls(
            text_query=data.get("text_query", ""),
            media_type=data.get("media_type"),
            library_id=data.get("library_id"),
            year_min=data.get("year_min"),
            year_max=data.get("year_max"),
            rating_min=data.get("rating_min"),
            rating_max=data.get("rating_max"),
            runtime_min=data.get("runtime_min"),
            runtime_max=data.get("runtime_max"),
            tags=data.get("tags", []),
            people=data.get("people", []),
            collections=data.get("collections", []),
            quick_filter=data.get("quick_filter"),
            sort_by=data.get("sort_by", "title"),
            sort_order=data.get("sort_order", "asc"),
            page_size=data.get("page_size", 50),
            page=data.get("page", 0),
        )
    
    def is_empty(self) -> bool:
        """Check if all filters are empty/default."""
        return (
            not self.text_query
            and self.media_type is None
            and self.library_id is None
            and self.year_min is None
            and self.year_max is None
            and self.rating_min is None
            and self.rating_max is None
            and self.runtime_min is None
            and self.runtime_max is None
            and not self.tags
            and not self.people
            and not self.collections
            and self.quick_filter is None
        )
