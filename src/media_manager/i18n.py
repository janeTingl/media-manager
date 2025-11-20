"""Internationalization helpers for the media manager UI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Sequence

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from media_manager.logging import get_logger

logger = get_logger().get_logger(__name__)

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
    normalized_lang = normalize_language_code(language)
    logger.info(
        f"Installing translators for language: {language} (normalized: {normalized_lang})"
    )
    logger.info(f"Running in PyInstaller mode: {hasattr(sys, '_MEIPASS')}")
    if hasattr(sys, "_MEIPASS"):
        logger.info(f"PyInstaller _MEIPASS path: {sys._MEIPASS}")

    locale = QLocale(normalized_lang)
    logger.info(f"QLocale name: {locale.name()}")
    translators: list[QTranslator] = []

    app_translator = _load_app_translator(app, locale)
    if app_translator is not None:
        translators.append(app_translator)
        logger.info("Application translator loaded successfully")
    else:
        logger.warning("Failed to load application translator")

    qt_translators = _load_qt_translators(app, locale)
    translators.extend(qt_translators)
    logger.info(f"Loaded {len(qt_translators)} Qt translators")

    # Keep translators referenced on the application instance to avoid GC.
    if translators:
        app._installed_translators = translators  # type: ignore[attr-defined]
        logger.info(f"Total {len(translators)} translators installed")
    else:
        logger.warning("No translators were installed")


def _load_app_translator(app: QApplication, locale: QLocale) -> QTranslator | None:
    """Load the media manager translation for the given locale if available."""
    logger.info(
        f"Loading app translator for locale: {locale.name()}, basename: {TRANSLATION_BASENAME}"
    )

    search_paths = list(_iter_translation_search_paths())
    logger.info(f"Translation search paths: {search_paths}")

    for path in search_paths:
        logger.info(f"Trying to load translation from: {path}")

        # Check if path exists and list its contents
        if path.exists():
            qm_files = list(path.glob("*.qm"))
            logger.info(f"  Path exists. QM files found: {[f.name for f in qm_files]}")
        else:
            logger.warning("  Path does not exist!")
            continue

        translator = QTranslator(app)

        # Expected filename pattern: media_manager_zh_CN.qm
        expected_filename = f"{TRANSLATION_BASENAME}_{locale.name()}.qm"
        logger.info(f"  Looking for file: {expected_filename}")

        load_result = translator.load(
            locale,
            TRANSLATION_BASENAME,
            "_",
            str(path),
        )

        if load_result:
            logger.info(f"  ✓ Successfully loaded translator from {path}")
            app.installTranslator(translator)
            return translator
        else:
            logger.warning(f"  ✗ Failed to load translator from {path}")

    logger.error(
        f"Could not load translation for locale {locale.name()} from any search path"
    )
    return None


def _load_qt_translators(app: QApplication, locale: QLocale) -> list[QTranslator]:
    """Load Qt base translations for the locale (qtbase/qt)."""
    qt_trans_path = _qt_translations_path()
    logger.info(f"Loading Qt translators from: {qt_trans_path}")

    translators: list[QTranslator] = []
    prefixes = ("qtbase", "qt")
    for prefix in prefixes:
        translator = QTranslator(app)
        filename = f"{prefix}_{locale.name()}"
        logger.info(f"  Trying to load Qt translator: {filename}")

        if translator.load(filename, qt_trans_path):
            app.installTranslator(translator)
            translators.append(translator)
            logger.info(f"  ✓ Loaded {filename}")
        else:
            logger.warning(f"  ✗ Failed to load {filename}")

    return translators


def _iter_translation_search_paths() -> Iterator[Path]:
    """Yield candidate directories that may contain compiled QM files."""
    candidates: list[Path] = []

    if hasattr(sys, "_MEIPASS"):
        meipass_base = Path(sys._MEIPASS)
        logger.info(f"PyInstaller mode detected, _MEIPASS: {meipass_base}")
        candidates.append(meipass_base / "resources" / "i18n")
        logger.info(f"Added PyInstaller candidate path: {candidates[-1]}")

    package_dir = Path(__file__).resolve().parent
    package_path = package_dir / "resources" / "i18n"
    candidates.append(package_path)
    logger.info(f"Added package candidate path: {package_path}")

    seen: set[Path] = set()
    for candidate in candidates:
        logger.info(f"Checking candidate path: {candidate}")
        logger.info(f"  Exists: {candidate.exists()}")
        logger.info(f"  Already seen: {candidate in seen}")

        if candidate.exists() and candidate not in seen:
            seen.add(candidate)
            logger.info("  → Yielding this path")
            yield candidate
        else:
            logger.warning("  → Skipping this path")


def _qt_translations_path() -> str:
    """Return the path that contains Qt translation files."""
    if hasattr(sys, "_MEIPASS"):
        meipass_base = Path(sys._MEIPASS)
        bundled = meipass_base / "PySide6" / "translations"
        logger.info(f"Checking for bundled Qt translations at: {bundled}")
        logger.info(f"  Exists: {bundled.exists()}")
        if bundled.exists():
            logger.info(f"Using bundled Qt translations path: {bundled}")
            return str(bundled)

    qt_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    logger.info(f"Using system Qt translations path: {qt_path}")
    return qt_path


__all__ = [
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "get_language_choices",
    "install_translators",
    "language_label",
    "normalize_language_code",
]
