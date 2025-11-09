# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Media Manager v0.1.0

This spec file builds a single-file Windows executable for the Media Manager application.
Build with: pyinstaller media-manager.spec
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/media_manager/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'media_manager',
        'media_manager.main',
        'media_manager.main_window',
        'media_manager.match_manager',
        'media_manager.models',
        'media_manager.scanner',
        'media_manager.scan_engine',
        'media_manager.workers',
        'media_manager.settings',
        'media_manager.logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='media-manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)