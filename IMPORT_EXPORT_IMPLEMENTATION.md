# Import/Export Implementation Summary

This document summarizes the implementation of the data portability feature.

## Overview

The import/export feature provides comprehensive data portability for 影藏·媒体管理器, allowing users to backup, restore, migrate, and share their media library metadata.

## Components Implemented

### 1. Core Service (`import_export_service.py`)

**Key Features:**
- Export to JSON and Excel (XLSX) formats
- Import from JSON and Excel formats
- Configurable field inclusion (files, external IDs, artwork, subtitles)
- Flexible filtering (by library, media type, date range)
- Three merge strategies for imports:
  - Skip: Ignore existing items
  - Replace: Delete and recreate existing items
  - Update: Update existing items with new data
- Conflict detection and preview
- Validation (required fields, library existence, file paths)
- History event logging for all import operations

**Classes:**
- `ImportExportService`: Main service class
- `ExportOptions`: Configuration for exports
- `ImportOptions`: Configuration for imports
- `ImportResult`: Results and statistics from imports
- `ImportConflict`: Represents detected conflicts
- `ExportFormat`: Enum for JSON/Excel formats
- `MergeStrategy`: Enum for conflict resolution strategies

### 2. UI Wizards (`import_export_wizard.py`)

**Export Wizard:**
- Page 1: Choose format (JSON/Excel) and destination file
- Page 2: Select scope (libraries, media types, date range)
- Page 3: Choose fields to include
- Page 4: Progress display with real-time status

**Import Wizard:**
- Page 1: Select source file with preview
- Page 2: Map columns (for Excel imports)
- Page 3: Detect and review conflicts
- Page 4: Configure import options (library, merge strategy, validation)
- Page 5: Progress display with results

### 3. Menu Integration

Added to main window Edit menu:
- Export Media (Ctrl+E)
- Import Media (Ctrl+I)

Both actions open their respective wizards.

### 4. Comprehensive Tests (`test_import_export.py`)

**Test Coverage:**
- JSON export (basic, filtered by library, filtered by media type)
- Excel export (basic, column auto-sizing)
- JSON import (basic, with conflicts)
- Excel import (basic, with column mapping)
- Round-trip testing (export then re-import)
- Error handling (missing fields, invalid formats, non-existent libraries)
- Conflict detection and preview
- All merge strategies (skip, replace, update)

**Test Results:** 17 tests, all passing ✓

### 5. Documentation

**User Guide (`IMPORT_EXPORT_GUIDE.md`):**
- Complete usage instructions
- File format specifications
- Export/import workflows
- Merge strategy explanations
- Best practices
- Troubleshooting tips
- Use cases (backup/restore, migration, bulk editing, sharing)
- Advanced usage (scripting, custom mappings, partial imports)

## File Formats

### JSON Format

Structured format with metadata version and timestamp:

```json
{
  "version": "1.0",
  "exported_at": "2024-01-15T10:30:00",
  "items": [
    {
      "id": 1,
      "title": "The Matrix",
      "media_type": "movie",
      "year": 1999,
      "files": [...],
      "external_ids": [...],
      "artworks": [...],
      "subtitles": [...]
    }
  ]
}
```

### Excel Format

Spreadsheet with headers and data rows:
- Core fields: ID, Library, Title, Media Type, Year, Season, Episode, etc.
- Optional fields: File Paths, External IDs, Artwork Paths, Subtitle Paths
- Auto-sized columns for readability
- Header row with bold styling

## Technical Implementation

### Database Integration

- Uses `transactional_context()` for atomic operations
- Properly handles SQLAlchemy sessions to avoid detached instance errors
- Eager loading of relationships using `selectinload()`
- Foreign key constraint handling for deletes

### Validation

- Required field validation (title, media_type)
- Library existence verification
- Optional file path validation
- Duplicate detection (by ID and by title/year)
- Data type validation (integers, floats)

### History Logging

- Creates `HistoryEvent` records for imports
- Event types: "imported" (new items), "imported_update" (updated items)
- Stores source information (file, row number) in event data
- Can be disabled via import options

### Error Handling

- Graceful handling of missing/invalid data
- Detailed error messages in import results
- Transaction rollback on failures
- Progress reporting during long operations

## Dependencies Added

- `openpyxl>=3.1.0` - Excel file handling

## Usage Examples

### Export All Movies to Excel

```python
from import_export_service import ImportExportService, ExportOptions, ExportFormat

service = ImportExportService()
options = ExportOptions(
    format=ExportFormat.EXCEL,
    media_types=["movie"],
    include_files=True,
    include_external_ids=True,
)
service.export_to_file(Path("movies.xlsx"), options)
```

### Import with Conflict Detection

```python
from import_export_service import ImportExportService, ImportOptions, MergeStrategy

service = ImportExportService()

# Preview first
data, conflicts = service.preview_import(Path("import.json"))
print(f"Found {len(conflicts)} conflicts")

# Import with skip strategy
options = ImportOptions(
    merge_strategy=MergeStrategy.SKIP,
    target_library_id=1,
    validate_files=False,
)
result = service.import_from_file(Path("import.json"), options)
print(result.to_message())
```

## Future Enhancements

Potential improvements for future versions:

1. **Incremental Exports**: Export only items modified since last export
2. **Compression**: Support for compressed export files (.zip, .gz)
3. **Cloud Integration**: Direct export/import to cloud storage
4. **Advanced Filtering**: More sophisticated query options
5. **CSV Format**: Add CSV support for simpler use cases
6. **Batch Processing**: Split large exports into multiple files
7. **Scheduling**: Automated periodic exports
8. **Merge Conflicts UI**: Interactive conflict resolution wizard

## Related Features

- **Batch Operations**: Complement to import/export for bulk operations
- **NFO Exporter**: Individual item export in Kodi format
- **Library Management**: Multi-library support enhances portability
- **Search**: Save and export search results

## Compliance and Standards

- Follows existing codebase patterns and conventions
- Uses established persistence layer and repositories
- Integrates with existing settings and service registry
- Maintains consistency with UI/UX patterns
- Comprehensive error handling and logging

## Testing Strategy

Tests cover:
- Normal operation (happy path)
- Error conditions (missing data, invalid formats)
- Edge cases (empty exports, duplicate data)
- Round-trip integrity (export then re-import)
- All export formats and import strategies
- Performance (through progress callbacks)

## Conclusion

The import/export feature provides a robust, user-friendly solution for data portability in 影藏·媒体管理器. It supports multiple formats, handles conflicts intelligently, validates data thoroughly, and integrates seamlessly with the existing application architecture.
