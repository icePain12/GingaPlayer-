# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['musicplayer.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('sources/img/black_bg.png', 'sources/img')
    ],
    hiddenimports=[
        'pygame._sdl2.audio',
        'readchar',
        'rich',
        'opacidad_temporal',
        'textwrap',
        'pygame'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    collect_all=['readchar']
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GingaPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    #icon='icon.ico'  # Optional: add if you have an icon file
)