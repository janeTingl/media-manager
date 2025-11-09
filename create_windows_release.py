#!/usr/bin/env python3
"""
Windows Release Creation Script for Media Manager

This helper orchestrates a clean end-to-end build of the Windows release
artifacts using the shared build helpers from ``build_windows.py``.

The workflow:
1. Optional environment verification and dependency installation
2. Compilation of the executable via the selected backend (Nuitka by default)
3. Optional smoke testing of the resulting executable
4. Creation of portable + installer packages
5. Generation of release metadata and ZIP archives

Run with:
    python create_windows_release.py [--backend nuitka|pyinstaller]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime

from build_windows import (
    APP_NAME,
    EXECUTABLE_NAME,
    PACKAGE_DIR,
    PROJECT_NAME,
    VERSION,
    DIST_DIR,
    SUPPORTED_BACKENDS,
    build_executable,
    clean_directories,
    create_installer_package,
    create_portable_package,
    create_release_info,
    find_icon,
    install_dependencies,
    setup_environment,
    test_executable,
)


def run_tool_version_check(module: str) -> bool:
    """Return True if ``python -m <module> --version`` succeeds."""

    try:
        subprocess.run(
            [sys.executable, "-m", module, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def verify_environment(backend: str) -> bool:
    """Basic environment validation before starting the release build."""

    if os.name != "nt":
        print("❌ ERROR: Windows environment is required to produce the final executable.")
        print("   Please run this script from a Windows host, VM, or CI runner.")
        return False

    if sys.version_info < (3, 8):
        print("❌ ERROR: Python 3.8 or higher is required.")
        return False

    module = "nuitka" if backend == "nuitka" else "PyInstaller"
    if not run_tool_version_check(module):
        print(f"❌ ERROR: {module} is not available. Install dependencies using build_windows.py or pip.")
        return False

    print("✅ Windows environment verified")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create full Windows release packages")
    parser.add_argument(
        "--backend",
        choices=SUPPORTED_BACKENDS,
        default="nuitka",
        help="Build backend to use (default: nuitka)",
    )
    parser.add_argument(
        "--skip-dependency-install",
        action="store_true",
        help="Skip installing build dependencies",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running the smoke tests on the generated executable",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clean previous build artifacts before building",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    backend_label = "Nuitka" if args.backend == "nuitka" else "PyInstaller"

    print(f"🎯 Creating {APP_NAME} v{VERSION} Windows Release using {backend_label}")
    print("=" * 60)

    if not verify_environment(args.backend):
        return 1

    if not args.no_clean:
        clean_directories(include_packages=True)

    setup_environment()

    if not args.skip_dependency_install:
        install_dependencies(args.backend)

    icon_path = find_icon()

    try:
        exe_path = build_executable(args.backend, icon_path)
    except Exception as exc:  # pragma: no cover - packaging errors propagate
        print(f"❌ Build failed: {exc}")
        return 1

    if not args.skip_tests:
        test_executable(exe_path)

    portable_dir = create_portable_package(exe_path, args.backend)
    installer_dir = create_installer_package(portable_dir)
    create_release_info(exe_path, portable_dir, installer_dir, args.backend)

    portable_zip = PACKAGE_DIR / f"{PROJECT_NAME}-portable-{VERSION}.zip"
    installer_zip = PACKAGE_DIR / f"{PROJECT_NAME}-installer-{VERSION}.zip"

    print("\n" + "=" * 60)
    print("🎉 WINDOWS RELEASE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Backend: {backend_label}")
    print(f"Executable: {exe_path} ({exe_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Portable ZIP: {portable_zip} ({portable_zip.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Installer ZIP: {installer_zip} ({installer_zip.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Release info: {PACKAGE_DIR / 'RELEASE_INFO.txt'}")
    print("Dist directory:", DIST_DIR)
    print("Package directory:", PACKAGE_DIR)

    print("\n📋 Release summary saved to RELEASE_INFO.txt")
    print("📄 Portable package located at:", portable_dir)
    print("📄 Installer package located at:", installer_dir)
    print("\n✅ Release build completed at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print("\nNext steps:")
    print(" 1. Test the portable package on a clean Windows machine")
    print(" 2. Verify file hashes using the values in RELEASE_INFO.txt")
    print(" 3. Upload the ZIP files and RELEASE_INFO.txt to your release channel")

    return 0


if __name__ == "__main__":
    sys.exit(main())
