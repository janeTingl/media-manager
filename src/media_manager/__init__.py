"""影藏·媒体管理器 - A PySide6-based media management application."""

__version__ = "0.1.0"
APP_DISPLAY_NAME = "影藏·媒体管理器"
APP_EXECUTABLE_NAME = APP_DISPLAY_NAME
APP_ORGANIZATION_NAME = "影藏·媒体管理器团队"
APP_ORGANIZATION_DOMAIN = "yingcang-media-manager.local"
APP_INTERNAL_NAME = "YingcangMediaManager"
APP_USER_AGENT = f"{APP_INTERNAL_NAME}/{__version__}"

from .models import MediaType, VideoMetadata
from .scan_engine import ScanEngine
from .scanner import ScanConfig, Scanner

__all__ = [
    "MediaType",
    "VideoMetadata",
    "ScanEngine",
    "ScanConfig",
    "Scanner",
    "__version__",
    "APP_DISPLAY_NAME",
    "APP_EXECUTABLE_NAME",
    "APP_ORGANIZATION_NAME",
    "APP_ORGANIZATION_DOMAIN",
    "APP_INTERNAL_NAME",
    "APP_USER_AGENT",
]
