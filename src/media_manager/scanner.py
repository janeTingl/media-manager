"""Filesystem scanner and filename parser for media files."""

import re
from pathlib import Path
from typing import List, Optional

from .logging import get_logger
from .models import MediaType, VideoMetadata


class MediaScanner:
    """Scanner for media files with filename parsing."""

    def __init__(self) -> None:
        self._logger = get_logger().get_logger(__name__)

        # Video file extensions
        self.video_extensions = {
            ".mkv",
            ".mp4",
            ".avi",
            ".mov",
            ".flv",
            ".wmv",
            ".webm",
            ".m4v",
            ".mpg",
            ".mpeg",
            ".m2ts",
            ".mts",
            ".ts",
            ".vob",
            ".f4v",
        }

        # Directories to ignore
        self.ignored_dirs = {
            ".git",
            ".svn",
            ".venv",
            "node_modules",
            "__pycache__",
            "System Volume Information",
            "$RECYCLE.BIN",
            ".DS_Store",
            "Thumbs.db",
            ".thumbnails",
            ".cache",
        }

        # Compile regex patterns
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for filename parsing."""
        # TV episode patterns
        self.tv_patterns = [
            # S01E02, S01 E02
            re.compile(r"(.*?)[\s._-]*S(\d{1,2})[\s._-]*E(\d{1,2})", re.IGNORECASE),
            # 1x02, 01x02
            re.compile(r"(.*?)[\s._-]*(\d{1,2})x(\d{1,2})(?![\d])", re.IGNORECASE),
            # Season 2 Episode 5
            re.compile(
                r"(.*?)[\s._-]*Season[\s._]*(\d{1,2})[\s._-]*Episode[\s._]*(\d{1,2})",
                re.IGNORECASE,
            ),
        ]

        # Year pattern
        self.year_pattern = re.compile(r"\b(19|20)\d{2}\b")

        # Quality indicators to remove
        self.quality_patterns = [
            re.compile(
                r"\b(1080p|720p|480p|4K|HD|BluRay|BRRip|DVDRip|WEBRip|WEB-DL)\b",
                re.IGNORECASE,
            ),
            re.compile(r"\b(x264|x265|h264|h265|hevc|avc)\b", re.IGNORECASE),
            re.compile(r"\b(HDTV|PDTV|SDTV)\b", re.IGNORECASE),
        ]

    def scan_directory(
        self, directory: Path, recursive: bool = True
    ) -> List[VideoMetadata]:
        """Scan a directory for media files.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of VideoMetadata objects
        """
        if not directory.exists() or not directory.is_dir():
            self._logger.error(f"Directory does not exist: {directory}")
            return []

        self._logger.info(f"Scanning directory: {directory}")
        media_files = []

        try:
            if recursive:
                files = directory.rglob("*")
            else:
                files = directory.iterdir()

            for file_path in files:
                if self._should_ignore_file(file_path):
                    continue

                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in self.video_extensions
                ):
                    metadata = self.parse_filename(file_path)
                    if metadata:
                        media_files.append(metadata)
                        self._logger.debug(f"Found media file: {file_path}")

        except OSError as e:
            self._logger.error(f"Error scanning directory {directory}: {e}")

        self._logger.info(f"Found {len(media_files)} media files in {directory}")
        return media_files

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored."""
        # Check if any parent directory is in ignored list
        for part in file_path.parts:
            if part in self.ignored_dirs:
                return True

        # Hidden files
        if file_path.name.startswith("."):
            return True

        return False

    def parse_filename(self, file_path: Path) -> Optional[VideoMetadata]:
        """Parse a filename to extract metadata.

        Args:
            file_path: Path to the media file

        Returns:
            VideoMetadata object or None if parsing failed
        """
        filename = file_path.stem

        # Try TV episode patterns first
        for pattern in self.tv_patterns:
            match = pattern.search(filename)
            if match:
                title = self._clean_title(match.group(1))
                season = int(match.group(2))
                episode = int(match.group(3))

                # Extract year if present
                year = self._extract_year(filename)

                return VideoMetadata(
                    file_path=file_path,
                    title=title,
                    media_type=MediaType.TV_EPISODE,
                    year=year,
                    season=season,
                    episode=episode,
                )

        # If no TV pattern matched, treat as movie
        title = self._clean_title(filename)
        year = self._extract_year(filename)

        # Basic heuristics to distinguish movies from TV shows
        if self._is_likely_tv_show(title, filename):
            # Try to extract season/episode from title or directory
            season, episode = self._extract_season_episode_from_context(file_path)
            if season is not None and episode is not None:
                return VideoMetadata(
                    file_path=file_path,
                    title=title,
                    media_type=MediaType.TV_EPISODE,
                    year=year,
                    season=season,
                    episode=episode,
                )

        return VideoMetadata(
            file_path=file_path,
            title=title,
            media_type=MediaType.MOVIE,
            year=year,
        )

    def _clean_title(self, title: str) -> str:
        """Clean up the title by removing unwanted text."""
        if not title:
            return "Unknown"

        # Remove quality indicators
        for pattern in self.quality_patterns:
            title = pattern.sub("", title)

        # Remove common separators and clean up
        title = re.sub(r"[\._\-\+]+", " ", title)

        # Remove years from title (they're handled separately)
        title = self.year_pattern.sub("", title)

        # Remove extra whitespace and trim
        title = re.sub(r"\s+", " ", title).strip()

        # Remove leading/trailing brackets
        title = re.sub(r"^[\[\(\{]\s*|\s*[\]\)\}]$", "", title)

        return title or "Unknown"

    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text."""
        match = self.year_pattern.search(text)
        if match:
            year = int(match.group())
            # Validate year range
            if 1900 <= year <= 2099:
                return year
        return None

    def _is_likely_tv_show(self, title: str, filename: str) -> bool:
        """Heuristics to determine if content is likely a TV show."""
        # Check for TV-related keywords in title
        tv_keywords = [
            "episode",
            "ep",
            "season",
            "series",
            "show",
            "pilot",
            "part",
            "chapter",
            "vol",
            "volume",
        ]

        title_lower = title.lower()
        for keyword in tv_keywords:
            if keyword in title_lower:
                return True

        # Check parent directory for TV-related patterns
        # This would be used when we have the full path context
        return False

    def _extract_season_episode_from_context(
        self, file_path: Path
    ) -> tuple[Optional[int], Optional[int]]:
        """Try to extract season/episode from directory structure or filename."""
        # Check parent directory for season info
        parent_name = file_path.parent.name
        season_match = re.search(
            r"Season\s*(\d+)|S(\d{1,2})", parent_name, re.IGNORECASE
        )
        if season_match:
            season = int(season_match.group(1) or season_match.group(2))

            # Try to extract episode from filename
            filename = file_path.stem
            episode_match = re.search(
                r"Episode\s*(\d+)|E(\d{1,2})|(\d{1,2})\s*of", filename, re.IGNORECASE
            )
            if episode_match:
                episode = int(
                    episode_match.group(1)
                    or episode_match.group(2)
                    or episode_match.group(3)
                )
                return season, episode

        return None, None

    def scan_multiple_directories(self, directories: List[Path]) -> List[VideoMetadata]:
        """Scan multiple directories for media files.

        Args:
            directories: List of directories to scan

        Returns:
            Combined list of VideoMetadata objects
        """
        all_media = []

        for directory in directories:
            media_files = self.scan_directory(directory)
            all_media.extend(media_files)

        return all_media
