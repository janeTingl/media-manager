"""Provider-agnostic adapter for unified metadata lookups."""

from __future__ import annotations

from typing import Any

from ..cache_service import get_cache_service
from ..instrumentation import get_instrumentation
from ..logging import get_logger
from ..models import MediaMatch, MediaType, MatchStatus, DownloadStatus, PosterInfo, PosterType, VideoMetadata
from .base import BaseProvider, ProviderError, ProviderResult


class ProviderAdapter:
    """Adapter that merges results from multiple providers."""

    def __init__(self, providers: list[BaseProvider] | None = None, use_cache: bool = True) -> None:
        """Initialize the adapter with providers.

        Args:
            providers: List of provider instances. If None, uses mock providers.
            use_cache: Whether to use caching for provider results
        """
        self.providers = providers or []
        self._logger = get_logger().get_logger(__name__)
        self._use_cache = use_cache
        self._cache_service = get_cache_service() if use_cache else None
        self._instrumentation = get_instrumentation()

    def search_and_match(
        self, metadata: VideoMetadata, fallback_to_mock: bool = False
    ) -> MediaMatch:
        """Search for a match using all providers and create a MediaMatch.

        Args:
            metadata: Video metadata to match
            fallback_to_mock: If True, fall back to mock results if providers fail

        Returns:
            MediaMatch with results from best provider
        """
        results = []

        with self._instrumentation.timer("provider_adapter.search_and_match"):
            for provider in self.providers:
                try:
                    # Try to get from cache first
                    cached_results = None
                    if self._use_cache and self._cache_service:
                        cache_key_params = {
                            "title": metadata.title,
                            "year": metadata.year,
                        }
                        query_type = "search_movie" if metadata.is_movie() else "search_tv"
                        
                        with self._instrumentation.timer("provider_adapter.cache_lookup"):
                            cached_results = self._cache_service.get(
                                provider.name, query_type, **cache_key_params
                            )
                        
                        if cached_results:
                            self._instrumentation.increment_counter("provider_adapter.cache_hits")
                            self._logger.debug(f"Cache hit for {provider.name}")
                            # Convert cached dict back to ProviderResult objects
                            provider_results = [
                                ProviderResult(**r) for r in cached_results
                            ]
                            results.extend(provider_results)
                            continue

                    # Cache miss - query provider
                    self._instrumentation.increment_counter("provider_adapter.cache_misses")
                    
                    with self._instrumentation.timer(f"provider.{provider.name}.search"):
                        if metadata.is_movie():
                            provider_results = provider.search_movie(metadata.title, metadata.year)
                        else:
                            provider_results = provider.search_tv(metadata.title, metadata.year)

                    # Cache the results
                    if self._use_cache and self._cache_service and provider_results:
                        cache_key_params = {
                            "title": metadata.title,
                            "year": metadata.year,
                        }
                        query_type = "search_movie" if metadata.is_movie() else "search_tv"
                        
                        # Convert to dict for caching
                        cached_data = [r.as_dict() for r in provider_results]
                        
                        with self._instrumentation.timer("provider_adapter.cache_store"):
                            self._cache_service.set(
                                provider.name, query_type, cached_data, **cache_key_params
                            )

                    results.extend(provider_results)
                    self._logger.debug(f"Got {len(provider_results)} results from {provider.name}")
                except ProviderError as exc:
                    self._logger.warning(f"Provider {provider.name} error: {exc}")
                    self._instrumentation.increment_counter(f"provider.{provider.name}.errors")
                except Exception as exc:
                    self._logger.error(f"Unexpected error from {provider.name}: {exc}")
                    self._instrumentation.increment_counter(f"provider.{provider.name}.exceptions")

        if not results and fallback_to_mock:
            self._logger.debug("No results from providers, using mock")
            return self._create_mock_match(metadata)

        if not results:
            self._logger.warning(f"No matches found for {metadata.title}")
            match = MediaMatch(
                metadata=metadata,
                status=MatchStatus.PENDING,
                confidence=0.0,
            )
            return match

        # Sort by confidence and select best
        results.sort(key=lambda x: x.confidence, reverse=True)
        best_result = results[0]

        return self._result_to_match(metadata, best_result)

    def get_full_details(self, metadata: VideoMetadata, external_id: str, provider_name: str) -> MediaMatch:
        """Get full details for a matched item.

        Args:
            metadata: Video metadata
            external_id: Provider-specific ID
            provider_name: Name of provider to use

        Returns:
            MediaMatch with full details
        """
        # Find provider
        provider = None
        for p in self.providers:
            if p.name == provider_name:
                provider = p
                break

        if not provider:
            self._logger.warning(f"Provider {provider_name} not found")
            match = MediaMatch(metadata=metadata, status=MatchStatus.PENDING)
            return match

        try:
            if metadata.is_movie():
                result = provider.get_movie_details(external_id)
            else:
                result = provider.get_tv_details(external_id, metadata.season, metadata.episode)

            return self._result_to_match(metadata, result)
        except ProviderError as exc:
            self._logger.error(f"Failed to get details: {exc}")
            match = MediaMatch(metadata=metadata, status=MatchStatus.PENDING)
            return match

    def search_and_match_all(
        self, metadata_list: list[VideoMetadata], fallback_to_mock: bool = False
    ) -> list[MediaMatch]:
        """Search for matches for multiple items.

        Args:
            metadata_list: List of video metadata to match
            fallback_to_mock: If True, fall back to mock results if providers fail

        Returns:
            List of MediaMatch objects
        """
        return [
            self.search_and_match(metadata, fallback_to_mock)
            for metadata in metadata_list
        ]

    def search_results(
        self, query: str, media_type: MediaType, year: int | None = None
    ) -> list[ProviderResult]:
        """Search across all providers for results.

        Args:
            query: Search query
            media_type: Type of media to search for
            year: Optional year for disambiguation

        Returns:
            Merged list of results sorted by confidence
        """
        results = []

        for provider in self.providers:
            try:
                if media_type == MediaType.MOVIE:
                    provider_results = provider.search_movie(query, year)
                else:
                    provider_results = provider.search_tv(query, year)

                results.extend(provider_results)
            except ProviderError as exc:
                self._logger.warning(f"Provider {provider.name} error: {exc}")
            except Exception as exc:
                self._logger.error(f"Unexpected error from {provider.name}: {exc}")

        # Merge duplicate results (same title and year) and keep highest confidence
        merged = {}
        for result in results:
            key = (result.title.lower(), result.year)
            if key not in merged or result.confidence > merged[key].confidence:
                merged[key] = result

        # Sort by confidence
        sorted_results = sorted(merged.values(), key=lambda x: x.confidence, reverse=True)
        return sorted_results

    def _result_to_match(self, metadata: VideoMetadata, result: ProviderResult) -> MediaMatch:
        """Convert a ProviderResult to a MediaMatch.

        Args:
            metadata: Original video metadata
            result: Provider result

        Returns:
            MediaMatch object
        """
        # Determine match status based on confidence
        if result.confidence > 0.8:
            status = MatchStatus.MATCHED
        elif result.confidence > 0.6:
            status = MatchStatus.PENDING
        else:
            status = MatchStatus.PENDING

        # Create poster info objects
        posters = {}
        if result.poster_url:
            posters[PosterType.POSTER] = PosterInfo(
                poster_type=PosterType.POSTER,
                url=result.poster_url,
                download_status=DownloadStatus.PENDING,
            )

        if result.fanart_url:
            posters[PosterType.FANART] = PosterInfo(
                poster_type=PosterType.FANART,
                url=result.fanart_url,
                download_status=DownloadStatus.PENDING,
            )

        if result.banner_url:
            posters[PosterType.BANNER] = PosterInfo(
                poster_type=PosterType.BANNER,
                url=result.banner_url,
                download_status=DownloadStatus.PENDING,
            )

        if result.thumbnail_url:
            posters[PosterType.THUMBNAIL] = PosterInfo(
                poster_type=PosterType.THUMBNAIL,
                url=result.thumbnail_url,
                download_status=DownloadStatus.PENDING,
            )

        match = MediaMatch(
            metadata=metadata,
            status=status,
            confidence=result.confidence,
            matched_title=result.title,
            matched_year=result.year,
            external_id=result.external_id,
            source=result.provider_name,
            poster_url=result.poster_url,
            overview=result.overview,
            posters=posters,
            runtime=result.runtime,
            aired_date=result.aired_date,
            cast=result.cast or [],
        )

        return match

    def _create_mock_match(self, metadata: VideoMetadata) -> MediaMatch:
        """Create a mock match for demonstration (fallback).

        Args:
            metadata: Video metadata

        Returns:
            MediaMatch with mock data
        """
        base_confidence = 0.9

        # Reduce confidence for generic titles
        generic_titles = ["movie", "video", "test", "sample"]
        if metadata.title.lower() in generic_titles:
            base_confidence = 0.3
        elif len(metadata.title) < 3:
            base_confidence = 0.5
        elif metadata.year is None:
            base_confidence = 0.7

        base_hash = hash(str(metadata.path)) % 10000
        poster_urls = {
            PosterType.POSTER: f"https://example.com/poster/{base_hash}.jpg",
            PosterType.FANART: f"https://example.com/fanart/{base_hash}.jpg",
        }

        posters = {
            PosterType.POSTER: PosterInfo(
                poster_type=PosterType.POSTER,
                url=poster_urls[PosterType.POSTER],
                download_status=DownloadStatus.PENDING,
            ),
            PosterType.FANART: PosterInfo(
                poster_type=PosterType.FANART,
                url=poster_urls[PosterType.FANART],
                download_status=DownloadStatus.PENDING,
            ),
        }

        match = MediaMatch(
            metadata=metadata,
            status=MatchStatus.MATCHED if base_confidence > 0.6 else MatchStatus.PENDING,
            confidence=base_confidence,
            matched_title=metadata.title,
            matched_year=metadata.year,
            external_id=f"mock_{base_hash}",
            source="MockAdapter",
            poster_url=poster_urls[PosterType.POSTER],
            overview=f"This is a mock overview for {metadata.title}. "
            f"A great {metadata.media_type.value} from {metadata.year or 'unknown'}.",
            posters=posters,
        )

        return match
