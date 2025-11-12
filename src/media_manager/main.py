"""Main entry point for the media manager application."""

import sys
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from .logging import get_logger, setup_logging
from .main_window import MainWindow
from .persistence.database import init_database_service
from .services import get_service_registry
from .settings import get_settings


def create_application() -> QApplication:
    """Create and configure the Qt application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Media Manager")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Media Manager Team")
    app.setOrganizationDomain("media-manager.local")

    # Setup translator
    translator = QTranslator()
    locale = QLocale.system()
    translations_path = str(Path(__file__).parent / "translations")
    if translator.load(locale, "media_manager", "_", translations_path):
        app.installTranslator(translator)

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

        # Show the main window
        main_window.show()

        logger.info("Application started successfully")

        # Run the application
        return app.exec()

    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
