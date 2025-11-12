# Metadata Editor Implementation

## Overview

This document describes the implementation of the rich metadata editor widget for the Media Manager application. The metadata editor provides a comprehensive UI for editing media item information with full database persistence, validation, and signal integration.

## Components

### 1. MetadataEditorWidget (`src/media_manager/metadata_editor_widget.py`)

A rich tabbed interface for editing media item metadata with the following features:

#### UI Tabs

1. **General Info Tab**
   - Title (required, max 255 chars)
   - Original Title
   - Year (1800-2100)
   - Runtime (0-1000 minutes)
   - Plot/Description (multi-line text)

2. **Episodic Tab**
   - Season (0-100)
   - Episode (0-1000)
   - Aired Date (YYYY-MM-DD format)

3. **Ratings Tab**
   - Rating (0-100 scale)

4. **Genres & Keywords Tab**
   - Genres (comma-separated input)
   - Keywords (one per line)

5. **Collections & Tags Tab**
   - Collections (table with add/remove)
   - Tags (comma-separated input)

6. **Cast & Crew Tab**
   - Cast table (Name, Character, Remove)
   - Crew table (Name, Role, Remove)

#### Core Features

- **Dirty Tracking**: Automatically detects when fields change
- **Form Validation**: Prevents invalid data with clear error messages
- **Undo/Cancel**: Reset button discards all unsaved changes
- **Database Persistence**: Changes saved to SQLite via repository pattern
- **Signal Integration**: Emits signals for cross-component communication
- **Quick Actions**: 
  - Open in TMDB (uses external TMDB ID)
  - Refresh metadata (placeholder for future provider integration)

#### Signals

- `match_updated`: Emitted when metadata is saved
- `save_requested`: Emitted when save completes
- `validation_error`: Emitted when validation fails

### 2. MetadataValidator (`src/media_manager/metadata_validator.py`)

Comprehensive validation logic for all metadata fields:

#### Validation Methods

- `validate(data)`: Batch validate metadata dictionary
- `validate_title(title)`: Validate title (required, max 255 chars)
- `validate_year(year)`: Validate year range (1800-2100)
- `validate_runtime(runtime)`: Validate runtime (0-1000 minutes)
- `validate_date(date_str)`: Validate date format (YYYY-MM-DD)

#### Error Handling

- Returns descriptive error messages
- Supports batch and single-field validation
- Validates boundary values and data types

### 3. MainWindow Integration

The MetadataEditorWidget is integrated into the MainWindow's right pane:

```python
# In _create_properties_pane()
layout.addWidget(self.metadata_editor_widget)

# In _connect_signals()
self.metadata_editor_widget.match_updated.connect(self.match_manager.update_match)
self.metadata_editor_widget.validation_error.connect(self.update_status)
```

## Database Integration

The metadata editor uses the repository pattern for database operations:

```python
# Saves use transactional_context() for atomicity
with transactional_context() as uow:
    media_repo = uow.get_repository(MediaItem)
    media_repo.update(self._current_media_item)
    uow.commit()
```

### Supported Operations

- Update MediaItem fields (title, year, runtime, description, etc.)
- Manage Cast/Crew relationships
- Manage Collections and Tags
- Create HistoryEvent records on save

## Validation Rules

### Required Fields

- Title: Must be non-empty, max 255 characters

### Numeric Ranges

- Year: 1800-2100
- Runtime: 0-1000 minutes
- Season: 0-100
- Episode: 0-1000
- Rating: 0-100

### Date Format

- Aired date: Must be YYYY-MM-DD format

## Signal Flow

```
1. User selects media item
   ↓ set_media_item() loads form with data
   
2. User edits field
   ↓ _on_field_changed() sets dirty flag
   ↓ Save/Reset buttons enabled
   
3. User clicks Save
   ↓ _validate_form() checks constraints
   ↓ If invalid: validation_error signal emitted
   ↓ If valid: _update_media_item_from_form()
   
4. _save_to_database() persists changes
   ↓ match_updated signal emitted
   ↓ save_requested signal emitted
   ↓ match_manager.update_match() processes update
   
5. Status bar updated with confirmation
```

## Usage Example

```python
from media_manager.metadata_editor_widget import MetadataEditorWidget
from media_manager.persistence.models import MediaItem

# Create editor widget
editor = MetadataEditorWidget()

# Load a media item
editor.set_media_item(media_item)

# User edits fields in UI...

# Save is triggered by user clicking Save button
# Or programmatically:
editor._on_save_clicked()

# Listen to updates
editor.match_updated.connect(on_match_updated)
editor.validation_error.connect(on_validation_error)
```

## Testing

### Test Files

1. **test_metadata_validator.py** (19 tests)
   - Field validation tests
   - Boundary value testing
   - Error message generation
   - Single and batch validation

2. **test_metadata_editor.py** (Requires Qt GUI)
   - Widget initialization
   - Form loading and clearing
   - Dirty flag tracking
   - Field change detection
   - Signal emission

3. **test_metadata_editor_integration.py** (Requires Qt GUI)
   - End-to-end workflows
   - Database persistence
   - Signal flow testing
   - Multi-item switching

### Running Tests

```bash
# Validator tests (run without Qt)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_metadata_validator.py -v

# All tests (with Qt environment)
python -m pytest tests/test_metadata* -v
```

## Architecture

The metadata editor follows these design patterns:

1. **MVC Pattern**: Model (MediaItem) → View (MetadataEditorWidget) → Controller (Business Logic)
2. **Repository Pattern**: Database access via generic Repository[T]
3. **Signal/Slot Pattern**: Loose coupling via Qt signals
4. **Validation Pattern**: Separate validator class for testability
5. **UnitOfWork Pattern**: Atomic database transactions

## Error Handling

- Validation errors prevent invalid data
- Database errors caught and logged
- User-friendly error messages in dialogs
- Rollback on transaction failure

## Performance Considerations

- Lazy loading of related data (cast, crew, collections, tags)
- Efficient form updates
- Transactional database operations
- Minimal signal emissions

## Future Enhancements

1. **Provider Integration**
   - Implement actual Refresh functionality to fetch from TMDB/TVDB
   - Auto-populate fields from provider data

2. **Advanced Editing**
   - Bulk edit multiple items
   - Copy/paste metadata between items
   - Undo/redo history for multiple changes

3. **Image Editing**
   - Crop/select alternate poster images
   - Manage multiple artwork types

4. **Search Integration**
   - Quick search to update metadata from current match
   - Suggest corrections based on filename

## Notes

- All datetime fields use UTC with default_factory
- Relationships use forward references for circular dependencies
- Use `session.exec(select(...))` pattern (SQLModel best practice)
- Always use transactional_context() for atomic operations
- Dirty flag prevents accidental unsaved changes
