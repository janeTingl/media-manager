"""Fuzzy search helpers for media matching."""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rapidfuzz import fuzz

from media_manager.models import MediaType, Movie, SearchResult, TVShow

logger = logging.getLogger(__name__)


@dataclass
class ParsedFilename:
    """Parsed filename components."""
    title: str
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    media_type: Optional[MediaType] = None
    quality: Optional[str] = None
    source: Optional[str] = None
    codec: Optional[str] = None
    release_group: Optional[str] = None
    raw_title: str = ""


class FilenameParser:
    """Parse media filenames to extract metadata."""

    # Common patterns
    TV_PATTERNS = [
        r'(.+?)[\s._-]+S(\d{1,2})E(\d{1,2})',  # S01E01
        r'(.+?)[\s._-]+(\d{1,2})x(\d{1,2})',   # 1x01
        r'(.+?)[\s._-]+Season[\s._-]*(\d{1,2})[\s._-]*Episode[\s._-]*(\d{1,2})',  # Season 1 Episode 1
    ]

    MOVIE_PATTERNS = [
        r'(.+?)[\s._-]+\((\d{4})\)',  # Title (Year)
        r'(.+?)[\s._-]+(\d{4})[\s._-]',  # Title Year
    ]

    # Quality, source, codec patterns
    PATTERNS = {
        'quality': r'(1080p|720p|480p|2160p|4K|HD|SD|BluRay|BRRip|DVDRip|WEBRip|WEB-DL)',
        'source': r'(BluRay|DVD|WEB|HDTV|TVRip|CAM|TS)',
        'codec': r'(x264|x265|H\.264|H\.265|HEVC|AVC|XviD|DivX)',
        'release_group': r'(-([A-Za-z0-9]+)$|\[([A-Za-z0-9]+)\]$)',
    }

    @classmethod
    def parse(cls, filename: str) -> ParsedFilename:
        """Parse a media filename."""
        # Clean the filename
        clean_name = cls._clean_filename(filename)

        # Extract metadata first
        metadata = cls._extract_metadata(clean_name)

        # Try TV patterns first
        for pattern in cls.TV_PATTERNS:
            match = re.search(pattern, clean_name, re.IGNORECASE)
            if match:
                title = cls._clean_title(match.group(1))
                season = int(match.group(2))
                episode = int(match.group(3))

                # Extract year from the remaining part of the filename
                remaining_text = clean_name[match.end():]
                year = cls._extract_year_from_title(remaining_text) or cls._extract_year_from_title(match.group(1))
                if year and cls._extract_year_from_title(match.group(1)):
                    title = re.sub(r'[\s._-]+\(' + str(year) + r'\)', '', title, flags=re.IGNORECASE)

                return ParsedFilename(
                    title=title,
                    year=year,
                    season=season,
                    episode=episode,
                    media_type=MediaType.TV_SHOW,
                    quality=metadata['quality'],
                    source=metadata['source'],
                    codec=metadata['codec'],
                    release_group=metadata['release_group'],
                    raw_title=clean_name
                )

        # Try movie patterns
        for pattern in cls.MOVIE_PATTERNS:
            match = re.search(pattern, clean_name, re.IGNORECASE)
            if match:
                title = cls._clean_title(match.group(1))
                year = int(match.group(2))

                return ParsedFilename(
                    title=title,
                    year=year,
                    media_type=MediaType.MOVIE,
                    quality=metadata['quality'],
                    source=metadata['source'],
                    codec=metadata['codec'],
                    release_group=metadata['release_group'],
                    raw_title=clean_name
                )

        # Fallback: treat as movie without year
        title = cls._clean_title(clean_name)
        year = cls._extract_year_from_title(clean_name)
        if year:
            title = re.sub(r'[\s._-]+\(' + str(year) + r'\)', '', title, flags=re.IGNORECASE)

        return ParsedFilename(
            title=title,
            year=year,
            media_type=MediaType.MOVIE,
            quality=metadata['quality'],
            source=metadata['source'],
            codec=metadata['codec'],
            release_group=metadata['release_group'],
            raw_title=clean_name
        )

    @classmethod
    def _clean_filename(cls, filename: str) -> str:
        """Clean filename by removing extension and common separators."""
        # Remove file extension
        filename = re.sub(r'\.[a-zA-Z0-9]+$', '', filename)

        # Replace common separators with spaces
        filename = re.sub(r'[._-]+', ' ', filename)

        # Remove brackets and extra spaces
        filename = re.sub(r'[\[\](){}]', ' ', filename)
        filename = re.sub(r'\s+', ' ', filename).strip()

        return filename

    @classmethod
    def _clean_title(cls, title: str) -> str:
        """Clean title by removing quality, source, etc."""
        # Remove common patterns
        for _pattern_type, pattern in cls.PATTERNS.items():
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)

        # Clean up extra spaces
        title = re.sub(r'\s+', ' ', title).strip()

        return title

    @classmethod
    def _extract_metadata(cls, clean_name: str) -> Dict[str, Optional[str]]:
        """Extract quality, source, codec, and release group from filename."""
        metadata = {
            'quality': None,
            'source': None,
            'codec': None,
            'release_group': None
        }

        for pattern_type, pattern in cls.PATTERNS.items():
            match = re.search(pattern, clean_name, re.IGNORECASE)
            if match:
                if pattern_type == 'release_group':
                    # Get the last group that matches
                    for group in match.groups():
                        if group and group.strip():
                            metadata[pattern_type] = group.strip()
                            break
                else:
                    metadata[pattern_type] = match.group(1).strip() if match.group(1) else None

        return metadata

    @classmethod
    def _extract_year_from_title(cls, title: str) -> Optional[int]:
        """Extract year from title if present."""
        match = re.search(r'\((\d{4})\)', title)
        if match:
            return int(match.group(1))

        match = re.search(r'\b(19\d{2}|20\d{2})\b', title)
        if match:
            return int(match.group(1))

        return None


