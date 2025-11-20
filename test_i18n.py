#!/usr/bin/env python3
"""Test script to verify i18n translation loading."""

import sys
from pathlib import Path

# Make sure we can import from src
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication

from media_manager.i18n import install_translators
from media_manager.logging import setup_logging


def main() -> None:
    # Setup logging first
    setup_logging("INFO")

    # Create Qt application
    app = QApplication(sys.argv)

    print("\n" + "=" * 80)
    print("Testing i18n translation loading")
    print("=" * 80 + "\n")

    # Test with zh_CN
    print(">>> Testing zh_CN translation loading:")
    install_translators(app, "zh_CN")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
