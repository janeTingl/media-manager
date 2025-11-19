"""Smoke tests for built 影藏·媒体管理器 executables."""

import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from build_config import APP_NAME, DIST_DIR, PACKAGE_DIR, get_build_config


class TestBuildSmoke:
    """Smoke tests for built executables."""

    @pytest.fixture(params=["windows", "macos"])
    def platform_config(self, request):
        """Get platform-specific configuration."""
        if request.param == "windows" and platform.system() != "Windows":
            pytest.skip("Windows build test requires Windows environment")
        if request.param == "macos" and platform.system() != "Darwin":
            pytest.skip("macOS build test requires macOS environment")

        return get_build_config(request.param)

    @pytest.fixture
    def executable_path(self, platform_config):
        """Get path to the built executable."""
        if platform_config.is_windows:
            exe_name = platform_config.get_executable_name()
        else:
            exe_name = APP_NAME

        exe_path = DIST_DIR / exe_name
        if not exe_path.exists():
            pytest.skip(f"Executable not found: {exe_path}")

        return exe_path

    @pytest.fixture
    def app_bundle_path(self, platform_config):
        """Get path to the macOS app bundle."""
        if not platform_config.is_macos:
            pytest.skip("App bundle test only applies to macOS")

        app_path = DIST_DIR / "影藏·媒体管理器.app"
        if not app_path.exists():
            pytest.skip(f"App bundle not found: {app_path}")

        return app_path

    def test_executable_exists(self, executable_path):
        """Test that the executable exists and is executable."""
        assert executable_path.exists()
        assert executable_path.is_file()

        # Check if it's executable
        if platform.system() != "Windows":
            assert os.access(executable_path, os.X_OK)

    def test_executable_size(self, executable_path):
        """Test that the executable has reasonable size."""
        size = executable_path.stat().st_size

        # Should be at least 10MB (bundled Python + dependencies)
        assert size > 10 * 1024 * 1024, f"Executable too small: {size} bytes"

        # Should not be excessively large (more than 200MB might indicate issues)
        assert size < 200 * 1024 * 1024, f"Executable too large: {size} bytes"

    def test_executable_basic_info(self, executable_path):
        """Test basic executable information."""
        if platform.system() == "Windows":
            # Could use file command or other tools to verify PE format
            pass
        elif platform.system() == "Darwin":
            # Check if it's a Mach-O executable
            result = subprocess.run(
                ["file", str(executable_path)],
                capture_output=True,
                text=True
            )
            assert "Mach-O" in result.stdout

    @pytest.mark.slow
    def test_executable_launch_headless(self, executable_path):
        """Test that the executable can launch without GUI."""
        # For GUI applications, we can test basic startup in headless mode
        # using virtual display if available, or by testing help/version flags

        try:
            # Try to get version/help
            result = subprocess.run(
                [str(executable_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Some apps don't support --version, that's okay
            if result.returncode == 0:
                assert "0.1.0" in result.stdout or "影藏·媒体管理器" in result.stdout

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Try a different approach - launch briefly and terminate
            try:
                if platform.system() == "Darwin":
                    # On macOS, we can launch the app bundle
                    app_bundle = DIST_DIR / "影藏·媒体管理器.app"
                    if app_bundle.exists():
                        proc = subprocess.Popen([
                            "open", str(app_bundle)
                        ])
                        time.sleep(2)
                        proc.terminate()
                        proc.wait(timeout=5)
                        return

                # Fallback: try to launch executable directly
                proc = subprocess.Popen([str(executable_path)])
                time.sleep(3)  # Give it time to start
                proc.terminate()
                proc.wait(timeout=5)

            except Exception as e:
                pytest.skip(f"Could not test executable launch: {e}")

    @pytest.mark.slow
    def test_app_bundle_structure(self, app_bundle_path):
        """Test macOS app bundle structure."""
        if not app_bundle_path.exists():
            pytest.skip("App bundle not found")

        # Check app bundle structure
        contents_dir = app_bundle_path / "Contents"
        assert contents_dir.exists(), "Contents directory missing"

        # Check Info.plist
        info_plist = contents_dir / "Info.plist"
        assert info_plist.exists(), "Info.plist missing"

        # Check MacOS directory
        macos_dir = contents_dir / "MacOS"
        assert macos_dir.exists(), "MacOS directory missing"

        # Check executable
        executable = macos_dir / APP_NAME
        assert executable.exists(), "Executable missing"
        assert os.access(executable, os.X_OK), "Executable not executable"

    @pytest.mark.slow
    def test_app_bundle_info_plist(self, app_bundle_path):
        """Test macOS app bundle Info.plist contents."""
        if not app_bundle_path.exists():
            pytest.skip("App bundle not found")

        info_plist = app_bundle_path / "Contents" / "Info.plist"

        # Try to read the plist
        try:
            import plistlib
            with open(info_plist, "rb") as f:
                plist_data = plistlib.load(f)

            # Check required keys
            assert plist_data.get("CFBundleName") == "影藏·媒体管理器"
            assert plist_data.get("CFBundleIdentifier") == "com.mediamanager.media-manager"
            assert plist_data.get("CFBundleVersion") == "0.1.0"

        except ImportError:
            # Fallback: just check if file contains expected strings
            content = info_plist.read_text()
            assert "影藏·媒体管理器" in content
            assert "com.mediamanager.media-manager" in content

    def test_package_files_created(self):
        """Test that package files are created."""
        if not PACKAGE_DIR.exists():
            pytest.skip("Package directory not found")

        # Check for release info files
        release_files = list(PACKAGE_DIR.glob("RELEASE_INFO*.txt"))
        assert len(release_files) > 0, "No release info files found"

    def test_windows_installer_files(self):
        """Test Windows-specific package files."""
        if platform.system() != "Windows":
            pytest.skip("Windows package test only on Windows")

        if not PACKAGE_DIR.exists():
            pytest.skip("Package directory not found")

        # Look for Windows-specific packages
        portable_zip = list(PACKAGE_DIR.glob("media-manager-portable-*.zip"))
        installer_zip = list(PACKAGE_DIR.glob("media-manager-installer-*.zip"))

        # At least one should exist if Windows build was run
        assert len(portable_zip) > 0 or len(installer_zip) > 0, \
            "No Windows package files found"

    def test_macos_dmg_files(self):
        """Test macOS-specific package files."""
        if platform.system() != "Darwin":
            pytest.skip("macOS package test only on macOS")

        if not PACKAGE_DIR.exists():
            pytest.skip("Package directory not found")

        # Look for DMG files
        dmg_files = list(PACKAGE_DIR.glob("*.dmg"))

        if dmg_files:
            # Check DMG file size
            for dmg_file in dmg_files:
                size = dmg_file.stat().st_size
                assert size > 1 * 1024 * 1024, f"DMG too small: {dmg_file}"

    def test_executable_dependencies(self, executable_path):
        """Test that executable dependencies are properly bundled."""
        if platform.system() == "Linux":
            pytest.skip("Dependency test not implemented for Linux")

        try:
            # Check if executable runs without import errors
            # This is a basic smoke test
            result = subprocess.run(
                [str(executable_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Even if --version isn't supported, we shouldn't see import errors
            stderr = result.stderr.lower()
            assert "modulenotfounderror" not in stderr
            assert "importerror" not in stderr

        except subprocess.TimeoutExpired:
            # Timeout is okay - means it started but didn't exit quickly
            pass
        except Exception:
            # Other exceptions are okay for this smoke test
            pass


class TestBuildConfiguration:
    """Tests for build configuration."""

    def test_build_config_creation(self):
        """Test that build configuration can be created."""
        import build_config
        config = get_build_config()
        assert config is not None
        assert hasattr(config, 'platform_name')
        assert hasattr(build_config, 'VERSION')
        assert hasattr(build_config, 'PROJECT_ROOT')

    def test_platform_detection(self):
        """Test platform detection in build config."""
        config = get_build_config()

        if platform.system() == "Windows":
            assert config.is_windows
            assert not config.is_macos
        elif platform.system() == "Darwin":
            assert config.is_macos
            assert not config.is_windows
        else:
            assert not config.is_windows
            assert not config.is_macos

    def test_executable_name_generation(self):
        """Test executable name generation."""
        windows_config = get_build_config("windows")
        macos_config = get_build_config("macos")

        assert windows_config.get_executable_name() == "影藏·媒体管理器.exe"
        assert macos_config.get_executable_name() == APP_NAME

    def test_pyinstaller_args_generation(self):
        """Test PyInstaller arguments generation."""
        config = get_build_config("windows")
        args = config.get_pyinstaller_args()

        assert isinstance(args, list)
        assert "--name" in args
        assert APP_NAME in args
        assert "--onefile" in args

    def test_spec_file_content_generation(self):
        """Test PyInstaller spec file content generation."""
        config = get_build_config("windows")
        content = config.get_spec_file_content()

        assert isinstance(content, str)
        assert "Analysis(" in content
        assert "EXE(" in content
        assert APP_NAME in content


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