class FuzzyMatcher:
    """Fuzzy matching for media search results."""

    def __init__(self, min_score: float = 60.0):
        self.min_score = min_score

    def match_movie(self, parsed: ParsedFilename, movies: List[Movie]) -> List[SearchResult]:
        """Match parsed filename against movie list."""
        if parsed.media_type != MediaType.MOVIE:
            return []

        results = []

        for movie in movies:
            score = self._calculate_movie_score(parsed, movie)
            if score >= self.min_score:
                results.append(SearchResult(
                    media_type=MediaType.MOVIE,
                    item=movie,
                    score=score,
                    provider="unknown"  # Will be set by caller
                ))

        return sorted(results, key=lambda x: x.score, reverse=True)

    def match_tv_show(self, parsed: ParsedFilename, shows: List[TVShow]) -> List[SearchResult]:
        """Match parsed filename against TV show list."""
        if parsed.media_type != MediaType.TV_SHOW:
            return []

        results = []

        for show in shows:
            score = self._calculate_tv_show_score(parsed, show)
            if score >= self.min_score:
                results.append(SearchResult(
                    media_type=MediaType.TV_SHOW,
                    item=show,
                    score=score,
                    provider="unknown"  # Will be set by caller
                ))

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _calculate_movie_score(self, parsed: ParsedFilename, movie: Movie) -> float:
        """Calculate match score for movie."""
        scores = []

        # Title similarity
        title_score = fuzz.ratio(parsed.title.lower(), movie.title.lower())
        if movie.original_title and movie.original_title != movie.title:
            title_score = max(title_score, fuzz.ratio(parsed.title.lower(), movie.original_title.lower()))
        scores.append(title_score)

        # Year match (if available)
        if parsed.year and movie.release_date:
            year_diff = abs(parsed.year - movie.release_date.year)
            if year_diff == 0:
                scores.append(100)  # Perfect year match
            elif year_diff == 1:
                scores.append(80)   # Close year match
            elif year_diff <= 2:
                scores.append(60)   # Reasonable year match
            else:
                scores.append(20)   # Poor year match

        # Weight the scores
        if len(scores) == 1:
            return scores[0]
        else:
            # Title is more important than year
            return (scores[0] * 0.7) + (scores[1] * 0.3)

    def _calculate_tv_show_score(self, parsed: ParsedFilename, show: TVShow) -> float:
        """Calculate match score for TV show."""
        scores = []

        # Title similarity
        title_score = fuzz.ratio(parsed.title.lower(), show.title.lower())
        if show.original_title and show.original_title != show.title:
            title_score = max(title_score, fuzz.ratio(parsed.title.lower(), show.original_title.lower()))
        scores.append(title_score)

        # Year match (if available)
        if parsed.year and show.first_air_date:
            year_diff = abs(parsed.year - show.first_air_date.year)
            if year_diff == 0:
                scores.append(100)  # Perfect year match
            elif year_diff == 1:
                scores.append(80)   # Close year match
            elif year_diff <= 2:
                scores.append(60)   # Reasonable year match
            else:
                scores.append(20)   # Poor year match

        # Weight the scores
        if len(scores) == 1:
            return scores[0]
        else:
            # Title is more important than year
            return (scores[0] * 0.7) + (scores[1] * 0.3)


