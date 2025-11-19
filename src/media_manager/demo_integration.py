"""Demo integration script to showcase the scan-to-match workflow."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from .logging import get_logger, setup_logging
from .main_window import MainWindow
from .scan_engine import ScanEngine
from .scanner import ScanConfig
from .services import get_service_registry
from .settings import get_settings
from .workers import WorkerManager


def setup_demo_services() -> None:
    """Setup services for the demo."""
    registry = get_service_registry()
    registry.clear()

    # Register worker manager
    registry.register(WorkerManager, lambda: WorkerManager())


def run_demo_scan(main_window: MainWindow) -> None:
    """Run a demo scan on a sample directory."""
    logger = get_logger().get_logger(__name__)

    # Try to find a good demo directory
    demo_paths = [
        Path.home() / "Videos",
        Path.home() / "Movies",
        Path.home() / "Downloads",
        Path("/tmp"),
    ]

    demo_dir = None
    for path in demo_paths:
        if path.exists() and path.is_dir():
            # Check if it contains video files
            video_files = list(path.glob("**/*.mkv")) + list(path.glob("**/*.mp4"))
            if video_files:
                demo_dir = path
                break

    if not demo_dir:
        # Ask user to select a directory
        demo_dir = QFileDialog.getExistingDirectory(
            main_window,
            "Select Directory for Demo Scan",
            str(Path.home())
        )
        if not demo_dir:
            return
        demo_dir = Path(demo_dir)

    logger.info(f"Starting demo scan of: {demo_dir}")
    main_window.update_status(f"Scanning {demo_dir}...")

    # Create scan engine
    engine = ScanEngine()

    # Connect signals
    def on_scan_progress(current: int, total: int, path: str) -> None:
        main_window.update_status(f"Scanning {current}/{total}: {Path(path).name}")

    def on_scan_completed(results) -> None:
        logger.info(f"Scan completed: {len(results)} items found")
        main_window.update_status(f"Scan complete: {len(results)} items found")

        if results:
            # Add to matching queue
            main_window.add_scan_results(results)
        else:
            QMessageBox.information(
                main_window,
                "No Media Found",
                "No video files were found in the selected directory.\n"
                "Please try a different directory containing video files."
            )

    def on_scan_error(error: str) -> None:
        logger.error(f"Scan error: {error}")
        QMessageBox.warning(main_window, "Scan Error", f"Scan failed: {error}")

    engine.scan_progress.connect(on_scan_progress)
    engine.scan_completed.connect(on_scan_completed)
    engine.scan_error.connect(on_scan_error)

    # Start scan
    config = ScanConfig(root_paths=[demo_dir])
    try:
        engine.scan(config)
    except Exception as e:
        logger.error(f"Demo scan failed: {e}")
        QMessageBox.critical(main_window, "Scan Error", f"Demo scan failed: {e}")


def show_demo_instructions(main_window: MainWindow) -> None:
    """Show demo instructions to the user."""
    instructions = (
        "Welcome to the 影藏·媒体管理器 Demo!\n\n"
        "This demo showcases the scan-to-match workflow:\n\n"
        "1. Click 'Demo Scan' to scan a directory for video files\n"
        "2. View the results in the 'Matching' tab\n"
        "3. Click 'Start Matching' to find automatic matches\n"
        "4. Select items to review detailed match information\n"
        "5. Use 'Manual Search' to override automatic matches\n"
        "6. Accept, skip, or manually match items\n\n"
        "The matching uses mock data for demonstration purposes.\n"
        "In a real application, this would connect to external APIs."
    )

    QMessageBox.information(main_window, "Demo Instructions", instructions)


def main() -> int:
    """Main entry point for the demo application."""
    # Setup logging
    log_file = Path.home() / ".media-manager" / "logs" / "demo.log"
    setup_logging("INFO", log_file)
    logger = get_logger().get_logger(__name__)

    try:
        # Create Qt application
        app = QApplication(sys.argv)

        # Setup demo services
        setup_demo_services()

        # Get settings and create main window
        settings = get_settings()
        main_window = MainWindow(settings)

        # Add demo menu action
        demo_menu = main_window.menuBar().addMenu("&Demo")

        demo_scan_action = demo_menu.addAction("&Demo Scan")
        demo_scan_action.triggered.connect(lambda: run_demo_scan(main_window))

        demo_menu.addSeparator()

        instructions_action = demo_menu.addAction("&Instructions")
        instructions_action.triggered.connect(lambda: show_demo_instructions(main_window))

        # Show instructions on startup
        QTimer.singleShot(500, lambda: show_demo_instructions(main_window))

        # Show main window
        main_window.show()

        logger.info("Demo application started successfully")

        # Run the application
        return app.exec()

    except Exception as e:
        logger.error(f"Demo application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
