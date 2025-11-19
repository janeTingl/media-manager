"""Main entry point for the media manager application."""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from media_manager.logging import get_logger, setup_logging
from media_manager.main_window import MainWindow
from media_manager.persistence.database import init_database_service
from media_manager.services import get_service_registry
from media_manager.settings import get_settings



def create_application() -> QApplication:
    """Create and configure the Qt application."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Media Manager")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Media Manager Team")
    app.setOrganizationDomain("media-manager.local")

    return app


def _install_translator(app: QApplication, language: Optional[str] = None) -> None:
    """Install Qt translations for the requested language if available."""
    translations_path = Path(__file__).parent / "translations"
    if not translations_path.exists():
        return

    translator = QTranslator()
    locale = _resolve_locale(language)
    if translator.load(locale, "media_manager", "_", str(translations_path)):
        app.installTranslator(translator)
        setattr(app, "_installed_translator", translator)


def _resolve_locale(language: Optional[str]) -> QLocale:
    """Return a QLocale for the requested language or the system default."""
    if language:
        normalized = language.replace("-", "_")
        return QLocale(normalized)
    return QLocale.system()


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

        # Install translator based on preferred language
        _install_translator(app, settings.get_language())

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
