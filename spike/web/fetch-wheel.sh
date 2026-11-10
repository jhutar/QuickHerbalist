#!/bin/sh
# Fetch the kivy 3.0.0.dev0 WASM wheel (not committed: >1 MB file limit).
# Source: kivy-school/kivy-browser published site (same wheel their CI builds
# from psychowasp/kivy wasm-support with cibuildwheel + pyodide 0.29.5).
set -e
cd "$(dirname "$0")"
curl -fL -O "https://kivy-school.github.io/kivy-browser/wheels/97d713a6f350/kivy-3.0.0.dev0-cp313-cp313-pyemscripten_2025_0_wasm32.whl"
