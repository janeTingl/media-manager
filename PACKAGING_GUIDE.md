# Media Manager Windows Executable Packaging Guide

This document provides comprehensive instructions for packaging the Media Manager application as a Windows executable (.exe) file using Nuitka (recommended) or the legacy PyInstaller flow.

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

### Option 1: Automated Nuitka Build (Recommended)

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd media-manager
   ```

2. **Run the automated build script (Nuitka backend):**
   ```bash
   python build_windows.py --backend nuitka
   ```

This command will:
- Install Nuitka and supporting dependencies
- Build the standalone executable with Nuitka
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

### Option 3: Legacy PyInstaller Build

1. **Install dependencies (optional if you've run option 1/2):**
   ```bash
   python build_windows.py --backend pyinstaller --only-install-deps
   ```

2. **Build using the legacy backend:**
   ```bash
   python build_windows.py --backend pyinstaller --skip-dependency-install
   ```

This path produces the same packaging artifacts but uses PyInstaller instead of Nuitka.

## Build Configuration

### Nuitka Configuration Highlights

The automated Nuitka build executed by `build_windows.py` enables the following key options:

- `--onefile` and `--standalone` for a fully self-contained executable
- `--enable-plugin=pyside6` with explicit Qt plugin inclusion (`platforms`, `styles`, `imageformats`, `iconengines`)
- Inclusion of application data folders (translations, resources, assets, etc.)
- Windows metadata (`--windows-company-name`, `--windows-product-name`, version and description fields)
- Automatic discovery of PySide6 modules via `--include-package=media_manager` and targeted hidden imports

These defaults can be customised by editing `build_windows.py` if additional data folders or modules need to be bundled.

### Legacy PyInstaller Notes

The PyInstaller backend is still available for compatibility. The build script uses command-line options equivalent to the previous `media-manager.spec` file (now deprecated):

- One-file, windowed build with PySide6 collection
- Automatic inclusion of required data directories
- Optional UPX compression if the tool is installed

If you require a bespoke PyInstaller configuration, use `python build_windows.py --backend pyinstaller --skip-dependency-install` and extend the script as needed.

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