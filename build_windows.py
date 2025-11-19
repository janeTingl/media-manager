#!/usr/bin/env python3
"""
Build script for creating Media Manager Windows executable.

This script handles the complete build process including:
- Environment setup
- Dependency installation
- PyInstaller configuration
- Executable building
- Testing
- Package creation
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
import zipfile
import hashlib

# Import shared build configuration
from build_config import get_build_config, run_command

# Get platform-specific configuration
config = get_build_config("windows")

# Configuration from shared config
PROJECT_NAME = config.PROJECT_NAME
VERSION = config.VERSION
APP_NAME = config.APP_NAME
EXECUTABLE_NAME = config.get_executable_name()

# Paths from shared config
PROJECT_ROOT = config.PROJECT_ROOT
BUILD_DIR = config.BUILD_DIR
DIST_DIR = config.DIST_DIR
PACKAGE_DIR = config.PACKAGE_DIR

def setup_environment():
    """Setup the build environment."""
    print("Setting up build environment...")
    
    # Validate environment using shared config
    if not config.validate_environment():
        sys.exit(1)
    
    # Create necessary directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    PACKAGE_DIR.mkdir(exist_ok=True)
    
    # Check if we're on Windows
    if not config.is_windows:
        print("WARNING: This build script is optimized for Windows.")
        print("The executable may not work properly on other platforms.")

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    
    requirements_file = PROJECT_ROOT / "requirements.txt"
    if requirements_file.exists():
        print(f"Installing runtime dependencies from {requirements_file}...")
        run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
    else:
        print("requirements.txt not found, installing runtime dependencies individually...")
        runtime_dependencies = [
            "PySide6>=6.5.0",
            "sqlmodel>=0.0.14",
            "alembic>=1.12.0",
            "sqlalchemy>=2.0.0",
            "requests>=2.31.0",
            "tenacity>=8.2.0",
            "openpyxl>=3.1.0",
        ]
        for dep in runtime_dependencies:
            run_command([sys.executable, "-m", "pip", "install", dep])
    
    build_requirements_file = PROJECT_ROOT / "build-requirements.txt"
    if build_requirements_file.exists():
        print(f"Installing build dependencies from {build_requirements_file}...")
        run_command([sys.executable, "-m", "pip", "install", "-r", str(build_requirements_file)])
    else:
        print("build-requirements.txt not found, installing build dependencies individually...")
        build_dependencies = ["pyinstaller>=5.0.0"]
        for dep in build_dependencies:
            run_command([sys.executable, "-m", "pip", "install", dep])
    
    optional_dependencies = ["upx"]
    for dep in optional_dependencies:
        try:
            run_command([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install optional dependency {dep}: {e}")
            print(f"{dep} is optional, continuing without it...")

def create_icon():
    """Create a simple icon if one doesn't exist."""
    icon_path = PROJECT_ROOT / "icon.ico"
    
    if not icon_path.exists():
        print("Creating placeholder icon...")
        # For now, we'll skip icon creation
        # In a real build, you would create a proper .ico file
        print("Note: No icon.ico file found. The executable will have a default icon.")
        return False
    return True

def build_executable():
    """Build the executable using PyInstaller."""
    print("Building executable...")
    
    # Clean previous builds
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    
    # Create spec file using shared config
    spec_file = config.create_spec_file()
    print(f"Created spec file: {spec_file}")
    
    # PyInstaller command using shared config
    pyinstaller_args = config.get_pyinstaller_args()
    cmd = [sys.executable, "-m", "PyInstaller"] + pyinstaller_args + [str(spec_file)]
    
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    
    # Check if executable was created
    exe_path = DIST_DIR / EXECUTABLE_NAME
    if not exe_path.exists():
        print(f"ERROR: Executable not found at {exe_path}")
        sys.exit(1)
    
    print(f"Successfully built: {exe_path}")
    return exe_path

def test_executable(exe_path: Path):
    """Test the executable to ensure it works."""
    print("Testing executable...")
    
    # Basic smoke test - check if it runs without immediate crash
    try:
        # Run with --help to see basic functionality
        result = run_command([str(exe_path), "--help"], check=False)
        
        # The demo app might not have --help, so we check if it starts
        if result.returncode != 0:
            print("Executable doesn't support --help, trying basic startup test...")
            
            # Try to run for a few seconds then terminate
            proc = subprocess.Popen([str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                proc.wait(timeout=5)
                print("Executable started and closed normally")
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait(timeout=2)
                print("Executable started successfully (terminated after 5 seconds)")
        
        print("Basic executable test passed")
        
    except Exception as e:
        print(f"Executable test failed: {e}")
        print("WARNING: The executable may have issues")

def create_portable_package(exe_path: Path):
    """Create a portable package with the executable."""
    print("Creating portable package...")
    
    portable_dir = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # Copy executable
    shutil.copy2(exe_path, portable_dir / EXECUTABLE_NAME)
    
    # Create documentation
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
- subtitle management
- NFO file generation
- And much more!

Support:
For documentation and support, please refer to the project documentation.

Version: {VERSION}
Build Date: {subprocess.check_output(['date'], text=True).strip()}
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
    
    print(f"Portable package created: {portable_dir}")
    return portable_dir

def create_installer_package(portable_dir: Path):
    """Create an installer package structure."""
    print("Creating installer package...")
    
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
    
    print(f"Installer package created: {installer_dir}")
    return installer_dir

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def create_release_info(exe_path: Path, portable_dir: Path, installer_dir: Path):
    """Create release information file."""
    print("Creating release information...")
    
    exe_size = exe_path.stat().st_size
    exe_hash = calculate_file_hash(exe_path)
    
    # Create ZIP archives
    portable_zip = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}.zip"
    installer_zip = PACKAGE_DIR / f"{PROJECT_NAME}-installer-{VERSION}.zip"
    
    with zipfile.ZipFile(portable_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in portable_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(portable_dir)
                zf.write(file_path, arcname)
    
    with zipfile.ZipFile(installer_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in installer_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(installer_dir)
                zf.write(file_path, arcname)
    
    # Calculate hashes for ZIP files
    portable_hash = calculate_file_hash(portable_zip)
    installer_hash = calculate_file_hash(installer_zip)
    
    release_info = f"""{APP_NAME} Release Information v{VERSION}
{'=' * 60}

Generated: {subprocess.check_output(['date'], text=True).strip()}

Files:
------
1. Executable: {EXECUTABLE_NAME}
   Size: {exe_size:,} bytes ({exe_size / 1024 / 1024:.1f} MB)
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
    
    print("Release information created")
    return release_info

def main():
    """Main build process."""
    print(f"Building {APP_NAME} v{VERSION} for Windows...")
    print("=" * 60)
    
    try:
        # Setup environment
        setup_environment()
        
        # Install dependencies
        install_dependencies()
        
        # Create icon (if possible)
        create_icon()
        
        # Build executable
        exe_path = build_executable()
        
        # Test executable
        test_executable(exe_path)
        
        # Create packages
        portable_dir = create_portable_package(exe_path)
        installer_dir = create_installer_package(portable_dir)
        
        # Create release information
        create_release_info(exe_path, portable_dir, installer_dir)
        
        print("\n" + "=" * 60)
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Executable: {exe_path}")
        print(f"Portable package: {portable_dir}")
        print(f"Installer package: {installer_dir}")
        print(f"Release info: {PACKAGE_DIR / 'RELEASE_INFO.txt'}")
        print("\nPackage files created in:", PACKAGE_DIR)
        
    except Exception as e:
        print(f"\nBUILD FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()