# 影藏·媒体管理器 - User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Main Interface](#main-interface)
3. [Scanning Media](#scanning-media)
4. [Matching Media](#matching-media)
5. [Processing and Organization](#processing-and-organization)
6. [Preferences and Settings](#preferences-and-settings)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### Starting the Application

#### Option 1: Using Command (Recommended)

```bash
# For production installation
media-manager

# For development
python -m media_manager.main

# Demo with example data
media-manager-demo
```

#### Option 2: Direct Execution

```bash
python src/media_manager/main.py
```

### First-Run Configuration

On first startup, the application will:

1. Create configuration directory: `~/.media-manager/`
2. Initialize default settings
3. Create logs directory
4. Display setup wizard (future)

**Recommended first steps:**

1. Configure API keys (if available)
2. Set up scan directories
3. Configure download preferences

## Main Interface

### Window Layout

```
┌──────────────────────────────────────────────────────────────┐
│ File  Edit  View  Help                                        │
├──────────────────────────────────────────────────────────────┤
│ ┌────────────┐ ┌─────────────────────────┐ ┌──────────────┐ │
│ │  Navigation│ │   Content Area (Tabs)  │ │  Properties  │ │
│ │            │ │                       │ │              │ │
│ │ • Library  │ │ [Library] [Recent]    │ │ • Title      │ │
│ │ • Recent   │ │ [Favorites][Matching] │ │ • Type       │ │
│ │ • Favorites│ │ [Search]              │ │ • Location   │ │
│ │            │ │                       │ │              │ │
│ │            │ │                       │ │              │ │
│ └────────────┘ └─────────────────────────┘ └──────────────┘ │
├──────────────────────────────────────────────────────────────┤
│ Status: Ready | Items: 0                         [Preferences]│
└──────────────────────────────────────────────────────────────┘
```

### Resizing Panes

- Click and drag the divider between panes
- Double-click to maximize/minimize a pane
- Window layout is saved on exit

### Tabs

| Tab | Purpose |
|-----|---------|
| **Library** | Browse organized media library |
| **Recent** | Recently accessed items |
| **Favorites** | Bookmarked items |
| **Matching** | Scan and match media workflow |
| **Search** | Find media by title/metadata |

## Scanning Media

### Starting a Scan

1. **Navigate to Matching tab**
   - Click "Matching" tab in center pane

2. **Add directories to scan**
   - Click "Add Directory" button
   - Select folder containing media files
   - Can add multiple directories

3. **Start scan**
   - Click "Start Scan" button
   - Progress bar shows scan progress

### Scan Queue

The Scan Queue displays all discovered media files:

```
┌─────────────────────────────────────────────────────┐
│ Scan Queue                                          │
│ Filter: [Search box...]              [Clear filter] │
├─────────────────────────────────────────────────────┤
│ ⏳ Inception (2010)                         0.95 ✓  │
│ ⏳ The Dark Knight (2008)                  0.92 ✓  │
│ 🔧 Unknown Movie 123                       0.45 !  │
│ ⊘ Corrupted File (2015)                   Skipped  │
│                                                     │
│ Status: 156 items, 3 pending, 150 matched          │
└─────────────────────────────────────────────────────┘
```

### Status Indicators

| Icon | Status | Meaning |
|------|--------|---------|
| ⏳ | Pending | Waiting for user review |
| ✓ | Matched | Auto-matched successfully |
| 🔧 | Manual | Manually matched by user |
| ⊘ | Skipped | User skipped this item |
| ⚠ | Error | Problem during processing |

### Filtering and Searching

```
Filter: [Inception────────────┐]
        └─ Shows only items containing "Inception"
```

**Features:**

- Real-time filtering as you type
- Case-insensitive search
- Matches title and filename
- Click "Clear filter" to reset

## Matching Media

### Understanding Confidence Scores

Each match shows a confidence score (0.0 to 1.0):

- **0.95-1.00** (Green): Excellent match
- **0.80-0.94** (Yellow): Good match
- **0.50-0.79** (Orange): Uncertain
- **Below 0.50** (Red): Poor match - consider manual search

### Auto-Matched Items

Auto-matched items (✓) have been successfully matched to a database:

1. **View details** - Click item to show full information
2. **Accept match** - Click checkmark to confirm
3. **Override** - Click pencil icon for manual search
4. **Skip** - Click X to skip this item

### Manual Search

For uncertain or failed matches:

1. **Select item** - Click on uncertain match
2. **Click "Search Manually"** button
3. **Enter search terms** - Title, year, or other info
4. **Review results** - See matching options
5. **Select match** - Click the correct result
6. **Confirm** - Accept the selection

### Match Details

When viewing a match, you see:

```
Title:              Inception
Original Title:     Inception
Year:               2010
Runtime:            148 minutes
Type:               Movie
External ID:        550 (TMDB)

Overview:
A skilled thief who steals corporate secrets through the use of
dream-sharing technology is given the inverse task of planting
an idea into the mind of a C.E.O.

Cast:
• Leonardo DiCaprio
• Marion Cotillard
• Ellen Page
```

## Processing and Organization

### Post-Processing Options

After matching, you can enable post-processing:

1. **Rename files**
   - Generates standardized names
   - Example: `Inception (2010).mkv`

2. **Organize by type**
   - Movies → `/target/movies/`
   - TV Shows → `/target/tv_shows/`

3. **Generate NFO files**
   - Creates XML metadata files
   - Compatible with media servers (Kodi, Plex)
   - Alongside media files

4. **Download posters**
   - Saves artwork images
   - Multiple formats: poster, fanart, banner
   - Configurable sizes
   - Smart caching

5. **Download subtitles**
   - Multiple language support
   - Various formats: SRT, ASS, VTT
   - Automatic naming

### Organization Templates

**Movie Example:**

```
Source:  /downloads/Inception.2010.1080p.BluRay.mkv
Target:  /media/movies/Inception (2010)/Inception (2010).mkv
Files:   - Poster.jpg
         - Fanart.jpg
         - Inception (2010).nfo
         - Inception (2010).en.srt
         - Inception (2010).es.srt
```

**TV Show Example:**

```
Source:  /downloads/Breaking.Bad.S05E16.Felina.mkv
Target:  /media/tv_shows/Breaking Bad/Season 05/
Files:   - Breaking Bad - S05E16 - Felina.mkv
         - Breaking Bad - S05E16 - Felina.nfo
         - Breaking Bad - S05E16 - Felina.en.srt
         - poster.jpg
         - fanart.jpg
```

### Processing Workflow

1. **Prepare matches**
   - Scan and review all items
   - Correct any mismatches
   - Mark items to skip

2. **Configure options**
   - Choose what to process
   - Set target directories
   - Select languages/formats

3. **Start processing**
   - Click "Process All" button
   - Monitor progress
   - Watch for errors

4. **Review results**
   - Check summary report
   - Verify file placements
   - Handle any errors

## Preferences and Settings

### Opening Preferences

**Method 1:** Menu → Edit → Preferences
**Method 2:** Status bar → Preferences button
**Keyboard:** Ctrl+, (Comma)

### General Settings

- **Language**: Application language
- **Theme**: Light or dark mode
- **Window state**: Remember position and size
- **Logging level**: DEBUG, INFO, WARNING, ERROR

### Scan Settings

```
Scan Paths:
  • /home/user/Videos
  • /mnt/external/media

Ignored Directories:
  • .git
  • .vscode
  • System Volume Information
  ☑ Custom patterns

File Extensions:
  ☑ .mkv  ☑ .mp4  ☑ .avi  ☑ .mov
  ☑ .flv  ☑ .wmv  ☑ .webm
```

### API Keys

Configure metadata providers in Edit → Preferences → Providers:

```
Alternative TMDB API Address:
[https://api.themoviedb.org..................]

Alternative TMDB Image Address:
[https://image.tmdb.org.....................]

Alternative TMDB API Key:
[Enter your API key........................]

Alternative TVDB API Key:
[Enter your API key........................]

☑ Enable TMDB provider
☑ Enable TVDB provider

Retry attempts: [3]
API timeout (seconds): [10]
```

**Note:** The API address fields can be left empty to use default endpoints. 
Custom addresses are useful when using proxy services or alternative TMDB/TVDB mirrors.

### Poster Download Settings

```
☑ Enable poster downloads

Types to download:
  ☑ Poster (main artwork)
  ☑ Fanart (background)
  ☑ Banner (horizontal)
  ☑ Thumbnail (small preview)

Preferred sizes:
  Poster: ◯ Small ◉ Medium ○ Large ○ Original
  Fanart: ◯ Small ○ Medium ◉ Large ○ Original

Cache location:
/home/user/.media-manager/poster-cache

Cache settings:
  Max size: [500────────] MB
  [Clear Cache] [Browse...]
```

### Subtitle Settings

```
☑ Enable subtitle downloads

Languages:
  ☑ English (en)
  ☑ Spanish (es)
  ☑ French (fr)
  ☑ German (de)
  ☑ Italian (it)
  ☑ Portuguese (pt)
  ☑ Russian (ru)
  ☑ Chinese (zh)
  ☑ Japanese (ja)
  ☑ Korean (ko)

Format: ◉ SRT ○ ASS ○ VTT

Provider: [OpenSubtitles────────────────]

☑ Auto-download on match
☐ Retry failed downloads

Cache location:
/home/user/.media-manager/subtitle-cache
[Clear Cache] [Browse...]
```

### NFO Export Settings

```
☑ Enable NFO generation

Target:
◉ Alongside media files
○ In subfolder: [metadata────────]

Types:
  ☑ Include poster URLs
  ☑ Include cast information
  ☑ Include runtime
  ☑ Include plot synopsis
```

### Target Folders

```
Movies:        [/path/to/movies..........] [Browse]
TV Shows:      [/path/to/tv_shows.......] [Browse]
Downloaded:    [/path/to/downloads.......] [Browse]
Cache:         [/path/to/cache...........] [Browse]
```

## Advanced Usage

### Command-Line Options

```bash
# Show help
media-manager --help

# Show version
media-manager --version

# Verbose logging
media-manager --verbose

# Scan directory directly
media-manager --scan /path/to/media

# Configuration file
media-manager --config /path/to/settings.json

# Reset to defaults
media-manager --reset-settings
```

### Configuration Files

**Location:** `~/.media-manager/settings.json`

**Edit directly:**

```bash
# Backup first!
cp ~/.media-manager/settings.json ~/.media-manager/settings.json.backup

# Edit with your editor
nano ~/.media-manager/settings.json

# Or using environment variable
MEDIA_MANAGER_CONFIG=/custom/path/settings.json media-manager
```

### Python API Usage

For developers integrating 影藏·媒体管理器:

```python
from media_manager.scanner import Scanner, ScanConfig
from pathlib import Path

# Create scanner
scanner = Scanner()

# Configure scan
config = ScanConfig(root_paths=[Path("/media/movies")])

# Scan files
for video_path in scanner.iter_video_files(config):
    metadata = scanner.parse_video(video_path)
    print(f"Found: {metadata.title} ({metadata.year})")
```

### Batch Processing

For large libraries:

```bash
# Process multiple directories
media-manager --scan /media/movies --scan /media/tv_shows --process

# With custom settings
media-manager --config custom.json --scan /media --process
```

### Exporting Data

**Export matched library:**

```bash
# As JSON
media-manager --export matches.json

# As CSV
media-manager --export matches.csv

# Statistics
media-manager --export stats.json --statistics
```

## Troubleshooting

### Application Won't Start

**Problem:** Error when launching media-manager

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install --upgrade -e ".[dev]"
   ```

3. **Check logs:**
   ```bash
   cat ~/.media-manager/logs/app.log
   ```

4. **Reset settings:**
   ```bash
   rm ~/.media-manager/settings.json
   media-manager
   ```

### Scan Not Finding Files

**Problem:** Scan completes but finds no videos

**Solutions:**

1. **Verify directory:**
   - Check path exists: `ls -la /path/to/media`
   - Verify read permissions: `ls -la` should show r-x

2. **Check file extensions:**
   - Verify files are supported: .mkv, .mp4, .avi, etc.
   - Check for unusual extensions: `find /path -name "*.xyz"`

3. **Check ignored directories:**
   - Make sure your path isn't in ignored list
   - Go to Preferences → Scan Settings

4. **Manually add directory:**
   - Preferences → Scan Settings → Add Directory

### Matches Have Low Confidence

**Problem:** Most matches show low confidence scores

**Solutions:**

1. **Check filenames:**
   - Use standard naming: "Title (Year)" or "Show - SxEy"
   - Remove extra info: quality, releases, etc.

2. **Verify with manual search:**
   - Click "Search Manually" on uncertain items
   - Usually finds correct match

3. **Check API keys** (future):
   - Verify TMDB/TVDB API keys are correct
   - Check API rate limits

### Files Not Organizing

**Problem:** Post-processing started but files not moved

**Solutions:**

1. **Check permissions:**
   - Source directory readable: `ls -la`
   - Target directory writable: `touch /target/test.txt`

2. **Check disk space:**
   - View free space: `df -h`
   - Need at least 10% free

3. **Check target path:**
   - Verify target directory exists
   - Path should be absolute, not relative

4. **Review error log:**
   ```bash
   tail -50 ~/.media-manager/logs/app.log | grep -i error
   ```

### Subtitles Not Downloading

**Problem:** Subtitle download enabled but no results

**Solutions:**

1. **Verify settings:**
   - Check "Enable subtitle downloads" is checked
   - Select at least one language

2. **Check provider:**
   - OpenSubtitles is mock in current version
   - Will show mock results

3. **Manual download:**
   - Use external subtitle site
   - Save in same folder as video
   - Naming: `movie.en.srt` or `show.S01E01.en.srt`

### High Memory Usage

**Problem:** Application consuming too much RAM

**Solutions:**

1. **Reduce scan scope:**
   - Scan fewer directories
   - Skip large media folders

2. **Clear caches:**
   - Preferences → Clear Cache (posters)
   - Preferences → Clear Cache (subtitles)

3. **Reduce UI responsiveness:**
   - Close large lists
   - Filter to fewer items

4. **Monitor usage:**
   ```bash
   ps aux | grep media-manager
   ```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Q | Quit application |
| Ctrl+, | Open preferences |
| Ctrl+F | Focus search box |
| Ctrl+L | Focus library navigation |
| Ctrl+S | Start scan |
| Ctrl+P | Start processing |
| Ctrl+R | Refresh current view |
| Ctrl+Z | Undo last action |
| Ctrl+Y | Redo last action |
| F1 | Open help |
| F5 | Refresh |
| F11 | Fullscreen toggle |

## Tips and Best Practices

### Organization

✅ **DO:**
- Use standard naming: "Movie Title (2020)" or "Show - S01E01 - Episode Title"
- Keep media in separate folders for movies and TV
- Use consistent quality markers: 720p, 1080p, 4K

❌ **DON'T:**
- Mix movies and TV shows in same folder
- Use special characters in filenames
- Have deeply nested directory structures

### File Naming

**Best Naming Patterns:**

Movies:
- `Inception (2010).mkv`
- `Inception.2010.1080p.BluRay.mkv` (auto-cleaned)
- `The Dark Knight.mkv`

TV Shows:
- `Breaking Bad/Season 01/Breaking Bad - S01E01 - Pilot.mkv`
- `Breaking Bad/Season 01/Breaking Bad 01x01 - Pilot.mkv`
- `ShowName - 1x01 - Title.mkv`

### Backup Strategy

Before first use:

1. **Backup configuration:**
   ```bash
   cp -r ~/.media-manager ~/.media-manager.backup
   ```

2. **Export settings:**
   ```bash
   cp ~/.media-manager/settings.json settings.backup.json
   ```

3. **Keep originals:**
   - Don't delete original files immediately
   - Verify organization is correct first
   - Keep originals for 24 hours after processing

### Performance Optimization

**Faster scanning:**
- Use SSD if possible
- Scan fewer directories
- Pre-filter with file system

**Faster matching:**
- Ensure filenames are accurate
- Use API keys when available
- Consider batching large libraries

**Memory efficiency:**
- Close other applications
- Clear caches regularly
- Filter to smaller result sets

### Privacy and Security

- Settings stored locally: `~/.media-manager/`
- No data sent without explicit action
- API keys stored unencrypted (use read-only accounts)
- Enable encryption on system disk for protection

### Regular Maintenance

**Weekly:**
- Clear cache if processing large amounts
- Check logs for errors
- Update application if available

**Monthly:**
- Review and organize new media
- Verify all matches are correct
- Update API keys if needed

**Quarterly:**
- Backup settings
- Archive logs
- Review performance metrics
