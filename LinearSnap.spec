# -*- mode: python ; coding: utf-8 -*-


import os
import platform

_system = platform.system()
_binaries = []
_icon = None


def _add_tree(src_root, dest_root, out):
    for root, _, files in os.walk(src_root):
        rel_dir = os.path.relpath(root, src_root)
        target_dir = dest_root if rel_dir == '.' else os.path.join(dest_root, rel_dir)
        for name in files:
            out.append((os.path.join(root, name), target_dir))

if _system == 'Darwin':
    _framework_root = os.path.join(
        SPECPATH,
        'canon-sdk', 'mac', 'EDSDK', 'Framework', 'EDSDK.framework',
    )
    _add_tree(_framework_root, 'EDSDK.framework', _binaries)
    _icon = ['icon.icns']
elif _system == 'Windows':
    _dll_dir = os.path.join(SPECPATH, 'canon-sdk', 'windows', 'EDSDK_64', 'Dll')
    _binaries.append((os.path.join(_dll_dir, 'EDSDK.dll'), '.'))
    _binaries.append((os.path.join(_dll_dir, 'EdsImage.dll'), '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=_binaries,
    datas=[],
    hiddenimports=[],
    # edsdk.py is in the root; PyInstaller picks it up automatically
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
    name='LinearSnap',
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
    name='LinearSnap',
)
if _system == 'Darwin':
    app = BUNDLE(
        coll,
        name='LinearSnap.app',
        icon='icon.icns',
        bundle_identifier=None,
    )
