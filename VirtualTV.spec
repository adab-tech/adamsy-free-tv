# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['tv_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('tv_channels.json', '.'),
        ('assets\\branding\\adamsy-free-tv.ico', 'assets\\branding'),
    ],
    hiddenimports=['tv_updater'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VirtualTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\branding\\adamsy-free-tv.ico',
    version='installer\\VirtualTV.version.txt',
)
