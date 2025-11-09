#!/usr/bin/env python3
"""
Build verification script for Media Manager Windows executable.

This script verifies that all necessary files and configurations are in place
for building the Windows executable.
"""

import os
import sys
from pathlib import Path
import subprocess

def check_file_exists(filepath: Path, description: str) -> bool:
    """Check if a file exists and report status."""
    if filepath.exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description}: {filepath} (MISSING)")
        return False

def check_python_version() -> bool:
    """Check Python version compatibility."""
    version = sys.version_info
    print(f"\nPython Version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 8):
        print("✓ Python version is compatible (3.8+)")
        return True
    else:
        print("✗ Python version is too old (requires 3.8+)")
        return False

def check_module_installed(module_name: str) -> bool:
    """Check if a Python module is installed."""
    try:
        __import__(module_name)
        print(f"✓ {module_name} is installed")
        return True
    except ImportError:
        print(f"✗ {module_name} is NOT installed")
        return False

def check_spec_file() -> bool:
    """Check PyInstaller spec file."""
    spec_file = Path("media-manager.spec")
    if not spec_file.exists():
        return False
    
    # Try to compile the spec file
    try:
        with open(spec_file, 'r') as f:
            spec_content = f.read()
        compile(spec_content, str(spec_file), 'exec')
        print("✓ Spec file syntax is valid")
        return True
    except SyntaxError as e:
        print(f"✗ Spec file has syntax error: {e}")
        return False

def check_source_files() -> bool:
    """Check that main source files exist."""
    src_dir = Path("src/media_manager")
    required_files = [
        "__init__.py",
        "main.py",
        "demo_integration.py",
        "main_window.py",
        "models.py",
        "settings.py",
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = src_dir / file_name
        if not check_file_exists(file_path, f"Source file {file_name}"):
            all_exist = False
    
    return all_exist

def check_build_files() -> bool:
    """Check build-related files."""
    build_files = [
        ("media-manager.spec", "PyInstaller spec file"),
        ("build-requirements.txt", "Build requirements"),
        ("build_windows.py", "Build script"),
        ("version_info.txt", "Version info"),
        ("Makefile.windows", "Windows Makefile"),
        ("build.bat", "Batch build script"),
        ("build.ps1", "PowerShell build script"),
        ("PACKAGING_GUIDE.md", "Packaging guide"),
        ("README_WINDOWS.md", "Windows README"),
    ]
    
    all_exist = True
    for file_name, description in build_files:
        file_path = Path(file_name)
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_pyinstaller_availability() -> bool:
    """Check if PyInstaller is available."""
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ PyInstaller is installed: {version}")
            return True
        else:
            print("✗ PyInstaller is not working properly")
            return False
    except FileNotFoundError:
        print("✗ PyInstaller is not installed")
        return False

def check_pyside6_availability() -> bool:
    """Check if PySide6 is available."""
    try:
        result = subprocess.run([sys.executable, "-c", "import PySide6; print(PySide6.__version__)"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✓ PySide6 is installed: {version}")
            return True
        else:
            print("✗ PySide6 is not working properly")
            return False
    except Exception:
        print("✗ PySide6 is not installed")
        return False

def check_icon_file() -> bool:
    """Check if icon file exists or placeholder."""
    icon_file = Path("icon.ico")
    if icon_file.exists():
        print("✓ Icon file exists: icon.ico")
        return True
    else:
        print("⚠ Icon file missing (icon.ico) - using default icon")
        return True  # Not critical

def check_directory_structure() -> bool:
    """Check project directory structure."""
    required_dirs = [
        ("src", "Source directory"),
        ("src/media_manager", "Main package directory"),
        ("tests", "Tests directory"),
    ]
    
    all_exist = True
    for dir_name, description in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists() and dir_path.is_dir():
            print(f"✓ {description}: {dir_name}")
        else:
            print(f"✗ {description}: {dir_name} (MISSING)")
            all_exist = False
    
    return all_exist

def verify_entry_points() -> bool:
    """Verify that entry points are properly defined."""
    main_file = Path("src/media_manager/main.py")
    demo_file = Path("src/media_manager/demo_integration.py")
    
    # Check main function exists
    if main_file.exists():
        with open(main_file, 'r') as f:
            content = f.read()
            if "def main()" in content:
                print("✓ Main entry point exists in main.py")
            else:
                print("✗ Main entry point missing in main.py")
                return False
    
    # Check demo function exists
    if demo_file.exists():
        with open(demo_file, 'r') as f:
            content = f.read()
            if "def main()" in content:
                print("✓ Demo entry point exists in demo_integration.py")
            else:
                print("✗ Demo entry point missing in demo_integration.py")
                return False
    
    return True

def main():
    """Run all verification checks."""
    print("Media Manager Windows Build Verification")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Directory Structure", check_directory_structure),
        ("Source Files", check_source_files),
        ("Build Files", check_build_files),
        ("Spec File", check_spec_file),
        ("Entry Points", verify_entry_points),
        ("Icon File", check_icon_file),
        ("PySide6", check_pyside6_availability),
        ("PyInstaller", check_pyinstaller_availability),
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * len(check_name))
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to build.")
        print("\nNext steps:")
        print("1. Run: python build_windows.py")
        print("2. Or run: build.bat (Windows)")
        print("3. Or run: .\\build.ps1 (PowerShell)")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed. Please fix issues before building.")
        return 1

if __name__ == "__main__":
    sys.exit(main())