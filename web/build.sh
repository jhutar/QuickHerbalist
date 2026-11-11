#!/bin/sh
# Build the static web bundle into web/dist/ (GitHub Pages deployable).
# Fetches the Kivy WASM wheel + pyodide runtime, builds the app wheel, and
# combines them with index.html/main.js. Run from anywhere.
set -eu
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"

PYODIDE_VERSION="0.29.5"  # cp313 line; matches the kivy WASM wheel (314.x is py3.14)
# Kivy 3.0.0.dev0 WASM wheel, built by kivy-school CI from psychowasp/kivy
# branch "wasm-support" (see spike/FINDINGS.md). Pinned by build commit.
KIVY_WHEEL_URL="https://kivy-school.github.io/kivy-browser/wheels/97d713a6f350/kivy-3.0.0.dev0-cp313-cp313-pyemscripten_2025_0_wasm32.whl"
KIVY_WHEEL="kivy-3.0.0.dev0-cp313-cp313-pyemscripten_2025_0_wasm32.whl"
PYODIDE_BASE="https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full"
# pyodide C build of the app's only third-party dependency
PYYAML_WHEEL="pyyaml-6.0.2-cp313-cp313-pyemscripten_2025_0_wasm32.whl"
# pure-python dep kivy.core.image imports (not in the pyodide index)
FILETYPE_WHEEL="filetype-1.2.0-py2.py3-none-any.whl"
FILETYPE_WHEEL_URL="https://files.pythonhosted.org/packages/18/79/1b8fa1bb3568781e84c9200f951c735f3f157429f44be0495da55894d620/${FILETYPE_WHEEL}"

rm -rf dist
mkdir -p dist dist/pyodide

curl -fL -o "dist/$KIVY_WHEEL" "$KIVY_WHEEL_URL"
curl -fsSL -o "dist/$PYYAML_WHEEL" "$PYODIDE_BASE/$PYYAML_WHEEL"
curl -fsSL -o "dist/$FILETYPE_WHEEL" "$FILETYPE_WHEEL_URL"

uv build --wheel -o dist "$ROOT"
APP_WHEEL="$(basename "$(ls dist/quick_herbalist-*.whl | head -1)")"
echo "$APP_WHEEL" > dist/app-wheel.txt

# Minimal pyodide runtime set (no full distribution zip needed):
# loader, wasm binary, stdlib, and the PEP 658 lockfile.
for f in pyodide.js pyodide.asm.js pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
  curl -fsSL -o "dist/pyodide/$f" "$PYODIDE_BASE/$f"
done

cp index.html main.js dist/

echo "Web bundle ready in $(pwd)/dist"
