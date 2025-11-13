# Import/Export Guide

This guide describes how to use the import and export functionality in Media Manager to achieve data portability.

## Overview

The Import/Export feature allows you to:

- **Export** media metadata to JSON or Excel formats
- **Import** media metadata from JSON or Excel files
- Handle conflicts during import with various merge strategies
- Include/exclude specific data fields (files, artwork, subtitles, etc.)
- Validate data before importing
- Track import/export operations in history logs

## Export Media Metadata

### Starting an Export

1. Open Media Manager
2. Go to **Edit** → **Export Media...** (or press `Ctrl+E`)
3. Follow the Export Wizard steps

### Export Wizard Steps

#### Step 1: Export Format

Choose the export format:

- **JSON**: Human-readable text format, good for version control and scripting
- **Excel (XLSX)**: Spreadsheet format, easy to view and edit in Excel/LibreOffice

Select the destination file where the export will be saved.

#### Step 2: Export Scope

Select which media items to export:

- **Libraries**: Choose specific libraries or all libraries
- **Media Types**: Filter by Movies, TV Shows, or both
- **Date Range**: Filter by creation/update date (optional)

#### Step 3: Export Fields

Choose which data to include in the export:

- **File Paths**: Include paths to media files
- **External IDs**: Include TMDB, IMDB, TVDB IDs
- **Artwork Paths**: Include paths to downloaded posters and artwork
- **Subtitle Paths**: Include paths to downloaded subtitle files

#### Step 4: Export Progress

The wizard will show progress as it exports your data. When complete, you can view the results and access the exported file.

### Export File Formats

#### JSON Format

```json
{
  "version": "1.0",
  "exported_at": "2024-01-15T10:30:00",
  "items": [
    {
      "id": 1,
      "library_id": 1,
      "library_name": "Movies",
      "title": "The Matrix",
      "media_type": "movie",
      "year": 1999,
      "description": "A computer hacker learns...",
      "genres": "Action, Sci-Fi",
      "runtime": 136,
      "rating": 8.7,
      "files": [
        {
          "path": "/movies/The Matrix (1999)/The Matrix.mkv",
          "filename": "The Matrix.mkv",
          "file_size": 2147483648,
          "container": "mkv",
          "video_codec": "h264",
          "audio_codec": "aac",
          "resolution": "1920x1080"
        }
      ],
      "external_ids": [
        {"source": "tmdb", "external_id": "603"},
        {"source": "imdb", "external_id": "tt0133093"}
      ],
      "artworks": [
        {
          "artwork_type": "poster",
          "url": "https://...",
          "local_path": "/posters/matrix_poster.jpg",
          "size": "large",
          "download_status": "completed"
        }
      ],
      "subtitles": [
        {
          "language": "en",
          "format": "srt",
          "local_path": "/movies/The Matrix (1999)/The Matrix.en.srt",
          "provider": "opensubtitles",
          "download_status": "completed"
        }
      ]
    }
  ]
}
```

#### Excel Format

The Excel export creates a spreadsheet with the following columns:

| Column | Description |
|--------|-------------|
| ID | Internal database ID |
| Library | Library name |
| Title | Media title |
| Media Type | "movie" or "tv" |
| Year | Release year |
| Season | Season number (TV only) |
| Episode | Episode number (TV only) |
| Description | Plot summary |
| Genres | Comma-separated genres |
| Runtime | Duration in minutes |
| Aired Date | Original air date |
| Rating | Rating (0-10) |
| Created At | When added to library |
| Updated At | Last update time |
| File Paths | Semicolon-separated file paths |
| File Count | Number of files |
| TMDB ID | The Movie Database ID |
| IMDB ID | Internet Movie Database ID |
| TVDB ID | The TV Database ID |
| Poster Path | Path to poster artwork |
| Fanart Path | Path to fanart artwork |
| Artwork Count | Number of artwork files |
| Subtitle Paths | Semicolon-separated subtitle paths |
| Subtitle Count | Number of subtitle files |

## Import Media Metadata

### Starting an Import

1. Open Media Manager
2. Go to **Edit** → **Import Media...** (or press `Ctrl+I`)
3. Follow the Import Wizard steps

### Import Wizard Steps

#### Step 1: Import File

Choose the file to import:

- Supported formats: JSON (`.json`), Excel (`.xlsx`, `.xls`)
- The wizard will show a preview of the file contents

#### Step 2: Column Mapping (Excel only)

For Excel imports, map the columns from your file to the expected database fields:

- The wizard will auto-detect common column names
- You can manually map columns or skip unwanted columns
- Required fields: `title`, `media_type`

#### Step 3: Conflict Detection

The wizard will analyze the import data and detect potential conflicts:

- **Duplicate ID**: Item with same ID already exists
- **Duplicate Title**: Item with same title and year already exists
- **Missing Title**: Required field is missing
- **Missing Library**: Target library doesn't exist

Review the conflicts before proceeding.

#### Step 4: Import Options

Configure how to handle the import:

**Target Library**: Choose which library to import items into

**Conflict Resolution**:
- **Skip existing items**: Don't import items that already exist
- **Replace existing items**: Delete and recreate existing items
- **Update existing items**: Update existing items with new data

