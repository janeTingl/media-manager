"""
Shared build configuration for 影藏·媒体管理器 cross-platform builds.

This module provides common functionality and configuration for building
影藏·媒体管理器 executables on different platforms using PyInstaller.
"""

import platform
import subprocess
from pathlib import Path
from typing import List, Optional

# Project configuration
PROJECT_NAME = "media-manager"
VERSION = "0.1.0"
APP_NAME = "影藏·媒体管理器"
MAIN_SCRIPT = "src/media_manager/main.py"

# Paths
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_DIR = PROJECT_ROOT / "package"


class BuildConfig:
    """Shared build configuration class."""

    def __init__(self, platform_name: Optional[str] = None):
        self.platform_name = platform_name or platform.system().lower()
        self.is_windows = self.platform_name == "windows"
        self.is_macos = self.platform_name == "darwin"
        self.is_linux = self.platform_name == "linux"

    def get_executable_name(self) -> str:
        """Get the platform-specific executable name."""
        base_name = APP_NAME
        if self.is_windows:
            return f"{base_name}.exe"
        return base_name

    def get_pyinstaller_args(self) -> List[str]:
        """Get platform-specific PyInstaller arguments."""
        args = [
            "--clean",
            "--noconfirm",
            "--name",
            APP_NAME,
            "--onefile",
            (
                "--windowed" if not self.is_windows else ""
            ),  # Console on Windows for debugging
        ]

        # Add platform-specific arguments
        if self.is_macos:
            args.extend(
                [
                    "--osx-bundle-identifier",
                    f"com.mediamanager.{PROJECT_NAME}",
                    "--icon",
                    (
                        "resources/icon.icns"
                        if Path("resources/icon.icns").exists()
                        else ""
                    ),
                ]
            )
        elif self.is_windows:
            args.extend(
                [
                    "--icon",
                    "icon.ico" if Path("icon.ico").exists() else "",
                    "--add-data",
                    "src/media_manager;media_manager",  # Include source
                    "--hidden-import",
                    "PySide6.QtCore",
                    "--hidden-import",
                    "PySide6.QtWidgets",
                    "--hidden-import",
                    "PySide6.QtGui",
                    "--hidden-import",
                    "sqlmodel",
                    "--hidden-import",
                    "sqlalchemy",
                    "--hidden-import",
                    "sqlalchemy.sql.default_comparator",
                    "--hidden-import",
                    "alembic",
                    "--hidden-import",
                    "requests",
                    "--hidden-import",
                    "tenacity",
                    "--hidden-import",
                    "openpyxl",
                    # Include Qt plugins
                    "--collect-all",
                    "PySide6",
                    # Include multimedia backends if available
                    "--hidden-import",
                    "PySide6.QtMultimedia",
                    "--hidden-import",
                    "PySide6.QtMultimediaWidgets",
                ]
            )

        # Filter out empty strings
        return [arg for arg in args if arg]

    def get_data_files(self) -> List[tuple]:
        """Get data files to include in the build."""
        data_files = []

        # Include any resource files
        resources_dir = PROJECT_ROOT / "resources"
        if resources_dir.exists():
            for resource_file in resources_dir.rglob("*"):
                if resource_file.is_file():
                    rel_path = resource_file.relative_to(resources_dir)
                    data_files.append(
                        (str(resource_file), f"resources/{rel_path.parent}")
                    )

        return data_files

    def get_excludes(self) -> List[str]:
        """Get modules to exclude from the build."""
        excludes = [
            # Development and testing modules
            "pytest",
            "black",
            "ruff",
            "mypy",
            "setuptools",
            "pip",
            # Unused Qt modules
            "PySide6.QtWebEngine",
            "PySide6.QtWebEngineWidgets",
            "PySide6.QtSql",
            "PySide6.QtTest",
            "PySide6.QtDesigner",
            "PySide6.QtHelp",
            "PySide6.QtNetwork",
            "PySide6.QtOpenGL",
            "PySide6.QtPrintSupport",
            "PySide6.QtSql",
            "PySide6.QtTest",
            "PySide6.QtUiTools",
            "PySide6.QtXml",
            "PySide6.QtXmlPatterns",
        ]
        return excludes

    def get_spec_file_content(self) -> str:
        """Generate PyInstaller spec file content."""
        executable_name = self.get_executable_name()

        # Basic analysis configuration
        analysis_config = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Project configuration
