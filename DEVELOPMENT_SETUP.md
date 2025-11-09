# Media Manager - Development Setup Guide

## Quick Start

### Prerequisites
- Python 3.8+ (tested with 3.12.3)
- pip package manager
- Git

### Installation

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd media-manager

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -e ".[dev]"
pip install requests

# 4. (Optional) Install system libraries for GUI support
sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 xvfb

# 5. Verify installation
media-manager --help
```

## Running the Application

### GUI Mode
```bash
# Using entry point
media-manager

# Using Python module
python -m src.media_manager.main

# Demo mode with sample workflows
media-manager-demo
```

### Headless Testing
```bash
# With virtual X server
xvfb-run -a media-manager

# With offscreen rendering
QT_QPA_PLATFORM=offscreen media-manager
```

## Testing

### Run All Tests
```bash
# With xvfb (recommended)
xvfb-run -a pytest tests/ -v

# Quick test summary
xvfb-run -a pytest tests/ -q --tb=no
```

### Run Specific Test Categories
```bash
# Core application tests
xvfb-run -a pytest tests/test_smoke.py -v

# File scanning tests
pytest tests/test_scanner.py -v

# Settings tests
pytest tests/test_settings.py -v

# NFO generation tests
pytest tests/test_nfo_*.py -v

# Subtitle tests
pytest tests/test_subtitle_*.py -v

# Non-GUI tests only (fast)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_scanner.py tests/test_settings.py tests/test_nfo_*.py tests/test_subtitle_*.py -v
```

### Test Coverage
```bash
xvfb-run -a pytest tests/ --cov=src/media_manager --cov-report=html
# Open htmlcov/index.html in browser
```

## Code Quality

### Formatting
```bash
# Format all code
black src/ tests/

# Format specific file
black src/media_manager/main.py
```

### Linting
```bash
# Check for issues
ruff check src/ tests/

# Fix automatically fixable issues
ruff check --fix src/ tests/
```

### Type Checking
```bash
# Check types
mypy src/

# Strict mode
mypy src/ --strict
```

## Project Structure

```
media-manager/
├── src/media_manager/          # Main application
│   ├── main.py                 # Entry point
│   ├── main_window.py          # Main GUI window
│   ├── models.py               # Data models
│   ├── scanner.py              # File scanning
│   ├── scan_engine.py          # Scan workflow
│   ├── settings.py             # Settings management
│   ├── logging.py              # Logging setup
│   ├── services.py             # Service registry (DI)
│   ├── workers.py              # Background workers
│   ├── match_manager.py        # Match workflow
│   ├── match_resolution_widget.py # Match UI
│   ├── scan_queue_widget.py    # Queue UI
│   ├── poster_downloader.py    # Poster downloads
│   ├── poster_settings_widget.py # Poster settings
│   ├── subtitle_provider.py    # Subtitle providers
│   ├── subtitle_downloader.py  # Subtitle downloads
│   ├── nfo_exporter.py         # NFO file generation
│   ├── renamer.py              # File renaming
│   └── demo_integration.py     # Demo workflow
│
├── tests/                       # Test suite (149 tests)
│   ├── conftest.py             # Pytest configuration
│   ├── test_smoke.py           # Basic functionality tests
│   ├── test_scanner.py         # Scanner tests
│   ├── test_settings.py        # Settings tests
│   ├── test_nfo_*.py           # NFO tests
│   ├── test_subtitle_*.py      # Subtitle tests
│   ├── test_poster_*.py        # Poster tests
│   ├── test_match_*.py         # Match workflow tests
│   └── test_scan_engine.py     # Scan engine tests
│
├── pyproject.toml              # Project configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # User documentation
├── TEST_REPORT.md             # Test results and status
├── DEVELOPMENT_SETUP.md       # This file
├── .gitignore                 # Git ignore rules
└── Makefile                   # Development commands (optional)
```

## Key Features

### Implemented & Tested ✅
- **File Scanning:** Recursive directory scanning for media files
- **Settings Management:** JSON-based persistent settings
- **NFO Generation:** XML metadata files for movies and TV episodes
- **Subtitles:** Search, download, and cache management
- **File Organization:** Move/copy files with conflict handling
- **GUI Framework:** Qt-based modern interface
- **Logging:** Structured logging to files and console

### Partially Implemented ⚠️
- **Poster Download:** Implementation ready, mock testing issues
- **API Integration:** Framework ready, needs API keys configuration

### Framework Ready 📋
- **TMDB Integration:** File structure ready
- **TheTVDB Integration:** File structure ready
- **Advanced Matching:** Workflow ready

## Configuration

### API Keys (Optional)
Create or edit `~/.media-manager/settings.json`:

```json
{
  "api_keys": {
    "tmdb": "your-tmdb-api-key",
    "tvdb": "your-tvdb-api-key"
  },
  "target_folders": {
    "movies": "/path/to/movies",
    "tv_shows": "/path/to/tv_shows"
  }
}
```

### Logging
Logs are written to:
- File: `~/.media-manager/logs/app.log`
- Console: DEBUG level during development

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
```bash
# Edit code
vim src/media_manager/your_module.py

# Add tests
vim tests/test_your_module.py
```

### 3. Run Tests
```bash
xvfb-run -a pytest tests/ -v
```

### 4. Check Code Quality
```bash
black src/ tests/
ruff check --fix src/ tests/
mypy src/
```

### 5. Commit and Push
```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

## Troubleshooting

### GUI Tests Failing
```bash
# Use xvfb
xvfb-run -a pytest tests/ -v

# Or offscreen mode
QT_QPA_PLATFORM=offscreen pytest tests/ -v

# Or skip GUI tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v
```

### Import Errors
```bash
# Reinstall in development mode
pip install -e ".[dev]" --force-reinstall

# Check installation
python -c "from src.media_manager.main import main; print('OK')"
```

### Missing Dependencies
```bash
# Check installed packages
pip list

# Install missing packages
pip install PySide6 pytest pytest-qt black ruff mypy requests

# Or reinstall all
pip install -e ".[dev]"
```

### Performance Issues
```bash
# Use faster test subset
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_scanner.py tests/test_settings.py -v

# Or specific test
pytest tests/test_smoke.py::TestApplicationSmoke::test_create_application -v
```

## Environment Variables

### Development
```bash
# Enable debug logging
LOG_LEVEL=DEBUG media-manager

# Use offscreen rendering
QT_QPA_PLATFORM=offscreen media-manager

# Skip pytest plugins
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v
```

## Resources

- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://github.com/psf/black)
- [Ruff Linter](https://github.com/astral-sh/ruff)
- [MyPy Type Checker](https://mypy.readthedocs.io/)

## Support

For issues or questions:
1. Check [TEST_REPORT.md](TEST_REPORT.md) for known issues
2. Review code comments and docstrings
3. Check application logs in `~/.media-manager/logs/`
4. Run tests with `-v` flag for detailed output

## Version Information

- **Python:** 3.12.3 (tested)
- **PySide6:** 6.10.0
- **Pytest:** 9.0.0
- **Black:** 25.9.0
- **Ruff:** 0.14.4
- **MyPy:** 1.18.2
