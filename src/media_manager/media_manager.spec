# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

entry_script = 'src/media_manager/main.py'

a = Analysis(
    [entry_script],
    pathex=['.'],
    binaries=[],

    # 如果有资源文件，请加入下面 datas 列表
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

# —— 单文件核心 —— #
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name='MediaManager',
    console=False,         # GUI 程序必须 False
    icon=None,             # 若需要图标：icon='icon.ico'

    # 单文件关键参数
    exclude_binaries=True,
    strip=False,
    upx=False,
    runtime_tmpdir=None    # 解压到系统临时目录（最稳定）
)

# —— 单文件的其他内容统一放这 —— #
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='MediaManager'
)
