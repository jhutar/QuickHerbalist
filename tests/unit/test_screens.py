"""Tests for menu screen navigation and the game menu hub label."""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, call

# Setup mocks for Kivy BEFORE importing anything that uses it
kivy_module = types.ModuleType("kivy")
kivy_app_module = types.ModuleType("kivy.app")
kivy_core_module = types.ModuleType("kivy.core")
kivy_window_module = types.ModuleType("kivy.core.window")
kivy_lang_module = types.ModuleType("kivy.lang")
kivy_factory_module = types.ModuleType("kivy.factory")
kivy_uix_module = types.ModuleType("kivy.uix")
kivy_button_module = types.ModuleType("kivy.uix.button")
kivy_boxlayout_module = types.ModuleType("kivy.uix.boxlayout")
kivy_screenmanager_module = types.ModuleType("kivy.uix.screenmanager")


class FakeScreen:
    """Stand-in for Kivy Screen allowing subclassing in tests."""

    def __init__(self, **kwargs):
        self.manager = MagicMock()
        self.ids = MagicMock()


kivy_app_module.App = MagicMock()
kivy_window_module.Window = MagicMock()
kivy_lang_module.Builder = MagicMock()
kivy_factory_module.Factory = MagicMock()
kivy_button_module.Button = MagicMock()
kivy_button_module.Button.side_effect = lambda **kwargs: MagicMock()
kivy_boxlayout_module.BoxLayout = MagicMock()
kivy_screenmanager_module.Screen = FakeScreen

sys.modules["kivy"] = kivy_module
sys.modules["kivy.app"] = kivy_app_module
sys.modules["kivy.core"] = kivy_core_module
sys.modules["kivy.core.window"] = kivy_window_module
sys.modules["kivy.lang"] = kivy_lang_module
sys.modules["kivy.factory"] = kivy_factory_module
sys.modules["kivy.uix"] = kivy_uix_module
sys.modules["kivy.uix.button"] = kivy_button_module
sys.modules["kivy.uix.screenmanager"] = kivy_screenmanager_module

kivy_module.app = kivy_app_module
kivy_module.core = kivy_core_module
kivy_module.lang = kivy_lang_module
kivy_module.factory = kivy_factory_module
kivy_module.uix = kivy_uix_module
kivy_core_module.window = kivy_window_module
kivy_uix_module.button = kivy_button_module
kivy_uix_module.boxlayout = kivy_boxlayout_module
kivy_uix_module.screenmanager = kivy_screenmanager_module

# game_scene import needs these kivy modules stubbed too
kivy_uix_widget_module = types.ModuleType("kivy.uix.widget")
kivy_uix_label_module = types.ModuleType("kivy.uix.label")
kivy_uix_floatlayout_module = types.ModuleType("kivy.uix.floatlayout")
kivy_uix_image_module = types.ModuleType("kivy.uix.image")
kivy_clock_module = types.ModuleType("kivy.clock")
kivy_graphics_module = types.ModuleType("kivy.graphics")


class RealWidget:
    """Minimal Widget stand-in for game_scene inheritance."""

    def __init__(self, **kwargs):
        self.size = (100, 100)
        self.pos = (0, 0)
        self.children = []

    def add_widget(self, widget):
        self.children.append(widget)

    def clear_widgets(self):
        self.children = []

    def bind(self, **kwargs):
        return None

    def collide_point(self, x, y):
        return False


kivy_uix_widget_module.Widget = RealWidget
kivy_uix_floatlayout_module.FloatLayout = RealWidget
kivy_uix_image_module.Image = RealWidget
kivy_uix_label_module.Label = MagicMock()
kivy_clock_module.Clock = MagicMock()
kivy_graphics_module.Color = MagicMock()
kivy_graphics_module.Rectangle = MagicMock()

sys.modules["kivy.uix.boxlayout"] = kivy_boxlayout_module
sys.modules["kivy.uix.widget"] = kivy_uix_widget_module
sys.modules["kivy.uix.label"] = kivy_uix_label_module
sys.modules["kivy.uix.floatlayout"] = kivy_uix_floatlayout_module
sys.modules["kivy.uix.image"] = kivy_uix_image_module
sys.modules["kivy.clock"] = kivy_clock_module
sys.modules["kivy.graphics"] = kivy_graphics_module
kivy_uix_module.widget = kivy_uix_widget_module
kivy_uix_module.label = kivy_uix_label_module
kivy_uix_module.floatlayout = kivy_uix_floatlayout_module
kivy_uix_module.image = kivy_uix_image_module
kivy_module.clock = kivy_clock_module
kivy_module.graphics = kivy_graphics_module

