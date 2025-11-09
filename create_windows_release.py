#!/usr/bin/env python3
"""
Windows Release Creation Script for Media Manager

This script creates the complete release package structure for Windows.
It should be run on a Windows system with Python and all dependencies installed.

Usage:
    python create_windows_release.py

This script will:
1. Build the Windows executable
2. Create portable and installer packages  
3. Generate checksums and documentation
4. Prepare files for GitHub Release upload
"""

import os
import sys
import shutil
import subprocess
import hashlib
import zipfile
from pathlib import Path
from datetime import datetime

# Configuration
PROJECT_NAME = "media-manager"
VERSION = "0.1.0"
APP_NAME = "Media Manager"
EXECUTABLE_NAME = "media-manager.exe"

# Paths
PROJECT_ROOT = Path(__file__).parent.absolute()
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_DIR = PROJECT_ROOT / "package"

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    
    if result.stdout:
        print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    
    return result

def verify_windows_environment():
    """Verify we're running on Windows with required tools."""
    if os.name != 'nt':
        print("ERROR: This script must be run on Windows to create a Windows executable")
        print("On Linux/macOS, you can use:")
        print("  - A Windows VM")
        print("  - Cross-compilation tools")
        print("  - GitHub Actions with Windows runner")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher required")
        return False
    
    # Check if PyInstaller is available
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("ERROR: PyInstaller not found. Install with: pip install pyinstaller")
        return False
    
    print("✅ Windows environment verified")
    return True

