import sys
from unittest.mock import MagicMock


class RealWidget:
    def __init__(self, **kwargs):
        self.canvas = MagicMock()
        self.size = (100, 100)

    def add_widget(self, *args, **kwargs):
        pass


# Mocking kivy.uix.widget.Widget
import types  # noqa: E402

kivy_module = types.ModuleType("kivy")
kivy_ui_module = types.ModuleType("kivy.uix")
kivy_widget_module = types.ModuleType("kivy.uix.widget")
kivy_widget_module.Widget = RealWidget
kivy_ui_module.widget = kivy_widget_module
kivy_module.uix = kivy_ui_module
sys.modules["kivy"] = kivy_module
sys.modules["kivy.uix"] = kivy_ui_module
sys.modules["kivy.uix.widget"] = kivy_widget_module


class AnimatedSprite(RealWidget):
    def __init__(self, sprite_name, **kwargs):
        super().__init__(**kwargs)
        self.sprite_name = sprite_name


sprite = AnimatedSprite(sprite_name="hero_run")
print(f"sprite.sprite_name: {sprite.sprite_name}")
assert sprite.sprite_name == "hero_run"
