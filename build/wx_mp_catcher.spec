# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包 — 精简 Qt 依赖，输出 dist/wx-mp-catcher/."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

block_cipher = None
project_root = Path(SPECPATH).parent
src = project_root / "src"
assets = project_root / "assets"

# 仅收集 GUI 必需 Qt 组件，避免 700MB+ 安装包
pyside6_binaries = collect_dynamic_libs("PySide6")
pyside6_datas: list = []
for sub in (
    "plugins/platforms",
    "plugins/styles",
    "plugins/imageformats",
    "plugins/iconengines",
    "translations/qtbase",
):
    pyside6_datas += collect_data_files("PySide6", subdir=sub)

watchdog_hidden = collect_submodules("watchdog")

extra_datas = []
if (assets / "icon.ico").exists():
    extra_datas.append((str(assets / "icon.ico"), "assets"))

a = Analysis(
    [str(src / "wx_mp_catcher" / "__main__.py")],
    pathex=[str(src)],
    binaries=pyside6_binaries,
    datas=pyside6_datas + extra_datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        *watchdog_hidden,
        "watchdog.observers.winapi",
        "Crypto.Cipher.AES",
        "Crypto.Util.Padding",
        "pydantic",
        "pydantic_settings",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / "build" / "runtime_hook_qt.py")],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.Qt3D",
        "PySide6.QtCharts",
        "PySide6.QtMultimedia",
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
    name="wx-mp-catcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets / "icon.ico") if (assets / "icon.ico").exists() else None,
    version=str(project_root / "build" / "version_info.txt") if sys.platform == "win32" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="wx-mp-catcher",
)
