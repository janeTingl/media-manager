# Media Manager

A modern PySide6-based media management application built with Python.

> **📚 New to the project?** Start with [QUICK_START.md](QUICK_START.md) (5 minutes) or check the [DOCUMENTATION.md](DOCUMENTATION.md) index for complete guides.

## Features

- **Cross-platform GUI** built with PySide6 (Qt6)
- **Modular architecture** with dependency injection
- **Persistent settings** with JSON storage and QSettings fallback
- **Structured logging** with file output
- **Comprehensive testing** with pytest and pytest-qt
- **Performance monitoring** with automated benchmarks and regression detection
- **Modern tooling** with ruff, black, mypy, and pytest

## Project Structure

```
media-manager/
├── src/
│   └── media_manager/
│       ├── __init__.py          # Package initialization
│       ├── main.py              # Application entry point
│       ├── main_window.py       # Main GUI window
│       ├── settings.py          # Settings management
│       ├── logging.py           # Logging configuration
│       └── services.py          # Dependency injection
├── tests/
│   ├── conftest.py              # Pytest configuration
│   ├── test_smoke.py            # Smoke tests
│   └── test_settings.py         # Settings tests
├── pyproject.toml               # Project configuration
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip or poetry package manager

### Building and Distribution

### Cross-Platform Builds

The project includes a unified build system that supports multiple platforms:

```bash
# Build for current platform with packages
python build.py --package

# Build for all platforms (requires different OS environments)
python build.py --platform all --package

# Build with code signing (requires setup)
python build.py --platform macos --sign --package
```

### Platform-Specific Scripts

- **Windows**: `build_windows.py` - Creates .exe with installer
- **macOS**: `build_macos.py` - Creates .app bundle and .dmg
- **Unified**: `build.py` - Cross-platform build interface

### Build Configuration

Shared configuration is managed in `build_config.py`:

- PyInstaller spec generation
- Platform-specific settings
- Dependency management
- Icon and resource handling

### Continuous Integration

GitHub Actions workflows handle automated builds:

- **Windows builds** on `windows-latest`
- **macOS builds** on `macos-latest`
- **Artifact uploads** for distribution
- **Smoke tests** for verification
- **PyPI publishing** on tags

### Testing Builds

Smoke tests verify built executables:

```bash
# Run build smoke tests
python -m pytest tests/test_build_smoke.py -v

