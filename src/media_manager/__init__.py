"""Media Manager - A PySide6-based media management application."""

from .models import MediaType, VideoMetadata
from .scan_engine import ScanEngine
from .scanner import ScanConfig, Scanner

__version__ = "0.1.0"

__all__ = [
    "MediaType",
    "VideoMetadata",
    "ScanEngine",
    "ScanConfig",
    "Scanner",
    "__version__",
]