**Additional Options**:
- **Validate file paths exist**: Check that referenced files actually exist
- **Create history events**: Log the import operation in history

#### Step 5: Import Progress

The wizard will show progress as it imports your data. When complete, you can view the results including:

- Number of items imported
- Number of items updated
- Number of items skipped
- Any errors that occurred

### Import Best Practices

1. **Always preview first**: Review conflicts before importing
2. **Backup your database**: Make a backup before large imports
3. **Use skip strategy**: For initial imports, use "skip" to avoid duplicates
4. **Validate paths**: Enable file validation to catch missing files
5. **Check results**: Review the import results for any errors

## Use Cases

### Backup and Restore

1. Export all libraries to JSON format
2. Store the JSON file in a safe location
3. To restore, import the JSON file with "skip" strategy

### Migrate Between Installations

1. Export from the old installation
2. Copy media files to the new location
3. Import into the new installation
4. Update file paths if necessary

### Bulk Edit in Excel

1. Export to Excel format
2. Open in Excel/LibreOffice
3. Edit metadata (genres, ratings, descriptions)
4. Save the file
5. Import with "update" strategy

### Share Library Information

1. Export to JSON format (exclude file paths)
2. Share the JSON file with others
3. They can import to see your library metadata

### Data Analysis

1. Export to Excel format
2. Use Excel's data analysis tools
3. Create charts, pivot tables, statistics
4. Share reports with others

## Merge Strategies

### Skip Strategy

- **When to use**: First-time imports, adding new items only
- **Behavior**: Existing items are left unchanged, only new items are added
- **Safe**: Yes, won't modify existing data

### Replace Strategy

- **When to use**: Full restore from backup
- **Behavior**: Existing items are deleted and recreated with imported data
- **Safe**: No, will lose any changes made since export
- **Warning**: This will delete related data (files, artwork, subtitles)

### Update Strategy

- **When to use**: Sync metadata changes, bulk edits
- **Behavior**: Existing items are updated with new values from import
- **Safe**: Mostly, but will overwrite current values
- **Note**: Only updates fields present in import data

## Validation and Error Handling

### Import Validation

The import process validates:

- Required fields (title, media_type)
- Data types (year, rating must be numbers)
- Library existence
- File paths (if enabled)
- Duplicate detection

### Common Errors

**"Missing required field: title"**
- Solution: Ensure all items have a title field

**"Library with ID X not found"**
- Solution: Select a valid target library or update library_id in import data

**"File not found: /path/to/file"**
- Solution: Disable file validation or ensure files exist at specified paths

**"Unsupported import format"**
- Solution: Use JSON (.json) or Excel (.xlsx, .xls) files only

## Advanced Usage

### Scripting with JSON

The JSON format is designed for scripting and automation:

```python
import json

# Load export
with open('export.json', 'r') as f:
    data = json.load(f)

# Modify data
for item in data['items']:
    if item['media_type'] == 'movie':
        item['genres'] = item['genres'] + ', Updated'

# Save modified data
with open('modified.json', 'w') as f:
    json.dump(data, f, indent=2)

# Import modified.json in Media Manager
```

### Custom Column Mapping

For Excel imports with non-standard column names, you can manually map:

| Your Column | Maps To |
|-------------|---------|
| Name | title |
| Type | media_type |
| Released | year |
| Plot | description |
| Category | genres |
| Length | runtime |
| Score | rating |

### Partial Imports

You can create a minimal import file with just the fields you want to update:

```json
{
  "version": "1.0",
  "items": [
    {
      "id": 1,
      "rating": 9.5,
      "description": "Updated description"
    }
  ]
}
```

Then import with "update" strategy to only update those fields.

## Troubleshooting

### Export is slow

- Exports with many items or large artwork can take time
- Consider exporting in smaller batches by library
- Exclude artwork/subtitles if not needed

### Import fails with "Transaction rollback"

- Check the error messages for specific issues
- Ensure data format is correct
- Try importing a smaller subset first

### File paths not working after import

- File paths are absolute and may not be valid on different systems
- Update paths in Excel before importing
- Or use find/replace on JSON file paths

### Imported items missing artwork/subtitles

- Artwork and subtitle references are imported, but files must exist
- Copy the actual artwork/subtitle files to the expected locations
- Or re-download artwork/subtitles after import

## History Logging

When "Create history events" is enabled:

- Each imported item gets a history event with type "imported"
- The event data includes the source file and row number
- View history in the item's detail panel
- Useful for tracking data provenance

## Performance Tips

- **Large exports**: Export by library to create smaller files
- **Large imports**: Disable file validation for faster imports
- **Network drives**: Export/import to local drives for better performance
- **Database size**: Regular exports help with backup and disaster recovery

## Related Features

- **Batch Operations**: Use for renaming, moving, and bulk metadata updates
- **NFO Export**: Export individual items to Kodi NFO format
- **Search**: Use saved searches to export specific subsets
- **Libraries**: Organize items into libraries before exporting

## Support

For issues or questions:

- Check the logs in `~/.media_manager/logs/`
- Review error messages in the import wizard
- Validate your data format against the examples
- Create a backup before experimenting with import/export
