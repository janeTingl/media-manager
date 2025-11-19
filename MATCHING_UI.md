# Matching UI Implementation

This document describes the matching UI implementation for the 影藏·媒体管理器 application.

## Overview

The matching UI provides a comprehensive workflow for scanning media files and resolving matches with external databases. It consists of several key components:

## Components

### 1. Enhanced Data Models (`models.py`)

- **MatchStatus**: Enum for tracking match status (PENDING, MATCHED, MANUAL, SKIPPED)
- **MediaMatch**: Dataclass containing metadata, match information, confidence scores
- **SearchRequest**: Dataclass for manual search requests
- **SearchResult**: Dataclass for search results with confidence scores

### 2. Background Workers (`workers.py`)

- **MatchWorker**: Performs automatic matching in background threads
- **SearchWorker**: Performs manual searches in background threads
- **WorkerManager**: Manages thread pools and worker lifecycle
- Uses mock data for demonstration (would integrate with real APIs like TMDB)

### 3. UI Components

#### ScanQueueWidget (`scan_queue_widget.py`)
- Lists pending media items with status indicators
- Provides filtering by title
- Shows progress during matching operations
- Color-coded status indicators (⏳ pending, ✓ matched, 🔧 manual, ⊘ skipped)

#### MatchResolutionWidget (`match_resolution_widget.py`)
- Displays detailed match information
- Shows confidence scores with color coding
- Provides manual search functionality
- Action buttons for accept/skip/manual search

#### MatchManager (`match_manager.py`)
- Coordinates the matching workflow
- Manages state and signals between components
- Integrates with the service registry

### 4. Integration

#### Main Window Integration (`main_window.py`)
- New "Matching" tab in the main interface
- Integrated with existing scan engine
- Connects all components via signals/slots

#### Demo Integration (`demo_integration.py`)
- Complete demo application showcasing the workflow
- Menu commands for demo scanning and instructions
- Mock integration with external APIs

## Features

### 1. Scan Queue Management
- Display pending media items with parsed metadata
- Filter items by title
- Show matching progress with progress bar
- Start/stop/clear operations

### 2. Match Resolution
- Review detailed match information
- Confidence score display with visual indicators
- Manual search override functionality
- Accept, skip, or manually match items

### 3. Background Processing
- Non-blocking UI operations
- Progress indicators and status messages
- Thread-safe operations using Qt signals
- Proper worker cleanup

### 4. User Experience
- Intuitive workflow from scan to match
- Clear visual feedback
- Keyboard shortcuts and accessibility
- Persistent user selections

## Usage

### Basic Workflow
1. Scan a directory for media files
2. View results in the "Matching" tab
3. Click "Start Matching" to find automatic matches
4. Review matches with confidence scores
5. Accept good matches or use manual search
6. Skip items that don't need matching

### Manual Search
1. Select an item from the queue
2. Click "Manual Search" or edit the search field
3. Review search results with confidence scores
4. Apply the desired result

## Testing

### Integration Tests (`tests/test_match_integration.py`)
- Complete scan-to-match workflow tests
- Signal flow verification
- UI component integration tests
- Error handling and edge cases
- Filtering functionality tests

### Running Tests
```bash
# Install dependencies
pip install -e ".[dev]"

# Run integration tests (requires X11 display)
pytest tests/test_match_integration.py -v
```

## Architecture

### Signal/Slot Communication
- All UI components use Qt signals/slots for communication
- Loose coupling between components
- Thread-safe operations

### Service Registry Integration
- WorkerManager registered as a service
- Dependency injection pattern
- Centralized service management

### Model-View-Controller Pattern
- Models: Data structures and business logic
- Views: UI components
- Controllers: MatchManager and signal coordination

## Future Enhancements

### Real API Integration
- Replace mock data with real TMDB/TVDB APIs
- API key management
- Rate limiting and error handling

### Enhanced UI
- Poster image display
- Multiple selection support
- Batch operations
- Advanced filtering options

### Performance
- Caching of search results
- Optimized threading
- Memory management for large libraries

## Technical Notes

### Threading
- Uses QThreadPool for worker management
- Proper signal/slot thread safety
- Worker lifecycle management

### Error Handling
- Comprehensive exception handling
- User-friendly error messages
- Graceful degradation

### Memory Management
- Efficient data structures
- Proper cleanup of resources
- No memory leaks in worker threads