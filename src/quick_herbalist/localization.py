"""Locale and asset path helpers, plus the gettext translation helper."""

import gettext
import locale
import os
import re

# --- Asset and locale path helpers ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

#: Locales shipped with the app; must match the locale dir names under locales/.
VALID_LOCALES = ("en", "cs")


def get_locales_dir():
    """Return absolute path to the locales directory."""
    return os.path.join(BASE_DIR, "locales")


def _system_locale():
    """Resolve the environment locale to a shipped locale.

    Returns "cs" only when the 2-letter language subtag is "cs"
    (covers cs, cs_CZ, cs-CZ, cs_CZ.UTF-8); anything else, empty, or
    unparseable returns "en".
    """
    try:
        loc, _ = locale.getlocale()
    except ValueError:
        loc = None
    if not loc:
        return "en"
    lang = re.split(r"[_.-]", loc)[0].lower()
    return "cs" if lang == "cs" else "en"


def select_locale(config_locale):
    """Pick the effective locale from the config value with environment fallback.

    "system" (or None for an unset config key) follows the environment locale;
    "en"/"cs" are used as-is. Any other config value raises ValueError.
    """
    if config_locale is None or config_locale == "system":
        return _system_locale()
    if config_locale not in VALID_LOCALES:
        raise ValueError(
            f"Invalid settings.locale {config_locale!r}; expected one of: en, cs, system"
        )
    return config_locale


# --- Localization initialization ---
gettext.bindtextdomain("base", get_locales_dir())
gettext.textdomain("base")

#: Active gettext catalog; swapped at startup by initialize_locale().
_catalog = gettext.translation("base", get_locales_dir(), ["en"])


def _(message):
    """Translate message through the currently active catalog."""
    return _catalog.gettext(message)


def initialize_locale(locale_name):
    """Switch the active catalog to locale_name ("en" or "cs")."""
    global _catalog
    _catalog = gettext.translation("base", get_locales_dir(), [locale_name])
