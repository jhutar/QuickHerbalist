"""Base screen class with keyboard support, shared by all menu/flow screens."""

import os

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

# Directory holding the per-screen KV rule files.
KV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kv")


def load_screen_kv(filename):
    """Load a screen's KV rule file from the package's kv directory."""
    Builder.load_file(os.path.join(KV_DIR, filename))


class KeyboardScreen(Screen):
    """Base screen class with keyboard support."""

    def on_enter(self):
        """Handle screen entry and request keyboard."""
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def on_leave(self):
        """Handle screen exit and unbind keyboard."""
        if self._keyboard:
            self._keyboard.unbind(
                on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
            )
            self._keyboard = None

    def _keyboard_closed(self):
        """Callback when keyboard is closed."""
        self._keyboard = None

    def on_back(self):
        """Default back behaviour: return to the main menu."""
        self.manager.current = "menu"

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle escape/q as back; return True when the key was handled."""
        if keycode[1] in ("escape", "q"):
            self.on_back()
            return True
        return False

    def _on_keyboard_up(self, keyboard, keycode):
        """Handle key up event."""
        return False
