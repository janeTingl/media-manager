from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator

from .logging import get_logger

SUPPORTED_LANGUAGES: Tuple[Tuple[str, str], ...] = (
    ("system", "System Default"),
    ("en", "English"),
    ("zh_CN", "简体中文"),
)

_LANGUAGE_ALIASES = {
    "": "system",
    "system": "system",
    "auto": "system",
    "default": "system",
    "en_us": "en",
    "en-gb": "en",
    "en_uk": "en",
    "en": "en",
    "zh": "zh_CN",
    "zh_cn": "zh_CN",
    "zh-cn": "zh_CN",
    "zh_hans": "zh_CN",
    "zh-hans": "zh_CN",
}

_LOGGER = get_logger().get_logger(__name__)


def get_supported_language_codes() -> List[str]:
    return [code for code, _ in SUPPORTED_LANGUAGES]


def get_language_display_name(code: str) -> str:
    for language_code, label in SUPPORTED_LANGUAGES:
        if language_code == code:
            return label
    return code


def normalize_language_code(code: Optional[str]) -> str:
    """Normalize user-provided language code to a supported variant."""
    if code is None:
        return "system"
    normalized = code.strip().lower().replace("-", "_")
    return _LANGUAGE_ALIASES.get(normalized, normalized)


def resolve_language_for_runtime(preference: Optional[str]) -> str:
    """Resolve a preference (which may be 'system') to a concrete locale code."""
    normalized = normalize_language_code(preference)
    if normalized == "system":
        system_locale = QLocale.system()
        normalized = normalize_language_code(system_locale.name())

    normalized_lower = normalized.lower()
    if normalized_lower not in {"en", "zh_cn"}:
        normalized_lower = "en"

    # Ensure canonical casing for downstream usage
    return "zh_CN" if normalized_lower == "zh_cn" else "en"


def _translation_directories() -> Iterable[Path]:
    """Yield candidate directories that may contain translation files."""
    locations: List[Path] = []

    package_root = Path(__file__).resolve().parent
    locations.append(package_root / "translations")

    # Development layout where package root lives in src/
    locations.append(package_root.parent / "translations")

    # PyInstaller extraction directory
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        locations.append(Path(meipass) / "media_manager" / "translations")

    seen = set()
    for location in locations:
        if location and location.exists():
            resolved = location.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield resolved


def _load_qt_base_translator(locale: QLocale) -> Optional[QTranslator]:
    qt_translations = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    if not qt_translations.exists():
        return None
    translator = QTranslator()
    if translator.load(locale, "qtbase", "_", str(qt_translations)):
        return translator
    return None


def _load_application_translator(locale: QLocale) -> Optional[QTranslator]:
    for directory in _translation_directories():
        translator = QTranslator()
        if translator.load(locale, "media_manager", "_", str(directory)):
            return translator
    return None


def install_language_translators(app, preference: Optional[str]) -> str:
    """Install translators for the requested preference and return the active locale."""
    resolved = resolve_language_for_runtime(preference)

    # Remove any existing translators we previously registered
    existing = getattr(app, "_installed_translators", [])
    for translator in existing:
        app.removeTranslator(translator)
    app._installed_translators = []

    if resolved == "en":
        _LOGGER.info("Using English locale; no translators required")
        return resolved

    locale = QLocale(resolved)
    translators: List[QTranslator] = []

    qt_translator = _load_qt_base_translator(locale)
    if qt_translator:
        app.installTranslator(qt_translator)
        translators.append(qt_translator)
    else:
        _LOGGER.warning("Unable to load Qt base translator for locale %s", resolved)

    app_translator = _load_application_translator(locale)
    if app_translator:
        app.installTranslator(app_translator)
        translators.append(app_translator)
    else:
        _LOGGER.warning("Unable to locate application translator for locale %s", resolved)

    app._installed_translators = translators
    return resolved


def language_choice_requires_restart(old_value: str, new_value: str) -> bool:
    """Return True if language preferences differ and require a restart."""
    return normalize_language_code(old_value) != normalize_language_code(new_value)


def iter_language_options() -> Iterable[Tuple[str, str]]:
    """Return supported language options as (code, label) pairs."""
    return SUPPORTED_LANGUAGES
