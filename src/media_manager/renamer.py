"""Filename generation utilities for finalizing media files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import MediaMatch, MediaType
from .settings import SettingsManager, get_settings

_INVALID_CHARS_PATTERN = re.compile(r"[\\/:*?\"<>|]")
_MULTISPACE_PATTERN = re.compile(r"\s+")


@dataclass
class RenameContext:
    """Context information used when rendering rename templates."""

    title: str
    year: Optional[int]
    season: Optional[int]
    episode: Optional[int]


class RenamingEngine:
    """Generate deterministic target paths for media items."""

    def __init__(self, settings: Optional[SettingsManager] = None) -> None:
        self._settings = settings or get_settings()

    def build_relative_path(self, match: MediaMatch) -> Path:
        """Return the relative path (excluding media-type root) for the match."""

        metadata = match.metadata
        extension = metadata.path.suffix or ""
        context = RenameContext(
            title=self._determine_title(match),
            year=match.matched_year or metadata.year,
            season=metadata.season,
            episode=metadata.episode,
        )

        if metadata.media_type is MediaType.MOVIE:
            base_name = self._render_movie_name(context)
            folder = self._sanitize_name(base_name)
            filename = self._sanitize_name(base_name) + extension
            return Path(folder) / filename

        if metadata.media_type is MediaType.TV:
            show_name = self._sanitize_name(context.title)
            season_number = context.season or 0
            episode_number = context.episode or 0
            season_dir = f"Season {season_number:02d}"
            filename = self._render_tv_filename(context) + extension
            return Path(show_name) / season_dir / self._sanitize_name(filename)

        raise ValueError(f"Unsupported media type: {metadata.media_type}")

    def suggest_unique(self, base_path: Path) -> Path:
        """Return a unique path by appending a numeric suffix."""

        if not base_path.exists():
            return base_path

        parent = base_path.parent
        stem = base_path.stem
        suffix = base_path.suffix
        index = 1

        while True:
            candidate = parent / f"{stem} ({index}){suffix}"
            if not candidate.exists():
                return candidate
            index += 1

    def _determine_title(self, match: MediaMatch) -> str:
        if match.matched_title:
            return match.matched_title
        return match.metadata.title

    def _render_movie_name(self, context: RenameContext) -> str:
        template = self._settings.get_rename_template("movie")
        if template:
            rendered = template.format(
                title=context.title,
                year=context.year or "",
            )
        else:
            rendered = context.title
            if context.year:
                rendered += f" ({context.year})"
        return rendered.strip()

    def _render_tv_filename(self, context: RenameContext) -> str:
        template = self._settings.get_rename_template("tv_episode")
        if template:
            rendered = template.format(
                title=context.title,
                year=context.year or "",
                season=(context.season or 0),
                episode=(context.episode or 0),
            )
        else:
            rendered = (
                f"{context.title} - "
                f"S{(context.season or 0):02d}E{(context.episode or 0):02d}"
            )
        return rendered.strip()

    def _sanitize_name(self, value: str) -> str:
        value = _INVALID_CHARS_PATTERN.sub(" ", value)
        value = value.replace("..", " ")
        value = _MULTISPACE_PATTERN.sub(" ", value)
        sanitized = value.strip()
        return sanitized or "Unknown"


__all__ = ["RenamingEngine"]
