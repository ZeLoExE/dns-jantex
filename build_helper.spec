# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['helper.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['core', 'core.dns_manager', 'core.network_adapter', 'core.powershell'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6'],
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
    name='DNSHelper',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=True,
    icon='assets/icon.ico',
)
