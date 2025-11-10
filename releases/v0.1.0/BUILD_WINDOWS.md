# Building media-manager.exe for Windows

This guide explains how to build the Windows executable (`media-manager.exe`) for Media Manager v0.1.0.

## Prerequisites

### System Requirements
- **OS**: Windows 7 or later (64-bit)
- **Python**: 3.8 - 3.12 (64-bit)
- **Visual C++ Build Tools**: Required by some dependencies
- **Disk Space**: At least 2 GB for build and dependencies

### Software Installation

1. **Install Python 3.11** (64-bit):
   - Download from https://www.python.org/downloads/
   - Enable "Add Python to PATH" during installation
   - Verify: `python --version` in Command Prompt

2. **Install Visual C++ Build Tools**:
   - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++"

3. **Clone Repository**:
   ```cmd
   git clone https://github.com/your-org/media-manager.git
   cd media-manager
   git checkout release-v0.1.0-upload-media-manager-exe-e01
   ```

## Quick Build (Recommended)

### Using Python Script

```cmd
# Install build dependencies
pip install -r build-requirements.txt

# Build executable
python build_windows.py
```

This creates:
- `dist\media-manager.exe` - Single executable file
- `package\media-manager-portable-0.1.0\` - Portable package
- `package\media-manager-installer-0.1.0\` - Installer package

### Using Makefile (if GNU Make installed)

```cmd
make -f Makefile.windows all
```

## Manual Build with PyInstaller

```cmd
# Install dependencies
pip install PySide6>=6.5.0
pip install pyinstaller>=5.0.0

# Run PyInstaller
pyinstaller --clean --noconfirm media-manager.spec
```

## Build Output

### Executable
- **Location**: `dist\media-manager.exe`
- **Size**: ~59 MB (includes all dependencies)
- **Type**: Single-file, no installation required
- **Requirements**: Windows 7+ (x64), .NET Framework 4.5+

### Verification

Test the executable:
```cmd
# Basic test (may not show output for GUI app)
dist\media-manager.exe

# Or from dist directory:
cd dist
media-manager.exe
```

## Troubleshooting

### Import Errors

If you see import errors, ensure all dependencies are installed:
```cmd
pip install --upgrade -r build-requirements.txt
pip install --break-system-packages PySide6 pyinstaller
```

### Visual C++ Build Tools Missing

```cmd
# Some packages need compilation
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### Python Path Issues

```cmd
# If python is not found, use full path
C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe build_windows.py
```

### Large Build Size

The 59MB size includes:
- Python runtime
- PySide6 GUI framework  
- All Qt6 libraries
- All dependencies

This is typical for PyInstaller builds with PySide6.

## Cross-Platform Notes

- **Windows Build**: Creates `.exe` file (this guide)
- **macOS Build**: Creates app bundle via PyInstaller
- **Linux Build**: Creates ELF binary
- **Source Distribution**: `pip install media-manager`

Each platform requires building on that platform.

## Performance Optimization

For faster startup, you can enable bytecode caching:
```cmd
pyinstaller --clean --noconfirm --onedir media-manager.spec
```

This creates a multi-file distribution which loads faster but requires separate files.

## Code Signing (Optional)

For production releases, sign the executable:
```cmd
# Requires a code signing certificate
signtool sign /f certificate.pfx /p password dist\media-manager.exe
```

## Version Specific Notes

### v0.1.0 MVP
- First release with PyInstaller
- No code signing (optional for future releases)
- Single-file executable format

### Building Previous Versions

Each release branch has its own build configuration:
```cmd
git checkout release-v0.1.0-upload-media-manager-exe-e01
python build_windows.py
```

## Support

For build issues:
1. Check the troubleshooting section above
2. Review [INSTALLATION.md](../../INSTALLATION.md) for system requirements
3. Open an issue on GitHub with:
   - Python version: `python --version`
   - Windows version: `winver`
   - Error message and last 50 lines of output

## Next Steps

After building:

1. **Test Locally**:
   - Run `dist\media-manager.exe`
   - Test basic functionality
   - Check Help → About for version info

2. **Create Distribution Package**:
   - Use `build_windows.py` output files
   - Package as ZIP for portability
   - Create installer if needed

3. **Upload to Release**:
   - Navigate to GitHub Release
   - Upload `dist\media-manager.exe`
   - Add your platform signature to release notes

---

Built with PyInstaller 6.16+ and PySide6 6.5+
