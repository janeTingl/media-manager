# -*- mode: python ; coding: utf-8 -*-
# ruff: noqa

import os

project_root = os.path.dirname(os.path.abspath(__file__))
entry_script = 'src/media_manager/main.py'

block_cipher = None

a = Analysis(
    [entry_script],
    pathex=['.'],
    binaries=[],

    datas=[
        ('assets/*', 'assets'),
        ('config/*', 'config'),
    ],

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
