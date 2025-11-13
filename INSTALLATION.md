# Media Manager - Installation Guide

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Methods](#installation-methods)
3. [Development Setup](#development-setup)
4. [Troubleshooting](#troubleshooting)
5. [Platform-Specific Notes](#platform-specific-notes)

## System Requirements

### Minimum Requirements

- **Python**: 3.8 or higher (3.9+ recommended)
- **OS**: Linux, macOS, or Windows
- **RAM**: 512 MB minimum
- **Disk Space**: 100 MB for installation + space for media cache

### Supported Versions

| Python Version | Status | Notes |
|---|---|---|
| 3.8 | Supported | Legacy support |
| 3.9 | Supported | Recommended |
| 3.10 | Supported | Recommended |
| 3.11 | Supported | Latest stable |
| 3.12 | Supported | Latest release |

## Installation Methods

### Method 1: Pre-built Binaries (Recommended)

Download pre-built executables from the [Releases](https://github.com/your-username/media-manager/releases) page:

#### Windows
1. Download `media-manager.exe` or `media-manager-installer-*.zip`
2. Extract the ZIP file
3. Run `media-manager.exe` or `install.bat` (for installer version)

#### macOS
1. Download `Media Manager-*.dmg`
2. Open the DMG file
3. Drag `Media Manager.app` to Applications folder
4. Launch from Applications or Launchpad

#### Linux (Coming Soon)
- AppImage format will be available in future releases

### Method 2: Production Installation (PyPI)

**Prerequisites:**
- pip (comes with Python 3.4+)
- Network access to PyPI

**Steps:**

```bash
# Install the latest version
pip install media-manager

# Verify installation
media-manager --version
```

### Method 2: Development Installation

This method is ideal for contributors and developers who want to modify the code.

**Prerequisites:**
- Git
- Python 3.8+
- pip and virtualenv

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/your-username/media-manager.git
cd media-manager

# 2. Create and activate virtual environment
python -m venv venv

# On Linux/macOS
source venv/bin/activate

# On Windows
venv\Scripts\activate

# 3. Install in development mode with all dependencies
pip install -e ".[dev]"

# 4. Verify installation
python -m media_manager.main --version
```

### Method 3: Poetry Installation

**Prerequisites:**
- Poetry (https://python-poetry.org/docs/#installation)

**Steps:**

```bash
# Clone the repository
git clone https://github.com/your-username/media-manager.git
cd media-manager

# Install with all dependencies
poetry install --with dev

# Activate the virtual environment
poetry shell

# Run the application
media-manager
```

### Method 4: Building from Source

This method is for developers who want to build executables from source code.

**Prerequisites:**
- Python 3.8+
- Git
- Platform-specific build tools

**Steps:**

```bash
# 1. Clone repository
git clone https://github.com/your-username/media-manager.git
cd media-manager

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install build dependencies
pip install -r build-requirements.txt

# 4. Build for your platform
python build.py --package

# 5. Find built packages
# Windows: dist/media-manager.exe, package/media-manager-*.zip
# macOS: dist/Media Manager.app, package/*.dmg
```

**Platform-Specific Builds:**

```bash
# Build only for Windows
python build.py --platform windows --package

# Build only for macOS
python build.py --platform macos --package

# Build with code signing (macOS only, requires setup)
python build.py --platform macos --sign --package

# Build for all platforms (requires different OS environments)
python build.py --platform all --package
```

## Development Setup

### Complete Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/your-username/media-manager.git
cd media-manager

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install development dependencies
pip install -e ".[dev]"

# 4. Verify all tools are installed
python -c "import pytest; import black; import ruff; import mypy; print('All tools installed!')"

# 5. Run tests to verify setup
pytest

# 6. Run code quality checks
black --check src/ tests/
ruff check src/ tests/
mypy src/

# 7. (Optional) Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Running the Application in Development

```bash
# Method 1: Using the installed command
media-manager

# Method 2: Using Python module
python -m media_manager.main

# Method 3: Direct script execution
python src/media_manager/main.py
```

### Running the Demo Application

```bash
# Demo with pre-built example data
media-manager-demo

# Or directly
python -m media_manager.demo_integration
```

## Dependency Installation

### Required Dependencies

The application has only one required dependency:

- **PySide6**: Qt6 bindings for Python (automatic with installation)

### Development Dependencies

These are installed with the `[dev]` extra:

- **pytest**: Testing framework
- **pytest-qt**: Qt testing utilities
- **black**: Code formatter
- **ruff**: Fast Python linter
- **mypy**: Static type checker
- **types-PySide6**: Type stubs for PySide6

### Optional Dependencies

Future versions may support optional features:

```bash
# For API integrations (when available)
pip install requests

# For advanced image processing
pip install Pillow
```

## Configuration

### First Run Setup

On first run, the application creates the configuration directory:

```
~/.media-manager/
├── settings.json           # Application settings
├── logs/
│   └── app.log             # Application logs
├── subtitle-cache/         # Downloaded subtitles
└── poster-cache/           # Downloaded posters
```

### Configuration Files

#### settings.json

Located at `~/.media-manager/settings.json`. Example:

```json
{
  "api_keys": {
    "tmdb": "your-tmdb-api-key",
    "tvdb": "your-tvdb-api-key"
  },
  "scan_paths": [
    "/path/to/media",
    "/mnt/storage/videos"
  ],
  "poster_settings": {
    "auto_download": true,
    "cache_enabled": true,
    "cache_size_mb": 500
  },
  "subtitle_settings": {
    "enabled_languages": ["en", "es", "fr"],
    "auto_download": false
  }
}
```

### Environment Variables

Create a `.env` file in the project root (optional):

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# API endpoints (when needed)
TMDB_API_KEY=your_key_here
TVDB_API_KEY=your_key_here

# Cache configuration
CACHE_DIR=~/.media-manager/cache
```

## Troubleshooting

### Common Installation Issues

#### Issue: "python command not found"

**Solution:**
- Ensure Python is installed: `python --version`
- On some systems, use `python3` instead of `python`
- Add Python to your PATH environment variable

#### Issue: "PySide6 fails to install"

**Solution:**
```bash
# Update pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel

# Try installation again
pip install -e ".[dev]"

# If still failing, try pre-built wheels
pip install --only-binary :all: PySide6
```

#### Issue: "No module named 'media_manager'"

**Solution:**
```bash
# Ensure you're in the project root directory
cd /path/to/media-manager

# Reinstall in development mode
pip install -e "."

# Verify installation
python -c "import media_manager; print(media_manager.__file__)"
```

#### Issue: "ImportError: cannot import name 'Signal' from 'PySide6.QtCore'"

**Solution:**
```bash
# Upgrade PySide6
pip install --upgrade PySide6

# Verify version
python -c "import PySide6; print(PySide6.__version__)"
```

### GUI-Related Issues

#### Issue: "No display" error on Linux

**Solution:**
```bash
# For headless systems, use virtual display
sudo apt-get install xvfb
xvfb-run media-manager

# Or set display explicitly
export DISPLAY=:0
media-manager
```

#### Issue: GUI doesn't render on macOS

**Solution:**
```bash
# Install platform-specific dependencies
pip install --upgrade PySide6

# Try running with Python 3.10+
python3.10 -m media_manager.main
```

#### Issue: Wayland compatibility (Linux)

**Solution:**
```bash
# Force X11 backend
export QT_QPA_PLATFORM=xcb
media-manager

# Or try native Wayland
export QT_QPA_PLATFORM=wayland
media-manager
```

### Performance Issues

#### Issue: Application starts slowly

**Solution:**
- First startup caches dependencies, subsequent runs are faster
- Check available disk space
- Close other applications to free up resources
- Check logs: `~/.media-manager/logs/app.log`

#### Issue: High memory usage

**Solution:**
- Reduce scan paths
- Limit subtitle languages
- Clear caches: Settings → Clear Cache
- Monitor with: `ps aux | grep media-manager`

## Platform-Specific Notes

### Linux

**Package Dependencies (Ubuntu/Debian):**

```bash
# Qt runtime dependencies
sudo apt-get install libqt6gui6 libqt6core6 libqt6widgets6

# For development
sudo apt-get install python3-dev python3-pip python3-venv

# Optional: For better GUI rendering
sudo apt-get install libxkbcommon0 libdbus-1-3
```

**Virtual Display (Headless):**

```bash
# Install xvfb
sudo apt-get install xvfb

# Run application
xvfb-run media-manager
```

### macOS

**Using Homebrew:**

```bash
# Install Python
brew install python@3.11

# Or update existing
brew upgrade python@3.11

# Install media-manager
pip install media-manager
```

**M1/M2 Chip (ARM64):**

```bash
# Use native Python
arch -arm64 python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Windows

**Using Windows Package Manager:**

```bash
# Install Python
winget install Python.Python.3.11

# Or use Chocolatey
choco install python

# Install media-manager
pip install media-manager
```

**Virtual Environment Activation:**

```bash
# Create venv
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Command Prompt)
venv\Scripts\activate.bat
```

**Path Issues:**

- Ensure Python is in PATH
- Use `py` launcher if available: `py -3.11 -m venv venv`

## Verification

After installation, verify everything works:

```bash
# 1. Check Python version
python --version  # Should be 3.8+

# 2. Check package installation
pip show media-manager

# 3. Check dependencies
pip show PySide6 pytest black ruff mypy

# 4. Run smoke tests
pytest tests/test_smoke.py -v

# 5. Start the application
media-manager

# 6. Check logs
cat ~/.media-manager/logs/app.log
```

## Uninstallation

### Complete Removal

```bash
# Remove package
pip uninstall media-manager

# Remove configuration and cache
rm -rf ~/.media-manager

# Remove virtual environment (if used)
rm -rf /path/to/venv
```

## Upgrade

### Updating to Latest Version

```bash
# Update installed version
pip install --upgrade media-manager

# Or with pip showing what changed
pip install --upgrade --force-reinstall media-manager

# Verify upgrade
media-manager --version
```

## Getting Help

- **Official Documentation**: https://github.com/your-username/media-manager/wiki
- **Issue Tracker**: https://github.com/your-username/media-manager/issues
- **Discussions**: https://github.com/your-username/media-manager/discussions
- **Logs**: `~/.media-manager/logs/app.log`
