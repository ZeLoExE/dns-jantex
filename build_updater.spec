# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Updater.exe

block_cipher = None

a = Analysis(
    ['updater.py'],
    pathex=[],
    binaries=[],
    datas=[('SIGNING_CERTIFICATE.txt', '.')],
    hiddenimports=['core', 'core.updater', 'core.elevated_client', 'core.helper_protocol', 'core.paths', 'core.storage', 'core.validation', 'core.powershell'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
