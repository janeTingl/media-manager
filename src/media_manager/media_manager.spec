# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PySide6.QtCore import QLibraryInfo

entry_script = 'src/media_manager/main.py'

# 获取 PySide6 翻译文件路径
translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)

a = Analysis(
    [entry_script],
    pathex=['.'],
    binaries=[],

    datas=[
        ('assets/*', 'assets'),
        ('config/*', 'config'),

        # 加入 Qt 中文翻译文件（关键）
        (translations_path + '/qtbase_zh_CN.qm', 'PySide6/translations'),
        (translations_path + '/qt_zh_CN.qm', 'PySide6/translations'),
    ],

    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# —— 单文件核心 —— #
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name='影藏·媒体管理器',
    console=False,         # GUI 程序必须 False
    icon=None,             # 若需要图标：icon='icon.ico'

    # 单文件关键参数
    exclude_binaries=True,
    strip=False,
    upx=False,
    runtime_tmpdir=None
)

# —— 单文件的其他内容统一放这 —— #
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='影藏·媒体管理器'
)
