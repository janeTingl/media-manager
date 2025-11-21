"""简体中文界面支持。

本模块为媒体管理器提供简体中文界面支持。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from media_manager.logging import get_logger

logger = get_logger().get_logger(__name__)

# 固定使用简体中文
DEFAULT_LANGUAGE = "zh_CN"
TRANSLATION_BASENAME = "media_manager"


def install_translators(app: QApplication, language: str | None = None) -> None:
    """安装简体中文翻译器。

    Args:
        app: Qt 应用程序实例
        language: 语言代码（忽略，始终使用简体中文）
    """
    # 固定使用简体中文
    lang = "zh_CN"
    logger.info("安装简体中文翻译器")
    logger.info(f"PyInstaller 模式: {hasattr(sys, '_MEIPASS')}")
    if hasattr(sys, "_MEIPASS"):
        logger.info(f"PyInstaller _MEIPASS 路径: {sys._MEIPASS}")

    locale = QLocale(lang)
    logger.info(f"QLocale 名称: {locale.name()}")
    translators: list[QTranslator] = []

    # 加载应用翻译
    app_translator = _load_app_translator(app, locale)
    if app_translator is not None:
        translators.append(app_translator)
        logger.info("应用翻译器加载成功")
    else:
        logger.warning("应用翻译器加载失败")

    # 加载 Qt 翻译
    qt_translators = _load_qt_translators(app, locale)
    translators.extend(qt_translators)
    logger.info(f"已加载 {len(qt_translators)} 个 Qt 翻译器")

    # 保持翻译器引用，避免被垃圾回收
    if translators:
        app._installed_translators = translators  # type: ignore[attr-defined]
        logger.info(f"共安装 {len(translators)} 个翻译器")
    else:
        logger.warning("未安装任何翻译器")


def _load_app_translator(app: QApplication, locale: QLocale) -> QTranslator | None:
    """加载应用翻译文件。"""
    logger.info(
        f"加载应用翻译: locale={locale.name()}, basename={TRANSLATION_BASENAME}"
    )

    search_paths = list(_iter_translation_search_paths())
    logger.info(f"翻译文件搜索路径: {search_paths}")

    for path in search_paths:
        logger.info(f"尝试从以下路径加载翻译: {path}")

        # 检查路径是否存在并列出内容
        if path.exists():
            qm_files = list(path.glob("*.qm"))
            logger.info(f"  路径存在。找到的 QM 文件: {[f.name for f in qm_files]}")
        else:
            logger.warning("  路径不存在!")
            continue

        translator = QTranslator(app)

        # 期望的文件名: media_manager_zh_CN.qm
        expected_filename = f"{TRANSLATION_BASENAME}_{locale.name()}.qm"
        logger.info(f"  查找文件: {expected_filename}")

        load_result = translator.load(
            locale,
            TRANSLATION_BASENAME,
            "_",
            str(path),
        )

        if load_result:
            logger.info(f"  ✓ 成功从 {path} 加载翻译")
            app.installTranslator(translator)
            return translator
        else:
            logger.warning(f"  ✗ 从 {path} 加载翻译失败")

    logger.error(f"无法从任何搜索路径加载 {locale.name()} 翻译文件")
    return None


def _load_qt_translators(app: QApplication, locale: QLocale) -> list[QTranslator]:
    """加载 Qt 基础翻译文件。"""
    qt_trans_path = _qt_translations_path()
    logger.info(f"从以下路径加载 Qt 翻译: {qt_trans_path}")

    translators: list[QTranslator] = []
    prefixes = ("qtbase", "qt")
    for prefix in prefixes:
        translator = QTranslator(app)
        filename = f"{prefix}_{locale.name()}"
        logger.info(f"  尝试加载 Qt 翻译: {filename}")

        if translator.load(filename, qt_trans_path):
            app.installTranslator(translator)
            translators.append(translator)
            logger.info(f"  ✓ 已加载 {filename}")
        else:
            logger.warning(f"  ✗ 加载 {filename} 失败")

    return translators


def _iter_translation_search_paths() -> Iterator[Path]:
    """迭代可能包含编译后 QM 文件的目录。"""
    candidates: list[Path] = []

    if hasattr(sys, "_MEIPASS"):
        meipass_base = Path(sys._MEIPASS)
        logger.info(f"检测到 PyInstaller 模式, _MEIPASS: {meipass_base}")
        candidates.append(meipass_base / "resources" / "i18n")
        logger.info(f"添加 PyInstaller 候选路径: {candidates[-1]}")

    package_dir = Path(__file__).resolve().parent
    package_path = package_dir / "resources" / "i18n"
    candidates.append(package_path)
    logger.info(f"添加包候选路径: {package_path}")

    seen: set[Path] = set()
    for candidate in candidates:
        logger.info(f"检查候选路径: {candidate}")
        logger.info(f"  存在: {candidate.exists()}")
        logger.info(f"  已检查过: {candidate in seen}")

        if candidate.exists() and candidate not in seen:
            seen.add(candidate)
            logger.info("  → 使用此路径")
            yield candidate
        else:
            logger.warning("  → 跳过此路径")


def _qt_translations_path() -> str:
    """返回包含 Qt 翻译文件的路径。"""
    if hasattr(sys, "_MEIPASS"):
        meipass_base = Path(sys._MEIPASS)
        bundled = meipass_base / "PySide6" / "translations"
        logger.info(f"检查打包的 Qt 翻译路径: {bundled}")
        logger.info(f"  存在: {bundled.exists()}")
        if bundled.exists():
            logger.info(f"使用打包的 Qt 翻译路径: {bundled}")
            return str(bundled)

    qt_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    logger.info(f"使用系统 Qt 翻译路径: {qt_path}")
    return qt_path


__all__ = [
    "DEFAULT_LANGUAGE",
    "install_translators",
]
