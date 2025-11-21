"""Poster downloading service with caching, retries, and size selection."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from PySide6.QtCore import QObject, Signal

from . import APP_USER_AGENT
from .logging import get_logger
from .models import DownloadStatus, PosterInfo, PosterSize, PosterType


class PosterDownloader(QObject):
    """Service for downloading poster images with caching and retries."""

    # Signals
    download_progress = Signal(str, int, int)  # poster_id, current, total
    download_completed = Signal(str, str)  # poster_id, local_path
    download_failed = Signal(str, str)  # poster_id, error_message

    def __init__(
        self,
        cache_dir: Path | None = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._cache_dir = cache_dir or Path.home() / ".media-manager" / "poster-cache"
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._timeout = timeout
        self._downloading: set[str] = set()

        # Ensure cache directory exists
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_poster_path(
        self,
        media_path: Path,
        poster_type: PosterType,
        size: PosterSize = PosterSize.MEDIUM,
    ) -> Path:
        """Get the standard local path for a poster."""
        # Determine poster filename based on media file and type
        if poster_type == PosterType.POSTER:
            poster_name = f"{media_path.stem}-poster.jpg"
        elif poster_type == PosterType.FANART:
            poster_name = f"{media_path.stem}-fanart.jpg"
        elif poster_type == PosterType.BANNER:
            poster_name = f"{media_path.stem}-banner.jpg"
        else:  # THUMBNAIL
            poster_name = f"{media_path.stem}-thumb.jpg"

        # Place poster next to media file or in cache directory
        if media_path.parent.exists():
            return media_path.parent / poster_name
        else:
            return self._cache_dir / poster_name

    def download_poster(
        self,
        poster_info: PosterInfo,
        media_path: Path,
        force_download: bool = False,
    ) -> bool:
        """Download a poster and update the PosterInfo object."""
        if not poster_info.url:
            self._logger.warning("No URL provided for poster download")
            poster_info.download_status = DownloadStatus.FAILED
            poster_info.error_message = "No URL provided"
            return False

        poster_id = self._get_poster_id(poster_info)

        # Check if already downloading
        if poster_id in self._downloading and not force_download:
            self._logger.info(f"Poster already downloading: {poster_id}")
            return False

        # Check if already exists locally
        local_path = self.get_poster_path(
            media_path, poster_info.poster_type, poster_info.size
        )
        if local_path.exists() and not force_download:
            self._logger.info(f"Poster already exists locally: {local_path}")
            poster_info.local_path = local_path
            poster_info.download_status = DownloadStatus.COMPLETED
            poster_info.file_size = local_path.stat().st_size
            return True

        # Check cache
        cached_path = self._get_cached_path(poster_info.url)
        if cached_path.exists() and not force_download:
            self._logger.info(f"Using cached poster: {cached_path}")
            try:
                # Copy from cache to target location
                import shutil

                shutil.copy2(cached_path, local_path)
                poster_info.local_path = local_path
                poster_info.download_status = DownloadStatus.COMPLETED
                poster_info.file_size = local_path.stat().st_size
                return True
            except Exception as exc:
                self._logger.warning(f"Failed to copy cached poster: {exc}")

        # Start download
        self._downloading.add(poster_id)
        poster_info.download_status = DownloadStatus.DOWNLOADING
        poster_info.retry_count = 0

        try:
            success = self._download_with_retries(poster_info, media_path)
            if success:
                self.download_completed.emit(poster_id, str(poster_info.local_path))
            else:
                self.download_failed.emit(
                    poster_id, poster_info.error_message or "下载失败"
                )
            return success
        finally:
            self._downloading.discard(poster_id)

    def _download_with_retries(self, poster_info: PosterInfo, media_path: Path) -> bool:
        """Download poster with retry logic."""
        url = poster_info.url

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                self._logger.info(
                    f"Retrying poster download (attempt {attempt + 1}): {url}"
                )
                time.sleep(self._retry_delay * attempt)  # Exponential backoff

            try:
                # Create request with user agent
                req = Request(url, headers={"User-Agent": APP_USER_AGENT})

                with urlopen(req, timeout=self._timeout) as response:
                    content_type = response.headers.get("content-type", "")
                    if not content_type.startswith("image/"):
                        raise ValueError(f"Invalid content type: {content_type}")

                    content_length = response.headers.get("content-length")
                    total_size = int(content_length) if content_length else 0

                    # Download to cache first
                    cached_path = self._get_cached_path(url)
                    with open(cached_path, "wb") as f:
                        downloaded = 0
                        chunk_size = 8192

                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break

                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                int((downloaded / total_size) * 100)
                                poster_id = self._get_poster_id(poster_info)
                                self.download_progress.emit(
                                    poster_id, downloaded, total_size
                                )

                    # Move to final location
                    local_path = self.get_poster_path(
                        media_path, poster_info.poster_type, poster_info.size
                    )
                    import shutil

                    shutil.move(str(cached_path), str(local_path))

                    # Update poster info
                    poster_info.local_path = local_path
                    poster_info.download_status = DownloadStatus.COMPLETED
                    poster_info.file_size = local_path.stat().st_size
                    poster_info.error_message = None

                    self._logger.info(f"Successfully downloaded poster: {local_path}")
                    return True

            except Exception as exc:
                poster_info.error_message = str(exc)
                self._logger.warning(f"Download attempt {attempt + 1} failed: {exc}")

                if attempt == self._max_retries:
                    poster_info.download_status = DownloadStatus.FAILED
                    return False

        return False

    def _get_poster_id(self, poster_info: PosterInfo) -> str:
        """Generate a unique ID for a poster."""
        if poster_info.url:
            return hashlib.md5(poster_info.url.encode()).hexdigest()[:16]
        else:
            return f"{poster_info.poster_type.value}_{id(poster_info)}"

    def _get_cached_path(self, url: str) -> Path:
        """Get the cache path for a URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        # Extract file extension from URL
        parsed = urlparse(url)
        ext = ""
        if "." in parsed.path:
            ext = "." + parsed.path.split(".")[-1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                ext = ".jpg"  # Default to jpg

        return self._cache_dir / f"{url_hash}{ext}"

    def clear_cache(self) -> None:
        """Clear the poster cache."""
        try:
            for file_path in self._cache_dir.iterdir():
                if file_path.is_file():
                    file_path.unlink()
            self._logger.info("Poster cache cleared")
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

    def is_downloading(self, poster_info: PosterInfo) -> bool:
        """Check if a poster is currently being downloaded."""
        poster_id = self._get_poster_id(poster_info)
        return poster_id in self._downloading
