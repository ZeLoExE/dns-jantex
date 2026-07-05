# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for DNS Changer

import os

block_cipher = None

# Collect assets but exclude exe files and large unnecessary items
asset_datas = []
asset_dir = 'assets'
for f in os.listdir(asset_dir):
    if f.lower().endswith(('.exe', '.msi')):
        continue  # skip executables
    asset_datas.append((os.path.join(asset_dir, f), 'assets'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('translations/*.json', 'translations'),
    ] + asset_datas,
    hiddenimports=['ui', 'ui.main_window', 'ui.components', 'ui.styles', 'ui.custom_dns_dialog', 'ui.animations', 'core', 'core.dns_manager', 'core.network_adapter', 'core.dns_providers', 'core.custom_dns', 'core.powershell', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.QtOpenGL',
        'PySide6.Qt3D',
        'PySide6.QtDataVisualization',
        'PySide6.QtPdf',
        'PySide6.QtMultimedia',
        'PySide6.QtWebEngine',
        'PySide6.QtWebChannel',
        'PySide6.QtPositioning',
        'PySide6.QtLocation',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtNfc',
        'PySide6.QtBluetooth',
        'PySide6.QtRemoteObjects',
        'PySide6.QtTextToSpeech',
        'opengl32sw.dll',
    ],
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
    console=False,  # No console window
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
