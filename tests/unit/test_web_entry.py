"""Tests for the web (Emscripten/pyodide) entry point, mocked without a browser."""

import json
import os
import sys
from unittest import mock

import pytest

from quick_herbalist import profiles, web_entry


class _JsNull:
    """Stand-in for pyodide.ffi.JsNull (the localStorage null sentinel)."""


@pytest.fixture
def web_env(tmp_path, monkeypatch):
    """Install fake js/pyodide modules, point DATA_DIR at tmp_path.

    Returns (localStorage store dict, tmp_path). The localStorage mock also
    exposes JsNull-flavored behavior: getItem returns None for missing keys
    here, which the production code accepts as well.
    """
    store = {}
    localStorage = mock.MagicMock()
    localStorage.getItem.side_effect = lambda key: store.get(key)
    localStorage.setItem.side_effect = lambda key, value: store.__setitem__(key, value)
    js_mod = mock.MagicMock(localStorage=localStorage)
    ffi_mod = mock.MagicMock(JsNull=_JsNull, to_js=lambda value: value)
    pyodide_mod = mock.MagicMock(ffi=ffi_mod)
    monkeypatch.setitem(sys.modules, "js", js_mod)
    monkeypatch.setitem(sys.modules, "pyodide", pyodide_mod)
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi_mod)

    monkeypatch.setattr(web_entry, "DATA_DIR", str(tmp_path))
    # prepare() monkeypatches ProfileManager; restore the originals on teardown
    monkeypatch.setattr(
        profiles.ProfileManager,
        "_resolve_config_dir",
        profiles.ProfileManager._resolve_config_dir,
    )
    monkeypatch.setattr(
        profiles.ProfileManager,
        "save_config",
        profiles.ProfileManager.save_config,
    )
    return store, tmp_path


def test_is_web_false_on_desktop():
    """is_web must report False outside Emscripten (this suite runs on desktop)."""
    if "emscripten" in sys.platform:  # pragma: no cover
        pytest.skip("running under Emscripten")
    assert web_entry.is_web() is False


def test_prepare_routes_saves_to_localstorage(web_env):
    store, tmp_path = web_env
    web_entry.prepare()

    pm = profiles.ProfileManager()
    assert pm.config_dir == str(tmp_path)
    pm.create_character("WebHero")

    assert web_entry.LOCALSTORAGE_KEY in store
    state = json.loads(store[web_entry.LOCALSTORAGE_KEY])
    assert "config.yaml" in state


def test_prepare_restores_saved_state(web_env):
    store, tmp_path = web_env
    web_entry.prepare()
    pm = profiles.ProfileManager()
    pm.create_character("WebHero")
    # simulate a page reload: FS wiped, localStorage intact
    os.remove(pm.config_path)
    web_entry.prepare()

    pm2 = profiles.ProfileManager()
    assert pm2.active_character_name == "WebHero"


def test_prepare_without_previous_save(web_env):
    store, tmp_path = web_env
    web_entry.prepare()  # localStorage empty -> no restore, no crash
    assert not os.path.exists(os.path.join(str(tmp_path), "config.yaml"))
    pm = profiles.ProfileManager()
    assert pm.active_character_name is None
