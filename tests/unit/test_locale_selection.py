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

    def test_config_en_wins_over_cs_env(self, monkeypatch):
        """Explicit en in config beats a Czech environment locale."""
        _set_env_locale(monkeypatch, "cs_CZ")
        assert localization.select_locale("en") == "en"

    def test_config_cs_wins_over_en_env(self, monkeypatch):
        """Explicit cs in config beats an English environment locale."""
        _set_env_locale(monkeypatch, "en_US")
        assert localization.select_locale("cs") == "cs"

    def test_system_with_cs_env(self, monkeypatch):
        """system follows a cs environment locale to cs."""
        _set_env_locale(monkeypatch, "cs_CZ")
        assert localization.select_locale("system") == "cs"

    def test_system_with_bare_cs_env(self, monkeypatch):
        """system with a bare 'cs' locale (no territory) resolves to cs."""
        _set_env_locale(monkeypatch, "cs")
        assert localization.select_locale("system") == "cs"

    def test_system_with_dashed_cs_env(self, monkeypatch):
        """system with a cs-CZ (dash-separated) locale resolves to cs."""
        _set_env_locale(monkeypatch, "cs-CZ")
        assert localization.select_locale("system") == "cs"

    def test_system_with_non_cs_env(self, monkeypatch):
        """system with a non-Czech environment locale falls back to en."""
        _set_env_locale(monkeypatch, "de_DE")
        assert localization.select_locale("system") == "en"

    def test_system_with_english_env(self, monkeypatch):
        """system with an English environment locale resolves to en."""
        _set_env_locale(monkeypatch, "en_US")
        assert localization.select_locale("system") == "en"

    def test_system_with_unset_env(self, monkeypatch):
        """system with no environment locale falls back to en."""
        _set_env_locale(monkeypatch, None)
        assert localization.select_locale("system") == "en"

    def test_system_with_unparseable_env(self, monkeypatch):
        """system with an unparseable environment locale falls back to en."""
        _set_unparseable_env(monkeypatch)
        assert localization.select_locale("system") == "en"

    def test_missing_key_behaves_as_system(self, monkeypatch):
        """None (missing config key) behaves exactly like system."""
        _set_env_locale(monkeypatch, "cs_CZ")
        assert localization.select_locale(None) == "cs"
        _set_env_locale(monkeypatch, "de_DE")
        assert localization.select_locale(None) == "en"

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
