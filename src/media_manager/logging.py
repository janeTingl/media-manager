"""Logging configuration for the media manager application."""

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from PySide6.QtCore import QObject

if TYPE_CHECKING:
    pass


class Logger(QObject):
    """Centralized logging manager for the application."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._loggers: dict[str, logging.Logger] = {}

    def setup_logging(
        self, log_level: str = "INFO", log_file: Optional[Path] = None
    ) -> None:
        """Configure logging for the application."""
        level = getattr(logging, log_level.upper(), logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        # Setup file handler if specified
        handlers: list[Union[logging.StreamHandler, logging.FileHandler]] = [
            console_handler
        ]
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # Configure root logger
        logging.basicConfig(level=level, handlers=handlers, force=True)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the specified name."""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]


# Global logger instance
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


def setup_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """Setup logging for the application."""
    get_logger().setup_logging(log_level, log_file)
