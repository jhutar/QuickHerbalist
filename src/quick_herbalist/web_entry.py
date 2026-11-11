"""Web (Emscripten/pyodide) entry point for QuickHerbalist.

Imported only by the web bundle loader (web/main.js); the desktop entry
point remains quick_herbalist.app.main(). This module is never imported
from app code, so its browser-only logic cannot affect the desktop build.

Saves live in browser localStorage: on startup the saved state is restored
into the Emscripten virtual FS (DATA_DIR), and after every ProfileManager
save the directory is serialized back to localStorage, so per-browser
profile data survives page reloads. (The pyodide build does not include
Emscripten IDBFS, so fs.syncfs is not an option.)
"""

import base64
import json
import os
import sys

DATA_DIR = "/idb"
LOCALSTORAGE_KEY = "quick_herbalist_save"


def is_web() -> bool:
    """Return True when running under Emscripten (pyodide)."""
    return "emscripten" in sys.platform


def _load_state() -> None:
    """Restore previously saved DATA_DIR files from localStorage into the FS."""
    from js import localStorage
    from pyodide.ffi import JsNull

    raw = localStorage.getItem(LOCALSTORAGE_KEY)
    if raw is None or isinstance(raw, JsNull):
        return
    for name, encoded in json.loads(str(raw)).items():
        with open(os.path.join(DATA_DIR, name), "wb") as f:
            f.write(base64.b64decode(encoded))


def _save_state() -> None:
    """Serialize DATA_DIR files to localStorage as base64 JSON."""
    from js import localStorage
    from pyodide.ffi import to_js

    state = {}
    for name in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, name)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                state[name] = base64.b64encode(f.read()).decode("ascii")
    localStorage.setItem(LOCALSTORAGE_KEY, to_js(json.dumps(state)))


def prepare() -> None:
    """Prepare the save directory and route ProfileManager saves through it."""
    os.makedirs(DATA_DIR, exist_ok=True)
    _load_state()

    from quick_herbalist import profiles

    def _resolve_config_dir(self, explicit_dir):
        """Use the web data dir so profile saves persist per browser."""
        return explicit_dir or DATA_DIR

    original_save = profiles.ProfileManager.save_config

    def _save_persisted(self):
        """Persist config.yaml, then write it through to localStorage."""
        original_save(self)
        _save_state()

    profiles.ProfileManager._resolve_config_dir = _resolve_config_dir
    profiles.ProfileManager.save_config = _save_persisted


def main() -> None:
    """Bootstrap web storage, then run the game."""
    prepare()
    from quick_herbalist.app import QuickHerbalistApp

    QuickHerbalistApp().run()
