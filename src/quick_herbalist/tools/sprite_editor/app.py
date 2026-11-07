import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from quick_herbalist.core.config_parser import get_asset_path
from quick_herbalist.core.sprite_config import SpriteConfig
from quick_herbalist.tools.sprite_editor.ui.main_layout import SpriteEditorMainLayout


class SpriteEditorApp(App):
    """Main Kivy application for the sprite editor tool."""

    def build(self):
        """Initialize the app, resolve asset paths, validate configs, and return the main layout."""
        # Use get_asset_path for finding configurations robustly by convention
        self.yaml_path = get_asset_path("sprites.yaml")
        self.atlas_path = get_asset_path("sprites.atlas")

        # Check configuration integrity on startup
        self._check_config_integrity()

        return SpriteEditorMainLayout()

    def _check_config_integrity(self):
        """Validate sprites.yaml and sprites.atlas consistency; show error popup on mismatch."""
        # If files exist and are invalid, show a warning.
        if os.path.exists(self.yaml_path) and os.path.exists(self.atlas_path):
            if not SpriteConfig.validate(self.yaml_path, self.atlas_path):
                self._show_error_popup()

    def _show_error_popup(self):
        """Display a Kivy popup informing the user of config inconsistencies."""
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        label = Label(
            text=(
                "Configuration Error!\n\n"
                "Inconsistency detected between\nsprites.yaml and sprites.atlas."
            )
        )
        close_button = Button(text="Close", size_hint=(1, 0.3))

        content.add_widget(label)
        content.add_widget(close_button)

        popup = Popup(title="Validation Error", content=content, size_hint=(0.8, 0.4))

        close_button.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    SpriteEditorApp().run()
