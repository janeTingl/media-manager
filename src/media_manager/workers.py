"""Background workers for async operations in the media manager."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from .library_postprocessor import (
    LibraryPostProcessor,
    PostProcessingError,
    PostProcessingOptions,
    PostProcessingSummary,
    ProcessingEvent,
    ProcessingEventType,
)
from .logging import get_logger
from .models import (
    DownloadStatus,
    MatchStatus,
    MediaMatch,
    PosterInfo,
    PosterType,
    SearchRequest,
    SearchResult,
    SubtitleInfo,
    SubtitleLanguage,
    VideoMetadata,
)
from .providers.adapter import ProviderAdapter
from .providers.tmdb import TMDBProvider
from .providers.tvdb import TVDBProvider
from .settings import get_settings


class MatchWorkerSignals(QObject):
    """Signals for the match worker."""

    match_found = Signal(object)  # MediaMatch
    match_failed = Signal(str, str)  # path, error
    progress = Signal(int, int)  # current, total
    finished = Signal()


class MatchWorker(QRunnable):
    """Worker for finding matches in background threads."""

    def __init__(self, metadata_list: list[VideoMetadata]) -> None:
        super().__init__()
        self.metadata_list = metadata_list
        self.signals = MatchWorkerSignals()
        self._logger = get_logger().get_logger(__name__)
        self._should_stop = False

    @Slot()
    def run(self) -> None:
        """Run the matching process."""
        total = len(self.metadata_list)
        
        # Initialize provider adapter
        adapter = self._get_adapter()

        for index, metadata in enumerate(self.metadata_list, start=1):
            if self._should_stop:
                break

            try:
                # Use provider adapter for matching
                match = adapter.search_and_match(metadata, fallback_to_mock=True)

                self.signals.match_found.emit(match)
                self.signals.progress.emit(index, total)

            except Exception as exc:
                error_msg = f"Failed to match {metadata.path}: {exc}"
                self._logger.error(error_msg)
                self.signals.match_failed.emit(str(metadata.path), str(exc))

        self.signals.finished.emit()

    def stop(self) -> None:
        """Stop the worker."""
        self._should_stop = True

    def _get_adapter(self) -> ProviderAdapter:
        """Get or create provider adapter.

        Returns:
            ProviderAdapter with configured providers
        """
        settings = get_settings()
        providers = []

        # Initialize enabled providers
        enabled_providers = settings.get_enabled_providers()

        if "TMDB" in enabled_providers:
            tmdb_key = settings.get_tmdb_api_key()
            if tmdb_key:
                providers.append(TMDBProvider(tmdb_key))
            else:
                self._logger.warning("TMDB provider enabled but API key not configured")

        if "TVDB" in enabled_providers:
            tvdb_key = settings.get_tvdb_api_key()
            if tvdb_key:
                providers.append(TVDBProvider(tvdb_key))
            else:
                self._logger.warning("TVDB provider enabled but API key not configured")

        adapter = ProviderAdapter(providers if providers else None)
        return adapter

    def _create_mock_match(self, metadata: VideoMetadata) -> MediaMatch:
        """Create a mock match for demonstration."""
        # Simulate different confidence levels based on title clarity
        base_confidence = 0.9

        # Reduce confidence for generic titles
        generic_titles = ["movie", "video", "test", "sample"]
        if metadata.title.lower() in generic_titles:
            base_confidence = 0.3
        elif len(metadata.title) < 3:
            base_confidence = 0.5
        elif metadata.year is None:
            base_confidence = 0.7

        # Create mock poster URLs
        base_hash = hash(str(metadata.path)) % 10000
        poster_urls = {
            PosterType.POSTER: f"https://example.com/poster/{base_hash}.jpg",
            PosterType.FANART: f"https://example.com/fanart/{base_hash}.jpg",
        }

        # Create poster info objects
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

        # Create mock subtitles
        subtitles = self._create_mock_subtitles(metadata)

        # Create mock match data
        match = MediaMatch(
            metadata=metadata,
            status=MatchStatus.MATCHED if base_confidence > 0.6 else MatchStatus.PENDING,
            confidence=base_confidence,
            matched_title=metadata.title,
            matched_year=metadata.year,
            external_id=f"mock_{base_hash}",
            source="MockAPI",
            poster_url=poster_urls[PosterType.POSTER],
            overview=f"This is a mock overview for {metadata.title}. "
                    f"A great {metadata.media_type.value} from {metadata.year or 'unknown'}.",
            posters=posters,
            subtitles=subtitles,
        )

        return match

    def _create_mock_subtitles(self, metadata: VideoMetadata) -> dict[SubtitleLanguage, SubtitleInfo]:
        """Create mock subtitles for demonstration."""
        subtitles = {}
        base_hash = hash(str(metadata.path)) % 10000

        # Add mock subtitles in common languages
        languages = [SubtitleLanguage.ENGLISH, SubtitleLanguage.SPANISH, SubtitleLanguage.FRENCH]

        for idx, language in enumerate(languages):
            subtitle_info = SubtitleInfo(
                language=language,
                url=f"https://example.com/subtitle/{base_hash}_{idx}.srt",
                download_status=DownloadStatus.PENDING,
                provider="MockAPI",
                subtitle_id=f"mock_sub_{base_hash}_{idx}",
            )
            subtitles[language] = subtitle_info

        return subtitles


class SearchWorkerSignals(QObject):
    """Signals for the search worker."""

    search_completed = Signal(list)  # List[SearchResult]
    search_failed = Signal(str)  # error


class SearchWorker(QRunnable):
    """Worker for searching media matches in background."""

    def __init__(self, request: SearchRequest) -> None:
        super().__init__()
        self.request = request
        self.signals = SearchWorkerSignals()
        self._logger = get_logger().get_logger(__name__)

    @Slot()
    def run(self) -> None:
        """Run the search process."""
        try:
            # Use provider adapter for search
            adapter = self._get_adapter()
            provider_results = adapter.search_results(
                self.request.query,
                self.request.media_type,
                self.request.year
            )

            # Convert provider results to SearchResult
            results = self._convert_to_search_results(provider_results)

            # Fallback to mock if no results
            if not results:
                self._logger.debug("No provider results, using mock")
                results = self._create_mock_results()

            self.signals.search_completed.emit(results)

        except Exception as exc:
            error_msg = f"Search failed: {exc}"
            self._logger.error(error_msg)
            self.signals.search_failed.emit(error_msg)

    def _get_adapter(self) -> ProviderAdapter:
        """Get or create provider adapter.

        Returns:
            ProviderAdapter with configured providers
        """
        settings = get_settings()
        providers = []

        # Initialize enabled providers
        enabled_providers = settings.get_enabled_providers()

        if "TMDB" in enabled_providers:
            tmdb_key = settings.get_tmdb_api_key()
            if tmdb_key:
                providers.append(TMDBProvider(tmdb_key))
            else:
                self._logger.debug("TMDB provider enabled but API key not configured")

        if "TVDB" in enabled_providers:
            tvdb_key = settings.get_tvdb_api_key()
            if tvdb_key:
                providers.append(TVDBProvider(tvdb_key))
            else:
                self._logger.debug("TVDB provider enabled but API key not configured")

        adapter = ProviderAdapter(providers if providers else None)
        return adapter

    def _convert_to_search_results(self, provider_results: list) -> list[SearchResult]:
        """Convert provider results to SearchResult objects.

        Args:
            provider_results: List of ProviderResult objects

        Returns:
            List of SearchResult objects
        """
        results = []
        for result in provider_results[:10]:  # Limit to top 10
            poster_urls = {}
            if result.poster_url:
                poster_urls[PosterType.POSTER] = result.poster_url
            if result.fanart_url:
                poster_urls[PosterType.FANART] = result.fanart_url

            search_result = SearchResult(
                title=result.title,
                year=result.year,
                external_id=result.external_id,
                source=result.provider_name,
                poster_url=result.poster_url,
                poster_urls=poster_urls,
                overview=result.overview,
                confidence=result.confidence,
            )
            results.append(search_result)

        return results

    def _create_mock_results(self) -> list[SearchResult]:
        """Create mock search results."""
        results = []

        # Generate 3-5 mock results
        base_query = self.request.query.lower()

        for i in range(3):
            confidence = 0.9 - (i * 0.1)  # Decreasing confidence
            year = self.request.year or (2020 + i)
            result_hash = hash(base_query + str(i)) % 10000

            poster_urls = {
                PosterType.POSTER: f"https://example.com/poster/{result_hash}.jpg",
                PosterType.FANART: f"https://example.com/fanart/{result_hash}.jpg",
            }

            result = SearchResult(
                title=f"{self.request.query.title()} ({i + 1})",
                year=year,
                external_id=f"search_{result_hash}",
                source="MockSearchAPI",
                poster_url=poster_urls[PosterType.POSTER],
                poster_urls=poster_urls,
                overview=f"This is search result {i + 1} for '{self.request.query}'. "
                        f"A matching {self.request.media_type.value} from {year}.",
                confidence=confidence
            )
            results.append(result)

        return results


class WorkerManager(QObject):
    """Manages background workers and thread pools."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread_pool = QThreadPool()
        self._logger = get_logger().get_logger(__name__)
        self._active_workers: list[QRunnable] = []

    def start_match_worker(self, metadata_list: list[VideoMetadata]) -> MatchWorker:
        """Start a match worker and return it."""
        worker = MatchWorker(metadata_list)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        # Connect finished signal to cleanup
        worker.signals.finished.connect(
            lambda: self._cleanup_worker(worker)
        )

        self._logger.info(f"Started match worker for {len(metadata_list)} items")
        return worker

    def start_search_worker(self, request: SearchRequest) -> SearchWorker:
        """Start a search worker and return it."""
        worker = SearchWorker(request)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        # Connect finished signal to cleanup
        worker.signals.search_completed.connect(
            lambda: self._cleanup_worker(worker)
        )
        worker.signals.search_failed.connect(
            lambda: self._cleanup_worker(worker)
        )

        self._logger.info(f"Started search worker for '{request.query}'")
        return worker

    def start_poster_download_worker(self, matches: list[MediaMatch], poster_types: list[PosterType]) -> PosterDownloadWorker:
        """Start a poster download worker and return it."""
        worker = PosterDownloadWorker(matches, poster_types)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        # Connect finished signal to cleanup
        worker.signals.finished.connect(
            lambda: self._cleanup_worker(worker)
        )

        self._logger.info(f"Started poster download worker for {len(matches)} matches")
        return worker

    def start_subtitle_download_worker(self, matches: list[MediaMatch], languages: list[SubtitleLanguage]) -> SubtitleDownloadWorker:
        """Start a subtitle download worker and return it."""
        worker = SubtitleDownloadWorker(matches, languages)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        # Connect finished signal to cleanup
        worker.signals.finished.connect(
            lambda: self._cleanup_worker(worker)
        )

        self._logger.info(f"Started subtitle download worker for {len(matches)} matches")
        return worker

    def start_post_processing_worker(self, matches: list[MediaMatch], options: PostProcessingOptions) -> LibraryPostProcessorWorker:
        """Start a library post-processing worker and return it."""
        worker = LibraryPostProcessorWorker(matches, options)
        self._active_workers.append(worker)
        self._thread_pool.start(worker)

        worker.signals.finished.connect(
            lambda _summary: self._cleanup_worker(worker)
        )

        self._logger.info(
            "Started library post-processing worker for %d items", len(matches)
        )
        return worker

    def stop_all_workers(self) -> None:
        """Stop all active workers."""
        for worker in self._active_workers:
            if hasattr(worker, 'stop'):
                worker.stop()

        self._thread_pool.clear()
        self._logger.info("Stopped all background workers")

    def _cleanup_worker(self, worker: QRunnable) -> None:
        """Remove worker from active list when finished."""
        if worker in self._active_workers:
            self._active_workers.remove(worker)
        self._logger.debug(f"Cleaned up worker: {type(worker).__name__}")

    def get_active_count(self) -> int:
        """Get the number of active workers."""
        return len(self._active_workers)


