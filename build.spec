# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for DNS Changer

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('translations/*.json', 'translations'),
        ('assets/*', 'assets'),
        ('assets/icons/*', 'assets/icons'),
    ],
    hiddenimports=['ui', 'ui.main_window', 'ui.components', 'ui.styles', 'ui.custom_dns_dialog', 'ui.animations', 'core', 'core.dns_manager', 'core.network_adapter', 'core.dns_providers', 'core.custom_dns', 'core.powershell', 'psutil'],
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
    [],
    exclude_binaries=True,
    name='DNSChanger',
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

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DNSChanger',
)
