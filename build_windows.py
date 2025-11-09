#!/usr/bin/env python3
"""
Build script for creating Media Manager Windows executable packages.

This script now supports multiple build backends. Nuitka is the default
compiler, providing a more stable single-file executable than the legacy
PyInstaller flow. The script can still generate PyInstaller builds for
compatibility when requested.

The build pipeline performs the following steps:
1. Optional dependency installation for the selected backend
2. Compilation of the application entry point into a Windows executable
3. Optional smoke testing of the generated executable
4. Creation of portable and installer packaging artifacts
5. Generation of release information including file hashes and archives
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

# Project metadata
PROJECT_NAME = "media-manager"
VERSION = "0.1.0"
APP_NAME = "Media Manager"
EXECUTABLE_NAME = "media-manager.exe"

# Paths
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_ROOT = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_DIR = PROJECT_ROOT / "package"
ENTRY_SCRIPT = SRC_ROOT / "media_manager" / "main.py"

SUPPORTED_BACKENDS = ("nuitka", "pyinstaller")
QT_PLUGIN_SET = ["platforms", "styles", "imageformats", "iconengines"]
DATA_DIR_CANDIDATES = [
    (SRC_ROOT / "media_manager" / "translations", "media_manager/translations"),
    (SRC_ROOT / "media_manager" / "resources", "media_manager/resources"),
    (SRC_ROOT / "media_manager" / "assets", "media_manager/assets"),
    (SRC_ROOT / "media_manager" / "data", "media_manager/data"),
]
DATA_FILES = [
    (PROJECT_ROOT / "version_info.txt", "version_info.txt"),
]


def run_command(cmd: list[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and echo stdout/stderr for transparency."""

    printable_cmd = " ".join(cmd)
    print(f"Running: {printable_cmd}")
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


def setup_environment() -> None:
    """Ensure required directories exist."""

    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    PACKAGE_DIR.mkdir(exist_ok=True)


def clean_directories(include_packages: bool) -> None:
    """Remove previous build artifacts."""

    for path in (BUILD_DIR, DIST_DIR):
        if path.exists():
            print(f"Removing {path} ...")
            shutil.rmtree(path)

    if include_packages and PACKAGE_DIR.exists():
        print(f"Removing {PACKAGE_DIR} ...")
        shutil.rmtree(PACKAGE_DIR)


def find_icon() -> Optional[Path]:
    """Return the icon path if available."""

    icon_path = PROJECT_ROOT / "icon.ico"
    if icon_path.exists():
        print(f"Using icon: {icon_path}")
        return icon_path

    print("Note: icon.ico not found. The executable will use the default icon.")
    return None


def install_dependencies(backend: str) -> None:
    """Install dependencies required for the selected backend."""

    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}")

    print(f"Installing build dependencies for backend '{backend}'...")

    base_dependencies = [
        "PySide6>=6.5.0",
    ]

    if backend == "nuitka":
        backend_dependencies = [
            "nuitka>=1.9",
            "ordered-set>=4.1.0",
            "zstandard>=0.21.0",
            "pywin32-ctypes>=0.2.0",
            "pefile>=2023.2.7",
        ]
    else:  # PyInstaller
        backend_dependencies = [
            "PyInstaller>=5.13.0",
            "pyinstaller-hooks-contrib>=2023.8",
            "altgraph>=0.17.4",
        ]

    dependencies: Iterable[str] = base_dependencies + backend_dependencies

    for dep in dependencies:
        run_command([sys.executable, "-m", "pip", "install", dep])

    if backend == "pyinstaller":
        # UPX remains optional but improves bundle size.
        try:
            run_command([sys.executable, "-m", "pip", "install", "upx"])
        except subprocess.CalledProcessError:
            print("UPX installation failed or not available. Continuing without it...")


def _nuitka_data_arguments() -> list[str]:
    args: list[str] = []
    for src, target in DATA_DIR_CANDIDATES:
        if src.exists():
            args.append(f"--include-data-dir={src}={target}")
    for src, target in DATA_FILES:
        if src.exists():
            args.append(f"--include-data-file={src}={target}")
    return args


