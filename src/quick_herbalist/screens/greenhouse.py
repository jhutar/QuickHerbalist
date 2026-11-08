"""Greenhouse showcase screen (placeholder for the future greenhouse system)."""

from quick_herbalist.localization import _
from quick_herbalist.screens.base import KeyboardScreen, load_screen_kv


class GreenhouseScreen(KeyboardScreen):
    """Screen for greenhouse showcase (placeholder)."""

    def on_pre_enter(self):
        """Initialize greenhouse screen UI."""
        self.ids.title.text = _("Greenhouse")
        self.ids.desc.text = _("Placeholder Screen: Future greenhouse system will be here!")
        self.ids.back_btn.text = _("Back to Game Menu")

    def on_back(self):
        """Return to game menu hub when leaving the greenhouse screen."""
        self.manager.current = "game_menu"


load_screen_kv("greenhouse.kv")
