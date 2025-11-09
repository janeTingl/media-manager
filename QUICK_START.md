# Media Manager - Quick Start Guide

Get up and running with Media Manager in 5 minutes!

## Installation (2 minutes)

### Option 1: PyPI (Recommended)

```bash
pip install media-manager
media-manager
```

### Option 2: From Source

```bash
git clone https://github.com/your-username/media-manager.git
cd media-manager
pip install -e ".[dev]"
media-manager
```

### Option 3: Demo

```bash
pip install media-manager
media-manager-demo
```

## First Run (3 minutes)

### 1. Start Application
```bash
media-manager
```

### 2. Navigate to Matching Tab
- Click the **"Matching"** tab in the center panel

### 3. Add Directory to Scan
- Click **"Add Directory"** button
- Select folder with media files (e.g., `~/Downloads`, `~/Videos`)

### 4. Start Scan
- Click **"Start Scan"** button
- Watch progress bar

### 5. Review Matches
- Green ✓: Good auto-matches (accept as-is)
- Yellow 🔧: Uncertain (use Manual Search)
- Red ⊘: Skip unwanted items

### 6. Process Library
- Click **"Process All"** button
- Files are renamed and organized
- Check target folder for results

## Common Tasks

### Scan a Directory

1. Matching → Add Directory
2. Select folder
3. Click Start Scan
4. Wait for completion

### Manually Match Item

1. Click uncertain match
2. Click "Search Manually"
3. Enter search terms (title, year)
4. Click correct result
5. Click Confirm

### Download Posters

1. Edit → Preferences
2. Select "Posters" tab
3. Check "Enable Poster Downloads"
4. Select types (poster, fanart, banner)
5. Click OK

### Download Subtitles

1. Edit → Preferences
2. Select "Subtitles" tab
3. Check "Enable Subtitle Downloads"
4. Select languages (English, Spanish, etc.)
5. Click OK

### Export as NFO

1. Edit → Preferences
2. Select "NFO" tab
3. Check "Enable NFO Generation"
4. Click OK
5. Files will generate during processing

## Settings

### Quick Access

**Preferences Dialog:**
- Menu: Edit → Preferences
- Shortcut: Ctrl+,

**Configuration File:**
- Location: `~/.media-manager/settings.json`
- Can edit directly with text editor

### Key Settings

| Setting | Purpose | Default |
|---------|---------|---------|
| Scan Paths | Directories to scan | Empty |
| Target Folders | Where to organize | Empty |
| Poster Auto-download | Download artwork | Disabled |
| Subtitle Languages | Which languages | English |
| NFO Export | Generate XML metadata | Enabled |

## File Organization

### Before Processing
```
~/Downloads/
├── Inception.2010.1080p.mkv
├── The.Dark.Knight.2008.BluRay.mkv
├── Breaking.Bad.S01E01.mkv
└── ...
```

### After Processing
```
~/Media/
├── Movies/
│   ├── Inception (2010)/
│   │   ├── Inception (2010).mkv
│   │   ├── Inception (2010).nfo
│   │   └── poster.jpg
│   └── The Dark Knight (2008)/
│       ├── The Dark Knight (2008).mkv
│       ├── The Dark Knight (2008).nfo
│       └── poster.jpg
└── TV Shows/
    └── Breaking Bad/
        └── Season 01/
            ├── Breaking Bad - S01E01 - Pilot.mkv
            ├── Breaking Bad - S01E01 - Pilot.nfo
            └── poster.jpg
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+Q | Quit |
| Ctrl+, | Preferences |
| Ctrl+F | Search |
| Ctrl+S | Start Scan |
| Ctrl+P | Process |
| F1 | Help |

## Troubleshooting

### App Won't Start

```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall
pip install --upgrade media-manager

# Check logs
cat ~/.media-manager/logs/app.log
```

### No Files Found

1. Check directory path exists
2. Verify files are supported (.mkv, .mp4, .avi, etc.)
3. Check file read permissions
4. Settings → Scan Settings → Check ignored directories

### Matches Uncertain

1. Use Manual Search for better results
2. Rename files to standard format:
   - Movies: "Title (Year).ext"
   - TV: "Show - SxxExx - Episode.ext"

### Files Not Processing

1. Check target directory is writable
2. Verify disk has free space
3. Check read/write permissions
4. See logs for details

## Getting Help

### Documentation
- **User Guide**: See `USAGE.md`
- **API Reference**: See `API.md`
- **Architecture**: See `ARCHITECTURE.md`

### Logs
```bash
# View logs
cat ~/.media-manager/logs/app.log

# Watch logs in real-time
tail -f ~/.media-manager/logs/app.log

# Search for errors
grep ERROR ~/.media-manager/logs/app.log
```

### Online
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Documentation: Full guides included

## Next Steps

1. ✓ Install application
2. ✓ Scan sample directory
3. ✓ Review and accept matches
4. ✓ Configure preferences
5. → Read full documentation (USAGE.md)
6. → Explore API (API.md)
7. → Contribute (CONTRIBUTING.md)

## Tips & Tricks

### Organize Large Libraries

```bash
# Process in batches
# Scan → Process → Clear cache → Scan again
```

### Better Matching

```bash
# Improve filenames first:
# Movie: "Title (YYYY).ext"
# TV: "Show - SxxEyy - Title.ext"

# Then scan for better matches
```

### Disk Space Management

```bash
# Clear old caches
# Preferences → Posters → Clear Cache
# Preferences → Subtitles → Clear Cache

# Monitor usage
du -sh ~/.media-manager/
```

### Batch Operations

```bash
# Process multiple directories
# Add multiple paths in Scan Settings
# Start single scan
```

## Common Workflows

### Workflow 1: New Library (30 min for 100 files)

```
1. Create media directory: ~/media/
2. Copy/move files there
3. media-manager → Matching tab
4. Add Directory → ~/media/
5. Start Scan (2-5 min)
6. Review matches (5 min)
7. Process All → Choose options (2 min)
8. Done! Check ~/media/ for organized library
```

### Workflow 2: Mixed Library

```
1. Scan specific subdirectories:
   - Add: ~/Downloads/movies
   - Add: ~/Downloads/tv_shows
2. Start Scan
3. Fix mismatches manually
4. Process with move to target folders
5. Clean up ~/Downloads
```

### Workflow 3: Subtitles Only

```
1. Organize media first
2. Edit → Preferences → Subtitles
3. Enable download
4. Select languages
5. Edit → Preferences → General
6. Set target folder
7. Scan library
8. Accept all matches
9. Process (subtitles only)
```

## Uninstall

```bash
# Remove application
pip uninstall media-manager

# Remove settings and cache
rm -rf ~/.media-manager/

# For development
rm -rf venv/
```

## Upgrade

```bash
# Check current version
media-manager --version

# Upgrade to latest
pip install --upgrade media-manager

# Verify
media-manager --version
```

---

**Questions?** Check `USAGE.md` for comprehensive documentation!

**Want to contribute?** See `CONTRIBUTING.md` for guidelines.

**Need API details?** Check `API.md` for full reference.

**Interested in architecture?** See `ARCHITECTURE.md` for design details.
