# Tags, Favorites, and Collections Implementation

## Overview
This document describes the implementation of media categorization features including tags, favorites, and user-defined collections (Watchlist, Kids, etc.) for the Media Manager application.

## Database Schema

### New Migration: `002_add_tags_favorites.py`
Located in: `src/media_manager/persistence/migrations/versions/`

Creates the following tables:
- **Tag**: User-defined tags for organizing media
  - `id` (Primary Key)
  - `name` (Unique, Indexed)
  - `color` (Optional hex color for UI display)
  - `created_at` (Timestamp)

- **MediaItemTag**: Association table (many-to-many)
  - `media_item_id` (Foreign Key to MediaItem)
  - `tag_id` (Foreign Key to Tag)
  - Composite Primary Key (media_item_id, tag_id)

- **Collection**: User-defined collections for grouping media
  - `id` (Primary Key)
  - `name` (Unique, Indexed)
  - `description` (Optional)
  - `created_at` (Timestamp)
  - `updated_at` (Timestamp)

- **MediaItemCollection**: Association table (many-to-many)
  - `media_item_id` (Foreign Key to MediaItem)
  - `collection_id` (Foreign Key to Collection)
  - Composite Primary Key (media_item_id, collection_id)

- **Favorite**: Marks media items as favorites
  - `id` (Primary Key)
  - `media_item_id` (Foreign Key to MediaItem, Unique)
  - `favorited_at` (Timestamp)
  - `notes` (Optional user notes)

## Persistence Layer

### Models
All models already defined in `src/media_manager/persistence/models.py`:
- `Tag` (lines 223-234)
- `MediaItemTag` (lines 13-19)
- `Collection` (lines 237-249)
- `MediaItemCollection` (lines 22-30)
- `Favorite` (lines 252-261)

### Relationships
- `MediaItem.tags`: Many-to-many relationship via MediaItemTag
- `MediaItem.collections`: Many-to-many relationship via MediaItemCollection
- `MediaItem.favorites`: One-to-many relationship (one item can have one favorite record)
- `Tag.media_items`: Reverse relationship to MediaItem
- `Collection.media_items`: Reverse relationship to MediaItem

## UI Components

### Metadata Editor Widget
File: `src/media_manager/metadata_editor_widget.py`

Enhancements:
1. **Collections & Tags Tab** (redesigned):
   - Favorite checkbox for quick marking
   - Collections list with checkboxes for multi-select
   - Tags list with checkboxes for multi-select
   - Add New Tag button for creating tags inline
   - Add Collection button for creating collections

2. **New Methods**:
   - `_load_collections()`: Loads available collections with checked states
   - `_load_tags()`: Loads available tags with checked states
   - `_on_add_new_tag()`: Creates new tag from input field
   - `_on_add_collection()`: Creates new collection with description
   - `_save_collections_and_tags()`: Persists tag/collection/favorite changes to database

### Main Window Context Menu
File: `src/media_manager/main_window.py`

Enhancements:
1. **Quick Tags Submenu**:
   - Lists all available tags as checkable menu items
   - Shows current tag status (checked/unchecked)
   - Add New Tag option for quick tag creation
   - Toggle tag on/off for selected item

2. **Toggle Favorite Action**:
   - Quick favorite toggle from context menu
   - Shows current favorite status (checked/unchecked)

3. **New Helper Methods**:
   - `_toggle_tag_on_item()`: Adds or removes tag from item
   - `_create_new_tag_for_item()`: Creates and adds new tag
   - `_toggle_favorite()`: Marks/unmarks item as favorite

### Search Filter Widget
File: `src/media_manager/search_filter_widget.py`

Already implemented:
- Tags filter (QListWidget with multi-select)
- Collections filter (QListWidget with multi-select)
- People filter (actors/directors/etc)
- Favorites quick filter button
- Tag/collection loading from database

## Service Layer

### Search Service
File: `src/media_manager/search_service.py`

Already implemented:
- `get_available_tags()`: Returns all tags for filtering
- `get_available_collections()`: Returns all collections for filtering
- Tag filtering in `_build_query()` (lines 122-129): Items must have ALL specified tags
- Collection filtering (lines 139-145): Items must be in ANY of specified collections
- Favorites quick filter (lines 186-190): Filters items marked as favorites

### Batch Operations Service
File: `src/media_manager/batch_operations_service.py`

Already implemented:
- `tags_to_add` configuration field for batch tag assignment
- `_apply_tags()` method (lines 419-449): 
  - Creates tags if they don't exist
  - Adds tags to media items in batch
  - Returns list of applied tags

