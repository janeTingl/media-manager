# Media Manager - Architecture Guide

## Overview

The Media Manager is a modular, event-driven application built with PySide6 (Qt6) for managing media libraries. This document describes the overall architecture, design patterns, and component interactions.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Modules](#core-modules)
3. [Data Flow](#data-flow)
4. [Design Patterns](#design-patterns)
5. [Component Relationships](#component-relationships)
6. [Threading Model](#threading-model)
7. [Settings and Configuration](#settings-and-configuration)
8. [Extensibility](#extensibility)

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Window (Qt GUI)                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │  Scan Queue      │  │  Match Resolution│  │  Settings  │ │
│  │  Widget          │  │  Widget          │  │  Dialog    │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────────┘ │
└───────────┼──────────────────────┼───────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Match Manager (State Coordinator)              │
├─────────────────────────────────────────────────────────────┤
│  - Workflow orchestration                                   │
│  - Signal routing                                           │
│  - State management                                         │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────────────────────┐
    │                                 │
    ▼                                 ▼
┌──────────────┐          ┌──────────────────────────┐
│ ScanEngine   │          │  Background Workers      │
├──────────────┤          ├──────────────────────────┤
│ - Scanner    │          │ - MatchWorker            │
│ - Signals    │          │ - PosterDownloadWorker   │
└──────┬───────┘          │ - SubtitleDownloadWorker │
       │                  │ - WorkerManager          │
       │                  └────────┬─────────────────┘
       │                           │
       ▼                           ▼
┌──────────────┐          ┌──────────────────────────┐
│ Data Models  │          │ Post-Processing          │
├──────────────┤          ├──────────────────────────┤
│ MediaType    │          │ - LibraryPostProcessor   │
│ VideoMetadata│          │ - Renamer                │
│ MediaMatch   │          │ - NFO Exporter           │
│ PosterInfo   │          │ - Poster Downloader      │
│ SubtitleInfo │          │ - Subtitle Downloader    │
└──────────────┘          └──────────────────────────┘
                                   │
                                   ▼
                          ┌──────────────────────────┐
                          │ Filesystem & Services    │
                          ├──────────────────────────┤
                          │ - Settings (JSON)        │
                          │ - Logging                │
                          │ - Service Registry       │
                          └──────────────────────────┘
```

## Core Modules

### 1. Data Models (`models.py`)

**Purpose:** Defines all data structures used throughout the application.

**Key Classes:**

| Class | Purpose |
|-------|---------|
| `MediaType` | Enum for MOVIE or TV |
| `MatchStatus` | Enum for match state (PENDING, MATCHED, MANUAL, SKIPPED) |
| `VideoMetadata` | Extracted file metadata |
| `MediaMatch` | Complete match info including external IDs |
| `PosterType`, `PosterSize`, `DownloadStatus` | Poster management |
| `SubtitleLanguage`, `SubtitleFormat`, `SubtitleInfo` | Subtitle support |
| `SearchRequest`, `SearchResult` | Manual search workflow |

**Design:** Data classes use `@dataclass` decorator for clean, type-safe structures.

### 2. Scanning Module (`scanner.py`, `scan_engine.py`)

**Purpose:** Discovers video files and parses metadata from filenames.

**Components:**

```
ScanConfig (Configuration)
    ↓
Scanner (File discovery + parsing)
    ├─ iter_video_files() → Path iterator
    └─ parse_video() → VideoMetadata
    ↓
ScanEngine (Qt signals + coordination)
    ├─ scan() → List[VideoMetadata]
    └─ Signals: scan_started, scan_progress, scan_completed, scan_error
```

**Regex Patterns Used:**

- Episode patterns: `S01E01`, `1x01` format
- Quality patterns: 720p, 1080p, BluRay, etc.
- Year detection: 4-digit years from 1900-2099
- Bracket removal: Cleans `[GROUP]`, `(release)` info

**Example Flow:**

```
/media/movies/Inception.2010.1080p.BluRay.mkv
    ↓ (parse)
VideoMetadata(
    title="Inception",
    year=2010,
    media_type=MediaType.MOVIE
)
    ↓ (enrichment callback)
MatchWorker starts matching
```

### 3. Matching System (`workers.py`, `match_manager.py`)

**Purpose:** Automatically and manually match videos to external databases.

**Components:**

```
MatchWorker (Background thread)
    ├─ Signals: match_found, match_failed, progress, finished
    └─ Creates mock MediaMatch objects

SearchWorker (Background thread)
    └─ Handles manual user searches

WorkerManager (Thread pool)
    ├─ Manages QThreadPool
    └─ Coordinates worker lifecycle
```

**Match Workflow:**

```
VideoMetadata (from scanner)
    ↓
MatchWorker.run()
    ├─ Simulate API lookup
    ├─ Extract basic info
    └─ Emit match_found signal
    ↓
MatchManager
    ├─ Update UI with results
    ├─ Calculate confidence score
    └─ Create MediaMatch object
    ↓
UI displays match for user review
```

### 4. Post-Processing (`library_postprocessor.py`, `renamer.py`)

**Purpose:** Organize and enhance media after matching.

**Components:**

| Component | Responsibility |
|-----------|-----------------|
| `LibraryPostProcessor` | Coordinates all post-processing |
| `RenamingEngine` | Generates standardized paths |
| `PosterDownloader` | Fetches and caches poster art |
| `SubtitleDownloader` | Searches and downloads subtitles |
| `NFOExporter` | Generates XML metadata files |

**Processing Pipeline:**

```
List[MediaMatch]
    ↓
LibraryPostProcessor.process()
    ├─ RenamingEngine: Generate target paths
    ├─ PosterDownloader: Fetch poster art (if enabled)
    ├─ SubtitleDownloader: Fetch subtitles (if enabled)
    ├─ NFOExporter: Generate NFO files (if enabled)
    └─ Filesystem operations
    ↓
PostProcessingSummary (success/error counts)
```

### 5. Settings Management (`settings.py`)

**Purpose:** Persistent configuration with JSON storage.

**Features:**

- JSON file at `~/.media-manager/settings.json`
- Fallback to QSettings for migration
- Specialized getters/setters for common settings
- Type-safe value access

**Settings Structure:**

```json
{
  "api_keys": {
    "tmdb": "...",
    "tvdb": "..."
  },
  "scan_paths": [...],
  "target_folders": {...},
  "poster_settings": {...},
  "subtitle_settings": {...},
  "nfo_settings": {...},
  "window_geometry": "...",
  "window_state": "..."
}
```

### 6. GUI Components

**Main Window (`main_window.py`):**

```
Main Window
├─ Menu Bar (File, Edit, View, Help)
├─ Central Widget
│  └─ Splitter (resizable panes)
│     ├─ Left: Navigation tree
│     ├─ Center: Tabbed content
│     │  ├─ Library view
│     │  ├─ Recent files
│     │  ├─ Matching tab
│     │  └─ Search results
│     └─ Right: Properties/preview
└─ Status Bar
```

**Matching UI Widgets:**

- `ScanQueueWidget`: Lists pending items, filtering, progress
- `MatchResolutionWidget`: Match details, confidence scores, manual search
- `PosterSettingsWidget`: Poster download preferences
- `MatchManager`: Coordinates workflow

### 7. Service Registry (`services.py`)

**Purpose:** Dependency injection container.

**Pattern:**

```python
registry = ServiceRegistry()
registry.register("SettingsManager", settings_instance)

# Later...
settings = registry.get("SettingsManager")

# Or with decorator
@inject("SettingsManager")
def my_function(settings):
    ...
```

**Services Registered:**

- SettingsManager
- ScanEngine
- MatchManager
- WorkerManager
- LibraryPostProcessor

### 8. Logging (`logging.py`)

**Purpose:** Structured logging with file and console output.

**Configuration:**

- Log level: DEBUG, INFO, WARNING, ERROR
- Output: File at `~/.media-manager/logs/app.log`
- Format: Timestamp, level, logger name, message

**Usage:**

```python
from media_manager.logging import get_logger

logger = get_logger().get_logger(__name__)
logger.info("Message")
logger.error("Error", exc_info=True)
```

## Data Flow

### Scan to Match to Process Flow

```
1. USER INITIATES SCAN
   ├─ Select directory
   └─ Start scan
        ↓
2. SCAN PHASE
   ├─ ScanEngine.scan(config)
   ├─ Scanner.iter_video_files() → file list
   ├─ For each file: Scanner.parse_video() → VideoMetadata
   ├─ Emit scan_progress signals
   └─ Emit enrichment_task_created for each file
        ↓
3. MATCH PHASE
   ├─ MatchManager receives enrichment_task_created
   ├─ MatchWorker.run() in background thread
   ├─ Create MediaMatch with mock/real data
   ├─ Emit match_found signal
   └─ ScanQueueWidget displays pending matches
        ↓
4. USER REVIEW
   ├─ User reviews matches in UI
   ├─ Accept auto-match → status = MATCHED
   ├─ Manual search → SearchWorker
   └─ Or skip → status = SKIPPED
        ↓
5. PROCESS PHASE (optional)
   ├─ LibraryPostProcessor.process()
   ├─ RenamingEngine: Generate paths
   ├─ PosterDownloader: Fetch artwork
   ├─ SubtitleDownloader: Fetch subtitles
   ├─ NFOExporter: Generate metadata
   └─ Emit PostProcessingSummary
```

### Signal Flow Diagram

```
ScanEngine                          Workers
  ├─ scan_started ──────────┐
  ├─ scan_progress ─────────┼──→ MatchManager
  ├─ enrichment_task_created┤
  └─ scan_completed ────────┘
                               │
                               ↓
                          MatchWorker
                               │
                               ├─ match_found ──────────┐
                               ├─ match_failed ────────┬┼──→ MatchManager
                               ├─ progress ────────────┘│
                               └─ finished ─────────────┘
                                    ↓
                          SearchWorker (manual)
                               │
                               └─ search_completed ──→ MatchManager
                                    ↓
                            UI Updates
                          (ScanQueueWidget,
                       MatchResolutionWidget)
```

## Design Patterns

### 1. Dependency Injection

Services are registered in a global registry and injected where needed:

```python
from media_manager.services import get_service_registry

registry = get_service_registry()
settings = registry.get("SettingsManager")
```

**Benefits:**
- Loose coupling
- Easy testing with mock services
- Clear dependencies

### 2. Observer Pattern (Qt Signals/Slots)

Qt signals implement the observer pattern for event-driven architecture:

```python
worker.signals.match_found.connect(on_match_found)
engine.scan_progress.connect(on_scan_progress)
```

**Benefits:**
- Non-blocking UI
- Loose coupling
- Type-safe connections

### 3. Strategy Pattern

Different processing strategies are encapsulated:

```python
# RenamingEngine strategy
processor.rename_media = True

# Poster download strategy
processor.download_posters = True

# Subtitle language strategy
options.subtitle_languages = ["en", "es"]
```

### 4. Factory Pattern

Workers are created by WorkerManager:

```python
manager = WorkerManager()
worker = manager.start_match_worker(metadata_list)
```

### 5. Dataclass Pattern

Immutable data structures with automatic `__init__` and `__repr__`:

```python
@dataclass
class VideoMetadata:
    path: Path
    title: str
    media_type: MediaType
```

**Benefits:**
- Concise, readable code
- Type hints
- JSON serialization

## Component Relationships

### Dependency Matrix

```
Component                   Depends On
─────────────────────────────────────────────────────────
MainWindow                  MatchManager, ScanQueueWidget,
                            MatchResolutionWidget, Settings

MatchManager                ScanEngine, WorkerManager,
                            LibraryPostProcessor

ScanEngine                  Scanner, Logging

MatchWorker                 VideoMetadata, Logging

LibraryPostProcessor        RenamingEngine, PosterDownloader,
                            SubtitleDownloader, NFOExporter,
                            Settings

PosterDownloader            DownloadStatus, Logging, Settings

SubtitleDownloader          SubtitleProvider, DownloadStatus,
                            Logging, Settings

NFOExporter                 MediaMatch, Settings

Settings                    JsonFile, Logging
```

## Threading Model

### Thread Safety

**Main Thread (GUI):**
- Runs Qt event loop
- Processes signals/slots
- Updates UI

**Worker Threads (ThreadPool):**
- MatchWorker: Performs matching
- PosterDownloadWorker: Downloads posters
- SubtitleDownloadWorker: Downloads subtitles
- SearchWorker: Performs searches

**Communication:**
- Workers emit Qt signals from background threads
- Main thread receives and processes signals
- Settings accessed from multiple threads (thread-safe)

**Example:**

```
Main Thread                 Worker Thread
─────────────────────────────────────────────
MainWindow
  ├─ start_matching()
  │  └─ thread_pool.start(worker)
  │                             │
  │                     worker.run()
  │                      (background)
  │                             │
  │                  worker.match_found.emit(data)
  │◄─── receive signal ─────────┘
  │
  └─ on_match_found(data)
     └─ update_ui()
```

### QThreadPool Configuration

```python
thread_pool = QThreadPool()
thread_pool.setMaxThreadCount(4)  # Configurable
thread_pool.start(worker)
```

## Settings and Configuration

### Configuration File Location

```
~/.media-manager/
├── settings.json          # Main settings
├── logs/
│  └── app.log             # Application logs
├── subtitle-cache/        # Downloaded subtitles
└── poster-cache/          # Downloaded posters
```

### Settings Schema

**Essential Settings:**

```python
{
  "api_keys": {
    "tmdb": str,
    "tvdb": str
  },
  "scan_paths": [Path],
  "target_folders": {
    "movies": Path,
    "tv_shows": Path
  }
}
```

**Optional Settings:**

```python
{
  "poster_settings": {
    "auto_download": bool,
    "cache_enabled": bool,
    "enabled_types": [str],
    "size_preference": str
  },
  "subtitle_settings": {
    "enabled_languages": [str],
    "auto_download": bool,
    "format": str,
    "cache_dir": Path
  },
  "nfo_settings": {
    "enabled": bool,
    "target_subfolder": str
  }
}
```

### Settings Access Pattern

```python
settings = get_settings()

# Direct access
tmdb_key = settings.get("api_keys.tmdb")

# Specialized getters
tmdb_key = settings.get_api_key("tmdb")
scan_paths = settings.get_scan_paths()

# Settings with defaults
debug = settings.get("debug_mode", False)

# Modifications
settings.set_api_key("tmdb", "new-key")
settings.save()
```

## Extensibility

### Adding New Features

#### 1. Add Data Model

```python
# In models.py
@dataclass
class NewFeature:
    """New feature data."""
    field1: str
    field2: int
```

#### 2. Add Background Worker

```python
# In workers.py
class NewFeatureWorker(QRunnable):
    def __init__(self, data):
        super().__init__()
        self.signals = NewFeatureSignals()
        
    def run(self):
        # Implementation
        pass
```

#### 3. Integrate with UI

```python
# In match_manager.py
def _create_new_feature_worker(self):
    worker = NewFeatureWorker(...)
    worker.signals.completed.connect(self.on_feature_completed)
    self.worker_manager.start_worker(worker)
```

#### 4. Add Settings

```python
# In settings.py
def get_new_feature_enabled(self) -> bool:
    return self.get("new_feature.enabled", False)

def set_new_feature_enabled(self, enabled: bool) -> None:
    self.set("new_feature.enabled", enabled)
```

### Adding API Integrations

**Current:** Mock data for TMDB/TVDB
**Future:** Real API integration

```python
# In subtitle_provider.py or new provider
class RealProvider(SubtitleProvider):
    def search(self, request: SearchRequest) -> List[SearchResult]:
        # Make HTTP request to real API
        response = requests.get(self.api_url, params={...})
        # Parse and return results
        return self._parse_response(response)
```

## Performance Considerations

### Optimization Strategies

1. **Filesystem Scanning:**
   - Use iterators to avoid loading all files in memory
   - Skip ignored directories early
   - Cache directory listings

2. **Matching:**
   - Batch API requests
   - Cache search results
   - Implement retry logic with exponential backoff

3. **UI Responsiveness:**
   - All I/O on background threads
   - Batch UI updates
   - Use Qt model-view architecture

4. **Memory Management:**
   - Clear caches periodically
   - Use weak references for callbacks
   - Clean up completed workers

### Scaling

- Configurable thread pool size
- Batch processing for large libraries
- Pagination in UI lists
- Cache management with size limits

## Security Considerations

1. **API Keys:**
   - Stored locally in settings.json
   - Never logged or exposed
   - User-configurable storage location

2. **File Permissions:**
   - Settings directory: 0700 (user only)
   - Downloaded files: Preserve media permissions
   - Cache: 0700 (user only)

3. **Input Validation:**
   - Paths validated before use
   - URLs validated before download
   - Filename sanitization for safety

4. **Error Handling:**
   - All exceptions logged with details
   - User-friendly error messages
   - Graceful degradation on failure

## Future Architecture Improvements

1. **Plugin System:**
   - Abstract provider interfaces
   - Dynamic provider loading
   - Custom post-processing plugins

2. **Database Backend:**
   - SQLite for library metadata
   - Faster searches
   - Offline availability

3. **Web Interface:**
   - Remote library management
   - REST API
   - Web dashboard

4. **Mobile Support:**
   - Cross-platform synchronization
   - Mobile client
   - Cloud storage integration