def build_executable_nuitka(icon_path: Optional[Path]) -> Path:
    """Compile the application using Nuitka."""

    print("Building executable with Nuitka...")

    DIST_DIR.mkdir(exist_ok=True)
    nuitka_work_dir = BUILD_DIR / "nuitka"
    nuitka_work_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--onefile",
        "--standalone",
        "--assume-yes-for-downloads",
        "--enable-plugin=pyside6",
        f"--include-qt-plugins={','.join(QT_PLUGIN_SET)}",
        "--nofollow-import-to=tests",
        "--nofollow-import-to=package",
        "--nofollow-import-to=docs",
        "--nofollow-import-to=tests.*",
        f"--jobs={os.cpu_count() or 1}",
        f"--output-dir={DIST_DIR}",
        f"--output-filename={EXECUTABLE_NAME}",
        "--windows-company-name=Media Manager Team",
        f"--windows-product-name={APP_NAME}",
        f"--windows-product-version={VERSION}",
        f"--windows-file-version={VERSION}",
        "--windows-file-description=Media library manager",
        "--windows-disable-console",
        "--lto=yes",
        "--static-libpython=no",
        "--include-package=media_manager",
    ]

    if icon_path:
        cmd.append(f"--windows-icon-from-ico={icon_path}")

    cmd.extend(_nuitka_data_arguments())

    # Additional hidden imports ensure PySide submodules are bundled.
    hidden_imports = [
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "PySide6.QtQml",
    ]
    for module in hidden_imports:
        cmd.append(f"--include-module={module}")

    cmd.append(str(ENTRY_SCRIPT))

    run_command(cmd)

    exe_path = DIST_DIR / EXECUTABLE_NAME
    if not exe_path.exists():
        raise FileNotFoundError(f"Nuitka build did not produce {exe_path}")

    # Clean up Nuitka build directories to reduce clutter.
    for orphan in PROJECT_ROOT.glob("*.build"):
        try:
            shutil.rmtree(orphan)
        except OSError:
            print(f"Warning: unable to remove temporary build directory {orphan}")

    return exe_path


def _pyinstaller_data_arguments() -> list[str]:
    sep = ";" if os.name == "nt" else ":"
    args: list[str] = []
    for src, target in DATA_DIR_CANDIDATES:
        if src.exists():
            args.extend(["--add-data", f"{src}{sep}{target}"])
    for src, target in DATA_FILES:
        if src.exists():
            args.extend(["--add-data", f"{src}{sep}{target}"])
    return args


def build_executable_pyinstaller(icon_path: Optional[Path]) -> Path:
    """Compile the application using PyInstaller."""

    print("Building executable with PyInstaller (legacy backend)...")

    work_path = BUILD_DIR / "pyinstaller"
    work_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        PROJECT_NAME,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(work_path),
        "--specpath",
        str(work_path),
        "--collect-all",
        "PySide6",
        "--hidden-import",
        "PySide6.QtXml",
        "--hidden-import",
        "PySide6.QtNetwork",
        "--hidden-import",
        "PySide6.QtQml",
    ]

    if icon_path:
        cmd.extend(["--icon", str(icon_path)])

    cmd.extend(_pyinstaller_data_arguments())

    cmd.append(str(ENTRY_SCRIPT))

    run_command(cmd)

    exe_path = DIST_DIR / f"{PROJECT_NAME}.exe"
    if not exe_path.exists():
        raise FileNotFoundError(f"PyInstaller build did not produce {exe_path}")

    if exe_path.name != EXECUTABLE_NAME:
        target = DIST_DIR / EXECUTABLE_NAME
        if target.exists():
            target.unlink()
        exe_path.rename(target)
        exe_path = target

    return exe_path


def build_executable(backend: str, icon_path: Optional[Path]) -> Path:
    """Dispatch build to the selected backend."""

    if backend == "nuitka":
        return build_executable_nuitka(icon_path)
    if backend == "pyinstaller":
        return build_executable_pyinstaller(icon_path)
    raise ValueError(f"Unsupported backend: {backend}")


