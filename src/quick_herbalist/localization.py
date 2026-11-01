"""Locale and asset path helpers, plus the gettext translation helper."""

import gettext
import os

# --- Asset and locale path helpers ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename):
    """Return absolute path to an asset file."""
    return os.path.join(BASE_DIR, "assets", filename)


def get_locales_dir():
    """Return absolute path to the locales directory."""
    return os.path.join(BASE_DIR, "locales")


# --- Localization initialization ---
gettext.bindtextdomain("base", get_locales_dir())
gettext.textdomain("base")
_ = gettext.gettext