PROJECT_ROOT = Path(r"{PROJECT_ROOT}")
SRC_DIR = PROJECT_ROOT / "src"
MAIN_SCRIPT = SRC_DIR / "media_manager" / "main.py"

# PyInstaller analysis
a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas={self.get_data_files()},
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "sqlmodel",
        "sqlalchemy",
        "sqlalchemy.sql.default_comparator",
        "alembic",
        "requests",
        "tenacity",
        "openpyxl",
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={self.get_excludes()},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
"""

        # Platform-specific configurations
        if self.is_windows:
            analysis_config += """
# Windows-specific configuration
a.datas += Tree(str(SRC_DIR / "media_manager"), prefix="media_manager", excludes=["__pycache__"])

# Include Qt plugins
import PySide6
qt_plugins_path = Path(PySide6.__file__).parent / "Qt" / "plugins"
if qt_plugins_path.exists():
    a.datas += Tree(str(qt_plugins_path), prefix="qt6/plugins", excludes=["__pycache__"])
"""

        # PYZ and EXE/APP configuration
        spec_content = (
            analysis_config
            + f"""
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    {self._get_exe_options()},
    name='{executable_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={not self.is_windows},  # Console on Windows for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
        )

        # macOS app bundle configuration
        if self.is_macos:
            spec_content += f"""
app = BUNDLE(
    exe,
    name='{APP_NAME}.app',
    icon='resources/icon.icns' if Path('resources/icon.icns').exists() else None,
    bundle_identifier='com.mediamanager.{PROJECT_NAME}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': '{APP_NAME}',
        'CFBundleVersion': '{VERSION}',
        'CFBundleShortVersionString': '{VERSION}',
        'CFBundleIdentifier': 'com.mediamanager.{PROJECT_NAME}',
        'NSHighResolutionCapable': True,
        'LSApplicationCategoryType': 'public.app-category.productivity',
    }}
)
"""

        return spec_content

    def _get_exe_options(self) -> str:
        """Get platform-specific EXE options."""
        if self.is_windows:
            return """
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    icon='icon.ico' if Path('icon.ico').exists() else None,
"""
        elif self.is_macos:
            return """
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
"""
        else:
            return """
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
"""

    def create_spec_file(self) -> Path:
        """Create the PyInstaller spec file."""
        spec_file = PROJECT_ROOT / f"{PROJECT_NAME}.spec"

        with open(spec_file, "w", encoding="utf-8") as f:
            f.write(self.get_spec_file_content())

        return spec_file

    def validate_environment(self) -> bool:
        """Validate that the build environment is properly set up."""
        print(f"Validating {self.platform_name} build environment...")

        # Check if main script exists
        main_script = SRC_DIR / "media_manager" / "main.py"
        if not main_script.exists():
            print(f"ERROR: Main script not found at {main_script}")
            return False

        # Check if PyInstaller is available
        try:
            import PyInstaller  # type: ignore[import-untyped]

            print(f"PyInstaller version: {PyInstaller.__version__}")
        except ImportError:
            print(
                "ERROR: PyInstaller not installed. Install with: pip install pyinstaller"
            )
            return False

        # Check platform-specific requirements
        if self.is_macos:
            # Check for code signing tools (optional)
            try:
                subprocess.run(["codesign", "--help"], capture_output=True, check=True)
                print("Code signing tools available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("WARNING: Code signing tools not found. App will be unsigned.")

        print("Environment validation passed")
        return True


def get_build_config(platform_name: Optional[str] = None) -> BuildConfig:
    """Get a build configuration for the specified platform."""
    return BuildConfig(platform_name)


def run_command(
    cmd: List[str], cwd: Optional[Path] = None, check: bool = True
) -> subprocess.CompletedProcess:
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
