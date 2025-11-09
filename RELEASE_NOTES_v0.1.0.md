Release Notes - Media Manager v0.1.0

🎉 Initial MVP Release

This is the first public release of Media Manager, a modern PySide6-based media management application.

## Key Features

### 📁 Media Scanning
- Intelligent filesystem scanning with configurable paths
- Automatic movie and TV episode detection
- Quality and release information extraction
- Recursive directory traversal with ignore patterns

### 🔍 Media Matching
- Automatic media matching with confidence scores
- Manual search workflow
- Match status tracking (PENDING, MATCHED, MANUAL, SKIPPED)
- Batch matching support

### 🎨 Poster Management
- Multiple poster types (poster, fanart, banner, thumbnail)
- Size selection and intelligent caching
- Progress tracking with retry logic

### 📝 Subtitle Support
- 10 language support (EN, ES, FR, DE, IT, PT, RU, ZH, JA, KO)
- Multiple format support (SRT, ASS, SUB, VTT, SSA)
- Provider abstraction with OpenSubtitles framework

### 📄 Metadata Export
- XML NFO file generation for media centers
- UTF-8 encoding with full Unicode support
- Cast member and ID handling

### 🖥️ Modern GUI
- Cross-platform PySide6/Qt6 interface
- Tab-based navigation with resizable panes
- Progress tracking and status indicators
- Comprehensive preferences dialog

## Installation

### From PyPI (recommended)
```bash
pip install media-manager
```

### From Source
```bash
git clone https://github.com/your-org/media-manager.git
cd media-manager
pip install -e .
```

### With Docker
```bash
docker-compose up -d
```

## Quick Start

1. Launch the application: `media-manager-demo`
2. Configure scan paths in preferences
3. Scan your media library
4. Review and confirm matches
5. Export metadata and download artwork

## Requirements

- Python 3.8 or higher
- PySide6 (automatically installed)
- Linux, macOS, or Windows

## Known Limitations

- Uses mock data for demonstration (TMDB/TVDB integration planned for v0.2.0)
- No persistent database (metadata stored in JSON files)
- Desktop application only (web interface planned for future versions)

## Documentation

- [Quick Start](QUICK_START.md)
- [Installation Guide](INSTALLATION.md)
- [User Manual](USAGE.md)
- [API Reference](API.md)
- [Architecture](ARCHITECTURE.md)

## Support

- Report issues on [GitHub Issues](https://github.com/your-org/media-manager/issues)
- Ask questions in [GitHub Discussions](https://github.com/your-org/media-manager/discussions)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

Built with ❤️ using PySide6 and modern Python practices.
