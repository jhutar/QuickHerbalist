# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Quick Herbalist game: onefile, console, with assets and locales bundled."""

import os

SRC = os.path.join("src", "quick_herbalist")

# Data files copied into _MEIPASS next to the package layout so that
# quick_herbalist.localization.BASE_DIR (derived from __file__) resolves.
datas = [
    (os.path.join(SRC, "assets"), os.path.join("quick_herbalist", "assets")),
    (os.path.join(SRC, "locales"), os.path.join("quick_herbalist", "locales")),
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
    name="quick-herbalist",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)
