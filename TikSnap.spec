# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None
base = os.path.abspath('.')

datas = [
    (os.path.join(base, 'templates'), 'templates'),
    (os.path.join(base, 'tiksnap.ico'), '.'),
]

# yt-dlp extractors / flask templates
hiddenimports = [
    'yt_dlp',
    'flask',
    'jinja2',
    'werkzeug',
    'webview',
    'clr_loader',
    'pythonnet',
]
hiddenimports += collect_submodules('yt_dlp')

tmp_ret = collect_all('yt_dlp')
datas += tmp_ret[0]
binaries = list(tmp_ret[1])
hiddenimports += tmp_ret[2]

tmp_ret = collect_all('webview')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['desktop_app.py'],
    pathex=[base],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='TikSnap',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # không hiện cửa sổ đen
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(base, 'tiksnap.ico'),
)
