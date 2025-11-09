#!/usr/bin/env python3
"""
Windows Release Status Checker

This script checks the current status of the Windows release preparation
and provides clear next steps.

Usage:
    python check_release_status.py
"""

import os
import sys
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists and return status."""
    if path.exists():
        size = path.stat().st_size if path.is_file() else "N/A"
        return f"✅ {description}: {path} ({size:,} bytes)"
    else:
        return f"❌ {description}: {path} (MISSING)"

def check_directory_exists(path, description):
    """Check if a directory exists and return status."""
    if path.exists() and path.is_dir():
        file_count = len(list(path.rglob('*'))) if path.is_dir() else 0
        return f"✅ {description}: {path} ({file_count} files)"
    else:
        return f"❌ {description}: {path} (MISSING)"

def main():
    """Check release status and provide next steps."""
    print("🔍 Media Manager Windows Release Status Check")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    
    # Check essential files
    print("\n📁 Essential Files:")
    print(check_file_exists(project_root / "build_windows.py", "Build script"))
    print(check_file_exists(project_root / "create_windows_release.py", "Release creator"))
    print(check_file_exists(project_root / "build-requirements.txt", "Build requirements"))
    
    # Check package structure
    print("\n📦 Package Structure:")
    package_dir = project_root / "package"
    print(check_directory_exists(package_dir, "Package directory"))
    print(check_file_exists(package_dir / "RELEASE_INFO.txt", "Release info"))
    print(check_file_exists(package_dir / "media-manager-portable-0.1.0.zip", "Portable ZIP"))
    print(check_file_exists(package_dir / "media-manager-installer-0.1.0.zip", "Installer ZIP"))
    
    # Check Windows executable
    print("\n🎯 Windows Executable:")
    dist_dir = project_root / "dist"
    exe_path = dist_dir / "media-manager.exe"
    if exe_path.exists():
        size = exe_path.stat().st_size
        print(f"✅ Windows executable: {exe_path} ({size:,} bytes)")
        print("🎉 READY FOR GITHUB RELEASE!")
    else:
        print(f"❌ Windows executable: {exe_path} (MISSING)")
        print("⚠️  Requires Windows environment to build")
    
    # Check GitHub Actions
    print("\n🤖 Automation:")
    github_actions = project_root / ".github" / "workflows" / "build-windows-release.yml"
    print(check_file_exists(github_actions, "GitHub Actions workflow"))
    
    # Documentation
    print("\n📚 Documentation:")
    docs = [
        ("PACKAGING_GUIDE.md", "Packaging guide"),
        ("DEPLOYMENT.md", "Deployment guide"),
        ("WINDOWS_RELEASE_STATUS.md", "Windows status"),
        ("WINDOWS_RELEASE_SUMMARY.md", "Release summary"),
    ]
    for doc, desc in docs:
        print(check_file_exists(project_root / doc, desc))
    
    # Current platform
    print(f"\n💻 Current Platform: {os.name}")
    if os.name == 'nt':
        print("✅ Running on Windows - can build executable now!")
    else:
        print("⚠️  Not on Windows - cannot build Windows executable")
    
    # Next steps
    print("\n🚀 Next Steps:")
    exe_exists = exe_path.exists()
    
    if exe_exists:
        print("1. ✅ Windows executable is ready!")
        print("2. 📤 Upload files to GitHub Release:")
        print("   - media-manager.exe")
        print("   - media-manager-portable-0.1.0.zip")
        print("   - media-manager-installer-0.1.0.zip")
        print("   - RELEASE_INFO.txt")
        print("3. 📝 Create GitHub Release with release notes")
        print("4. 🐍 Publish to PyPI: twine upload dist/*")
    else:
        print("1. 🪟 Set up Windows environment:")
        print("   Option A: Push to GitHub (automated build)")
        print("   Option B: Use Windows VM")
        print("   Option C: Use native Windows system")
        print("")
        print("2. 🔨 Build Windows executable:")
        if os.name == 'nt':
            print("   python build_windows.py --backend nuitka --only-install-deps")
            print("   python create_windows_release.py --backend nuitka")
        else:
            print("   Run on Windows: python build_windows.py --backend nuitka --only-install-deps")
            print("   Run on Windows: python create_windows_release.py --backend nuitka")
        print("")
        print("3. 📤 Upload to GitHub Release")
        print("4. 🐍 Publish to PyPI")
    
    print("\n" + "=" * 60)
    
    if exe_exists:
        print("🎉 STATUS: RELEASE READY")
        return 0
    else:
        print("🟡 STATUS: INFRASTRUCTURE READY, NEEDS WINDOWS BUILD")
        return 1

if __name__ == "__main__":
    sys.exit(main())