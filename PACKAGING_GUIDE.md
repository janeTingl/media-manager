# Media Manager Windows Executable Packaging Guide

This document provides comprehensive instructions for packaging the Media Manager application as a Windows executable (.exe) file using PyInstaller.

## Overview

The packaging process creates a standalone Windows executable that includes all dependencies and can run on any Windows system without requiring Python installation.

## Prerequisites

### System Requirements
- Windows 7 or higher
- 64-bit operating system
- Python 3.8 or higher installed
- 2GB free disk space for build process
- Internet connection for dependency installation

### Required Software
1. **Python 3.8+** - Download from [python.org](https://python.org)
2. **Git** - For cloning the repository (optional)
3. **UPX** - Optional executable compressor (recommended)

### Installing UPX (Optional but Recommended)
UPX reduces the executable size significantly:
1. Download from [upx.github.io](https://upx.github.io/)
2. Extract `upx.exe` to a directory in your PATH
3. Verify with: `upx --version`

## Build Process

### Option 1: Automated Build (Recommended)

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd media-manager
   ```

2. **Run the automated build script:**
   ```bash
   python build_windows.py
   ```

This script will:
- Install all dependencies
- Build the executable
- Test the executable
- Create portable and installer packages
- Generate release information

### Option 2: Manual Build with Makefile

1. **Install dependencies:**
   ```bash
   make -f Makefile.windows deps
   ```

2. **Build the executable:**
   ```bash
   make -f Makefile.windows build
   ```

3. **Create packages:**
   ```bash
   make -f Makefile.windows package
   ```

### Option 3: Direct PyInstaller Build

1. **Install dependencies:**
   ```bash
   pip install -r build-requirements.txt
   ```

2. **Build using spec file:**
   ```bash
   pyinstaller --clean --noconfirm media-manager.spec
   ```

## Build Configuration

### Spec File Configuration

The `media-manager.spec` file contains the PyInstaller configuration:

- **Entry Point**: `demo_integration.py` (demo version)
- **Mode**: `--onefile` (single executable)
- **GUI**: `--windowed` (no console window)
- **Compression**: UPX enabled (if available)
- **Hidden Imports**: All PySide6 modules and application modules

### Key Settings

```python
# Main executable configuration
exe = EXE(
    name='media-manager',
    console=False,        # GUI application
    windowed=True,        # No console window
    upx=True,            # Use UPX compression
    icon='icon.ico',     # Application icon
    version='version_info.txt',  # Version info
)
```

## Output Files

The build process generates the following files in the `package/` directory:

### 1. Executable
- **File**: `media-manager.exe`
- **Location**: `dist/media-manager.exe`
- **Size**: ~80-120 MB (varies with UPX)

### 2. Portable Package
- **Directory**: `media-manager-portable-0.1.0/`
- **Contents**:
  - `media-manager.exe` - Main executable
  - `README.txt` - User instructions
  - `start.bat` - Launch script

### 3. Installer Package
- **Directory**: `media-manager-installer-0.1.0/`
- **Contents**:
  - `files/` - Application files
  - `install.bat` - Installation script
  - `uninstall.bat` - Uninstallation script

### 4. Distribution Archives
- `media-manager-portable-0.1.0.zip` - Portable package
- `media-manager-installer-0.1.0.zip` - Installer package

### 5. Release Information
- `RELEASE_INFO.txt` - Complete release details with file hashes

## Installation Options

### Portable Version (No Installation Required)

1. **Download**: `media-manager-portable-0.1.0.zip`
2. **Extract**: To any folder
3. **Run**: Double-click `media-manager.exe` or `start.bat`

**Advantages:**
- No installation required
- Can run from USB drive
- No registry changes
- Easy to remove (just delete folder)

**Disadvantages:**
- No Start Menu shortcuts
- No file associations

### Installer Version (System Installation)

1. **Download**: `media-manager-installer-0.1.0.zip`
2. **Extract**: To temporary location
3. **Run**: `install.bat` as Administrator
4. **Launch**: From Start Menu or Desktop shortcut

**Advantages:**
- Creates Start Menu shortcuts
- Creates Desktop shortcut
- Proper installation in Program Files
- Includes uninstaller

**Disadvantages:**
- Requires Administrator privileges
- Makes system changes

## Troubleshooting

### Common Issues

#### 1. Build Fails with Missing Dependencies
```
Error: No module named 'PySide6'
```
**Solution:**
```bash
pip install -r build-requirements.txt
```

#### 2. Executable Crashes on Startup
```
Application failed to start
```
**Possible Causes:**
- Missing Visual C++ Runtime
- Antivirus interference
- Insufficient permissions

**Solutions:**
- Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Add to antivirus exclusions
- Run as Administrator

#### 3. Large Executable Size
**Issue**: Executable is >200MB
**Solutions:**
- Install UPX and rebuild
- Remove unused dependencies from spec file
- Use `--exclude-module` options

#### 4. Slow Startup
**Issue**: Application takes >30 seconds to start
**Solutions:**
- Use `--onedir` mode for development
- Optimize imports
- Consider using UPX compression

### Debug Mode Build

For troubleshooting, build in debug mode:
```bash
make -f Makefile.windows dev
```

This creates:
- Debug information
- Console output
- Directory-based distribution (faster startup)

## Advanced Configuration

### Customizing the Spec File

1. **Add additional data files:**
   ```python
   datas=[
       ('path/to/assets', 'assets'),
       ('path/to/config', 'config'),
   ]
   ```

2. **Exclude unnecessary modules:**
   ```python
   excludes=[
       'tkinter',
       'matplotlib',
       'scipy',
   ]
   ```

3. **Add hidden imports:**
   ```python
   hiddenimports=[
       'custom_module',
       'package.submodule',
   ]
   ```

### Custom Icon Creation

1. **Create 256x256 PNG image**
2. **Convert to ICO using:**
   - Online converter (recommended)
   - GIMP with ICO plugin
   - `png2ico` command-line tool

3. **Save as `icon.ico` in project root**

### Version Information

Edit `version_info.txt` to update:
- Product version
- Company information
- File description
- Copyright details

## Performance Optimization

### Reducing Executable Size

1. **Enable UPX compression:**
   - Install UPX
   - Ensure `upx=True` in spec file

2. **Exclude unused modules:**
   - Analyze imports with `pyi-archive_viewer`
   - Add to `excludes` list

3. **Optimize Python code:**
   - Remove unused imports
   - Use conditional imports
   - Minimize dependencies

### Improving Startup Time

1. **Use onedir mode for development:**
   - Faster startup
   - Easier debugging

2. **Optimize imports:**
   - Lazy import heavy modules
   - Use conditional imports

3. **Reduce startup tasks:**
   - Move heavy initialization to background
   - Use splash screen

## Verification and Testing

### File Integrity Verification

Use the SHA-256 hashes in `RELEASE_INFO.txt`:
```cmd
certutil -hashfile media-manager.exe SHA256
```

### Functional Testing

Test on clean Windows systems:
1. **Windows 7** (minimum requirement)
2. **Windows 10** (most common)
3. **Windows 11** (latest)

Test scenarios:
- Fresh system (no Python)
- System with antivirus
- System with limited permissions
- Different user account types

### Automated Testing

Run the built-in test:
```bash
make -f Makefile.windows test
```

## Distribution

### Preparing for Release

1. **Verify all builds:**
   - Check executable functionality
   - Verify file hashes
   - Test installation packages

2. **Create release notes:**
   - List new features
   - Document known issues
   - Include system requirements

3. **Package for distribution:**
   - Upload ZIP files to release platform
   - Include `RELEASE_INFO.txt`
   - Provide installation instructions

### Recommended Distribution Channels

1. **GitHub Releases** - For open-source distribution
2. **Direct Download** - From project website
3. **Package Managers** - Chocolatey, Scoop (future)

## Support and Maintenance

### Updating the Build

When updating the application:

1. **Update version numbers:**
   - `pyproject.toml`
   - `version_info.txt`
   - `build_windows.py`

2. **Update dependencies:**
   - `build-requirements.txt`
   - Test with new versions

3. **Test thoroughly:**
   - Build on clean system
   - Test all functionality
   - Verify compatibility

### Build Automation

For automated builds:
1. **Use GitHub Actions** or similar CI/CD
2. **Set up build agents** with Windows
3. **Automate testing** on multiple Windows versions
4. **Auto-generate releases** on tag creation

## Security Considerations

### Code Signing

For production distribution:
1. **Obtain code signing certificate**
2. **Sign the executable:**
   ```cmd
   signtool sign /f certificate.p12 /p password media-manager.exe
   ```
3. **Timestamp the signature**
4. **Verify signature**

### Security Best Practices

1. **Scan for malware** before distribution
2. **Use HTTPS** for all downloads
3. **Provide checksums** for verification
4. **Keep dependencies updated**
5. **Monitor security advisories**

## Conclusion

This packaging system provides a complete solution for distributing Media Manager as a Windows executable. The automated build script handles all complexity while allowing customization for specific needs.

For support or questions about the packaging process, please refer to the project documentation or create an issue in the project repository.