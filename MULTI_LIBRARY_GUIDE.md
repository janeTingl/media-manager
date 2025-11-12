# Multi-Library Management Guide

This guide explains how to use the multi-library management feature in Media Manager.

## Overview

Multi-library management allows you to organize your media into separate, independent libraries. Each library can have:

- **Distinct root paths**: Different storage locations for different media types
- **Media type settings**: Movie-only, TV-only, or mixed libraries
- **Scan roots**: Multiple directories to scan for media files
- **Default destinations**: Custom paths for processed files
- **Visual identification**: Color-coded libraries for easy recognition

## Getting Started

### 1. Database Migration

If you're upgrading from a previous version, run the migration script:

```bash
python scripts/migrate_database.py
```

This will add the new multi-library fields to your database.

### 2. Creating Your First Library

1. Launch Media Manager
2. Go to **File > Manage Libraries** (or press `Ctrl+L`)
3. Click **New** in the Library Manager dialog
4. Fill in the library details:
   - **Name**: A descriptive name (e.g., "My Movie Collection")
   - **Library Path**: The root directory for this library
   - **Media Type**: Choose "movie", "tv", or "mixed"
   - **Default Destination**: (Optional) Where to move processed files
   - **Scan Roots**: Add directories to scan for new media
   - **Color**: (Optional) Pick a color for visual identification
   - **Status**: Check "Active" to enable the library
   - **Description**: (Optional) Additional notes

5. Click **Save**

### 3. Using the Library Tree

The left navigation pane shows all your libraries in a tree structure:

```
📚 Movies
  ├─ All (145)
  └─ Movies (145)

📚 TV Shows
  ├─ All (87)
  └─ TV Shows (87)

📚 Mixed Media
  ├─ All (232)
  ├─ Movies (145)
  └─ TV Shows (87)
```

- Click on a library or media type node to filter the main view
- Numbers in parentheses show the count of items
- Libraries are color-coded if you assigned colors

## Features

### Library Types

#### Movie Library
- Optimized for movie collections
- Only shows movie-related media types
- Ideal for dedicated movie storage

#### TV Library
- Designed for TV show collections
- Only shows TV-related media types
- Perfect for series and episodes

#### Mixed Library
- Supports both movies and TV shows
- Shows separate nodes for each media type
- Great for general media storage

### Scan Roots

Each library can have multiple scan roots - directories that will be scanned for new media:

1. Open Library Manager
2. Select a library
3. In the "Scan Roots" section, click **Add Root...**
4. Select the directory to scan
5. Click **Save**

Example use case: A library with multiple external drives

```
Movies Library
  Scan Roots:
    - /mnt/drive1/movies
    - /mnt/drive2/movies
    - /media/usb/movies
```

### Default Destinations

When processing and organizing media, the default destination specifies where files should be moved:

- If set, files are moved to this path during finalization
- If not set, files remain in their original locations
- Can be different from the library path

### Library Management

#### Editing a Library

1. Open Library Manager (`Ctrl+L`)
2. Select the library from the list
3. Modify the fields in the form
4. Click **Save**

#### Deactivating a Library

To temporarily hide a library without deleting it:

1. Open Library Manager
2. Select the library
3. Uncheck the "Active" checkbox
4. Click **Save**

Inactive libraries won't appear in the library tree but their data is preserved.

#### Deleting a Library

⚠️ **Warning**: Deleting a library removes its database entries but does not delete actual media files.

1. Open Library Manager
2. Select the library
3. Click **Delete**
4. Confirm the action

If the library contains media items, you'll receive an additional warning.

## Integration with Scanning

The scan queue widget now includes library selection:

1. Scan for new media files
2. In the scan queue, select the target library from the dropdown
3. Start matching
4. Files will be associated with the selected library

The scan queue automatically selects the currently active library.

## Settings Persistence

Media Manager remembers:

- **Last active library**: Automatically selected when you restart the app
- **Default library**: Used for new scan operations
- **Library-specific filters**: Preserved between sessions