class PosterDownloadWorkerSignals(QObject):
    """Signals for the poster download worker."""

    poster_downloaded = Signal(object, object)  # MediaMatch, PosterInfo
    poster_failed = Signal(object, str)  # MediaMatch, error_message
    progress = Signal(int, int)  # current, total
    finished = Signal()


class PosterDownloadWorker(QRunnable):
    """Worker for downloading poster images in background."""

    def __init__(self, matches: list[MediaMatch], poster_types: list[PosterType]) -> None:
        super().__init__()
        self.matches = matches
        self.poster_types = poster_types
        self.signals = PosterDownloadWorkerSignals()
        self._logger = get_logger().get_logger(__name__)
        self._should_stop = False

        # Import here to avoid circular imports
        from .poster_downloader import PosterDownloader
        self.poster_downloader = PosterDownloader()

    @Slot()
    def run(self) -> None:
        """Run the poster download process."""
        total_posters = sum(
            len([pt for pt in self.poster_types if pt in match.posters and match.posters[pt].url])
            for match in self.matches
        )
        current = 0

        for match in self.matches:
            if self._should_stop:
                break

            for poster_type in self.poster_types:
                if self._should_stop:
                    break

                if poster_type not in match.posters:
                    continue

                poster_info = match.posters[poster_type]
                if not poster_info.url or poster_info.is_downloaded():
                    continue

                current += 1
                self.signals.progress.emit(current, total_posters)

                try:
                    success = self.poster_downloader.download_poster(
                        poster_info, match.metadata.path
                    )
                    if success:
                        self.signals.poster_downloaded.emit(match, poster_info)
                        self._logger.info(f"Downloaded {poster_type.value} for {match.metadata.title}")
                    else:
                        self.signals.poster_failed.emit(
                            match, f"Failed to download {poster_type.value}: {poster_info.error_message}"
                        )
                except Exception as exc:
                    error_msg = f"Error downloading {poster_type.value} for {match.metadata.title}: {exc}"
                    self._logger.error(error_msg)
                    self.signals.poster_failed.emit(match, error_msg)

        self.signals.finished.emit()

    def stop(self) -> None:
        """Stop the worker."""
        self._should_stop = True


