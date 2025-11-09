# Media Manager v0.1.0 Installation Guide

## Quick Install (Windows)

1. **Download** `media-manager.exe` from GitHub Release Assets
2. **Run** the executable (double-click)
3. **Done!** No installation or configuration needed

The application will automatically create configuration files on first run.

## System Requirements

### Windows (for .exe)
- ✅ Windows 7 or later (64-bit)
- ✅ 500 MB free disk space
- ✅ .NET Framework 4.5 or later (usually pre-installed)
- ✅ Optional: Internet connection (for downloads)

### macOS / Linux (build from source)
- ✅ Python 3.8 or later
- ✅ 1 GB free disk space
- ✅ Git (for cloning repository)
- ✅ C compiler (for some dependencies)

## Installation Methods

### Method 1: Windows Executable (Easiest)

**Steps:**
1. Go to [GitHub Releases](https://github.com/your-org/media-manager/releases)
2. Find v0.1.0 release
3. Download `media-manager.exe`
4. Double-click to run

**Advantages:**
- No installation required
- No dependencies to install
- Works immediately
- Can delete to uninstall (see below)

**Uninstall:**
- Delete the executable
- Optional: Delete `%USERPROFILE%\.media-manager\` folder (settings & cache)

---

### Method 2: Python Package (Recommended for Linux/macOS)

**Installation:**
```bash
# Using pip (easiest)
pip install media-manager

# Then run:
media-manager
```

**Upgrade:**
```bash
pip install --upgrade media-manager
```

**Uninstall:**
```bash
pip uninstall media-manager
```

---

### Method 3: Build from Source

**Prerequisites:**
- Python 3.8+
- Git
- C compiler (for some dependencies)

**Steps:**

1. **Clone Repository**:
```bash
git clone https://github.com/your-org/media-manager.git
cd media-manager
```

2. **Install Dependencies**:
```bash
pip install -e .
```

Or for development:
```bash
pip install -e ".[dev]"
```

3. **Run Application**:
```bash
media-manager
```

**Uninstall:**
```bash
pip uninstall media-manager
```

---

### Method 4: Docker (Linux/macOS)

**Prerequisite:** Docker installed

**Steps:**
```bash
# Clone repository
git clone https://github.com/your-org/media-manager.git
cd media-manager

# Start with docker-compose
docker-compose up -d

# Or build and run manually
docker build -t media-manager .
docker run -it media-manager media-manager
```

See [docker-compose.yml](../../docker-compose.yml) for configuration.

---

## First Run Setup

### Configuration Directory

After first run, configuration files are created in:

| OS | Location |
|----|----------|
| Windows | `%USERPROFILE%\.media-manager\` |
| macOS | `~/.media-manager/` |
| Linux | `~/.media-manager/` |

**Contents:**
```
.media-manager/
├── settings.json          # Application preferences
├── logs/
│   └── app.log           # Application logs
├── poster-cache/         # Downloaded posters
└── subtitle-cache/       # Downloaded subtitles
```

### First Launch

1. **Application Starts**:
   - Initializes settings
   - Creates configuration directories
   - Shows main window

2. **Configure Paths**:
   - Open "Preferences" (Windows menu)
   - Go to "Scan Settings" tab
   - Add your media folders
   - Click "Apply"

3. **Start Using**:
   - Go to "Scan" tab
   - Click "Scan" button
   - Application scans your media folders

## Verification

### Test Installation

**Windows (.exe):**
```cmd
# Run the executable
media-manager.exe

# Should open the GUI
# If not, check for error messages in Command Prompt
```

**Python Package:**
```bash
# Run the command
media-manager

# Should open the GUI
```

**Verify Version:**
Check "Help" → "About" in the application menu for version 0.1.0.

## Troubleshooting

### Windows Executable Won't Run

**Issue:** "Windows protected your PC" or "Unknown Publisher" warning

**Solution:**
- Click "More info"
- Click "Run anyway"
- This is normal for unsigned executables

**Issue:** "The application failed to start" or similar error

**Solution:**
1. Check Windows 7+ requirement
2. Verify 64-bit Windows version
3. Try running from Command Prompt for error details:
```cmd
cd Downloads
media-manager.exe
```

### Python Package Installation Issues

**Issue:** `pip install` fails with permission error

**Solution:**
- Use `--user` flag: `pip install --user media-manager`
- Or use virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows Command Prompt
pip install media-manager
```

**Issue:** `ModuleNotFoundError: No module named 'PySide6'`

**Solution:**
```bash
# Reinstall with all dependencies
pip install --upgrade --force-reinstall media-manager
```

### Configuration Issues

**Issue:** Settings not saving or loading

**Solution:**
1. Check `.media-manager/` directory permissions
   - Must be writable by user
2. Check disk space (need at least 100 MB free)
3. Check logs at `.media-manager/logs/app.log`
4. Delete `settings.json` and restart (resets to defaults)

### Application Won't Start

**Common Issues:**
- Missing dependencies
- Corrupted settings file
- Insufficient permissions

**Debug Steps:**
1. Delete `.media-manager/settings.json` and restart
2. Check logs in `.media-manager/logs/app.log`
3. If from source, reinstall: `pip install --force-reinstall media-manager`
4. Check Python version: `python --version` (need 3.8+)

## Advanced Installation

### Virtual Environment (Recommended for Development)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install in virtual environment
pip install media-manager

# Deactivate when done
deactivate
```

### Development Installation

For modifying source code:

```bash
# Clone repository
git clone https://github.com/your-org/media-manager.git
cd media-manager

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run application
media-manager
```

### Build Executable (Windows)

To create your own `media-manager.exe`:

```bash
# Install build tools
pip install -r build-requirements.txt

# Build executable
python build_windows.py

# Output: dist\media-manager.exe
```

See [BUILD_WINDOWS.md](BUILD_WINDOWS.md) for detailed instructions.

## System Integration

### Windows Start Menu

**Method 1: Executable in Start Menu**
1. Right-click `media-manager.exe`
2. Send to → Desktop (create shortcut)
3. Right-click and pin to Start Menu

**Method 2: Installer** (future versions)
- Will automatically create Start Menu shortcuts

### Desktop Shortcut

**Windows:**
1. Right-click `media-manager.exe`
2. Create shortcut
3. Move shortcut to Desktop

**macOS/Linux:**
1. Create `.desktop` file in `~/.local/share/applications/`
2. Or use application menu to create launcher

## Uninstallation

### Windows Executable

**Complete Removal:**
1. Delete `media-manager.exe`
2. Delete `%USERPROFILE%\.media-manager\` folder (settings & cache)

### Python Package

**Remove Application:**
```bash
pip uninstall media-manager
```

**Remove Settings (optional):**
```bash
# Linux/macOS
rm -rf ~/.media-manager/

# Windows PowerShell
Remove-Item $PROFILE\.media-manager -Recurse
```

### Docker

**Remove Container:**
```bash
docker-compose down
# or
docker rm media-manager
docker rmi media-manager
```

## Update to New Version

### Windows Executable
1. Delete old `media-manager.exe`
2. Download new version
3. Run new executable

### Python Package
```bash
pip install --upgrade media-manager
```

### From Source
```bash
cd media-manager
git pull
pip install -e . --upgrade
```

## Next Steps

1. **Configure Your Library**:
   - Open Preferences
   - Set media scan paths
   - Configure poster/subtitle options

2. **Scan Your Media**:
   - Click Scan tab
   - Click Scan button
   - Wait for scan to complete

3. **Review Matches**:
   - Go to Matching tab
   - Check automatic matches
   - Manually search if needed

4. **Download Assets**:
   - Download posters and artwork
   - Download subtitles
   - Generate NFO files

For detailed usage, see [QUICK_START.md](../../QUICK_START.md) and [USAGE.md](../../USAGE.md).

## Getting Help

- **Documentation**: See [QUICK_START.md](../../QUICK_START.md)
- **Issues**: Report at https://github.com/your-org/media-manager/issues
- **Discussions**: Ask at https://github.com/your-org/media-manager/discussions
- **Logs**: Check `~/.media-manager/logs/app.log` for errors

---

**Installation Help**: Most issues can be resolved by checking the logs or running from Command Prompt to see error messages.

Happy managing! 🎬