class MediaSearcher:
    """High-level media search with fuzzy matching."""

    def __init__(self, providers: Dict[str, Any], min_score: float = 60.0):
        self.providers = providers
        self.matcher = FuzzyMatcher(min_score)
        self.parser = FilenameParser()

    async def search_by_filename(self, filename: str, providers: Optional[List[str]] = None) -> List[SearchResult]:
        """Search for media by filename using fuzzy matching."""
        parsed = self.parser.parse(filename)
        logger.debug(f"Parsed filename: {parsed}")

        if not providers:
            providers = list(self.providers.keys())

        all_results = []

        # Search with each provider
        for provider_name in providers:
            if provider_name not in self.providers:
                logger.warning(f"Provider {provider_name} not available")
                continue

            provider = self.providers[provider_name]

            try:
                if parsed.media_type == MediaType.MOVIE:
                    movies = await provider.search_movie(parsed.title, parsed.year)
                    results = self.matcher.match_movie(parsed, movies)
                elif parsed.media_type == MediaType.TV_SHOW:
                    shows = await provider.search_tv_show(parsed.title, parsed.year)
                    results = self.matcher.match_tv_show(parsed, shows)
                else:
                    results = []

                # Set provider name for results
                for result in results:
                    result.provider = provider_name

                all_results.extend(results)

            except Exception as e:
                logger.error(f"Error searching with provider {provider_name}: {e}")
                continue

        # Sort by score and return top results
        return sorted(all_results, key=lambda x: x.score, reverse=True)

    async def search_by_query(self, query: str, media_type: MediaType, providers: Optional[List[str]] = None) -> List[SearchResult]:
        """Search by query string (for manual search)."""
        if not providers:
            providers = list(self.providers.keys())

        all_results = []

        for provider_name in providers:
            if provider_name not in self.providers:
                continue

            provider = self.providers[provider_name]

            try:
                if media_type == MediaType.MOVIE:
                    items = await provider.search_movie(query)
                elif media_type == MediaType.TV_SHOW:
                    items = await provider.search_tv_show(query)
                else:
                    continue

                # Create search results with perfect scores
                for item in items:
                    result = SearchResult(
                        media_type=media_type,
                        item=item,
                        score=100.0,
                        provider=provider_name
                    )
                    all_results.append(result)

            except Exception as e:
                logger.error(f"Error searching with provider {provider_name}: {e}")
                continue

        return all_results