Settings are stored in: `~/.media-manager/settings.json`

## Filtering and Views

### Library Filtering

Select a library in the tree to show only its media:

- Grid view shows posters from the selected library
- Table view shows details from the selected library
- Detail panel shows information about items in the selected library

### Media Type Filtering

Within a library, you can further filter:

- **All**: Show all media types
- **Movies**: Show only movies
- **TV Shows**: Show only TV shows

Use the toolbar buttons or select the tree nodes.

### Text Filtering

The search/filter box works within the currently selected library:

- Searches titles, descriptions, and years
- Only searches items in the active library
- Combines with media type filters

## Tips and Best Practices

### Organizing Your Libraries

1. **Separate by Media Type**: Create dedicated movie and TV libraries for better organization
2. **Multiple Physical Locations**: Use separate libraries for different storage devices
3. **Archived Content**: Create an inactive library for archived/backup media
4. **Work in Progress**: Use a dedicated library for media being processed

### Color Coding

Assign colors to libraries for quick visual identification:

- 🔴 Red: Movies
- 🔵 Blue: TV Shows
- 🟢 Green: Kids content
- 🟡 Yellow: Work in progress
- 🟣 Purple: Archived

### Performance Tips

- Keep active libraries under 10,000 items for best performance
- Use inactive status instead of deleting large libraries
- Regular database maintenance (vacuum) helps with speed

## Keyboard Shortcuts

- `Ctrl+L`: Open Library Manager
- `F9`: Toggle navigation panes
- Tree navigation: Arrow keys

## Troubleshooting

### Library not appearing in tree

- Check if the library is marked as "Active"
- Verify the library path exists and is accessible
- Try refreshing the library tree (right-click > Refresh)

### Can't delete library

- Ensure you have write permissions to the database
- Check if the library is being used by another process
- Try closing and reopening the Library Manager

### Scan roots not working

- Verify the paths exist and are readable
- Check for proper JSON formatting in the database
- Ensure paths are absolute, not relative

### Settings not persisting

- Check write permissions for `~/.media-manager/`
- Verify the settings.json file is not corrupted
- Try deleting settings.json and reconfiguring

## Migration from Single Library

If you previously used a single library setup:

1. Create a new library matching your old setup
2. The existing media items should appear in the first library (ID: 1)
3. Create additional libraries as needed
4. Consider splitting media by type into separate libraries
5. Update scan configurations to target specific libraries

## Advanced Usage

### Database Schema

The Library table includes these fields:

```sql
CREATE TABLE library (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,
    path VARCHAR UNIQUE NOT NULL,
    media_type VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    scan_roots TEXT,              -- JSON array
    default_destination VARCHAR,
    color VARCHAR,                -- Hex color code
    description TEXT,
    created_at DATETIME,
    updated_at DATETIME
)
```

### Direct Database Access

⚠️ **Advanced users only**: You can query libraries directly:

```python
from src.media_manager.persistence.repositories import LibraryRepository

repo = LibraryRepository()
libraries = repo.get_all()

for lib in libraries:
    print(f"{lib.name}: {lib.path} ({lib.media_type})")
```

### API Integration

Access libraries programmatically:

```python
from src.media_manager.main_window import MainWindow

# Get current library
current_lib = main_window.get_current_library()

# Switch library programmatically
main_window.library_tree_widget.select_library(library_id)
```

## Support

For issues or questions:

1. Check this guide
2. Review the main README.md
3. Check the CHANGELOG.md for recent changes
4. File an issue on the project repository

## Future Enhancements

Planned features for multi-library management:

- [ ] Library import/export
- [ ] Bulk library operations
- [ ] Library statistics dashboard
- [ ] Custom library templates
- [ ] Library synchronization between devices
- [ ] Smart library recommendations
- [ ] Library health checks and diagnostics

---

**Version**: 0.2.0  
**Last Updated**: 2024
