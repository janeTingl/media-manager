# Subtitle Management System Implementation

## Overview

The subtitle management system provides comprehensive support for searching, downloading, and managing subtitles for movies and TV episodes. It integrates with subtitle provider APIs (with OpenSubtitles support) and includes intelligent caching, retry logic, and user preferences management.

## Architecture

### Core Components

#### 1. **Models** (`src/media_manager/models.py`)

New enums and dataclasses for subtitle management:

- **SubtitleLanguage**: Enum for supported languages
  - ENGLISH, SPANISH, FRENCH, GERMAN, ITALIAN, PORTUGUESE, RUSSIAN, CHINESE, JAPANESE, KOREAN

- **SubtitleFormat**: Enum for subtitle formats
  - SRT, ASS, SUB, VTT, SSA

- **SubtitleInfo**: Dataclass tracking subtitle download state
  - `language`: SubtitleLanguage
  - `format`: SubtitleFormat (default: SRT)
  - `url`: Optional download URL
  - `local_path`: Downloaded file location
  - `download_status`: DownloadStatus
  - `provider`: API provider name
  - `subtitle_id`: Provider's subtitle ID
  - Methods: `is_downloaded()`, `as_dict()`

- **MediaMatch**: Extended to include subtitles
  - `subtitles`: Dict[SubtitleLanguage, SubtitleInfo]

#### 2. **Subtitle Provider** (`src/media_manager/subtitle_provider.py`)

Abstract provider interface with concrete implementations:

- **SubtitleProvider** (Abstract Base Class)
  - `search()`: Search for subtitles by title, language, year, season, episode
  - `download()`: Download a subtitle file

- **SubtitleResult**: Data class for search results
  - Contains: ID, provider, language, format, URL, file size, FPS, release name, downloads, rating

- **MockSubtitleProvider**: For testing and development
  - Generates mock search results
  - Creates dummy subtitle files for testing

- **OpenSubtitlesProvider**: Integration with OpenSubtitles API
  - Currently returns mock results (structure ready for real API)
  - Supports API key authentication

#### 3. **Subtitle Downloader** (`src/media_manager/subtitle_downloader.py`)

Main service for subtitle operations:

**Initialization**:
```python
downloader = SubtitleDownloader(
    provider=CustomProvider(),      # Optional
    cache_dir=Path(...),           # Optional: defaults to ~/.media-manager/subtitle-cache
    max_retries=3,                 # Retry attempts
    retry_delay=1.0,               # Exponential backoff delay
    timeout=30.0                   # HTTP timeout in seconds
)
```

**Key Methods**:

- `search_subtitles()`: Search for available subtitles
  - Emits `search_started`, `search_completed`, or `search_failed` signals

- `get_subtitle_path()`: Generate standard subtitle filename
  - Format: `{media_stem}.{language_code}.srt`
  - Places next to media file or in cache if directory doesn't exist

- `download_subtitle()`: Download and cache subtitle
  - Checks if file already exists locally
  - Uses cache to avoid re-downloads
  - Implements retry logic with exponential backoff
  - Emits `download_completed` or `download_failed` signals

- `set_provider()`: Switch subtitle provider at runtime

- `clear_cache()`: Clear cached subtitle files

- `get_cache_size()`: Get total cache size in bytes

- `is_downloading()`: Check if subtitle is being downloaded

**Signals** (Qt):
- `download_progress`: (subtitle_id: str, current: int, total: int)
- `download_completed`: (subtitle_id: str, local_path: str)
- `download_failed`: (subtitle_id: str, error_message: str)
- `search_started`: (title: str)
- `search_completed`: (results: List[SubtitleResult])
- `search_failed`: (error_message: str)

#### 4. **Background Worker** (`src/media_manager/workers.py`)

New worker class for background operations:

- **SubtitleDownloadWorkerSignals**: Qt signals for worker events
- **SubtitleDownloadWorker**: Downloads multiple subtitles in background
  - Non-blocking UI operations
  - Progress tracking
  - Error handling and reporting

**Integration with WorkerManager**:
```python
worker_manager.start_subtitle_download_worker(
    matches=[match1, match2],
    languages=[SubtitleLanguage.ENGLISH, SubtitleLanguage.SPANISH]
)
```

