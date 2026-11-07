"""Tests for menu screen navigation and the game menu hub label."""

import sys
import types
from unittest.mock import MagicMock, call

# Setup mocks for Kivy BEFORE importing anything that uses it
kivy_module = types.ModuleType("kivy")
kivy_app_module = types.ModuleType("kivy.app")
kivy_core_module = types.ModuleType("kivy.core")
kivy_window_module = types.ModuleType("kivy.core.window")
kivy_lang_module = types.ModuleType("kivy.lang")
kivy_uix_module = types.ModuleType("kivy.uix")
kivy_button_module = types.ModuleType("kivy.uix.button")
kivy_screenmanager_module = types.ModuleType("kivy.uix.screenmanager")


class FakeScreen:
    """Stand-in for Kivy Screen allowing subclassing in tests."""

    def __init__(self, **kwargs):
        self.manager = MagicMock()
        self.ids = MagicMock()


kivy_app_module.App = MagicMock()
kivy_window_module.Window = MagicMock()
kivy_lang_module.Builder = MagicMock()
kivy_button_module.Button = MagicMock()
kivy_screenmanager_module.Screen = FakeScreen

sys.modules["kivy"] = kivy_module
sys.modules["kivy.app"] = kivy_app_module
sys.modules["kivy.core"] = kivy_core_module
sys.modules["kivy.core.window"] = kivy_window_module
sys.modules["kivy.lang"] = kivy_lang_module
sys.modules["kivy.uix"] = kivy_uix_module
sys.modules["kivy.uix.button"] = kivy_button_module
sys.modules["kivy.uix.screenmanager"] = kivy_screenmanager_module

kivy_module.app = kivy_app_module
kivy_module.core = kivy_core_module
kivy_module.lang = kivy_lang_module
kivy_module.uix = kivy_uix_module
kivy_core_module.window = kivy_window_module
kivy_uix_module.button = kivy_button_module
kivy_uix_module.screenmanager = kivy_screenmanager_module

# game_scene import needs these kivy modules stubbed too
kivy_uix_widget_module = types.ModuleType("kivy.uix.widget")
kivy_uix_label_module = types.ModuleType("kivy.uix.label")
kivy_clock_module = types.ModuleType("kivy.clock")
kivy_graphics_module = types.ModuleType("kivy.graphics")


class RealWidget:
    """Minimal Widget stand-in for game_scene inheritance."""

    def __init__(self, **kwargs):
        self.size = (100, 100)
        self.pos = (0, 0)


kivy_uix_widget_module.Widget = RealWidget
kivy_uix_label_module.Label = MagicMock()
kivy_clock_module.Clock = MagicMock()
kivy_graphics_module.Rectangle = MagicMock()

sys.modules["kivy.uix.widget"] = kivy_uix_widget_module
sys.modules["kivy.uix.label"] = kivy_uix_label_module
sys.modules["kivy.clock"] = kivy_clock_module
sys.modules["kivy.graphics"] = kivy_graphics_module
kivy_uix_module.widget = kivy_uix_widget_module
kivy_uix_module.label = kivy_uix_label_module
kivy_module.clock = kivy_clock_module
kivy_module.graphics = kivy_graphics_module

# Import the code under test
from quick_herbalist.screens import (  # noqa: E402
    GameMenuScreen,
    GameOverScreen,
    GameWonScreen,
    GreenhouseScreen,
    MenuScreen,
    PotionsScreen,
)


def _make_app(next_level=1):
    """Build a fake running app with a profile manager."""
    app = MagicMock()
    app.profile_manager.next_level_number.return_value = next_level
    app.profile_manager.playable_level_numbers.return_value = list(range(1, next_level + 1))
    app.levels = [1, 2, 3]
    kivy_app_module.App.get_running_app.return_value = app
    return app


def test_game_menu_builds_button_per_playable_level():
    """Hub must show one Start Level button per playable level."""
    app = _make_app(next_level=3)
    kivy_button_module.Button.reset_mock()

    screen = GameMenuScreen()
    screen.on_pre_enter()

    assert app.profile_manager.playable_level_numbers.call_args == call(max_levels=3)
    texts = [c.kwargs["text"] for c in kivy_button_module.Button.call_args_list]
    assert texts == ["Start Level 1", "Start Level 2", "Start Level 3"]
    assert screen.ids.level_buttons.add_widget.call_count == 3


def test_game_menu_level_button_starts_chosen_level():
    """Pressing a level button must store the level and open the game."""
    app = _make_app(next_level=3)

    screen = GameMenuScreen()
    screen.start_level(2)

    assert app.selected_level_number == 2
    assert screen.manager.current == "game"


def test_main_menu_start_goes_to_game_menu():
    """Main menu Start Game must open the game menu hub, not the game."""
    screen = MenuScreen()
    screen.start_game()

    assert screen.manager.current == "game_menu"


def test_game_menu_s_key_starts_run():
    """Pressing 's' on the hub must go straight into the game at the next level."""
    app = _make_app(next_level=3)

    screen = GameMenuScreen()

    handled = screen._on_keyboard_down(MagicMock(), (0, "s"), "s", set())

    assert handled is True
    assert app.selected_level_number == 3
    assert screen.manager.current == "game"


def test_potions_screen_back_goes_to_game_menu():
    """Potions screen back/escape must return to the hub."""
    screen = PotionsScreen()

    screen.on_back()

    assert screen.manager.current == "game_menu"


def test_greenhouse_screen_back_goes_to_game_menu():
    """Greenhouse screen back/escape must return to the hub."""
    screen = GreenhouseScreen()

    screen.on_back()

    assert screen.manager.current == "game_menu"


def test_game_won_next_level_starts_next_level():
    """Win-screen 'Next Level' button must select the next level, not repeat the current one."""
    app = _make_app(next_level=4)
    app.selected_level_number = 3

    screen = GameWonScreen()
    screen.restart_game()

    assert app.selected_level_number == 4
    assert screen.manager.current == "game"


def test_game_won_menu_goes_to_game_menu():
    """Level-completed 'Main Menu' button must return to the hub."""
    screen = GameWonScreen()

    screen.goto_menu()

    assert screen.manager.current == "game_menu"


def test_game_over_menu_goes_to_game_menu():
    """Game-over 'Main Menu' button must return to the hub."""
    screen = GameOverScreen()

    screen.goto_menu()

    assert screen.manager.current == "game_menu"
