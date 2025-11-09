"""Filesystem scanning and filename parsing utilities."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Sequence

from .logging import get_logger
from .models import MediaType, VideoMetadata

DEFAULT_VIDEO_EXTENSIONS: tuple[str, ...] = (
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
)

DEFAULT_IGNORED_DIRECTORIES: tuple[str, ...] = (
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "System Volume Information",
    "$RECYCLE.BIN",
)

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
QUALITY_PATTERN = re.compile(
    r"\b(480p|576p|720p|1080p|1440p|2160p|4k|8k|hdtv|webrip|web[- ]?dl|"
    r"bluray|blu[- ]?ray|brrip|hdrip|dvdrip|dvdscr|remux|proper|repack|"
    r"xvid|x264|x265|h\.264|h\.265|hevc|aac|ac3|dts|ddp5\.1|5\.1|7\.1|"
    r"10bit|hdr|uhd|atm|dolby|truehd|limited|internal|sample)\b",
    re.IGNORECASE,
)
BRACKET_CONTENT_PATTERN = re.compile(r"\[[^\]]*\]|\([^\)]*\)|\{[^\}]*\}")
MULTISPACE_PATTERN = re.compile(r"\s+")
EPISODE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b[S](?P<season>\d{1,2})[.\s_-]*E(?P<episode>\d{1,2})\b"),
    re.compile(r"(?i)\b(?P<season>\d{1,2})x(?P<episode>\d{1,2})\b"),
    re.compile(
        r"(?i)Season[.\s_-]*(?P<season>\d{1,2})[.\s_-]*"
        r"(?:Episode|Ep)[.\s_-]*(?P<episode>\d{1,2})"
    ),
)


def _normalize_extension(extension: str) -> str:
    extension = extension.lower()
    if not extension.startswith("."):
        extension = f".{extension}"
    return extension


@dataclass
class ScanConfig:
    """Configuration used by the filesystem scanner."""

    root_paths: Sequence[Path]
    ignored_directories: Sequence[str] = DEFAULT_IGNORED_DIRECTORIES
    ignored_extensions: Sequence[str] = ()
    video_extensions: Sequence[str] = DEFAULT_VIDEO_EXTENSIONS
    _ignored_directory_set: set[str] = field(init=False, repr=False)
    _ignored_extension_set: set[str] = field(init=False, repr=False)
    _video_extension_set: set[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        normalized_roots = []
        for root in self.root_paths:
            normalized_roots.append(root if isinstance(root, Path) else Path(root))
        self.root_paths = tuple(normalized_roots)

        input_dirs = [directory.lower() for directory in self.ignored_directories]
        self.ignored_directories = tuple(sorted(set(input_dirs)))
        self._ignored_directory_set = set(self.ignored_directories)

        input_ignored_exts = [_normalize_extension(ext) for ext in self.ignored_extensions]
        self.ignored_extensions = tuple(sorted(set(input_ignored_exts)))
        self._ignored_extension_set = set(self.ignored_extensions)

        input_video_exts = [_normalize_extension(ext) for ext in self.video_extensions]
        self.video_extensions = tuple(sorted(set(input_video_exts)))
        self._video_extension_set = set(self.video_extensions)

    def with_roots(self, roots: Sequence[Path]) -> ScanConfig:
        """Return a new ScanConfig with the provided roots."""
        return ScanConfig(
            root_paths=tuple(roots),
            ignored_directories=self.ignored_directories,
            ignored_extensions=self.ignored_extensions,
            video_extensions=self.video_extensions,
        )


class Scanner:
    """Scanner that walks directories and extracts metadata from video files."""

    def __init__(self) -> None:
        self._logger = get_logger().get_logger(__name__)

    def scan(self, config: ScanConfig) -> list[VideoMetadata]:
        """Scan all configured paths and return video metadata instances."""
        return [self.parse_video(path) for path in self.iter_video_files(config)]

    def iter_video_files(self, config: ScanConfig) -> Iterator[Path]:
        """Yield video file paths discovered in the configured roots."""
        for root in config.root_paths:
            if not root.exists():
                self._logger.warning("Scan root does not exist: %s", root)
                continue

            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    dirnames[:] = [
                        dirname
                        for dirname in dirnames
                        if dirname.lower() not in config._ignored_directory_set
                    ]

                    for filename in filenames:
                        file_path = Path(dirpath) / filename
                        if not file_path.is_file():
                            continue

                        if self._should_include_file(file_path, config):
                            yield file_path
            except OSError as exc:
                self._logger.error("Failed to scan %s: %s", root, exc)

    def parse_video(self, path: Path) -> VideoMetadata:
        """Parse a single video file path into metadata."""
        stem = path.stem
        working_name = re.sub(r"[._]+", " ", stem)

        media_type = MediaType.MOVIE
        season = None
        episode = None

        for pattern in EPISODE_PATTERNS:
            match = pattern.search(working_name)
            if match:
                try:
                    season = int(match.group("season"))
                    episode = int(match.group("episode"))
                    media_type = MediaType.TV
                except (TypeError, ValueError):
                    season = None
                    episode = None
                    media_type = MediaType.MOVIE
                working_name = pattern.sub(" ", working_name, count=1)
                break

        year = self._extract_year(working_name)
        if year is not None:
            working_name = working_name.replace(str(year), " ", 1)

        title = self._clean_title(working_name)
        if not title:
            title = re.sub(r"[._]+", " ", stem).strip()

        return VideoMetadata(
            path=path,
            title=title,
            media_type=media_type,
            year=year,
            season=season,
            episode=episode,
        )

    def _should_include_file(self, file_path: Path, config: ScanConfig) -> bool:
        extension = file_path.suffix.lower()
        if extension in config._ignored_extension_set:
            return False
        return extension in config._video_extension_set

    def _extract_year(self, name: str) -> int | None:
        match = YEAR_PATTERN.search(name)
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                return None
        return None

    def _clean_title(self, raw_title: str) -> str:
        cleaned = BRACKET_CONTENT_PATTERN.sub(" ", raw_title)
        cleaned = QUALITY_PATTERN.sub(" ", cleaned)
        cleaned = re.sub(r"[-]+", " ", cleaned)
        cleaned = MULTISPACE_PATTERN.sub(" ", cleaned)
        return cleaned.strip(" ._-")