class SubtitleDownloadWorkerSignals(QObject):
    """Signals for the subtitle download worker."""

    subtitle_downloaded = Signal(object, object)  # MediaMatch, SubtitleInfo
    subtitle_failed = Signal(object, str)  # MediaMatch, error_message
    progress = Signal(int, int)  # current, total
    finished = Signal()


class SubtitleDownloadWorker(QRunnable):
    """Worker for downloading subtitles in background."""

    def __init__(self, matches: list[MediaMatch], languages: list[SubtitleLanguage]) -> None:
        super().__init__()
        self.matches = matches
        self.languages = languages
        self.signals = SubtitleDownloadWorkerSignals()
        self._logger = get_logger().get_logger(__name__)
        self._should_stop = False

        # Import here to avoid circular imports
        from .subtitle_downloader import SubtitleDownloader
        self.subtitle_downloader = SubtitleDownloader()

    @Slot()
    def run(self) -> None:
        """Run the subtitle download process."""
        total_subtitles = sum(
            len([lang for lang in self.languages if lang in match.subtitles and match.subtitles[lang].url])
            for match in self.matches
        )
        current = 0

        for match in self.matches:
            if self._should_stop:
                break

            for language in self.languages:
                if self._should_stop:
                    break

                if language not in match.subtitles:
                    continue

                subtitle_info = match.subtitles[language]
                if not subtitle_info.url or subtitle_info.is_downloaded():
                    continue

                current += 1
                self.signals.progress.emit(current, total_subtitles)

                try:
                    success = self.subtitle_downloader.download_subtitle(
                        subtitle_info, match.metadata.path
                    )
                    if success:
                        self.signals.subtitle_downloaded.emit(match, subtitle_info)
                        self._logger.info(
                            f"Downloaded {language.value} subtitle for {match.metadata.title}"
                        )
                    else:
                        self.signals.subtitle_failed.emit(
                            match,
                            f"Failed to download {language.value} subtitle: {subtitle_info.error_message}",
                        )
                except Exception as exc:
                    error_msg = f"Error downloading {language.value} subtitle for {match.metadata.title}: {exc}"
                    self._logger.error(error_msg)
                    self.signals.subtitle_failed.emit(match, error_msg)

        self.signals.finished.emit()

    def stop(self) -> None:
        """Stop the worker."""
        self._should_stop = True