# Import the code under test
from quick_herbalist.potions import Recipe  # noqa: E402
from quick_herbalist.screens import (  # noqa: E402
    GameMenuScreen,
    GameOverScreen,
    GameWonScreen,
    GreenhouseScreen,
    MenuScreen,
    NewCharacterScreen,
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


def test_game_menu_level_button_release_survives_kivy3_touch_arg():
    """Kivy 3 dispatches on_release as (instance, touch).

    The touch must not be captured by the level closure variable.
    """
    app = _make_app(next_level=2)
    kivy_button_module.Button.reset_mock()

    screen = GameMenuScreen()
    screen.on_pre_enter()

    buttons = [c.args[0] for c in screen.ids.level_buttons.add_widget.call_args_list]
    for expected_level, btn in enumerate(buttons, start=1):
        callback = btn.bind.call_args.kwargs["on_release"]
        callback(btn, object())
        assert app.selected_level_number == expected_level


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


def test_greenhouse_back_button_labeled_game_menu():
    """Greenhouse back button must say 'Back to Game Menu'."""
    screen = GreenhouseScreen()
    screen.on_pre_enter()

    assert screen.ids.back_btn.text == "Back to Game Menu"


def test_new_character_hints_checkbox_has_description():
    """New-character hints checkbox must be accompanied by a description label."""
    _make_app()
    screen = NewCharacterScreen()
    screen.on_pre_enter()

    assert screen.ids.hints_checkbox.text == "Show in-game hints"
    assert screen.ids.hints_desc.text == (
        "Tutorial popups shown the first time you encounter each game entity."
    )


def test_game_won_next_level_starts_next_level():
    """Win-screen 'Next Level' button must pick the level after the one just played."""
    app = _make_app(next_level=3)
    app.selected_level_number = 2

    screen = GameWonScreen()
    screen.restart_game()

    assert app.selected_level_number == 3
    assert screen.manager.current == "game"


def test_game_won_next_level_after_all_completed_advances_from_current():
    """With all levels finished, 'Next Level' must follow the re-run level, not jump to the last."""
    app = _make_app(next_level=4)
    app.selected_level_number = 1

    screen = GameWonScreen()
    screen.restart_game()

    assert app.selected_level_number == 2
    assert screen.manager.current == "game"


def test_game_won_next_level_clamps_at_last_level():
    """'Next Level' from the last level must stay on the last level."""
    app = _make_app(next_level=4)
    app.selected_level_number = 3

    screen = GameWonScreen()
    screen.restart_game()

    assert app.selected_level_number == 3
    assert screen.manager.current == "game"


def test_game_won_renders_row_per_flower_type():
    """Win screen must resolve the sprite of every collected flower type."""
    app = _make_app(next_level=2)
    app.sprite_manager.get.reset_mock()

    screen = GameWonScreen()
    screen.harvest = {"dandelion_sprite": 5, "bluebell_sprite": 3}
    screen.on_pre_enter()

    assert app.sprite_manager.get.call_args_list == [
        call("dandelion_sprite"),
        call("bluebell_sprite"),
    ]


def test_game_won_menu_goes_to_game_menu():
    """Level-completed 'Game Menu' button must return to the hub."""
    screen = GameWonScreen()

    screen.goto_menu()

    assert screen.manager.current == "game_menu"


def test_game_won_menu_button_labeled_game_menu():
    """Win-screen hub button must say 'Game Menu', not 'Main Menu'."""
    _make_app(next_level=2)
    screen = GameWonScreen()
    screen.harvest = {}
    screen.on_pre_enter()

    assert screen.ids.menu_btn.text == "Game Menu"


def test_game_over_menu_goes_to_game_menu():
    """Game-over 'Game Menu' button must return to the hub."""
    screen = GameOverScreen()

    screen.goto_menu()

    assert screen.manager.current == "game_menu"


def test_game_over_menu_button_labeled_game_menu():
    """Game-over hub button must say 'Game Menu', not 'Main Menu'."""
    screen = GameOverScreen()
    screen.on_pre_enter()

    assert screen.ids.menu_btn.text == "Game Menu"


def _recipe(recipe_id="potion_magnetism", ingredients=None):
    """Build a recipe for screen tests."""
    return Recipe(
        id=recipe_id,
        name_key=f"{recipe_id}_name",
        description_key=f"{recipe_id}_description",
        ingredients=ingredients or {"dandelion_sprite": 2, "bluebell_sprite": 1},
        duration_seconds=30,
    )


def _setup_potions_app(recipes, inventory=None, cauldron=None, potions=None, loadout=None):
    """Build a fake running app wired for the potions screen."""
    app = _make_app()
    app.recipes = recipes
    pm = app.profile_manager
    pm.get_inventory.return_value = inventory or {}
    pm.get_cauldron.return_value = cauldron or {}
    pm.get_potions.return_value = potions or {}
    pm.get_potion_count.side_effect = lambda p: (potions or {}).get(p, 0)
    pm.get_run_loadout.return_value = loadout or [None, None, None]
    app.sprite_manager.names.return_value = set(inventory or {}) | set(cauldron or {})
    app.sprite_manager.get.side_effect = _make_sprite_mock
    return app


def _make_sprite_mock(name):
    """Fake AnimatedSprite carrying the frame-image path the drag proxy needs."""
    sprite = MagicMock()
    sprite.frames_data = [{"image": f"{name}.png"}]
    return sprite


def test_potions_screen_brew_success_adds_potion():
    """Matching cauldron contents brew the potion and clear the cauldron."""
    app = _setup_potions_app([_recipe()], cauldron={"dandelion_sprite": 2, "bluebell_sprite": 1})

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_brew()

    app.profile_manager.add_potion.assert_called_once_with("potion_magnetism")
    app.profile_manager.clear_cauldron.assert_called_once_with()
    assert screen.ids.message_lbl.text == "Brewed: potion_magnetism_name"


def test_potions_screen_brew_no_match_wastes_ingredients():
    """Non-matching cauldron contents are wasted without brewing."""
    app = _setup_potions_app([_recipe()], cauldron={"dandelion_sprite": 3})

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_brew()

    app.profile_manager.add_potion.assert_not_called()
    app.profile_manager.clear_cauldron.assert_called_once_with()
    assert screen.ids.message_lbl.text == "Ingredients wasted"


def test_potions_screen_brew_empty_cauldron_shows_message():
    """Mixing an empty cauldron shows an error instead of brewing silently."""
    app = _setup_potions_app([_recipe()])

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_brew()

    app.profile_manager.clear_cauldron.assert_not_called()
    app.profile_manager.add_potion.assert_not_called()
    assert screen.ids.message_lbl.text == "Cauldron is empty"
    assert screen.ids.message_lbl.color == (1, 0.3, 0.3, 1)


def test_potions_screen_ingredient_drop_moves_to_cauldron():
    """Dropping an ingredient chip commits it into the cauldron."""
    app = _setup_potions_app([_recipe()], inventory={"dandelion_sprite": 2})

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_ingredient_dropped("dandelion_sprite")

    app.profile_manager.move_flower_to_cauldron.assert_called_once_with("dandelion_sprite")


def test_potions_screen_ingredient_chip_click_adds_to_cauldron():
    """A rendered ingredient chip wires a click handler that commits the flower."""
    app = _setup_potions_app([_recipe()], inventory={"dandelion_sprite": 2})

    screen = PotionsScreen()
    screen.on_pre_enter()

    chips = [c.args[0] for c in screen.ids.ingredient_strip.add_widget.call_args_list]
    assert len(chips) == 1
    chip = chips[0]
    assert callable(chip.click_handler)
    chip.click_handler()

    app.profile_manager.move_flower_to_cauldron.assert_called_once_with("dandelion_sprite")


def test_potions_screen_ingredient_chip_has_drag_proxy_image():
    """Each ingredient chip carries a drag-proxy image source so the flower follows the pointer."""
    from quick_herbalist.core.config_parser import get_asset_path

    _setup_potions_app([_recipe()], inventory={"dandelion_sprite": 2})

    screen = PotionsScreen()
    screen.on_pre_enter()

    chips = [c.args[0] for c in screen.ids.ingredient_strip.add_widget.call_args_list]
    assert len(chips) == 1
    assert chips[0].drag_image_source == get_asset_path("dandelion_sprite.png")


def test_potions_screen_cauldron_slot_tap_removes_ingredient():
    """Tapping a cauldron slot returns the ingredient to the inventory."""
    app = _setup_potions_app([_recipe()], cauldron={"dandelion_sprite": 1})

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_cauldron_ingredient_removed("dandelion_sprite")

    app.profile_manager.move_cauldron_ingredient_to_inventory.assert_called_once_with(
        "dandelion_sprite"
    )


def test_potions_screen_ingredient_strip_hides_zero_count():
    """Flowers with count 0 are not shown in the ingredient strip."""
    _setup_potions_app([_recipe()], inventory={"dandelion_sprite": 2, "bluebell_sprite": 0})

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.ingredient_strip.add_widget.call_count == 1


def test_potions_screen_recipe_book_shows_page_and_flips():
    """Recipe book shows the current page and wraps when flipping."""
    recipes = [
        _recipe("potion_a", {"dandelion_sprite": 1}),
        _recipe("potion_b", {"bluebell_sprite": 2}),
    ]
    _setup_potions_app(recipes)

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.recipe_name_lbl.text == "potion_a_name"
    screen._flip_recipe(1)
    assert screen.ids.recipe_name_lbl.text == "potion_b_name"
    screen._flip_recipe(1)
    assert screen.ids.recipe_name_lbl.text == "potion_a_name"
    screen._flip_recipe(-1)
    assert screen.ids.recipe_name_lbl.text == "potion_b_name"


def test_potions_screen_recipe_book_lists_ingredients():
    """Recipe page shows each ingredient with its count and the duration."""
    _setup_potions_app([_recipe()])

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.recipe_ingredients_lbl.text == "dandelion_sprite x2\nbluebell_sprite x1"
    assert screen.ids.recipe_duration_lbl.text == "Duration: 30"


def test_potions_screen_potion_click_assigns_first_free_slot():
    """Clicking a potion chip assigns it to the first free run slot."""
    app = _setup_potions_app([_recipe()], potions={"potion_magnetism": 2})

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_potion_clicked("potion_magnetism")

    app.profile_manager.assign_potion_to_slot.assert_called_once_with("potion_magnetism", None)


def test_potions_screen_potion_drop_targets_slot_under_touch():
    """Dropping a potion chip on a specific slot targets that slot."""
    app = _setup_potions_app([_recipe()], potions={"potion_magnetism": 1})

    screen = PotionsScreen()
    screen.on_pre_enter()
    for index, btn in enumerate(screen._slot_buttons):
        btn.collide_point.return_value = index == 1

    touch = MagicMock()
    touch.pos = (5, 5)
    screen._on_potion_dropped("potion_magnetism", touch)

    app.profile_manager.assign_potion_to_slot.assert_called_once_with("potion_magnetism", 1)


def test_potions_screen_potion_drop_miss_falls_back_to_first_free():
    """Dropping a potion chip off every slot falls back to the first free one."""
    app = _setup_potions_app([_recipe()], potions={"potion_magnetism": 1})

    screen = PotionsScreen()
    screen.on_pre_enter()
    for btn in screen._slot_buttons:
        btn.collide_point.return_value = False

    touch = MagicMock()
    touch.pos = (5, 5)
    screen._on_potion_dropped("potion_magnetism", touch)

    app.profile_manager.assign_potion_to_slot.assert_called_once_with("potion_magnetism", None)


def test_potions_screen_slot_click_releases_potion():
    """Clicking a filled run slot returns the potion to the inventory."""
    app = _setup_potions_app([_recipe()], loadout=["potion_magnetism", None, None])

    screen = PotionsScreen()
    screen.on_pre_enter()
    screen._on_run_slot_clicked(0)

    app.profile_manager.release_run_slot.assert_called_once_with(0)


def test_potions_screen_ingredient_strip_skips_unknown_sprites():
    """Legacy inventory keys without a sprite (e.g. 'flower') are skipped, not crashed on."""
    app = _setup_potions_app(
        [_recipe()], inventory={"dandelion_sprite": 2, "flower": 5, "bluebell_sprite": 1}
    )
    app.sprite_manager.names.return_value = {"dandelion_sprite", "bluebell_sprite"}

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.ingredient_strip.add_widget.call_count == 2
    app.sprite_manager.get.assert_any_call("dandelion_sprite")
    app.sprite_manager.get.assert_any_call("bluebell_sprite")
    assert not any(c.args and c.args[0] == "flower" for c in app.sprite_manager.get.call_args_list)


def test_potions_screen_recipe_book_uses_book_background_image():
    """Recipe book background loads recipes.png stretched over the book panel."""
    from quick_herbalist.core.config_parser import get_asset_path

    _setup_potions_app([_recipe()])

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.book_img.source == get_asset_path("recipes.png")


def test_potions_screen_empty_potion_strip_shows_placeholder():
    """With no potions brewed, the potion strip shows a placeholder label."""
    _setup_potions_app([_recipe()], potions={})

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.potion_strip.add_widget.call_count == 1


def test_potions_screen_ingredient_chip_labels_show_count():
    """Each ingredient chip shows the sprite name with its count like 'name (2x)'"""
    kivy_uix_label_module.Label.reset_mock()
    _setup_potions_app([_recipe()], inventory={"dandelion_sprite": 2})

    screen = PotionsScreen()
    screen.on_pre_enter()

    texts = [c.kwargs.get("text") for c in kivy_uix_label_module.Label.call_args_list]
    assert "dandelion_sprite (2x)" in texts


def test_potions_screen_spoon_uses_spoon_image():
    """Spoon widget and its drag proxy use the spoon.png asset."""
    from quick_herbalist.core.config_parser import get_asset_path

    _setup_potions_app([_recipe()])

    screen = PotionsScreen()
    screen.on_pre_enter()

    assert screen.ids.spoon_img.source == get_asset_path("spoon.png")
    assert screen.ids.spoon.drag_image_source == get_asset_path("spoon.png")


def test_game_screen_esc_routes_to_hint_not_quit():
    """While a hint box is open, Esc goes to the game view, not the quit screen."""
    from quick_herbalist.screens.game_flow import GameScreen

    screen = GameScreen()
    screen.manager = MagicMock()
    view = MagicMock()
    view.hint_active = True
    view.on_keyboard_down.return_value = True
    screen.game_view = view

    handled = screen._on_keyboard_down(None, (27, "escape"), "", ())

    assert handled is True
    view.on_keyboard_down.assert_called_once_with("escape")
    assert screen.manager.current != "quit"


def test_game_screen_esc_goes_to_quit_without_hint():
    """Without an open hint, Esc keeps the old quit behaviour."""
    from quick_herbalist.screens.game_flow import GameScreen

    screen = GameScreen()
    screen.manager = MagicMock()
    view = MagicMock()
    view.hint_active = False
    screen.game_view = view

    screen._on_keyboard_down(None, (27, "escape"), "", ())

    assert screen.manager.current == "quit"


def _kv_button_block(kv_text, button_id):
    """Return the kv block of the Button whose id is button_id."""
    lines = kv_text.splitlines()
    for i, line in enumerate(lines):
        if f"id: {button_id}" in line:
            indent = len(line) - len(line.lstrip())
            block = [line]
            for next_line in lines[i + 1 :]:
                if not next_line.strip():
                    continue
                if len(next_line) - len(next_line.lstrip()) < indent:
                    break
                block.append(next_line)
            return "\n".join(block)
    raise AssertionError(f"Button id {button_id} not found in kv text")


def test_menu_game_over_game_won_buttons_match_game_menu_height():
    """Main menu / game over / game won buttons use fixed 50px height like game menu."""
    kv_dir = Path(__file__).resolve().parents[2] / "src" / "quick_herbalist" / "screens" / "kv"
    expected = {
        "menu.kv": ["start_btn", "new_btn", "load_btn", "quit_btn"],
        "game_over.kv": ["restart_btn", "menu_btn"],
        "game_won.kv": ["restart_btn", "menu_btn"],
    }
    for kv_name, button_ids in expected.items():
        text = (kv_dir / kv_name).read_text(encoding="utf-8")
        for button_id in button_ids:
            block = _kv_button_block(text, button_id)
            assert "height: 50" in block, f"{kv_name} {button_id} missing height: 50"
            assert "size_hint_y: None" in block, f"{kv_name} {button_id} missing size_hint_y: None"
        assert "size_hint_y: 0.15" not in text, f"{kv_name} still uses proportional row height"