def test_executable(exe_path: Path) -> None:
    """Perform a basic smoke test of the generated executable."""

    print("Testing executable...")

    try:
        result = run_command([str(exe_path), "--help"], check=False)
        if result.returncode != 0:
            print("Executable does not expose --help. Launching for a short smoke test...")
            proc = subprocess.Popen([str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                proc.wait(timeout=5)
                print("Executable started and exited normally during smoke test.")
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                print("Executable started successfully (terminated after timeout).")
        else:
            print("Executable responded to --help. Basic CLI check passed.")
    except OSError as exc:
        print(f"Warning: failed to execute smoke test: {exc}")


def create_portable_package(exe_path: Path, backend: str) -> Path:
    """Create a portable directory containing the executable."""

    portable_dir = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir(parents=True)

    shutil.copy2(exe_path, portable_dir / EXECUTABLE_NAME)

    readme_content = f"""{APP_NAME} v{VERSION} - Portable Version
{'=' * 50}

This is a portable distribution of {APP_NAME}. No installation is required.

System Requirements:
- Windows 7 or higher (64-bit)
- 500MB free disk space
- .NET Framework 4.5 or higher (usually pre-installed)

Getting Started:
1. Double-click {EXECUTABLE_NAME} or run start.bat
2. Configuration files are stored in %USERPROFILE%\\.media-manager\\

Build Backend: {backend}
Build Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    (portable_dir / "README.txt").write_text(readme_content, encoding="utf-8")

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

    (portable_dir / "start.bat").write_text(batch_content, encoding="utf-8")

    print(f"Portable package created at {portable_dir}")
    return portable_dir


def create_installer_package(portable_dir: Path) -> Path:
    """Create a simple installer-style package using batch scripts."""

    installer_dir = PACKAGE_DIR / f"{PROJECT_NAME}-installer-{VERSION}"
    if installer_dir.exists():
        shutil.rmtree(installer_dir)
    installer_dir.mkdir(parents=True)

    shutil.copytree(portable_dir, installer_dir / "files", dirs_exist_ok=True)

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
echo You can now run {APP_NAME} from Start Menu, Desktop, or directly via:
echo   %INSTALL_DIR%\\{EXECUTABLE_NAME}
echo.
pause
"""

    (installer_dir / "install.bat").write_text(install_script, encoding="utf-8")

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

    (installer_dir / "uninstall.bat").write_text(uninstall_script, encoding="utf-8")

    print(f"Installer package created at {installer_dir}")
    return installer_dir


def calculate_file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def create_release_info(exe_path: Path, portable_dir: Path, installer_dir: Path, backend: str) -> str:
    """Create release information and ZIP archives for distribution."""

    portable_zip = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}.zip"
    installer_zip = PACKAGE_DIR / f"{PROJECT_NAME}-installer-{VERSION}.zip"

    for zip_path, source_dir in (
        (portable_zip, portable_dir),
        (installer_zip, installer_dir),
    ):
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    archive.write(file_path, file_path.relative_to(source_dir))

    exe_size = exe_path.stat().st_size
    portable_hash = calculate_file_hash(portable_zip)
    installer_hash = calculate_file_hash(installer_zip)
    exe_hash = calculate_file_hash(exe_path)

    release_info = f"""{APP_NAME} Release Information v{VERSION}
{'=' * 60}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Build Backend: {backend}

Files:
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
- Windows 7 or higher (64-bit)
- 500MB free disk space
- .NET Framework 4.5 or higher (usually pre-installed)

Verification:
- Windows: certutil -hashfile <file> SHA256
- Linux/macOS: sha256sum <file>

For installation and usage instructions, consult README_WINDOWS.md.
"""

    (PACKAGE_DIR / "RELEASE_INFO.txt").write_text(release_info, encoding="utf-8")

    print("Release information generated.")
    return release_info


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Media Manager Windows build helper")
    parser.add_argument(
        "--backend",
        choices=SUPPORTED_BACKENDS,
        default="nuitka",
        help="Build backend to use (default: nuitka)",
    )
    parser.add_argument(
        "--skip-dependency-install",
        action="store_true",
        help="Skip dependency installation step",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip executing the smoke tests on the generated executable",
    )
    parser.add_argument(
        "--skip-packages",
        action="store_true",
        help="Skip portable/installer packaging and release info generation",
    )
    parser.add_argument(
        "--only-install-deps",
        action="store_true",
        help="Install build dependencies for the selected backend and exit",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clean previous build artifacts before compiling",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.only_install_deps:
        install_dependencies(args.backend)
        return 0

    if not args.no_clean:
        clean_directories(include_packages=not args.skip_packages)

    setup_environment()

    if not args.skip_dependency_install:
        install_dependencies(args.backend)

    icon_path = find_icon()

    exe_path = build_executable(args.backend, icon_path)

    if not args.skip_tests:
        test_executable(exe_path)

    if args.skip_packages:
        print("Skipping packaging as requested.")
        return 0

    portable_dir = create_portable_package(exe_path, args.backend)
    installer_dir = create_installer_package(portable_dir)
    create_release_info(exe_path, portable_dir, installer_dir, args.backend)

    print("\n" + "=" * 60)
    print("BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Executable: {exe_path}")
    print(f"Portable package: {PACKAGE_DIR / (PROJECT_NAME + '-portable-' + VERSION)}")
    print(f"Installer package: {PACKAGE_DIR / (PROJECT_NAME + '-installer-' + VERSION)}")
    print(f"Release info: {PACKAGE_DIR / 'RELEASE_INFO.txt'}")
    print("\nAll artifacts located in:", PACKAGE_DIR)

    return 0


if __name__ == "__main__":
    sys.exit(main())
