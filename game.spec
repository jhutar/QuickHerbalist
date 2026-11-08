# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Quick Herbalist game: onefile, console, with assets and locales bundled."""

import os
import sys

# Per-OS names so Linux and macOS binaries do not collide in the release.
if sys.platform == "win32":
    NAME = "quick-herbalist-windows"
elif sys.platform == "darwin":
    NAME = "quick-herbalist-macos"
else:
    NAME = "quick-herbalist-linux"

SRC = os.path.join("src", "quick_herbalist")

# Data files copied into _MEIPASS next to the package layout so that
# quick_herbalist.localization.BASE_DIR (derived from __file__) resolves.
datas = [
    (os.path.join(SRC, "assets"), os.path.join("quick_herbalist", "assets")),
    (os.path.join(SRC, "locales"), os.path.join("quick_herbalist", "locales")),
    # Per-screen KV rule files loaded via __file__-relative paths in
    # quick_herbalist.screens.base.load_screen_kv (works frozen in _MEIPASS).
    (os.path.join(SRC, "screens", "kv"), os.path.join("quick_herbalist", "screens", "kv")),
]

a = Analysis(
    [os.path.join(SRC, "__main__.py")],
    pathex=["src"],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=NAME,
    debug=False,
    strip=False,
    upx=False,
    console=True,
)
