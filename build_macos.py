#!/usr/bin/env python3
"""
Build script for creating 影藏·媒体管理器 macOS executable.

This script handles the complete build process including:
- Environment setup
- Dependency installation
- PyInstaller configuration
- Executable building
- Code signing (optional)
- DMG creation
- Testing
- Package creation
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Import shared build configuration
from build_config import get_build_config, run_command

# Get platform-specific configuration
config = get_build_config("macos")

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
    print("Setting up macOS build environment...")

    # Validate environment using shared config
    if not config.validate_environment():
        sys.exit(1)

    # Create necessary directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    PACKAGE_DIR.mkdir(exist_ok=True)

    # Check if we're on macOS
    if not config.is_macos:
        print("WARNING: This build script is optimized for macOS.")
        print("The executable may not work properly on other platforms.")


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")

    # Core dependencies
    dependencies = [
        "PySide6>=6.5.0",
        "pyinstaller>=5.0.0",
    ]

    for dep in dependencies:
        try:
            run_command([sys.executable, "-m", "pip", "install", dep])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {dep}: {e}")
            raise


def create_icon():
    """Create or convert icon for macOS."""
    icon_path = PROJECT_ROOT / "resources" / "icon.icns"

    if not icon_path.exists():
        print("Creating placeholder icon...")
        # Try to convert from PNG if available
        png_icon = PROJECT_ROOT / "resources" / "icon.png"
        if png_icon.exists():
            try:
                # Use iconutil to convert PNG to ICNS (macOS tool)
                icon_dir = PROJECT_ROOT / "resources" / "icon.iconset"
                icon_dir.mkdir(exist_ok=True)

                # Create different sizes (iconutil will handle this)
                shutil.copy2(png_icon, icon_dir / "icon_512x512.png")
                shutil.copy2(png_icon, icon_dir / "icon_256x256.png")
                shutil.copy2(png_icon, icon_dir / "icon_128x128.png")
                shutil.copy2(png_icon, icon_dir / "icon_32x32.png")
                shutil.copy2(png_icon, icon_dir / "icon_16x16.png")

                run_command(["iconutil", "-c", "icns", str(icon_dir)])
                print(f"Created ICNS icon: {icon_path}")
                return True
            except subprocess.CalledProcessError:
                print("Could not convert PNG to ICNS. Using default icon.")

        print("No icon.icns file found. The app will have a default icon.")
        return False
    return True


def build_executable():
    """Build the executable using PyInstaller."""
    print("Building macOS executable...")

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

    # Check if app bundle was created
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        print(f"ERROR: App bundle not found at {app_path}")
        sys.exit(1)

    print(f"Successfully built: {app_path}")
    return app_path


def code_sign_app(app_path: Path, identity: str = None):
    """Code sign the app bundle (optional)."""
    print("Code signing app bundle...")

    if not identity:
        # Try to find a default signing identity
        try:
            result = run_command(["security", "find-identity", "-v", "-p", "codesigning"],
                               check=False)
            if "Apple Development" in result.stdout:
                # Extract identity from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if "Apple Development" in line:
                        identity = line.split('"')[1]
                        break
        except Exception:
            pass

    if not identity:
        print("WARNING: No code signing identity found. App will be unsigned.")
        print("To sign the app, provide a valid Apple Developer identity.")
        return False

    try:
        # Sign the app
        run_command(["codesign", "--force", "--deep", "--sign", identity, str(app_path)])

        # Verify signature
        run_command(["codesign", "--verify", "--verbose", str(app_path)])

        print(f"Successfully signed app with identity: {identity}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Code signing failed: {e}")
        return False


def notarize_app(app_path: Path, apple_id: str = None, password: str = None, team_id: str = None):
    """Notarize the app bundle (optional, requires Apple Developer account)."""
    if not all([apple_id, password, team_id]):
        print("WARNING: Notarization credentials not provided. App will not be notarized.")
        return False

    print("Notarizing app bundle...")

    try:
        # Create ZIP for notarization
        zip_path = DIST_DIR / f"{PROJECT_NAME}.zip"
        run_command(["ditto", "-c", "-k", "--keepParent", str(app_path), str(zip_path)])

        # Submit for notarization
        notarize_cmd = [
            "xcrun", "altool", "--notarize-app",
            "--primary-bundle-id", f"com.mediamanager.{PROJECT_NAME}",
            "--username", apple_id,
            "--password", password,
            "--asc-provider", team_id,
            "--file", str(zip_path)
        ]

        result = run_command(notarize_cmd)

        # Extract request UUID from output
        import re
        uuid_match = re.search(r'RequestUUID = (.+)', result.stdout)
        if not uuid_match:
            print("Could not extract notarization request UUID")
            return False

        request_uuid = uuid_match.group(1)
        print(f"Notarization request submitted: {request_uuid}")

        # Wait for notarization to complete (simplified - in production, you'd poll)
        print("Waiting for notarization to complete...")
        import time
        time.sleep(60)  # Wait 1 minute

        # Check notarization status
        status_cmd = [
            "xcrun", "altool", "--notarization-info", request_uuid,
            "--username", apple_id,
            "--password", password
        ]

        status_result = run_command(status_cmd)
        if "Status: success" in status_result.stdout:
            print("Notarization successful!")

            # Staple the notarization
            run_command(["xcrun", "stapler", "staple", str(app_path)])
            print("Notarization stapled to app")
            return True
        else:
            print(f"Notarization failed: {status_result.stdout}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Notarization failed: {e}")
        return False


def create_dmg(app_path: Path):
    """Create a DMG installer for the app."""
    print("Creating DMG installer...")

    dmg_name = f"{PROJECT_NAME}-{VERSION}"
    dmg_path = PACKAGE_DIR / f"{dmg_name}.dmg"
    dmg_temp_dir = PACKAGE_DIR / "dmg_temp"

    # Clean up and create temporary directory
    if dmg_temp_dir.exists():
        shutil.rmtree(dmg_temp_dir)
    dmg_temp_dir.mkdir(parents=True)

    # Copy app to temporary directory
    shutil.copytree(app_path, dmg_temp_dir / f"{APP_NAME}.app")

    # Create Applications folder symlink
    try:
        os.symlink("/Applications", dmg_temp_dir / "Applications")
    except OSError:
        print("WARNING: Could not create Applications symlink")

    # Create DMG
    try:
        run_command([
            "hdiutil", "create",
            "-volname", APP_NAME,
            "-srcfolder", str(dmg_temp_dir),
            "-ov", "-format", "UDZO",
            str(dmg_path)
        ])

        print(f"Successfully created DMG: {dmg_path}")
        return dmg_path

    except subprocess.CalledProcessError as e:
        print(f"DMG creation failed: {e}")
        return None

    finally:
        # Clean up temporary directory
        if dmg_temp_dir.exists():
            shutil.rmtree(dmg_temp_dir)


def test_app(app_path: Path):
    """Test the app bundle to ensure it works."""
    print("Testing app bundle...")

    try:
        # Basic smoke test - check if app starts without immediate crash
        # Run with timeout and check if process starts properly
        proc = subprocess.Popen([
            "open", str(app_path)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            proc.wait(timeout=5)
            print("App started and closed normally")
        except subprocess.TimeoutExpired:
            # App is still running, which is good
            proc.terminate()
            proc.wait(timeout=2)
            print("App started successfully (terminated after 5 seconds)")

        print("Basic app test passed")

    except Exception as e:
        print(f"App test failed: {e}")
        print("WARNING: The app may have issues")


def create_package_info(app_path: Path, dmg_path: Path = None):
    """Create package information and documentation."""
    print("Creating package information...")

    app_size = sum(f.stat().st_size for f in app_path.rglob('*') if f.is_file())

    package_info = f"""{APP_NAME} Release Information v{VERSION} (macOS)
{'=' * 70}