# Test specific platform builds
python -m pytest tests/test_build_smoke.py::TestBuildSmoke::test_executable_exists -v
```

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd media-manager
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

   Or using poetry:
   ```bash
   poetry install --with dev
   ```

### Production Installation

#### From PyPI (Recommended)

```bash
pip install media-manager
```

#### Pre-built Binaries

Download pre-built executables from the [Releases](https://github.com/your-repo/media-manager/releases) page:

- **Windows**: `media-manager.exe` with installer
- **macOS**: `Media Manager.app` with DMG installer
- **Linux**: AppImage (coming soon)

#### Building from Source

If you want to build the application yourself:

1. **Install build dependencies:**
   ```bash
   pip install -r build-requirements.txt
   ```

2. **Build for your platform:**
   ```bash
   # Build for current platform
   python build.py --package
   
   # Build for specific platform
   python build.py --platform windows --package
   python build.py --platform macos --package
   
   # Build for all platforms
   python build.py --platform all --package
   ```

3. **Find the built packages:**
   - Windows: `dist/media-manager.exe`, `package/media-manager-*.zip`
   - macOS: `dist/Media Manager.app`, `package/*.dmg`

## Usage

### Running the Application

#### Development Mode

```bash
# Using the installed command
media-manager

# Or directly with Python
python -m src.media_manager.main
```

#### From Source

```bash
python src/media_manager/main.py
```

### Application Interface

The main window consists of three resizable panes:

1. **Left Pane** - File system navigation tree
2. **Center Pane** - Tabbed content area with:
   - Library view
   - Recent files
   - Favorites
   - Search results
3. **Right Pane** - Properties and metadata

#### Menu Bar

- **File** - Open files, exit application
- **Edit** - Preferences and settings
- **View** - Toggle panes and view options
- **Help** - About dialog

#### Status Bar

Displays current status and item count

## Configuration

### Settings File

Settings are stored in `~/.media-manager/settings.json` in JSON format. The file includes:

- **API Keys** - External service authentication
- **Target Folders** - Default locations for different media types
- **Rename Templates** - Custom file naming patterns
- **Window State** - Saved window geometry and layout

### Example Settings File

```json
{
  "api_keys": {
    "tmdb": "your-tmdb-api-key",
    "tvdb": "your-tvdb-api-key"
  },
  "target_folders": {
    "movies": "/path/to/movies",
    "tv_shows": "/path/to/tv_shows",
    "images": "/path/to/images"
  },
  "rename_templates": {
    "movie": "{title} ({year})",
    "tv_episode": "{show_name} - S{season:02d}E{episode:02d} - {title}"
  },
  "window_geometry": "...",
  "window_state": "..."
}
```

### Logging

Logs are written to `~/.media-manager/logs/app.log` with the following levels:
- **DEBUG** - Detailed debugging information
- **INFO** - General information messages
- **WARNING** - Warning messages
- **ERROR** - Error messages

## Development

### Code Quality Tools

The project uses modern Python tooling:

- **Black** - Code formatting (88 character line length)
- **Ruff** - Linting and import sorting
- **MyPy** - Static type checking
- **Pytest** - Unit testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/media_manager

# Run specific test file
pytest tests/test_smoke.py

# Run with verbose output
pytest -v

# Run performance benchmarks
pytest tests/performance/ -m benchmark --benchmark-only

# Run tests excluding benchmarks (faster)
pytest -m "not benchmark"
```

### Performance Testing

The project includes comprehensive performance testing with automated regression detection:

```bash
# Run all performance benchmarks
python tests/performance/runner.py

# Run specific benchmark suite
python tests/performance/runner.py --suite database
python tests/performance/runner.py --suite ui
python tests/performance/runner.py --suite scanning
python tests/performance/runner.py --suite matching

# Generate performance report
python tests/performance/runner.py --report

# Set performance baseline
python tests/performance/runner.py --set-baseline
```

See [docs/performance.md](docs/performance.md) for detailed performance testing documentation.

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Fix ruff issues automatically
ruff check --fix src/ tests/

# Type checking with mypy
mypy src/
```

### Architecture

#### Dependency Injection

The application uses a simple service registry for dependency injection:

```python
from media_manager.services import get_service_registry, inject

# Register a service
registry = get_service_registry()
registry.register("SettingsService", settings_instance)

# Inject a service into a function
@inject("SettingsService")
def my_function(settings):
    return settings.get("some_key")
```

#### Settings Management

The `SettingsManager` class provides:
- JSON file persistence
- QSettings fallback for migration
- Type-safe getters/setters
- Specialized methods for common settings

#### Logging

The logging module provides:
- Centralized logging configuration
- File and console output
- Configurable log levels
- Structured log formatting

### Adding New Features

1. **Create new modules** in `src/media_manager/`
2. **Add tests** in `tests/`
3. **Register services** if needed
4. **Update settings schema** if adding new configuration
5. **Run tests** to ensure compatibility

### GUI Development

When working with GUI components:

1. **Use pytest-qt** for GUI testing
2. **Mark GUI tests** with `@pytest.mark.gui`
3. **Test window creation** and basic interactions
4. **Verify signal/slot connections**

## Troubleshooting

### Common Issues

#### Application Won't Start

1. **Check Python version** - Requires Python 3.8+
2. **Verify PySide6 installation** - `pip install PySide6`
3. **Check display server** - On Linux, ensure X11/Wayland is available

#### Settings Not Saving

1. **Check permissions** - Ensure `~/.media-manager/` is writable
2. **Verify JSON syntax** - Invalid JSON will fallback to QSettings
3. **Check disk space** - Ensure sufficient space for settings file

#### GUI Not Displaying

1. **Display environment** - Set `DISPLAY` on Linux if needed
2. **Virtual display** - Use `xvfb-run` on headless systems
3. **Platform compatibility** - Ensure Qt platform plugins are available

### Getting Help

- Check the logs in `~/.media-manager/logs/app.log`
- Run tests to verify installation
- Check the GitHub issues for known problems

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Style

- Follow PEP 8 with Black formatting
- Use type hints where appropriate
- Write descriptive docstrings
- Add tests for new features

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### v0.1.0 - Initial Release

- Basic PySide6 application framework
- Main window with navigation panes
- Settings management with JSON persistence
- Logging configuration
- Dependency injection system
- Comprehensive test suite
- Development tooling setup