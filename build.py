#!/usr/bin/env python3
"""
Unified build script for Media Manager cross-platform executables.

This script provides a single interface to build Media Manager for multiple platforms:
- Windows (executable with installer)
- macOS (app bundle with DMG)
- Linux (AppImage or similar, future enhancement)

Usage:
    python build.py [--platform PLATFORM] [--version VERSION] [--sign] [--package]

Options:
    --platform PLATFORM: Target platform (windows, macos, linux, all)
    --version VERSION: Override version (default: from pyproject.toml)
    --sign: Enable code signing (requires proper setup)
    --package: Create distribution packages
    --help: Show this help message
"""

import argparse
import sys
import platform
from pathlib import Path

# Import shared build configuration
from build_config import get_build_config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build Media Manager for multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py --platform windows
  python build.py --platform macos --sign
  python build.py --platform all --package
  python build.py --platform macos --version 1.0.0
        """
    )
    
    parser.add_argument(
        "--platform", "-p",
        choices=["windows", "macos", "linux", "all"],
        default=platform.system().lower(),
        help="Target platform (default: current platform)"
    )
    
    parser.add_argument(
        "--version", "-v",
        help="Override version (default: from pyproject.toml)"
    )
    
    parser.add_argument(
        "--sign", "-s",
        action="store_true",
        help="Enable code signing (requires proper setup)"
    )
    
    parser.add_argument(
        "--package", "-k",
        action="store_true", 
        help="Create distribution packages"
    )
    
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Clean build directories before building"
    )
    
    return parser.parse_args()


def get_version_from_pyproject():
    """Extract version from pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            print("WARNING: No TOML library available, using default version")
            return "0.1.0"
    
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return "0.1.0"
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            return data.get("project", {}).get("version", "0.1.0")
    except Exception as e:
        print(f"WARNING: Could not read version from pyproject.toml: {e}")
        return "0.1.0"


def build_platform(platform_name: str, args) -> bool:
    """Build for a specific platform."""
    print(f"\n{'='*60}")
    print(f"Building for platform: {platform_name.upper()}")
    print(f"{'='*60}")
    
    try:
        if platform_name == "windows":
            from build_windows import main as build_main
        elif platform_name == "macos":
            from build_macos import main as build_main
        elif platform_name == "linux":
            print("Linux builds are not yet implemented")
            return False
        else:
            print(f"Unknown platform: {platform_name}")
            return False
        
        # Override version if specified
        if args.version:
            import build_config
            build_config.VERSION = args.version
        
        # Run platform-specific build
        build_main()
        return True
        
    except ImportError as e:
        print(f"Could not import build script for {platform_name}: {e}")
        return False
    except Exception as e:
        print(f"Build failed for {platform_name}: {e}")
        return False


def clean_build_directories():
    """Clean build directories."""
    print("Cleaning build directories...")
    
    import shutil
    from build_config import BUILD_DIR, DIST_DIR, PACKAGE_DIR
    
    for directory in [BUILD_DIR, DIST_DIR, PACKAGE_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
            print(f"Cleaned: {directory}")
    
    print("Build directories cleaned")


def main():
    """Main build orchestrator."""
    args = parse_arguments()
    
    print("Media Manager Cross-Platform Build Tool")
    print("=" * 60)
    
    # Clean if requested
    if args.clean:
        clean_build_directories()
    
    # Determine platforms to build
    if args.platform == "all":
        platforms = ["windows", "macos", "linux"]
    else:
        platforms = [args.platform]
    
    # Get version
    version = args.version or get_version_from_pyproject()
    print(f"Version: {version}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Code signing: {'Enabled' if args.sign else 'Disabled'}")
    print(f"Packaging: {'Enabled' if args.package else 'Disabled'}")
    
    # Build for each platform
    successful_builds = []
    failed_builds = []
    
    for platform_name in platforms:
        try:
            success = build_platform(platform_name, args)
            if success:
                successful_builds.append(platform_name)
            else:
                failed_builds.append(platform_name)
        except Exception as e:
            print(f"Unexpected error building {platform_name}: {e}")
            failed_builds.append(platform_name)
    
    # Print summary
    print(f"\n{'='*60}")
    print("BUILD SUMMARY")
    print(f"{'='*60}")
    
    if successful_builds:
        print(f"✅ Successful builds: {', '.join(successful_builds)}")
    if failed_builds:
        print(f"❌ Failed builds: {', '.join(failed_builds)}")
    
    if failed_builds:
        print(f"\nBuild completed with {len(failed_builds)} failures")
        sys.exit(1)
    else:
        print(f"\n🎉 All builds completed successfully!")
        print(f"\nBuilt packages can be found in:")
        print(f"  - Executables: dist/")
        print(f"  - Distribution packages: package/")


if __name__ == "__main__":
    main()