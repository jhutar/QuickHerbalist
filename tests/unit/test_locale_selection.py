"""Unit tests for locale selection (config > env > en) and catalog binding."""

import locale as pylocale

import pytest

from quick_herbalist import localization


def _set_env_locale(monkeypatch, loc, encoding="UTF-8"):
    """Make locale.getlocale() return (loc, encoding)."""
    monkeypatch.setattr(pylocale, "getlocale", lambda *args: (loc, encoding))


def _set_unparseable_env(monkeypatch):
    """Make locale.getlocale() raise ValueError, as with an unparseable env locale."""

    def raise_value_error(*args):
        raise ValueError("unsupported locale setting")

    monkeypatch.setattr(pylocale, "getlocale", raise_value_error)


@pytest.fixture
def restore_default_gettext():
    """Restore the module-level catalog after each test that rebinds it."""
    original = localization._catalog
    yield
    localization._catalog = original


class TestSelectLocale:
    """select_locale precedence and validation."""

    @pytest.mark.parametrize(
        ("config", "env", "expected"),
        [
            ("en", "cs_CZ", "en"),  # explicit en beats a Czech environment locale
            ("cs", "en_US", "cs"),  # explicit cs beats an English environment locale
            ("system", "cs_CZ", "cs"),  # system follows a cs environment locale
            ("system", "cs", "cs"),  # bare 'cs' (no territory)
            ("system", "cs-CZ", "cs"),  # dash-separated
            ("system", "de_DE", "en"),  # non-Czech environment falls back to en
            ("system", "en_US", "en"),  # English environment
            ("system", None, "en"),  # no environment locale
            (None, "cs_CZ", "cs"),  # missing config key behaves like system
            (None, "de_DE", "en"),
        ],
        ids=[
            "config_en_over_cs_env",
            "config_cs_over_en_env",
            "system_cs_env",
            "system_bare_cs_env",
            "system_dashed_cs_env",
            "system_non_cs_env",
            "system_english_env",
            "system_unset_env",
            "missing_key_cs_env",
            "missing_key_non_cs_env",
        ],
    )
    def test_select_locale_precedence(self, monkeypatch, config, env, expected):
        """Explicit config beats env; system/None follow env (cs-like -> cs, else en)."""
        _set_env_locale(monkeypatch, env)
        assert localization.select_locale(config) == expected

    def test_system_with_unparseable_env(self, monkeypatch):
        """system with an unparseable environment locale falls back to en."""
        _set_unparseable_env(monkeypatch)
        assert localization.select_locale("system") == "en"

    @pytest.mark.parametrize("bad_value", ["cz", "fr", "EN", 123, ["cs"]])
    def test_invalid_config_value_raises(self, bad_value):
        """Unknown or non-string config values raise ValueError (fail fast)."""
        with pytest.raises(ValueError, match="Invalid settings.locale"):
            localization.select_locale(bad_value)


class TestInitializeLocale:
    """initialize_locale binds _ to the requested compiled catalog."""

    def test_cs_catalog_selected(self, restore_default_gettext):
        """After init with cs, _ returns Czech translations."""
        localization.initialize_locale("cs")
        assert localization._("Brewed: ") == "Vymícháno: "

    def test_en_catalog_selected(self, restore_default_gettext):
        """After init with en, _ returns English translations."""
        localization.initialize_locale("en")
        assert localization._("Brewed: ") == "Brewed: "

    def test_switch_catalog_at_startup(self, restore_default_gettext):
        """Selecting cs and initializing switches _ from English to Czech."""
        localization.initialize_locale("en")
        assert localization._("Brewed: ") == "Brewed: "
        localization.initialize_locale("cs")
        assert localization._("Brewed: ") == "Vymícháno: "