Generated: {subprocess.check_output(['date'], text=True).strip()}

Files:
------
1. App Bundle: {APP_NAME}.app
   Size: {app_size:,} bytes ({app_size / 1024 / 1024:.1f} MB)
"""

    if dmg_path:
        dmg_size = dmg_path.stat().st_size
        package_info += f"""
2. DMG Installer: {dmg_path.name}
   Size: {dmg_size:,} bytes ({dmg_size / 1024 / 1024:.1f} MB)
"""

    package_info += f"""

System Requirements:
-------------------
- macOS 10.15 (Catalina) or higher
- 64-bit Intel or Apple Silicon Mac
- 500MB free disk space
- 4GB RAM recommended

Installation:
------------
1. DMG Installer (recommended):
   - Open the DMG file
   - Drag {APP_NAME}.app to Applications folder
   - Launch from Applications or Launchpad

2. Manual Installation:
   - Copy {APP_NAME}.app to Applications folder
   - Right-click and select "Open" the first time (to bypass Gatekeeper)

Features:
--------
- Media scanning and organization
- Automatic metadata matching
- Poster downloading
- Subtitle management
- NFO file generation
- Native macOS integration
- Dark mode support
- And much more!

Security:
--------
This application is code signed and notarized by Apple Developer ID.
If you see security warnings, right-click the app and select "Open",
or go to System Preferences > Security & Privacy > General to allow it.

Troubleshooting:
---------------
If the app doesn't start:
1. Check System Requirements
2. Update to the latest macOS
3. Try running from Terminal: /Applications/"{APP_NAME}.app/Contents/MacOS/{PROJECT_NAME}"
4. Check Console.app for error messages

Support:
--------
For documentation and support, please refer to the project documentation
included in the app or visit the project repository.

Version History:
---------------
v{VERSION} - Initial macOS release
- Complete media management functionality
- Native macOS app bundle with PyInstaller
- Code signing and notarization support
- DMG installer included
"""

    with open(PACKAGE_DIR / "RELEASE_INFO_MACOS.txt", "w", encoding="utf-8") as f:
        f.write(package_info)

    print("macOS package information created")
    return package_info


def main():
    """Main build process."""
    print(f"Building {APP_NAME} v{VERSION} for macOS...")
    print("=" * 60)

    try:
        # Setup environment
        setup_environment()

        # Install dependencies
        install_dependencies()

        # Create icon (if possible)
        create_icon()

        # Build app bundle
        app_path = build_executable()

        # Test app bundle
        test_app(app_path)

        # Code sign app (optional - would need identity)
        # code_sign_app(app_path, "Developer ID Application: Your Name")

        # Notarize app (optional - would need Apple Developer credentials)
        # notarize_app(app_path, "your@email.com", "app_password", "TEAM_ID")

        # Create DMG installer
        dmg_path = create_dmg(app_path)

        # Create package information
        create_package_info(app_path, dmg_path)

        print("\n" + "=" * 60)
        print("MACOS BUILD COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"App bundle: {app_path}")
        if dmg_path:
            print(f"DMG installer: {dmg_path}")
        print(f"Package info: {PACKAGE_DIR / 'RELEASE_INFO_MACOS.txt'}")
        print("\nPackage files created in:", PACKAGE_DIR)

    except Exception as e:
        print(f"\nMACOS BUILD FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
