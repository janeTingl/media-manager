"""Main entry point for the media manager application."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from media_manager import (
    APP_DISPLAY_NAME,
    APP_ORGANIZATION_DOMAIN,
    APP_ORGANIZATION_NAME,
)
from media_manager.logging import get_logger, setup_logging
from media_manager.main_window import MainWindow
from media_manager.persistence.database import init_database_service
from media_manager.services import get_service_registry
from media_manager.settings import get_settings


def create_application() -> QApplication:
    """Create and configure the Qt application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationDisplayName(APP_DISPLAY_NAME)
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName(APP_ORGANIZATION_NAME)
    app.setOrganizationDomain(APP_ORGANIZATION_DOMAIN)

    return app


def main() -> int:
    """Main entry point for the application."""
    # Setup logging first
    log_file = Path.home() / ".media-manager" / "logs" / "app.log"
    setup_logging("INFO", log_file)
    logger = get_logger().get_logger(__name__)

    try:
        # Create Qt application
        app = create_application()

        # Get settings
        settings = get_settings()

        # Initialize database service
        db_service = init_database_service(settings.get_database_url())

        # Register database service in service registry
        service_registry = get_service_registry()
        service_registry.register("DatabaseService", db_service)

        # Create main window
        main_window = MainWindow(settings)
        main_window.setWindowTitle(APP_DISPLAY_NAME)
        main_window.show()

        logger.info("Application started successfully")

        # Run the application
        return app.exec()

    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
