# -*- mode: python ; coding: utf-8 -*-
# ruff: noqa

import os
import glob
from PySide6.QtCore import QLibraryInfo

project_root = os.path.dirname(os.path.abspath(__file__))
entry_script = 'src/media_manager/main.py'

# ---- 获取 PySide6 中文翻译文件 ----
translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
qt_translation_files = glob.glob(os.path.join(translations_path, "*_zh_CN.qm"))

block_cipher = None

a = Analysis(
    [entry_script],
    pathex=['.'],
    binaries=[],

    datas=[
        ('assets/*', 'assets'),
        ('config/*', 'config'),
        ('src/media_manager/resources/i18n/media_manager_zh_CN.qm', 'resources/i18n'),
    ]
    +
    [(f, "PySide6/translations") for f in qt_translation_files],

    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name='MediaManager',  # 生成的 EXE 文件名，不要中文！！
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,

    icon='icon.ico',
)
