# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['test_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['flask'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    cipher=None,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='TestApp', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=True, icon=None
)
