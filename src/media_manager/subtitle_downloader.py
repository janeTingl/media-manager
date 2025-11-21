"""Subtitle downloading service with caching, retries, and language support."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import QObject, Signal

from . import APP_USER_AGENT
from .logging import get_logger
from .models import DownloadStatus, SubtitleInfo, SubtitleLanguage
from .subtitle_provider import MockSubtitleProvider, SubtitleProvider, SubtitleResult


class SubtitleDownloader(QObject):
    """Service for downloading subtitles with caching and retries."""

    # Signals
    download_progress = Signal(str, int, int)  # subtitle_id, current, total
    download_completed = Signal(str, str)  # subtitle_id, local_path
    download_failed = Signal(str, str)  # subtitle_id, error_message
    search_started = Signal(str)  # title
    search_completed = Signal(list)  # List[SubtitleResult]
    search_failed = Signal(str)  # error_message

    def __init__(
        self,
        provider: SubtitleProvider | None = None,
        cache_dir: Path | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._provider = provider or MockSubtitleProvider()
        self._cache_dir = cache_dir or Path.home() / ".media-manager" / "subtitle-cache"
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._timeout = timeout
        self._downloading: set[str] = set()

        # Ensure cache directory exists
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def set_provider(self, provider: SubtitleProvider) -> None:
        """Set the subtitle provider."""
        self._provider = provider

    def search_subtitles(
        self,
        title: str,
        media_type,
        language: SubtitleLanguage,
        year: int | None = None,
        season: int | None = None,
        episode: int | None = None,
    ) -> list[SubtitleResult]:
        """Search for available subtitles."""
        try:
            self.search_started.emit(title)
            results = self._provider.search(
                title=title,
                media_type=media_type,
                language=language,
                year=year,
                season=season,
                episode=episode,
            )
            self.search_completed.emit(results)
            return results
        except Exception as exc:
            error_msg = f"Subtitle search failed: {exc}"
            self._logger.error(error_msg)
            self.search_failed.emit(error_msg)
            return []

    def get_subtitle_path(self, media_path: Path, language: SubtitleLanguage) -> Path:
        """Get the standard local path for a subtitle file."""
        # Use language code in filename: movie.en.srt, show.es.srt, etc.
        subtitle_name = f"{media_path.stem}.{language.value}.srt"

        # Place subtitle next to media file or in cache directory
        if media_path.parent.exists():
            return media_path.parent / subtitle_name
        else:
            return self._cache_dir / subtitle_name

    def download_subtitle(
        self,
        subtitle_info: SubtitleInfo,
        media_path: Path,
        subtitle_result: SubtitleResult | None = None,
        force_download: bool = False,
    ) -> bool:
        """Download a subtitle and update the SubtitleInfo object."""
        if not subtitle_info.url:
            self._logger.warning("No URL provided for subtitle download")
            subtitle_info.download_status = DownloadStatus.FAILED
            subtitle_info.error_message = "No URL provided"
            return False

        subtitle_id = self._get_subtitle_id(subtitle_info)

        # Check if already downloading
        if subtitle_id in self._downloading and not force_download:
            self._logger.info(f"Subtitle already downloading: {subtitle_id}")
            return False

        # Check if already exists locally
        local_path = self.get_subtitle_path(media_path, subtitle_info.language)
        if local_path.exists() and not force_download:
            self._logger.info(f"Subtitle already exists locally: {local_path}")
            subtitle_info.local_path = local_path
            subtitle_info.download_status = DownloadStatus.COMPLETED
            subtitle_info.file_size = local_path.stat().st_size
            return True

        # Check cache
        cached_path = self._get_cached_path(subtitle_info.url)
        if cached_path.exists() and not force_download:
            self._logger.info(f"Using cached subtitle: {cached_path}")
            try:
                import shutil

                shutil.copy2(cached_path, local_path)
                subtitle_info.local_path = local_path
                subtitle_info.download_status = DownloadStatus.COMPLETED
                subtitle_info.file_size = local_path.stat().st_size
                return True
            except Exception as exc:
                self._logger.warning(f"Failed to copy cached subtitle: {exc}")

        # Start download
        self._downloading.add(subtitle_id)
        subtitle_info.download_status = DownloadStatus.DOWNLOADING
        subtitle_info.retry_count = 0

        try:
            success = self._download_with_retries(
                subtitle_info, media_path, subtitle_result
            )
            if success:
                self.download_completed.emit(subtitle_id, str(subtitle_info.local_path))
            else:
                self.download_failed.emit(
                    subtitle_id, subtitle_info.error_message or "下载失败"
                )
            return success
        finally:
            self._downloading.discard(subtitle_id)

    def _download_with_retries(
        self,
        subtitle_info: SubtitleInfo,
        media_path: Path,
        subtitle_result: SubtitleResult | None = None,
    ) -> bool:
        """Download subtitle with retry logic."""
        # If we have a subtitle_result, use the provider's download method
        if subtitle_result is not None:
            for attempt in range(self._max_retries + 1):
                if attempt > 0:
                    self._logger.info(
                        f"Retrying subtitle download (attempt {attempt + 1})"
                    )
                    time.sleep(self._retry_delay * attempt)

                try:
                    local_path = self.get_subtitle_path(
                        media_path, subtitle_info.language
                    )
                    success = self._provider.download(subtitle_result, str(local_path))

                    if success:
                        subtitle_info.local_path = local_path
                        subtitle_info.download_status = DownloadStatus.COMPLETED
                        subtitle_info.file_size = local_path.stat().st_size
                        subtitle_info.error_message = None
                        self._logger.info(
                            f"Successfully downloaded subtitle: {local_path}"
                        )
                        return True
                    else:
                        subtitle_info.error_message = "Provider download failed"

                except Exception as exc:
                    subtitle_info.error_message = str(exc)
                    self._logger.warning(
                        f"Download attempt {attempt + 1} failed: {exc}"
                    )

                    if attempt == self._max_retries:
                        subtitle_info.download_status = DownloadStatus.FAILED
                        return False

        # Fallback: use URL directly
        url = subtitle_info.url
        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                self._logger.info(
                    f"Retrying subtitle download (attempt {attempt + 1}): {url}"
                )
                time.sleep(self._retry_delay * attempt)

            try:
                from urllib.request import Request, urlopen

                req = Request(url, headers={"User-Agent": APP_USER_AGENT})

                with urlopen(req, timeout=self._timeout) as response:
                    local_path = self.get_subtitle_path(
                        media_path, subtitle_info.language
                    )
                    cached_path = self._get_cached_path(url)

                    with open(cached_path, "wb") as f:
                        chunk_size = 8192
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)

                    # Move to final location
                    import shutil

                    shutil.move(str(cached_path), str(local_path))

                    # Update subtitle info
                    subtitle_info.local_path = local_path
                    subtitle_info.download_status = DownloadStatus.COMPLETED
                    subtitle_info.file_size = local_path.stat().st_size
                    subtitle_info.error_message = None

                    self._logger.info(f"Successfully downloaded subtitle: {local_path}")
                    return True

            except Exception as exc:
                subtitle_info.error_message = str(exc)
                self._logger.warning(f"Download attempt {attempt + 1} failed: {exc}")

                if attempt == self._max_retries:
                    subtitle_info.download_status = DownloadStatus.FAILED
                    return False

        return False

    def _get_subtitle_id(self, subtitle_info: SubtitleInfo) -> str:
        """Generate a unique ID for a subtitle."""
        if subtitle_info.url:
            return hashlib.md5(subtitle_info.url.encode()).hexdigest()[:16]
        elif subtitle_info.subtitle_id:
            return subtitle_info.subtitle_id
        else:
            return f"{subtitle_info.language.value}_{id(subtitle_info)}"

    def _get_cached_path(self, url: str) -> Path:
        """Get the cache path for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        # Extract file extension from URL
        parsed = urlparse(url)
        ext = ""
        if "." in parsed.path:
            ext = "." + parsed.path.split(".")[-1].lower()
            if ext not in [".srt", ".ass", ".sub", ".vtt", ".ssa"]:
                ext = ".srt"  # Default to srt
        else:
            ext = ".srt"

        return self._cache_dir / f"{url_hash}{ext}"

    def clear_cache(self) -> None:
        """Clear the subtitle cache."""
        try:
            for file_path in self._cache_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            self._logger.info("Subtitle cache cleared")
        except Exception as exc:
            self._logger.error(f"Failed to clear cache: {exc}")

    def get_cache_size(self) -> int:
        """Get the total size of the cache in bytes."""
        total_size = 0
        try:
            for file_path in self._cache_dir.iterdir():
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size

    def is_downloading(self, subtitle_info: SubtitleInfo) -> bool:
        """Check if a subtitle is currently being downloaded."""
        subtitle_id = self._get_subtitle_id(subtitle_info)
        return subtitle_id in self._downloading
