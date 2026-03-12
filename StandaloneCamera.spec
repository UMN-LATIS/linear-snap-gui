# -*- mode: python ; coding: utf-8 -*-


import os
import platform

_system = platform.system()
_binaries = []
_icon = None

if _system == 'Darwin':
    _edsdk_src = os.path.join(
        SPECPATH,
        'canon-sdk', 'mac', 'EDSDK', 'Framework', 'EDSDK.framework', 'Versions', 'A', 'EDSDK',
    )
    _binaries.append((_edsdk_src, 'EDSDK.framework/Versions/A'))
    _icon = ['icon.icns']
elif _system == 'Windows':
    _dll_dir = os.path.join(SPECPATH, 'canon-sdk', 'windows', 'EDSDK_64', 'Dll')
    _binaries.append((os.path.join(_dll_dir, 'EDSDK.dll'), '.'))
    _binaries.append((os.path.join(_dll_dir, 'EdsImage.dll'), '.'))

a = Analysis(
    ['standalone_camera_app.py'],
    pathex=[],
    binaries=_binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StandaloneCamera',
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
    icon=_icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StandaloneCamera',
)

if _system == 'Darwin':
    app = BUNDLE(
        coll,
        name='StandaloneCamera.app',
        icon='icon.icns',
        bundle_identifier=None,
    )