#### 5. **Settings** (`src/media_manager/settings.py`)

Persistent subtitle preferences:

- `get_enabled_subtitle_languages()`: Get preferred languages (default: ["en"])
- `get_auto_download_subtitles()`: Auto-download setting (default: False)
- `get_subtitle_format()`: Preferred format (default: "srt")
- `get_subtitle_provider()`: Active provider (default: "OpenSubtitles")
- `get_subtitle_cache_dir()`: Cache directory location
- `get_subtitle_setting(key, default)`: Generic getter
- `set_subtitle_setting(key, value)`: Generic setter

Settings are stored in `~/.media-manager/settings.json` under `subtitle_settings` key.

## Usage Examples

### Basic Subtitle Search and Download

```python
from pathlib import Path
from src.media_manager.models import MediaType, SubtitleLanguage
from src.media_manager.subtitle_downloader import SubtitleDownloader
from src.media_manager.subtitle_provider import MockSubtitleProvider

# Initialize downloader
provider = MockSubtitleProvider()
downloader = SubtitleDownloader(provider=provider)

# Search for subtitles
results = downloader.search_subtitles(
    title="The Matrix",
    media_type=MediaType.MOVIE,
    language=SubtitleLanguage.ENGLISH,
    year=1999
)

# Download first result
if results:
    media_path = Path("/path/to/The_Matrix.mkv")
    subtitle_info = SubtitleInfo(
        language=SubtitleLanguage.ENGLISH,
        url=results[0].download_url
    )
    success = downloader.download_subtitle(
        subtitle_info,
        media_path,
        subtitle_result=results[0]
    )
    if success:
        print(f"Downloaded to: {subtitle_info.local_path}")
```

### Multiple Language Downloads

```python
from src.media_manager.models import SubtitleLanguage

languages = [
    SubtitleLanguage.ENGLISH,
    SubtitleLanguage.SPANISH,
    SubtitleLanguage.FRENCH
]

for language in languages:
    results = downloader.search_subtitles(
        title="Inception",
        media_type=MediaType.MOVIE,
        language=language,
        year=2010
    )
    
    if results:
        subtitle_info = SubtitleInfo(language=language, url=results[0].download_url)
        downloader.download_subtitle(subtitle_info, media_path, results[0])
```

### Using Background Worker

```python
from src.media_manager.workers import SubtitleDownloadWorker

worker = SubtitleDownloadWorker(matches, [SubtitleLanguage.ENGLISH])

# Connect signals
worker.signals.subtitle_downloaded.connect(on_subtitle_downloaded)
worker.signals.subtitle_failed.connect(on_subtitle_failed)
worker.signals.progress.connect(on_progress)

# Run in thread pool
thread_pool.start(worker)
```

### Working with MediaMatch

```python
from src.media_manager.models import MediaMatch, SubtitleInfo, SubtitleLanguage

# Create match with subtitles
subtitles = {
    SubtitleLanguage.ENGLISH: SubtitleInfo(language=SubtitleLanguage.ENGLISH),
    SubtitleLanguage.SPANISH: SubtitleInfo(language=SubtitleLanguage.SPANISH),
}

match = MediaMatch(metadata=metadata, subtitles=subtitles)

# Access subtitles
for language, subtitle_info in match.subtitles.items():
    print(f"{language.value}: {subtitle_info.local_path}")

# Serialize
match_dict = match.as_dict()  # Includes subtitles
```

## File Naming Convention

Subtitles are named using language code following the media file stem:

```
Movie Title (2023).mkv       → Movie Title (2023).en.srt (English)
                             → Movie Title (2023).es.srt (Spanish)
                             → Movie Title (2023).fr.srt (French)

TV Show/S01E01.mkv           → TV Show/S01E01.en.srt
                             → TV Show/S01E01.es.srt
```

Language codes follow ISO 639-1 standard (en, es, fr, de, it, pt, ru, zh, ja, ko).

## Caching System

### Cache Directory
- Default: `~/.media-manager/subtitle-cache`
- Customizable via `SettingsManager.set_subtitle_cache_dir()`

### Cache Key Generation
- URL-based MD5 hash for unique identification
- Prevents duplicate downloads of same subtitle
- File extension preserved from URL

