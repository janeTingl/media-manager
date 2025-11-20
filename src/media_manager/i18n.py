"""Internationalization helpers for the media manager UI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Sequence

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

# Ordered so that the UI displays languages in a predictable order.
LANGUAGE_MAP: dict[str, str] = {
    "en_US": "English",
    "de_DE": "Deutsch",
    "fr_FR": "Français",
    "zh_CN": "简体中文",
}

DEFAULT_LANGUAGE = "en_US"
SUPPORTED_LANGUAGES: tuple[str, ...] = tuple(LANGUAGE_MAP.keys())
TRANSLATION_BASENAME = "media_manager"


def get_language_choices() -> Sequence[tuple[str, str]]:
    """Return the available language choices for UI controls."""
    return tuple(LANGUAGE_MAP.items())


def language_label(language: str) -> str:
    """Return the localized label for a language/locale code."""
    return LANGUAGE_MAP.get(normalize_language_code(language), language)


def normalize_language_code(language: str | None) -> str:
    """Normalize user-provided locale codes to the ones we ship."""
    if not language:
        return DEFAULT_LANGUAGE

    normalized = language.replace("-", "_")
    if normalized in SUPPORTED_LANGUAGES:
        return normalized

    # Allow matching on just the language part if someone stored "en" etc.
    for supported in SUPPORTED_LANGUAGES:
        if supported.split("_")[0] == normalized:
            return supported
    return DEFAULT_LANGUAGE


def install_translators(app: QApplication, language: str | None) -> None:
    """Install both application and Qt translators for the requested language."""
    locale = QLocale(normalize_language_code(language))
    translators: list[QTranslator] = []

    app_translator = _load_app_translator(app, locale)
    if app_translator is not None:
        translators.append(app_translator)

    translators.extend(_load_qt_translators(app, locale))

    # Keep translators referenced on the application instance to avoid GC.
    if translators:
        app._installed_translators = translators  # type: ignore[attr-defined]


def _load_app_translator(app: QApplication, locale: QLocale) -> QTranslator | None:
    """Load the media manager translation for the given locale if available."""
    for path in _iter_translation_search_paths():
        translator = QTranslator(app)
        if translator.load(
            locale,
            TRANSLATION_BASENAME,
            "_",
            str(path),
        ):
            app.installTranslator(translator)
            return translator
    return None


def _load_qt_translators(app: QApplication, locale: QLocale) -> list[QTranslator]:
    """Load Qt base translations for the locale (qtbase/qt)."""
    translators: list[QTranslator] = []
    prefixes = ("qtbase", "qt")
    for prefix in prefixes:
        translator = QTranslator(app)
        if translator.load(f"{prefix}_{locale.name()}", _qt_translations_path()):
            app.installTranslator(translator)
            translators.append(translator)
    return translators


def _iter_translation_search_paths() -> Iterator[Path]:
    """Yield candidate directories that may contain compiled QM files."""
    candidates: list[Path] = []
    if hasattr(sys, "_MEIPASS"):
        meipass_base = Path(sys._MEIPASS)
        candidates.append(meipass_base / "resources" / "i18n")
    package_dir = Path(__file__).resolve().parent
    candidates.append(package_dir / "resources" / "i18n")

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate.exists() and candidate not in seen:
            seen.add(candidate)
            yield candidate


def _qt_translations_path() -> str:
    """Return the path that contains Qt translation files."""
    if hasattr(sys, "_MEIPASS"):
        meipass_base = Path(sys._MEIPASS)
        bundled = meipass_base / "PySide6" / "translations"
        if bundled.exists():
            return str(bundled)
    return QLibraryInfo.location(QLibraryInfo.LibraryPath.TranslationsPath)


__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "get_language_choices",
    "install_translators",
    "language_label",
    "normalize_language_code",
]