class LibraryPostProcessorWorkerSignals(QObject):
    """Signals for the library post-processing worker."""

    item_processed = Signal(object, object, object)
    item_skipped = Signal(object, object, str)
    item_failed = Signal(object, str)
    progress = Signal(int, int)
    finished = Signal(object)
    error = Signal(str)


class LibraryPostProcessorWorker(QRunnable):
    """Worker that finalizes media files into the organized library."""

    def __init__(self, matches: list[MediaMatch], options: PostProcessingOptions) -> None:
        super().__init__()
        self.matches = matches
        self.options = options
        self.signals = LibraryPostProcessorWorkerSignals()
        self._logger = get_logger().get_logger(__name__)
        self._post_processor = LibraryPostProcessor()
        self._should_stop = False

    @Slot()
    def run(self) -> None:
        """Execute the post-processing workflow."""

        def progress_callback(current: int, total: int) -> None:
            if self._should_stop:
                raise PostProcessingError(
                    "Post-processing cancelled", None, PostProcessingSummary()
                )
            self.signals.progress.emit(current, total)

        def event_callback(event: ProcessingEvent) -> None:
            if event.type is ProcessingEventType.PROCESSED:
                self.signals.item_processed.emit(event.match, event.source, event.target)
            elif event.type is ProcessingEventType.SKIPPED:
                self.signals.item_skipped.emit(event.match, event.target, event.message or "")
            elif event.type is ProcessingEventType.FAILED:
                self.signals.item_failed.emit(event.match, event.message or "")

        try:
            summary = self._post_processor.process(
                self.matches,
                self.options,
                progress_callback=progress_callback,
                event_callback=event_callback,
            )
        except PostProcessingError as exc:
            self._logger.error("Library post-processing failed: %s", exc)
            self.signals.error.emit(str(exc))
            self.signals.finished.emit(exc.summary)
            return
        except Exception as exc:
            self._logger.error("Unexpected library post-processing error: %s", exc)
            self.signals.error.emit(str(exc))
            self.signals.finished.emit(PostProcessingSummary())
            return

        self.signals.finished.emit(summary)

    def stop(self) -> None:
        """Request the worker to stop."""
        self._should_stop = True
