# Phase 0 spike findings (issue #10)

Verdict: **gate PASSED.** A minimal Kivy app (window + one sprite + one .kv +
keyboard handler) runs in a real (headless Chromium, WebGL2) browser. Clock
loop, .kv loading, and `Window.request_keyboard` focus all verified.

## What works

- .kv layout loads and renders (`Builder.load_file` with a root rule class)
- `Clock.schedule_interval` game loop ticks (verified via throttled log)
- `Window.request_keyboard` + `on_key_down` delivers keypresses (a, space)
- PNG sprite loads from a file written into the Emscripten FS and renders
  (verified by pixel count in screenshots)

Verification: `probe_playground.mjs` (public kivy-browser playground) and
`probe_bundle.mjs` (local static bundle in `web/`). Both print
`PASS` for every assertion. Screenshots: `screenshot.png`,
`screenshot-bundle.png`.

## Toolchain — this is NOT the `kivy[webgl]` 2.3 + emcc story

The old official kivy 2.3 pure-Emscripten WASM demo repo is gone
(`kivy/kivy-wasm` 404s), and no maintained reference exists for compiling
kivy 2.3 to wasm. The only maintained web path found is:

- **Kivy 3.0.0.dev0** from `psychowasp/kivy` branch `wasm-support`
- window = **SDL3 + WebGL2** (`kivy/core/window/_window_sdl3.pyx`,
  `_emscripten.pyx`), image/clipboard backends are `img_sdl3`/`clipboard_sdl3`
- **Pyodide 0.29.5** runtime (cp313, `pyemscripten_2025_0_wasm32` wheels)
- wheel built via `cibuildwheel --only cp313-pyodide_wasm32`
  (**docker required** — not available on this machine, so the spike reuses
  the wheel published by `kivy-school/kivy-browser`, fetched in
  `web/fetch-wheel.sh`)
- SDL3 + satellites + ThorVG cross-compiled for wasm by
  `tools/build_emscripten_dependencies.sh` (`pyodide xbuildenv`, no docker)

## Bundle size / load time (spike, CDN-cached browser, cold start)

| item | size |
|---|---|
| kivy 3.0.0.dev0 wasm wheel | 4.3 MB |
| pyodide core (asm.wasm + stdlib zip) | ~5.0 MB |
| full local bundle transfer | ~11.8 MB |
| page load to "app started" | ~4.5 s (local server, CDN pyodide) |
| full probe run (incl. keypress checks) | ~8 s |

## Kivy 2.3 -> 3.0 API gaps hit by the spike (Phase 1 risk list)

Removed/changed in Kivy 3 (spike had to work around each):

- `Widget.find_class` — gone, use kv `ids` (game code: no usages found)
- `Keyboard.show()` — gone (game code: not used; `request_keyboard` only)
- `Image` core class — constructor no longer loads; `Image(path).size`
  triggers load; `.blit` gone (game code: no usages found)
- App-named kv root rules — no longer auto-resolved; use
  `Builder.load_file` + explicit root class (game code: all screens are
  classes, check their kv root rules in Phase 1)

Game code grep: only `Window.request_keyboard` (`screens/base.py`) and
standard widgets — no direct hits on removed APIs.

## Local standalone bundle (web/)

Static: `index.html` + `main.js` + kivy wheel; pyodide from CDN.
Run: `sh web/fetch-wheel.sh && python3 -m http.server 8321` then open
`http://127.0.0.1:8321/web/`. Probe: `node probe_bundle.mjs`.

Known quirk: writing into absolute paths under `/home/pyodide` fails with
ENOENT in this pyodide build; relative paths from cwd work.

## Phase 1 decisions forced by these findings

1. Web build targets **Kivy 3**, desktop stays Kivy 2.3 — app code must be
   compatible with both (or conditional per-platform), `pyproject.toml`
   `kivy[base]>=2.3.0` unaffected.
2. CI web job needs **docker** (cibuildwheel pyodide platform) or reuse of
   the published wheel; GH runners have docker, so building our own wheel
   from `psychowasp/kivy@wasm-support` is feasible.
3. Local web build without docker: reuse published wheel (as spike does)
   or document docker requirement.
