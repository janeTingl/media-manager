# Poster Downloading Implementation

This document summarizes the poster downloading functionality implemented for the media manager application.

## Overview

The poster downloading system provides comprehensive artwork management with caching, size selection, and retry logic. It integrates seamlessly with the existing matching workflow and offers user-configurable preferences.

## Key Components

### 1. Enhanced Models (`src/media_manager/models.py`)

**New Enums:**
- `PosterType`: POSTER, FANART, BANNER, THUMBNAIL
- `PosterSize`: SMALL, MEDIUM, LARGE, ORIGINAL  
- `DownloadStatus`: PENDING, DOWNLOADING, COMPLETED, FAILED, SKIPPED

**New Data Classes:**
- `PosterInfo`: Tracks download state, URLs, local paths, file sizes, error messages, and retry counts
- Extended `MediaMatch`: Includes `posters` dictionary mapping PosterType to PosterInfo
- Extended `SearchResult`: Includes `poster_urls` dictionary for multiple poster types

### 2. Poster Downloader (`src/media_manager/poster_downloader.py`)

**Core Features:**
- Downloads posters from URLs with configurable timeouts
- Intelligent caching using MD5 hash-based deduplication
- Size selection support (small, medium, large, original)
- Standardized filename generation next to media files
- Retry logic with exponential backoff
- Progress tracking via Qt signals
- Cache management with size calculation and clearing

**Key Methods:**
- `get_poster_path()`: Generates standardized local paths
- `download_poster()`: Main download method with retry logic
- `_get_cached_path()`: Cache path generation
- `clear_cache()`: Cache cleanup functionality
- `get_cache_size()`: Cache size calculation

### 3. Background Worker (`src/media_manager/workers.py`)

**PosterDownloadWorker:**
- Handles poster downloads in background threads
- Progress tracking across multiple downloads
- Error handling with retry counting
- Integration with WorkerManager for thread pool management

**Signals:**
- `poster_downloaded`: Emitted on successful download
- `poster_failed`: Emitted on download failure
- `progress`: Emitted for progress updates
- `finished`: Emitted when all downloads complete

### 4. Settings Integration (`src/media_manager/settings.py`)

**New Settings Methods:**
- `get/set_auto_download_posters()`: Automatic download preference
- `get/set_enabled_poster_types()`: Types to download
- `get/set_poster_size()`: Size preference per type
- `get/set_max_retries()`: Retry configuration
- `get/set_cache_dir()`: Cache directory location

### 5. UI Integration

#### Match Resolution Widget (`src/media_manager/match_resolution_widget.py`)
**New Features:**
- Poster preview display with aspect ratio preservation
- Download buttons for each poster type
- Status indicators and progress feedback
- Integration with existing match workflow

**New UI Elements:**
- Poster preview label (150x225px)
- Download buttons for poster and fanart
- Status label showing download state
- Image loading with error handling

#### Settings Widget (`src/media_manager/poster_settings_widget.py`)
**Comprehensive UI:**
- Poster type selection (poster, fanart, banner)
- Size preferences per poster type
- Cache directory selection and management
- Download settings (auto-download, retries, timeout)
- Clear cache functionality

#### Main Window (`src/media_manager/main_window.py`)
**Integration:**
- Preferences dialog with poster settings tab
- Signal routing for poster download requests
- Status updates and progress feedback

### 6. Testing

#### Unit Tests (`tests/test_poster_downloader.py`)
**Coverage:**
- Poster downloader initialization
- Path generation for different media types
- Download success and failure scenarios
- Caching functionality
- Retry logic with max retry handling
- Cache management operations
- URL hashing consistency

#### Integration Tests (`tests/test_poster_integration.py`)
**Workflow Testing:**
- Complete poster download workflow
- Multiple poster types for single match
- Caching behavior verification
- Retry functionality
- Progress tracking
- Error handling

#### Settings Tests (`tests/test_poster_settings.py`)
**UI Testing:**
- Settings loading and saving
- Widget interaction testing
- Dialog functionality
- Cache clearing with user confirmation

## Workflow

### User Experience

1. **Matching Phase**: Media is scanned and matched, poster URLs identified
2. **Configuration Phase**: User preferences checked (auto-download, types, sizes)
3. **Download Phase**: Posters downloaded in background with progress feedback
4. **Caching Phase**: Existing downloads detected and reused
5. **Integration Phase**: Local paths linked to media metadata
6. **Display Phase**: Posters shown in match resolution UI

### Technical Features

- **Thread Safety**: All downloads run in background threads
- **Memory Efficiency**: Intelligent caching prevents duplicate downloads
- **Error Resilience**: Comprehensive retry logic with exponential backoff
- **User Control**: Granular preferences for types and sizes
- **Progress Feedback**: Real-time status updates
- **Standardization**: Consistent filename patterns across media types

### File Organization

Posters are saved with standardized naming:
- Movies: `MovieName (Year)-poster.jpg`
- TV Episodes: `S01E01-poster.jpg`
- Fanart: `MovieName (Year)-fanart.jpg`

## Usage

### For Users

1. Configure preferences via Edit → Preferences → Posters tab
2. Enable desired poster types and sizes
3. Set cache directory if needed
4. Choose auto-download or manual download per item
5. Monitor progress in status bar
6. View downloaded posters in match resolution

### For Developers

```python
# Download posters for a match
from media_manager.models import PosterType
from media_manager.workers import PosterDownloadWorker

worker = PosterDownloadWorker([match], [PosterType.POSTER])
worker.signals.poster_downloaded.connect(on_download_complete)
worker.signals.progress.connect(on_progress)
```

## Configuration

### Default Settings
- Auto-download: Enabled
- Enabled types: Poster only
- Default sizes: Medium
- Max retries: 3
- Timeout: 30 seconds
- Cache directory: `~/.media-manager/poster-cache`

### Environment Variables
No specific environment variables required. All configuration managed through UI settings.

## Future Enhancements

### Potential Improvements
1. **Provider Integration**: Real TMDB/TVDB API integration
2. **Image Processing**: Automatic image optimization and resizing
3. **Batch Operations**: Bulk download management
4. **Quality Selection**: User preference for image quality
5. **Metadata Embedding**: Embed poster info in media files
6. **Cloud Storage**: Support for cloud-based poster storage
7. **API Rate Limiting**: Respect provider rate limits
8. **Preview Generation**: Generate thumbnails for faster UI loading

### Scalability Considerations
- Current implementation handles thousands of downloads efficiently
- Cache prevents redundant network requests
- Thread pool manages concurrent downloads
- Memory usage optimized for large media libraries

## Conclusion

The poster downloading system provides a robust, user-friendly solution for managing media artwork. It integrates seamlessly with the existing matching workflow while offering comprehensive configuration options and reliable performance through intelligent caching and retry mechanisms.

The implementation follows established patterns in the codebase and maintains consistency with existing UI components and data models.