# NFO Metadata Exporter Implementation

## Overview

The NFO (XML) metadata exporter generates standardized metadata files alongside renamed media files. It supports both movie and TV episode schemas with full UTF-8 support and comprehensive provider integration.

## Features

- **Dual Schema Support**: Movie and episode NFO formats
- **UTF-8 Encoding**: Full Unicode support for international characters
- **Provider Integration**: TMDB, TVDB, and generic ID support
- **Configurable Output**: Support for custom paths and subfolders
- **Metadata Fields**: Title, year, runtime, aired date, plot, cast, and IDs
- **Settings Integration**: Persistent configuration via JSON
- **XML Validation**: Built-in XML structure validation

## Architecture

### Components

1. **NFOExporter** (`src/media_manager/nfo_exporter.py`)
   - Main class for NFO generation and validation
   - `export_nfo()`: Generate NFO files
   - `validate_nfo()`: Verify XML structure
   - `read_nfo()`: Parse existing NFO files

2. **Settings** (`src/media_manager/settings.py`)
   - `get_nfo_enabled()`: Check if NFO generation is enabled
   - `set_nfo_enabled()`: Enable/disable NFO generation
   - `get_nfo_target_subfolder()`: Get NFO output subfolder
   - `set_nfo_target_subfolder()`: Set NFO output subfolder

3. **Models** (`src/media_manager/models.py`)
   - Extended `MediaMatch` with `runtime`, `aired_date`, and `cast` fields
   - All fields are serializable via `as_dict()`

## Usage

### Basic Movie NFO Export

```python
from pathlib import Path
from src.media_manager.models import MediaMatch, MediaType, MatchStatus, VideoMetadata
from src.media_manager.nfo_exporter import NFOExporter

# Create metadata
metadata = VideoMetadata(
    path=Path("movie.mkv"),
    title="My Movie",
    media_type=MediaType.MOVIE,
    year=2023,
)

# Create match with provider data
match = MediaMatch(
    metadata=metadata,
    status=MatchStatus.MATCHED,
    matched_title="My Movie",
    matched_year=2023,
    external_id="12345",
    source="tmdb",
    overview="A great movie",
    runtime=120,
    aired_date="2023-06-15",
    cast=["Actor One", "Actor Two"],
)

# Export NFO
exporter = NFOExporter()
nfo_path = exporter.export_nfo(match)
print(f"NFO created at: {nfo_path}")
```

### TV Episode NFO Export

```python
# Create episode metadata
metadata = VideoMetadata(
    path=Path("episode.mkv"),
    title="My Episode",
    media_type=MediaType.TV,
    season=1,
    episode=3,
)

# Create episode match
match = MediaMatch(
    metadata=metadata,
    status=MatchStatus.MATCHED,
    matched_title="Amazing Episode",
    external_id="54321",
    source="tvdb",
    overview="An amazing episode",
    runtime=45,
    aired_date="2023-01-15",
    cast=["Guest Star"],
)

# Export
nfo_path = exporter.export_nfo(match)
```

### With Settings

```python
from src.media_manager.settings import get_settings

settings = get_settings()

# Enable NFO generation
settings.set_nfo_enabled(True)

# Set NFO output subfolder
settings.set_nfo_target_subfolder("metadata")

# Export with subfolder
nfo_path = exporter.export_nfo(
    match, 
    target_subfolder=settings.get_nfo_target_subfolder()
)
```

### Validation and Reading

```python
# Validate existing NFO
if exporter.validate_nfo(nfo_path):
    print("NFO is valid XML")

# Read and parse NFO
nfo_data = exporter.read_nfo(nfo_path)
print(nfo_data)
```

## Generated NFO Format

### Movie NFO

```xml
<?xml version='1.0' encoding='utf-8'?>
<movie>
  <title>Movie Title</title>
  <originaltitle>Original Title</originaltitle>
  <year>2023</year>
  <aired>2023-06-15</aired>
  <runtime>120</runtime>
  <plot>Plot description</plot>
  <tmdbid>12345</tmdbid>
  <actor>
    <name>Actor One</name>
  </actor>
  <actor>
    <name>Actor Two</name>
  </actor>
</movie>
```

### Episode NFO

```xml
<?xml version='1.0' encoding='utf-8'?>
<episodedetails>
  <title>Episode Title</title>
  <season>1</season>
  <episode>3</episode>
  <aired>2023-01-15</aired>
  <runtime>45</runtime>
  <plot>Episode plot</plot>
  <tvdbid>54321</tvdbid>
  <actor>
    <name>Guest Star</name>
  </actor>
</episodedetails>
```

## File Naming

- NFO files use the media file's stem with `.nfo` extension
- Example: `movie.mkv` → `movie.nfo`
- Placed next to media file or in target subfolder if specified

## Settings

All NFO settings are stored in the `nfo_settings` section:

```json
{
  "nfo_settings": {
    "enabled": true,
    "target_subfolder": "metadata"
  }
}
```

## Testing

### Run Unit Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_nfo_exporter.py -v
```

### Run Integration Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_nfo_integration.py -v
```

### Run All NFO Tests

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_nfo_*.py -v
```

## Test Coverage

- **21 Unit Tests** covering:
  - Movie and episode NFO generation
  - UTF-8 encoding with international characters
  - XML validation
  - Custom output paths and subfolders
  - Cast handling (empty, large, multiple)
  - ID source handling (TMDB, TVDB, generic)
  - Filename handling (various formats)
  - Error handling

- **8 Integration Tests** covering:
  - Settings integration
  - Batch workflows
  - Manual match handling
  - Permission error handling
  - Optional field handling

## Error Handling

- Raises `ValueError` if trying to export unmatched media
- Raises `OSError` if unable to write NFO file
- Gracefully handles missing optional fields
- Validates XML before writing

## Integration with Media Manager

The NFO exporter integrates with the media manager workflow:

1. Scanner detects media files
2. Matching identifies provider data
3. NFO exporter generates metadata files
4. Optional: UI exposes NFO settings to users

## Provider ID Handling

- **TMDB**: Generates `<tmdbid>` tag
- **TVDB**: Generates `<tvdbid>` tag
- **Other**: Generates generic `<id>` tag

## UTF-8 Support

Full Unicode support for:
- International titles
- Diacritical marks (é, ñ, ü, etc.)
- Non-Latin scripts (Chinese, Japanese, Cyrillic, etc.)
- Special characters

Example:
```python
match = MediaMatch(
    matched_title="Tëst Möviè with Spëcíål Çhärs",
    overview="Übung macht den Meister",
    cast=["François", "José", "李明"],
)
nfo_path = exporter.export_nfo(match)
# All characters properly encoded in UTF-8
```

## Future Enhancements

- GUI settings panel for NFO preferences
- Support for additional NFO elements (rating, genre, director)
- Batch NFO generation from file lists
- NFO template customization
- Integration with media server applications (Plex, Kodi)
