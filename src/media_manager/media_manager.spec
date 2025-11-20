# ruff: noqa

block_cipher = None

from PySide6.QtCore import QLibraryInfo

entry_script = 'src/media_manager/main.py'

# 获取 PySide6 翻译文件路径
translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)

a = Analysis(
    [entry_script],
    pathex=['.'],
    binaries=[],

    datas=[
        ('assets/*', 'assets'),
        ('config/*', 'config'),
        ('src/media_manager/resources/i18n/*.qm', 'resources/i18n'),

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
    debug=False,           # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,         # GUI 程序必须 False
    icon=None,             # 若需要图标：icon='icon.ico'
    disable_windowed_traceback=False,
)
