# 影藏·媒体管理器 - API Reference

## Overview

This document provides comprehensive API reference for the 影藏·媒体管理器 library. It covers the main classes, methods, and data structures used throughout the application.

## Table of Contents

1. [Data Models](#data-models)
2. [Scanning API](#scanning-api)
3. [Matching API](#matching-api)
4. [Media Processing](#media-processing)
5. [Settings Management](#settings-management)
6. [Background Workers](#background-workers)
7. [Logging](#logging)
8. [Service Registry](#service-registry)

## Data Models

### MediaType Enum

```python
from media_manager.models import MediaType

class MediaType(str, Enum):
    """Types of media that can be detected."""
    MOVIE = "movie"
    TV = "tv"
```

### MatchStatus Enum

```python
from media_manager.models import MatchStatus

class MatchStatus(str, Enum):
    """Status of match resolution."""
    PENDING = "pending"      # Waiting to be matched
    MATCHED = "matched"      # Automatically matched
    MANUAL = "manual"        # Manually matched by user
    SKIPPED = "skipped"      # User skipped this item
```

### VideoMetadata Dataclass

```python
from media_manager.models import VideoMetadata
from pathlib import Path

@dataclass
class VideoMetadata:
    """Metadata extracted from a video filename."""
    path: Path
    title: str
    media_type: MediaType
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    
    def is_movie(self) -> bool:
        """Return True if this is a movie."""
        
    def is_episode(self) -> bool:
        """Return True if this is a TV episode."""
        
    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
```

**Example:**

```python
from media_manager.models import VideoMetadata, MediaType
from pathlib import Path

# Movie example
movie_meta = VideoMetadata(
    path=Path("/media/movies/Inception.2010.1080p.mkv"),
    title="Inception",
    media_type=MediaType.MOVIE,
    year=2010
)

# TV episode example
episode_meta = VideoMetadata(
    path=Path("/media/shows/Breaking.Bad/S05E16.Felina.mkv"),
    title="Felina",
    media_type=MediaType.TV,
    season=5,
    episode=16
)

# Check type
assert movie_meta.is_movie()
assert episode_meta.is_episode()
```

### MediaMatch Dataclass

```python
from media_manager.models import MediaMatch, MatchStatus, PosterInfo, SubtitleInfo
from typing import Dict, Optional

@dataclass
class MediaMatch:
    """Represents a matched media item with metadata."""
    metadata: VideoMetadata
    status: MatchStatus
    external_id: Optional[str] = None
    external_source: Optional[str] = None  # "tmdb" or "tvdb"
    matched_title: Optional[str] = None
    matched_year: Optional[int] = None
    confidence: float = 0.0  # 0.0 to 1.0
    overview: Optional[str] = None
    posters: Dict[str, PosterInfo] = field(default_factory=dict)
    subtitles: Dict[str, SubtitleInfo] = field(default_factory=dict)
    runtime: Optional[int] = None
    aired_date: Optional[str] = None
    cast: Optional[list[str]] = None
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
```

**Example:**

```python
from media_manager.models import MediaMatch, MatchStatus

match = MediaMatch(
    metadata=video_metadata,
    status=MatchStatus.MATCHED,
    external_id="550",
    external_source="tmdb",
    matched_title="Fight Club",
    matched_year=1999,
    confidence=0.95,
    overview="An insomniac office worker...",
    runtime=139
)

# Serialize for storage
match_dict = match.as_dict()
```

### PosterType and PosterInfo

```python
from media_manager.models import PosterType, PosterSize, DownloadStatus, PosterInfo
from dataclasses import dataclass

class PosterType(str, Enum):
    POSTER = "poster"
    FANART = "fanart"
    BANNER = "banner"
    THUMBNAIL = "thumbnail"

class PosterSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ORIGINAL = "original"

@dataclass
class PosterInfo:
    """Information about a downloaded poster."""
    url: Optional[str] = None
    local_path: Optional[Path] = None
    status: DownloadStatus = DownloadStatus.PENDING
    file_size: Optional[int] = None
    error: Optional[str] = None
    retry_count: int = 0
```

### SubtitleLanguage and SubtitleInfo

```python
from media_manager.models import SubtitleLanguage, SubtitleFormat, SubtitleInfo

class SubtitleLanguage(str, Enum):
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    RUSSIAN = "ru"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"

class SubtitleFormat(str, Enum):
    SRT = "srt"
    ASS = "ass"
    SUB = "sub"
    VTT = "vtt"
    SSA = "ssa"

@dataclass
class SubtitleInfo:
    """Information about a downloaded subtitle."""
    language: SubtitleLanguage
    format: SubtitleFormat
    url: Optional[str] = None
    local_path: Optional[Path] = None
    status: DownloadStatus = DownloadStatus.PENDING
    provider: str = "opensubtitles"
    subtitle_id: Optional[str] = None
```

## Scanning API

### ScanConfig Dataclass

```python
from media_manager.scanner import ScanConfig
from pathlib import Path
from typing import List, Tuple, Optional

@dataclass
class ScanConfig:
    """Configuration for filesystem scanning."""
    root_paths: List[Path]
    video_extensions: Tuple[str, ...] = DEFAULT_VIDEO_EXTENSIONS
    ignored_directories: Tuple[str, ...] = DEFAULT_IGNORED_DIRECTORIES
    
    def with_roots(self, roots: List[Path]) -> "ScanConfig":
        """Return a new config with different root paths."""
```

**Example:**

```python
from media_manager.scanner import ScanConfig
from pathlib import Path

config = ScanConfig(
    root_paths=[
        Path("/media/movies"),
        Path("/media/tv_shows")
    ]
)

# Or create with custom extensions
config = ScanConfig(
    root_paths=[Path("/media")],
    video_extensions=(".mkv", ".mp4", ".avi"),
    ignored_directories=(".git", ".venv", "node_modules")
)
```

### Scanner Class

```python
from media_manager.scanner import Scanner, ScanConfig
from pathlib import Path
from typing import Iterator

class Scanner:
    """Scans filesystem and parses video metadata."""
    
    def __init__(self) -> None:
        """Initialize the scanner."""
    
    def iter_video_files(self, config: ScanConfig) -> Iterator[Path]:
        """Iterate over all video files matching config."""
        
    def parse_video(self, path: Path) -> VideoMetadata:
        """Parse video filename and extract metadata."""
```

**Example:**

```python
from media_manager.scanner import Scanner, ScanConfig
from pathlib import Path

scanner = Scanner()
config = ScanConfig(root_paths=[Path("/media/movies")])

# Iterate over all video files
for video_path in scanner.iter_video_files(config):
    print(f"Found: {video_path}")

# Parse individual file
metadata = scanner.parse_video(Path("/media/movies/Inception.2010.1080p.mkv"))
print(f"Title: {metadata.title}, Year: {metadata.year}")
```

### ScanEngine Class

```python
from media_manager.scan_engine import ScanEngine
from PySide6.QtCore import Signal
from typing import Callable, List, Optional

class ScanEngine(QObject):
    """High-level scanning engine with Qt signals."""
    
    # Signals
    scan_started = Signal(str)                    # path
    scan_progress = Signal(int, int, str)        # current, total, current_file
    scan_completed = Signal(object)               # List[VideoMetadata]
    enrichment_task_created = Signal(object)     # VideoMetadata
    scan_error = Signal(str)                     # error_message
    
    def __init__(self, scanner: Optional[Scanner] = None) -> None:
        """Initialize the scan engine."""
    
    def scan(self, config: ScanConfig) -> List[VideoMetadata]:
        """Perform scan with provided configuration."""
    
    def register_enrichment_callback(
        self, callback: Callable[[VideoMetadata], None]
    ) -> None:
        """Register a callback for each scanned file."""
```

**Example:**

```python
from media_manager.scan_engine import ScanEngine
from media_manager.scanner import ScanConfig
from pathlib import Path

engine = ScanEngine()

# Connect to signals
engine.scan_started.connect(lambda path: print(f"Scanning: {path}"))
engine.scan_progress.connect(lambda c, t, f: print(f"{c}/{t}: {f}"))
engine.scan_completed.connect(lambda results: print(f"Found {len(results)} videos"))

# Register enrichment callback
def on_video_found(metadata):
    print(f"Processing: {metadata.title}")

engine.register_enrichment_callback(on_video_found)

# Perform scan
config = ScanConfig(root_paths=[Path("/media")])
results = engine.scan(config)
```

## Matching API

### MediaMatch and Searching

```python
from media_manager.models import MediaMatch, SearchRequest, SearchResult
from dataclasses import dataclass

@dataclass
class SearchRequest:
    """Request for manual media search."""
    query: str
    media_type: MediaType
    year: Optional[int] = None
    external_id: Optional[str] = None

@dataclass
class SearchResult:
    """Result from media search."""
    id: str
    title: str
    year: Optional[int]
    overview: Optional[str]
    confidence: float
    media_type: MediaType
    external_source: str
    poster_urls: Dict[str, Optional[str]] = field(default_factory=dict)
    subtitles: Dict[str, SubtitleInfo] = field(default_factory=dict)
```

## Media Processing

### LibraryPostProcessor

```python
from media_manager.library_postprocessor import (
    LibraryPostProcessor,
    PostProcessingOptions
)

class LibraryPostProcessor:
    """Handles post-processing of matched media."""
    
    def process(
        self,
        matches: List[MediaMatch],
        options: PostProcessingOptions
    ) -> PostProcessingSummary:
        """Process a list of matches."""
```

### PostProcessingOptions

```python
@dataclass
class PostProcessingOptions:
    """Options for media post-processing."""
    rename_media: bool = True
    organize_by_type: bool = True
    generate_nfo: bool = True
    download_posters: bool = False
    download_subtitles: bool = False
    target_folder: Optional[Path] = None
    subtitle_languages: List[str] = field(default_factory=list)
```

## Settings Management

### SettingsManager Class

```python
from media_manager.settings import SettingsManager, get_settings
from typing import Any, Dict, Optional

class SettingsManager:
    """Manages application settings with JSON persistence."""
    
    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize settings manager."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
    
    def save(self) -> None:
        """Save settings to file."""
    
    # Specialized getters
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for external service."""
    
    def set_api_key(self, service: str, key: str) -> None:
        """Set API key for external service."""
    
    def get_scan_paths(self) -> List[Path]:
        """Get configured scan paths."""
    
    def set_scan_paths(self, paths: List[Path]) -> None:
        """Set scan paths."""
```

**Example:**

```python
from media_manager.settings import SettingsManager, get_settings
from pathlib import Path

# Get global instance
settings = get_settings()

# Get values
tmdb_key = settings.get_api_key("tmdb")
scan_paths = settings.get_scan_paths()

# Set values
settings.set_api_key("tmdb", "your-api-key-here")
settings.set_scan_paths([Path("/media/movies"), Path("/media/tv")])
settings.save()

# Get/set custom values
debug_mode = settings.get("debug_mode", False)
settings.set("debug_mode", True)
```

## Background Workers

### MatchWorker

```python
from media_manager.workers import MatchWorker, MatchWorkerSignals
from typing import List

class MatchWorker(QRunnable):
    """Background worker for matching videos."""
    
    signals: MatchWorkerSignals
    
    def __init__(self, metadata_list: List[VideoMetadata]) -> None:
        """Initialize match worker."""
    
    def run(self) -> None:
        """Execute matching in background."""
    
    def stop(self) -> None:
        """Stop the worker gracefully."""

class MatchWorkerSignals(QObject):
    """Signals emitted by MatchWorker."""
    match_found = Signal(object)        # MediaMatch
    match_failed = Signal(str, str)     # path, error
    progress = Signal(int, int)         # current, total
    finished = Signal()
```

**Example:**

```python
from media_manager.workers import MatchWorker

# Create worker
worker = MatchWorker(metadata_list)

# Connect to signals
worker.signals.match_found.connect(on_match_found)
worker.signals.progress.connect(on_progress)
worker.signals.finished.connect(on_finished)

# Run in thread pool
thread_pool = QThreadPool()
thread_pool.start(worker)
```

### WorkerManager

```python
from media_manager.workers import WorkerManager
from typing import List, Optional

class WorkerManager:
    """Manages background worker threads."""
    
    def __init__(self) -> None:
        """Initialize worker manager."""
    
    def start_match_worker(
        self, metadata_list: List[VideoMetadata]
    ) -> MatchWorker:
        """Start a match worker."""
    
    def start_poster_download_worker(
        self, matches: List[MediaMatch]
    ) -> PosterDownloadWorker:
        """Start a poster download worker."""
    
    def start_subtitle_download_worker(
        self, matches: List[MediaMatch]
    ) -> SubtitleDownloadWorker:
        """Start a subtitle download worker."""
    
    def stop_all(self) -> None:
        """Stop all active workers."""
```

## Logging

### Logger Initialization

```python
from media_manager.logging import get_logger

# Get logger instance
logger_manager = get_logger()
logger = logger_manager.get_logger(__name__)

# Use logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

**Example:**

```python
from media_manager.logging import get_logger

logger = get_logger().get_logger("media_manager.scanner")

def scan_directory(path):
    logger.info(f"Starting scan of {path}")
    try:
        # scan code
        logger.debug(f"Found {n} files")
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        raise
```

## Service Registry

### ServiceRegistry

```python
from media_manager.services import ServiceRegistry, get_service_registry, inject
from typing import Any, Union, Type, TypeVar

T = TypeVar('T')

class ServiceRegistry(QObject):
    """Dependency injection container."""
    
    def register(
        self,
        service_type: Union[str, Type],
        implementation: Any,
        singleton: bool = True
    ) -> None:
        """Register a service."""
    
    def get(self, service_type: Union[str, Type]) -> Any:
        """Get a service instance."""
    
    def has(self, service_type: Union[str, Type]) -> bool:
        """Check if service is registered."""
    
    def clear(self) -> None:
        """Clear all services."""
```

**Example:**

```python
from media_manager.services import get_service_registry, inject

# Register services
registry = get_service_registry()
registry.register("SettingsManager", settings_instance)
registry.register("ScanEngine", engine_instance)

# Get services
settings = registry.get("SettingsManager")
engine = registry.get("ScanEngine")

# Use with decorator
@inject("SettingsManager")
def my_function(settings):
    return settings.get("some_key")
```

## Complete Example

```python
#!/usr/bin/env python3
"""Complete example of using 影藏·媒体管理器 API."""

from pathlib import Path
from media_manager.scanner import Scanner, ScanConfig
from media_manager.models import MediaType, MatchStatus, MediaMatch
from media_manager.settings import SettingsManager
from media_manager.library_postprocessor import (
    LibraryPostProcessor,
    PostProcessingOptions
)

# 1. Setup
settings = SettingsManager()
scanner = Scanner()

# 2. Scan directory
config = ScanConfig(root_paths=[Path("/media/movies")])
video_files = list(scanner.iter_video_files(config))
print(f"Found {len(video_files)} video files")

# 3. Parse metadata
metadata_list = [scanner.parse_video(f) for f in video_files]
for meta in metadata_list:
    print(f"  - {meta.title} ({meta.year})")

# 4. Create matches (mock)
matches = []
for meta in metadata_list:
    match = MediaMatch(
        metadata=meta,
        status=MatchStatus.MATCHED,
        matched_title=meta.title,
        matched_year=meta.year,
        confidence=0.95
    )
    matches.append(match)

# 5. Post-process (rename, organize)
processor = LibraryPostProcessor(settings)
options = PostProcessingOptions(
    rename_media=True,
    organize_by_type=True,
    target_folder=Path("/media/organized")
)
summary = processor.process(matches, options)

print(f"\nProcessed {summary.processed_count} items")
print(f"Errors: {summary.error_count}")
```

## Error Handling

All APIs use standard Python exceptions:

```python
from media_manager.scanner import ScannerError
from media_manager.library_postprocessor import PostProcessingError

try:
    metadata = scanner.parse_video(Path("/invalid/path.mkv"))
except Exception as e:
    print(f"Parse error: {e}")

try:
    summary = processor.process(matches, options)
except PostProcessingError as e:
    print(f"Processing error: {e}")
```

## Type Hints

The codebase uses comprehensive type hints. All public APIs include type annotations for parameters and return values.

```python
from typing import List, Optional, Dict
from pathlib import Path
from media_manager.models import VideoMetadata, MediaMatch

def process_videos(
    paths: List[Path],
    options: Optional[Dict[str, str]] = None
) -> List[MediaMatch]:
    """Process a list of video paths."""
    ...
```