### Cache Operations
```python
# Check cache size
size_bytes = downloader.get_cache_size()

# Clear all cached files
downloader.clear_cache()

# Cache is automatically checked before downloading
```

## Retry Logic

The downloader implements exponential backoff for failed downloads:

```python
max_retries = 3              # Total attempts = 4 (1 initial + 3 retries)
retry_delay = 1.0            # Base delay in seconds
# Actual delays: 0s, 1s, 2s, 3s
```

Failed downloads trigger:
1. Warning log entry
2. `subtitle_info.error_message` set
3. `download_failed` signal emitted after all retries exhausted

## Testing

Comprehensive test suite with 44 tests:

### Test Files
- `tests/test_subtitle_provider.py`: Provider interface and implementations
- `tests/test_subtitle_downloader.py`: Downloader core functionality
- `tests/test_subtitle_integration.py`: End-to-end workflows

### Test Coverage
- Provider search and download
- Multiple language support
- Cache behavior and clearing
- Retry logic and error handling
- MediaMatch integration
- Worker background operations
- Subtitle serialization
- TV episode and movie support

### Running Tests
```bash
pytest tests/test_subtitle_*.py -v
```

All tests use mocked providers to avoid external dependencies.

## Integration with Existing Systems

### Match Manager Integration
The matching system can populate subtitle recommendations:

```python
# In MatchWorker._create_mock_match()
subtitles = self._create_mock_subtitles(metadata)
match = MediaMatch(..., subtitles=subtitles)
```

### Settings Integration
Subtitle preferences persist across sessions:

```python
from src.media_manager.settings import get_settings

settings = get_settings()
languages = settings.get_enabled_subtitle_languages()  # ["en", "es"]
auto_download = settings.get_auto_download_subtitles()  # False
```

### Worker Manager Integration
```python
worker = worker_manager.start_subtitle_download_worker(
    matches=[match1, match2],
    languages=[SubtitleLanguage.ENGLISH, SubtitleLanguage.SPANISH]
)
```

## Provider Implementation Guide

To add a new subtitle provider:

```python
from src.media_manager.subtitle_provider import SubtitleProvider, SubtitleResult

class CustomProvider(SubtitleProvider):
    def search(self, title, media_type, language, year=None, season=None, episode=None):
        # Implement search logic
        results = [
            SubtitleResult(
                subtitle_id="...",
                provider="CustomProvider",
                language=language,
                format=SubtitleFormat.SRT,
                download_url="https://...",
                file_size=50000,
                fps=23.976,
                release_name="...",
                downloads=100,
                rating=4.5
            )
        ]
        return results
    
    def download(self, subtitle_result, output_path):
        # Implement download logic
        # Write file to output_path
        return success
```

## Future Enhancements

1. **Real OpenSubtitles API Integration**
   - Use actual OpenSubtitles API with authentication
   - Support hash-based search for accuracy

2. **Additional Providers**
   - Subscene integration
   - Subtitle database support
   - Custom provider plugins

3. **Advanced Features**
   - Automatic language detection
   - Subtitle format conversion
   - Quality scoring and rating
   - Sync offset detection and fixing

4. **UI Components**
   - Subtitle management widget
   - Provider settings interface
   - Download progress visualization
   - Language preference selector

5. **Import Functionality**
   - Manual subtitle file import
   - Automatic association with media
   - Batch import support

## Dependencies

- PySide6: For Qt signals and threading
- Python 3.8+: Core language features
- Standard library: pathlib, urllib, hashlib, json

No external API libraries required - implementation uses standard urllib for HTTP requests.

## Performance Considerations

- **Caching**: Avoids redundant downloads, speeds up repeated operations
- **Retry Logic**: Configurable delays prevent overwhelming servers
- **Threading**: Background workers keep UI responsive
- **Signals**: Qt signal/slot system minimizes blocking operations
- **Timeout**: Configurable HTTP timeout prevents hanging

## Error Handling

The system handles:
- Network errors (retried)
- File system errors (graceful fallback to cache)
- Invalid URLs (immediate failure)
- Timeout errors (retried with backoff)
- Missing directories (automatic creation)
- Corrupted cache files (re-downloaded)

All errors are logged and reported via signals.