def build_executable():
    """Build the Windows executable."""
    print("\n🔨 Building Windows executable...")
    
    # Clean previous builds
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    if PROJECT_ROOT / "build".exists():
        shutil.rmtree(PROJECT_ROOT / "build")
    
    # Build using PyInstaller with the spec file
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean", "--noconfirm",
        str(PROJECT_ROOT / "media-manager.spec")
    ]
    
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return None
    
    # Check if executable was created
    exe_path = DIST_DIR / EXECUTABLE_NAME
    if not exe_path.exists():
        print(f"❌ ERROR: Executable not found at {exe_path}")
        return None
    
    print(f"✅ Successfully built: {exe_path}")
    print(f"📊 Size: {exe_path.stat().st_size:,} bytes ({exe_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return exe_path

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def create_portable_package(exe_path):
    """Create portable package with the executable."""
    print("\n📦 Creating portable package...")
    
    portable_dir = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # Copy executable
    shutil.copy2(exe_path, portable_dir / EXECUTABLE_NAME)
    
    # Create README
    readme_content = f"""{APP_NAME} v{VERSION} - Portable Version
{'=' * 50}

This is a portable version of {APP_NAME}. No installation is required.

System Requirements:
- Windows 7 or higher
- 64-bit operating system  
- 500MB free disk space
- .NET Framework 4.5 or higher (usually pre-installed)

Getting Started:
1. Double-click {EXECUTABLE_NAME} to launch the application
2. The application will create configuration files in:
   %USERPROFILE%\\.media-manager\\

Features:
- Media scanning and organization
- Automatic metadata matching
- Poster downloading
- Subtitle management
- NFO file generation
- And much more!

Support:
For documentation and support, please refer to the project documentation.

Version: {VERSION}
Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Build System: {os.name}
"""
    
    with open(portable_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Create batch file for easy launching
    batch_content = f"""@echo off
title {APP_NAME}
echo Starting {APP_NAME}...
echo.
"{EXECUTABLE_NAME}"
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
"""
    
    with open(portable_dir / "start.bat", "w", encoding="utf-8") as f:
        f.write(batch_content)
    
    print(f"✅ Portable package created: {portable_dir}")
    return portable_dir

def create_installer_package(portable_dir):
    """Create installer package structure."""
    print("\n📦 Creating installer package...")
    
    installer_dir = PACKAGE_DIR / f"{PROJECT_NAME}-installer-{VERSION}"
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    
    installer_dir.mkdir(parents=True)
    
    # Copy portable contents
    shutil.copytree(portable_dir, installer_dir / "files", dirs_exist_ok=True)
    
    # Create installation script
    install_script = f"""@echo off
title {APP_NAME} Installer v{VERSION}
echo.
echo {APP_NAME} Installer v{VERSION}
echo ================================
echo.
echo This will install {APP_NAME} to your system.
echo.
set INSTALL_DIR=%PROGRAMFILES%\\{PROJECT_NAME}
set SHORTCUT_DIR=%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs
set DESKTOP_DIR=%USERPROFILE%\\Desktop

echo Installing to: %INSTALL_DIR%
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy "files\\{EXECUTABLE_NAME}" "%INSTALL_DIR%\\" >nul
copy "files\\README.txt" "%INSTALL_DIR%\\" >nul

echo Creating Start Menu shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_DIR%\\{APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{EXECUTABLE_NAME}'; $Shortcut.Save()"

echo Creating Desktop shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\\{APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\{EXECUTABLE_NAME}'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo.
echo You can now run {APP_NAME} from:
echo - Start Menu
echo - Desktop shortcut
echo - Directly from: %INSTALL_DIR%\\{EXECUTABLE_NAME}
echo.
pause
"""
    
    with open(installer_dir / "install.bat", "w", encoding="utf-8") as f:
        f.write(install_script)
    
    # Create uninstaller script
    uninstall_script = f"""@echo off
title {APP_NAME} Uninstaller
echo.
echo {APP_NAME} Uninstaller
echo =====================
echo.
echo This will remove {APP_NAME} from your system.
echo.
set INSTALL_DIR=%PROGRAMFILES%\\{PROJECT_NAME}
set SHORTCUT_DIR=%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs
set DESKTOP_DIR=%USERPROFILE%\\Desktop

echo Removing files...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo Removing shortcuts...
if exist "%SHORTCUT_DIR%\\{APP_NAME}.lnk" del "%SHORTCUT_DIR%\\{APP_NAME}.lnk"
if exist "%DESKTOP_DIR%\\{APP_NAME}.lnk" del "%DESKTOP_DIR%\\{APP_NAME}.lnk"

echo.
echo {APP_NAME} has been uninstalled successfully.
echo.
pause
"""
    
    with open(installer_dir / "uninstall.bat", "w", encoding="utf-8") as f:
        f.write(uninstall_script)
    
    print(f"✅ Installer package created: {installer_dir}")
    return installer_dir

def create_release_archives(portable_dir, installer_dir):
    """Create ZIP archives for distribution."""
    print("\n🗜️ Creating distribution archives...")
    
    # Create portable ZIP
    portable_zip = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}.zip"
    with zipfile.ZipFile(portable_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in portable_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(portable_dir)
                zf.write(file_path, arcname)
    
    # Create installer ZIP
    installer_zip = PACKAGE_DIR / f"{PROJECT_NAME}-installer-{VERSION}.zip"
    with zipfile.ZipFile(installer_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in installer_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(installer_dir)
                zf.write(file_path, arcname)
    
    print(f"✅ Created archives:")
    print(f"   Portable: {portable_zip.name} ({portable_zip.stat().st_size:,} bytes)")
    print(f"   Installer: {installer_zip.name} ({installer_zip.stat().st_size:,} bytes)")
    
    return portable_zip, installer_zip

def create_release_info(exe_path, portable_zip, installer_zip):
    """Create comprehensive release information."""
    print("\n📋 Creating release information...")
    
    exe_hash = calculate_file_hash(exe_path)
    portable_hash = calculate_file_hash(portable_zip)
    installer_hash = calculate_file_hash(installer_zip)
    
    release_info = f"""{APP_NAME} Release Information v{VERSION}
{'=' * 60}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Build System: Windows ({os.name})
Python: {sys.version}
PyInstaller: {subprocess.check_output([sys.executable, '-m', 'PyInstaller', '--version'], text=True).strip()}

Files:
------
1. Executable: {EXECUTABLE_NAME}
   Size: {exe_path.stat().st_size:,} bytes ({exe_path.stat().st_size / 1024 / 1024:.1f} MB)
   SHA-256: {exe_hash}

2. Portable Package: {portable_zip.name}
   Size: {portable_zip.stat().st_size:,} bytes ({portable_zip.stat().st_size / 1024 / 1024:.1f} MB)
   SHA-256: {portable_hash}

3. Installer Package: {installer_zip.name}
   Size: {installer_zip.stat().st_size:,} bytes ({installer_zip.stat().st_size / 1024 / 1024:.1f} MB)
   SHA-256: {installer_hash}

System Requirements:
-------------------
- Windows 7 or higher
- 64-bit operating system
- 500MB free disk space
- .NET Framework 4.5 or higher (usually pre-installed)

Installation Options:
--------------------
1. Portable Version:
   - Extract the ZIP file to any folder
   - Run {EXECUTABLE_NAME} or start.bat
   - No installation required

2. Installer Version:
   - Extract the ZIP file
   - Run install.bat as administrator
   - Creates shortcuts and proper installation

Verification:
------------
Use the SHA-256 hashes above to verify file integrity:
- Windows: certutil -hashfile filename SHA256
- Linux/macOS: sha256sum filename

GitHub Release Upload:
--------------------
Upload these files to the v{VERSION} GitHub Release:
1. {EXECUTABLE_NAME} - Main executable
2. {portable_zip.name} - Portable package
3. {installer_zip.name} - Installer package
4. RELEASE_INFO.txt - This file

Release Notes Template:
----------------------
## {APP_NAME} v{VERSION}

### 🚀 Features
- Complete media management system
- Automatic metadata matching
- Poster and subtitle downloading
- NFO file generation
- Modern PySide6 interface

### 📦 Installation
**Option 1: Portable (No installation required)**
1. Download `{portable_zip.name}`
2. Extract to any folder
3. Run `media-manager.exe`

**Option 2: Installer (System integration)**
1. Download `{installer_zip.name}`
2. Extract and run `install.bat` as administrator
3. Launch from Start Menu or Desktop

### 🔧 Requirements
- Windows 7 or higher (64-bit)
- 500MB free disk space
- .NET Framework 4.5+

### ✅ Verification
Verify file integrity with SHA-256 hashes:
```
certutil -hashfile {EXECUTABLE_NAME} SHA256
certutil -hashfile {portable_zip.name} SHA256  
certutil -hashfile {installer_zip.name} SHA256
```

### 📚 Documentation
- [Quick Start Guide](QUICK_START.md)
- [User Manual](USAGE.md)
- [Installation Guide](INSTALLATION.md)

Support:
--------
For documentation and support, please refer to the project documentation
included in the packages or visit the project repository.

Version History:
---------------
v{VERSION} - Initial release
- Complete media management functionality
- Windows executable with PyInstaller
- Portable and installer packages included
"""
    
    with open(PACKAGE_DIR / "RELEASE_INFO.txt", "w", encoding="utf-8") as f:
        f.write(release_info)
    
    print("✅ Release information created")
    return release_info

def main():
    """Main release creation process."""
    print(f"🎯 Creating {APP_NAME} v{VERSION} Windows Release")
    print("=" * 60)
    
    try:
        # Verify environment
        if not verify_windows_environment():
            print("\n❌ Cannot proceed with Windows build on this system")
            print("\n📋 To create the Windows release:")
            print("1. Set up a Windows environment (VM, native Windows, or GitHub Actions)")
            print("2. Install Python 3.8+ and PyInstaller")
            print("3. Run this script on Windows")
            print("4. Upload the generated files to GitHub Release")
            return False
        
        # Build executable
        exe_path = build_executable()
        if not exe_path:
            return False
        
        # Create packages
        portable_dir = create_portable_package(exe_path)
        installer_dir = create_installer_package(portable_dir)
        
        # Create archives
        portable_zip, installer_zip = create_release_archives(portable_dir, installer_dir)
        
        # Create release information
        release_info = create_release_info(exe_path, portable_zip, installer_zip)
        
        print("\n" + "=" * 60)
        print("🎉 WINDOWS RELEASE CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📁 Package directory: {PACKAGE_DIR}")
        print(f"📋 Release info: {PACKAGE_DIR / 'RELEASE_INFO.txt'}")
        print("\n📤 Files ready for GitHub Release:")
        print(f"  1. {EXECUTABLE_NAME}")
        print(f"  2. {portable_zip.name}")
        print(f"  3. {installer_zip.name}")
        print(f"  4. RELEASE_INFO.txt")
        
        return True
        
    except Exception as e:
        print(f"\n❌ RELEASE CREATION FAILED: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)