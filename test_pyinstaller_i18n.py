#!/usr/bin/env python3
"""
Test script to simulate PyInstaller environment for i18n testing.
This helps verify translation loading will work in a --onefile build.
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Simulate PyInstaller's _MEIPASS by creating a temporary directory
temp_dir = tempfile.mkdtemp(prefix="_MEI")
print(f"Created temporary _MEIPASS: {temp_dir}")

# Copy translation files to the temp directory structure
project_root = Path(__file__).parent
src_i18n = project_root / "src" / "media_manager" / "resources" / "i18n"
dest_i18n = Path(temp_dir) / "resources" / "i18n"

if src_i18n.exists():
    dest_i18n.mkdir(parents=True, exist_ok=True)
    for qm_file in src_i18n.glob("*.qm"):
        shutil.copy2(qm_file, dest_i18n)
        print(f"Copied {qm_file.name} to {dest_i18n}")

# Set sys._MEIPASS to simulate PyInstaller
sys._MEIPASS = temp_dir  # type: ignore

# Add src to path so we can import
sys.path.insert(0, str(project_root / "src"))

try:
    from PySide6.QtWidgets import QApplication

    from media_manager.i18n import install_translators
    from media_manager.logging import setup_logging

    # Setup logging
    setup_logging("INFO")

    # Create Qt application
    app = QApplication(sys.argv)

    print("\n" + "=" * 80)
    print("Testing i18n translation loading in simulated PyInstaller environment")
    print("=" * 80 + "\n")

    print(f"sys._MEIPASS = {sys._MEIPASS}")  # type: ignore[attr-defined]
    print(f"Translation files in _MEIPASS: {list(dest_i18n.glob('*.qm'))}")
    print()

    # Test with zh_CN
    print(">>> Testing zh_CN translation loading in PyInstaller mode:")
    install_translators(app, "zh_CN")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80 + "\n")

    # Check if translators were installed
    if hasattr(app, "_installed_translators"):
        print(f"✓ SUCCESS: {len(app._installed_translators)} translators installed")
        return_code = 0
    else:
        print("✗ FAILURE: No translators were installed")
        return_code = 1

finally:
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"\nCleaned up temporary directory: {temp_dir}")

sys.exit(return_code)
