"""Abstract interface and implementations for subtitle providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from .models import SubtitleLanguage, SubtitleFormat, MediaType


@dataclass
class SubtitleResult:
    """Result from a subtitle search."""

    subtitle_id: str
    provider: str
    language: SubtitleLanguage
    format: SubtitleFormat
    download_url: str
    file_size: Optional[int] = None
    fps: Optional[float] = None
    release_name: Optional[str] = None
    upload_date: Optional[str] = None
    downloads: int = 0
    rating: float = 0.0


class SubtitleProvider(ABC):
    """Abstract base class for subtitle providers."""

    @abstractmethod
    def search(
        self,
        title: str,
        media_type: MediaType,
        language: SubtitleLanguage,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
    ) -> List[SubtitleResult]:
        """Search for subtitles.
        
        Args:
            title: The title to search for
            media_type: The type of media (MOVIE or TV)
            language: The language of subtitles to find
            year: Release year (for movies)
            season: Season number (for TV episodes)
            episode: Episode number (for TV episodes)
            
        Returns:
            List of subtitle search results
        """
        pass

    @abstractmethod
    def download(self, subtitle_result: SubtitleResult, output_path: str) -> bool:
        """Download a subtitle file.
        
        Args:
            subtitle_result: The subtitle result to download
            output_path: The path to save the subtitle file
            
        Returns:
            True if download successful, False otherwise
        """
        pass


class MockSubtitleProvider(SubtitleProvider):
    """Mock subtitle provider for testing and demonstration."""

    def search(
        self,
        title: str,
        media_type: MediaType,
        language: SubtitleLanguage,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
    ) -> List[SubtitleResult]:
        """Search for subtitles using mock data."""
        results = []

        # Create mock results based on title
        base_hash = hash(title) % 10000
        
        for i in range(2):
            # Vary format and other details
            format_options = [SubtitleFormat.SRT, SubtitleFormat.ASS, SubtitleFormat.VTT]
            subtitle_format = format_options[i % len(format_options)]
            
            result = SubtitleResult(
                subtitle_id=f"mock_{base_hash}_{i}",
                provider="MockProvider",
                language=language,
                format=subtitle_format,
                download_url=f"https://example.com/subtitle/{base_hash}_{i}.{subtitle_format.value}",
                file_size=50000 + (i * 5000),
                fps=23.976 if i == 0 else 25.0,
                release_name=f"{title} {'720p' if i == 0 else '1080p'}",
                downloads=100 + (i * 50),
                rating=4.5 + (i * 0.3),
            )
            results.append(result)

        return results

    def download(self, subtitle_result: SubtitleResult, output_path: str) -> bool:
        """Download a subtitle file."""
        import time
        from pathlib import Path
        
        try:
            # Simulate download delay
            time.sleep(0.5)
            
            # Create a dummy subtitle file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write mock subtitle content
            mock_content = f"""1
00:00:00,000 --> 00:00:05,000
This is a mock subtitle from {subtitle_result.provider}
Language: {subtitle_result.language.value}

2
00:00:05,000 --> 00:00:10,000
For testing purposes only
"""
            output_file.write_text(mock_content, encoding="utf-8")
            return True
        except Exception:
            return False


class OpenSubtitlesProvider(SubtitleProvider):
    """Provider for OpenSubtitles API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize OpenSubtitles provider.
        
        Args:
            api_key: Optional API key for OpenSubtitles
        """
        self.api_key = api_key
        self.base_url = "https://api.opensubtitles.com/api/v1"

    def search(
        self,
        title: str,
        media_type: MediaType,
        language: SubtitleLanguage,
        year: Optional[int] = None,
        season: Optional[int] = None,
        episode: Optional[int] = None,
    ) -> List[SubtitleResult]:
        """Search for subtitles on OpenSubtitles."""
        # In a real implementation, this would call the OpenSubtitles API
        # For now, return mock results to demonstrate the interface
        import time
        
        results = []
        base_hash = hash(title) % 10000
        
        for i in range(3):
            result = SubtitleResult(
                subtitle_id=f"os_{base_hash}_{i}",
                provider="OpenSubtitles",
                language=language,
                format=SubtitleFormat.SRT,
                download_url=f"https://api.opensubtitles.com/download/{base_hash}_{i}",
                file_size=45000 + (i * 3000),
                fps=23.976,
                release_name=f"{title} Release {i + 1}",
                downloads=500 + (i * 100),
                rating=4.7 + (i * 0.1),
            )
            results.append(result)

        return results

    def download(self, subtitle_result: SubtitleResult, output_path: str) -> bool:
        """Download a subtitle from OpenSubtitles."""
        # In a real implementation, this would download from the actual API
        # For testing, use mock download
        import time
        from pathlib import Path
        
        try:
            time.sleep(0.3)
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            mock_content = f"""1
00:00:00,000 --> 00:00:05,000
OpenSubtitles: {subtitle_result.release_name}

2
00:00:05,000 --> 00:00:10,000
Language: {subtitle_result.language.value}
"""
            output_file.write_text(mock_content, encoding="utf-8")
            return True
        except Exception:
            return False