## NFO Export

File: `src/media_manager/nfo_exporter.py`

Enhancements:
1. Added tag export to movie NFO files
   - Each tag is written as `<tag>` element
2. Added tag export to episode NFO files
   - Each tag is written as `<tag>` element

Example NFO output:
```xml
<movie>
  <title>Movie Title</title>
  <year>2023</year>
  ...
  <tag>Action</tag>
  <tag>Adventure</tag>
  ...
</movie>
```

## Testing

File: `tests/test_tags_favorites.py`

Comprehensive test coverage for:

### Tag Management Tests
- Tag creation with unique constraint enforcement
- Adding single and multiple tags to media items
- Removing tags from media items
- Tag CRUD operations via repository
- Retrieving all tags

### Collection Management Tests
- Collection creation with unique constraint enforcement
- Adding single and multiple items to collections
- Retrieving items in a collection
- Collection CRUD operations via repository

### Favorite Management Tests
- Marking/unmarking items as favorite
- Adding favorite notes
- Updating favorite notes
- Favorite unique constraint enforcement
- Retrieving all favorite items
- Favorite CRUD operations via repository

### Integration Tests
- Combined tags, collections, and favorites on single item
- Batch tag assignment to multiple items
- Persistence across database sessions
- Search filtering by tags and collections

## Batch Operations

### Configuration
Users can specify:
- `tags_to_add`: List of tag names to apply to selected items
- Tags are created if they don't exist
- Multiple items can have tags assigned in batch

### Example Usage
1. Select multiple media items in library
2. Right-click → "Batch Operations..."
3. Configure: Add tags "Action", "Favorite"
4. Execute: Tags are created and applied to all selected items

## UI Workflow

### Quick Tag Assignment
1. Select media item in grid or table view
2. Right-click → "Quick Tags"
3. Click tag to toggle on/off
4. Click "+ Add New Tag..." to create and assign new tag

### Mark as Favorite
1. Select media item
2. Right-click → "Toggle Favorite"
3. Or open metadata editor → Collections & Tags tab → Check "Mark as Favorite"

### Create Collections
1. Open metadata editor
2. Go to Collections & Tags tab
3. Click "Add Collection"
4. Enter collection name (e.g., "Watchlist", "Kids")
5. Optionally add description
6. Click OK
7. Check boxes for collections to add item to

### Create Tags
1. Open metadata editor
2. Go to Collections & Tags tab
3. Enter tag name in text field
4. Click "Add New Tag"
5. Check boxes for tags to add item to
6. Or right-click in library → Quick Tags → + Add New Tag...

## Persistence Across Sessions

All tags, collections, and favorites are:
- Persisted to SQLite database
- Loaded automatically when application starts
- Preserved during library operations
- Searchable across sessions
- Exportable in NFO files

## Search Integration

### Tag Filter
- Search Filter Widget lists all available tags
- Multi-select tags (AND operator)
- Items must have ALL selected tags to appear in results

### Collection Filter
- Search Filter Widget lists all available collections
- Multi-select collections (OR operator)
- Items in ANY of selected collections appear in results

### Quick Filters
- "Favorites" quick filter button shows only marked favorites
- Works in combination with other filters

### Saved Searches
- Search criteria including tags/collections saved for later use
- Criteria serialized to JSON in database
- Can be reloaded and executed

## Performance Considerations

### Database Indexes
- Tag.name (unique, indexed) for quick lookups
- Collection.name (unique, indexed) for quick lookups
- MediaItemTag.media_item_id and tag_id (indexed) for association queries
- MediaItemCollection.media_item_id and collection_id (indexed) for association queries
- Favorite.media_item_id (unique index) for quick favorite status checks

### Query Optimization
- Eager loading of tags and collections in SearchService
- Composite indexes for common query patterns
- Efficient many-to-many filtering via subqueries

## Error Handling

All tag/favorite operations include:
- Try/except blocks for database errors
- User-friendly error messages in status bar
- Logging of errors for debugging
- Graceful fallbacks

## Future Enhancements

Possible improvements:
1. Tag color customization in UI
2. Hierarchical tags/categories
3. Tag autocomplete in text fields
4. Tag suggestions based on similar media
5. Collaborative tags/ratings
6. Tag-based playlists
7. Export tags to external formats (Plex, etc.)
8. Bulk tag editing
9. Tag statistics/analytics
10. Tag-based recommendations
