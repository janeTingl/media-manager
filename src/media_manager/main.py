"""Main entry point for the media manager application."""

import sys
from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtWidgets import QApplication

from .localization import install_language_translators
from .logging import get_logger, setup_logging
from .main_window import MainWindow
from .persistence.database import init_database_service
from .services import get_service_registry
from .settings import get_settings


def create_application(arguments: List[str]) -> QApplication:
    """Create and configure the Qt application."""
    app = QApplication(arguments)

    # Set application properties
    app.setApplicationName("Media Manager")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Media Manager Team")
    app.setOrganizationDomain("media-manager.local")

    return app


def _extract_language_override(argv: List[str]) -> Tuple[List[str], Optional[str]]:
    """Extract a --lang/--language override while preserving other arguments."""
    if not argv:
        return [], None

    sanitized: List[str] = [argv[0]]
    language: Optional[str] = None
    skip_next = False

    for arg in argv[1:]:
        if skip_next:
            language = arg.strip()
            skip_next = False
            continue
        if arg in {"--lang", "--language"}:
            skip_next = True
            continue
        if arg.startswith("--lang=") or arg.startswith("--language="):
            _, value = arg.split("=", 1)
            language = value.strip()
            continue
        sanitized.append(arg)

    return sanitized, language


def main() -> int:
    """Main entry point for the application."""
    # Setup logging first
    log_file = Path.home() / ".media-manager" / "logs" / "app.log"
    setup_logging("INFO", log_file)
    logger = get_logger().get_logger(__name__)

    try:
        # Prepare arguments and create Qt application
        qt_args, cli_language = _extract_language_override(sys.argv)
        app = create_application(qt_args)

        # Get settings
        settings = get_settings()

        # Install translators before creating any widgets
        resolved_language = install_language_translators(
            app, cli_language or settings.get_language()
        )
        app.setProperty("ui.language", resolved_language)
        if cli_language:
            logger.info(
                "Language override requested (%s), using %s",
                cli_language,
                resolved_language,
            )
        else:
            logger.info("Language set to %s", resolved_language)

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
