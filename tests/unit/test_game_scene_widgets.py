"""Regression tests for Flower/Stone construction in game_scene.

Verifies the MovingWidget signature: subclasses must forward
sprite_manager as the first positional argument (regression from
commit 25a399b, which added sprite_manager to Flower/Stone without
updating their super().__init__ calls, crashing on first spawn).
"""

import sys
import types
from unittest.mock import MagicMock

# Setup mocks for Kivy BEFORE importing anything that uses it
kivy_module = types.ModuleType("kivy")
kivy_app_module = types.ModuleType("kivy.app")
kivy_uix_module = types.ModuleType("kivy.uix")
kivy_widget_module = types.ModuleType("kivy.uix.widget")
kivy_label_module = types.ModuleType("kivy.uix.label")
kivy_clock_module = types.ModuleType("kivy.clock")
kivy_graphics_module = types.ModuleType("kivy.graphics")


# Define a real class for Widget to allow inheritance
class RealWidget:
    def __init__(self, **kwargs):
        self.size = (100, 100)
        self.pos = (0, 0)

    def add_widget(self, *args, **kwargs):
        pass

    def bind(self, *args, **kwargs):
        pass


kivy_widget_module.Widget = RealWidget
kivy_uix_module.widget = kivy_widget_module
kivy_uix_module.label = kivy_label_module
kivy_module.uix = kivy_uix_module
kivy_module.app = kivy_app_module
kivy_module.clock = kivy_clock_module
kivy_module.graphics = kivy_graphics_module

sys.modules["kivy"] = kivy_module
sys.modules["kivy.app"] = kivy_app_module
sys.modules["kivy.uix"] = kivy_uix_module
sys.modules["kivy.uix.widget"] = kivy_widget_module
sys.modules["kivy.uix.label"] = kivy_label_module
sys.modules["kivy.clock"] = kivy_clock_module
sys.modules["kivy.graphics"] = kivy_graphics_module

kivy_app_module.App = MagicMock()
kivy_clock_module.Clock = MagicMock()
kivy_graphics_module.Rectangle = MagicMock()
kivy_label_module.Label = MagicMock()

# Import the code under test
from quick_herbalist.game_scene import SCREEN_H, SCREEN_W, Flower, Stone  # noqa: E402


def _make_sprite_manager():
    sprite_manager = MagicMock()
    sprite_manager.get.return_value = MagicMock()
    return sprite_manager


def test_flower_forwards_sprite_manager_and_sprite_name():
    """Flower must pass sprite_manager through to MovingWidget unchanged."""
    sprite_manager = _make_sprite_manager()

    flower = Flower(sprite_manager)

    sprite_manager.get.assert_called_once_with("flower_sprite")
    assert flower.sprite is sprite_manager.get.return_value
    assert flower.size == (32, 32)
    assert flower.pos[0] >= SCREEN_W + 50
    assert flower.pos[0] <= SCREEN_W + 200
    assert 0 <= flower.pos[1] <= SCREEN_H - 32


def test_stone_forwards_sprite_manager_and_sprite_name():
    """Stone must pass sprite_manager through to MovingWidget unchanged."""
    sprite_manager = _make_sprite_manager()

    stone = Stone(sprite_manager)

    sprite_manager.get.assert_called_once_with("stone_sprite")
    assert stone.sprite is sprite_manager.get.return_value
    assert stone.size == (64, 53)
    assert stone.pos[0] >= SCREEN_W + 100
    assert stone.pos[0] <= SCREEN_W + 300
    assert 0 <= stone.pos[1] <= SCREEN_H - 64
