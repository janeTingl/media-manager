# Media Manager

A modern PySide6-based media management application built with Python.

## Features

- **Cross-platform GUI** built with PySide6 (Qt6)
- **Modular architecture** with dependency injection
- **Persistent settings** with JSON storage and QSettings fallback
- **Structured logging** with file output
- **Comprehensive testing** with pytest and pytest-qt
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

- **Python:** 3.8 or higher (tested with 3.12.3)
- **Package manager:** pip or poetry
- **System libraries (optional, for GUI display):**
  ```bash
  # Ubuntu/Debian
  sudo apt-get install -y libgl1 libegl1 libxkbcommon-x11-0 libxkbcommon0 xvfb

  # For headless testing with virtual display (optional)
  sudo apt-get install -y xvfb
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

   This installs:
   - PySide6 for GUI
   - pytest and pytest-qt for testing
   - ruff for linting
   - black for code formatting
   - mypy for type checking

4. **Install additional test dependencies:**
   ```bash
   pip install requests
   ```

5. **Verify installation:**
   ```bash
   python -m src.media_manager.main --help
   ```

### Production Installation

```bash
pip install media-manager
```

## Usage

### Running the Application

#### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Using the installed command
media-manager

# Or directly with Python
python -m src.media_manager.main

# Demo mode (comprehensive workflow demo)
media-manager-demo
```

#### Headless / Testing Environment

```bash
# With virtual X server (for CI/testing)
xvfb-run -a media-manager

# With offscreen rendering
QT_QPA_PLATFORM=offscreen media-manager
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

#### Test Environments

**Option 1: Virtual X Server (Recommended)**
```bash
# Run all tests with xvfb
xvfb-run -a pytest tests/ -v

# Run specific test file
xvfb-run -a pytest tests/test_smoke.py -v

# Run with coverage
xvfb-run -a pytest tests/ --cov=src/media_manager
```

**Option 2: Headless Mode**
```bash
# Run with offscreen rendering
QT_QPA_PLATFORM=offscreen pytest tests/ -v
```

**Option 3: Non-GUI Tests Only**
```bash
# Skip GUI tests entirely (fast)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_scanner.py tests/test_settings.py tests/test_nfo_exporter.py tests/test_subtitle_*.py -v
```

#### Test Results

Current test status:
- **Total:** 149 tests
- **Passing:** 128 (86%)
- **Failing:** 21 (mostly test infrastructure issues)

See [TEST_REPORT.md](TEST_REPORT.md) for detailed test results and known issues.

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