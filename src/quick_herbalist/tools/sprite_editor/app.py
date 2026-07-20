import os
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from quick_herbalist.tools.sprite_editor.ui.main_layout import SpriteEditorMainLayout
from quick_herbalist.core.config_parser import validate_configs


class SpriteEditorApp(App):
    def build(self):
        # Paths to configuration files
        self.yaml_path = os.path.join(
            "src", "quick_herbalist", "assets", "sprites.yaml"
        )
        self.atlas_path = os.path.join(
            "src", "quick_herbalist", "assets", "sprites.atlas"
        )

        # Check configuration integrity on startup
        self._check_config_integrity()

        return SpriteEditorMainLayout()

    def _check_config_integrity(self):
        # If files exist and are invalid, show a warning.
        if os.path.exists(self.yaml_path) and os.path.exists(self.atlas_path):
            if not validate_configs(self.yaml_path, self.atlas_path):
                self._show_error_popup()

    def _show_error_popup(self):
        content = BoxLayout(orientation="vertical", padding=10, spacing=10)
        label = Label(
            text="Configuration Error!\n\nInconsistency detected between\nsprites.yaml and sprites.atlas."
        )
        close_button = Button(text="Close", size_hint=(1, 0.3))

        content.add_widget(label)
        content.add_widget(close_button)

        popup = Popup(title="Validation Error", content=content, size_hint=(0.8, 0.4))

        close_button.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    SpriteEditorApp().run()
