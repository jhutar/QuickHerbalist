"""Regression tests for Flower/Stone construction in game_scene.

Verifies the MovingWidget signature: subclasses must forward
sprite_manager as the first positional argument (regression from
commit 25a399b, which added sprite_manager to Flower/Stone without
updating their super().__init__ calls, crashing on first spawn).
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

# Setup mocks for Kivy BEFORE importing anything that uses it
kivy_module = types.ModuleType("kivy")
kivy_app_module = types.ModuleType("kivy.app")
kivy_uix_module = types.ModuleType("kivy.uix")
kivy_widget_module = types.ModuleType("kivy.uix.widget")
kivy_label_module = types.ModuleType("kivy.uix.label")
kivy_clock_module = types.ModuleType("kivy.clock")
kivy_graphics_module = types.ModuleType("kivy.graphics")


# Define a real class for Widget to allow inheritance
class FakeCanvas:
    """Context-manager stand-in for a Kivy canvas."""

    def __enter__(self):
        """Enter the canvas context."""
        return self

    def __exit__(self, *args):
        """Exit the canvas context."""
        return False


class RealWidget:
    def __init__(self, **kwargs):
        self.size = (100, 100)
        self.pos = (0, 0)
        self.canvas = FakeCanvas()

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
from quick_herbalist.game_scene import SCREEN_W, SPAWN_POSITION_RETRIES, Flower, Stone  # noqa: E402


def _make_sprite_manager():
    sprite_manager = MagicMock()
    sprite_manager.get.return_value = MagicMock()
    return sprite_manager


def test_flower_forwards_sprite_manager_and_sprite_name():
    """Flower must pass sprite_manager through to MovingWidget unchanged."""
    sprite_manager = _make_sprite_manager()

    flower = Flower(sprite_manager, "flower_sprite", SCREEN_W + 50, 10)

    sprite_manager.get.assert_called_once_with("flower_sprite")
    assert flower.sprite is sprite_manager.get.return_value
    assert flower.size == (32, 32)
    assert flower.pos == (SCREEN_W + 50, 10)


def test_stone_forwards_sprite_manager_and_sprite_name():
    """Stone must pass sprite_manager through to MovingWidget unchanged."""
    sprite_manager = _make_sprite_manager()

    stone = Stone(sprite_manager, "stone_sprite", SCREEN_W + 100, 20)

    sprite_manager.get.assert_called_once_with("stone_sprite")
    assert stone.sprite is sprite_manager.get.return_value
    assert stone.size == (64, 53)
    assert stone.pos == (SCREEN_W + 100, 20)


def _make_game_view():
    """Build a GameView with mocked dependencies for spawn tests."""
    levels = [_make_level(1)]
    profile_manager = MagicMock(active_character_name="herb", next_level_number=lambda: 1)
    from quick_herbalist.game_scene import GameView

    return GameView(profile_manager, _make_sprite_manager(), levels)


def test_spawn_position_rejects_overlapping_spot():
    """_overlaps_entity must detect AABB overlap with a live entity."""
    view = _make_game_view()
    view.stones.append(Stone(_make_sprite_manager(), "lvl_stone", 900, 100))

    # Same spot -> overlap. Shifted just past the stone's edge -> no overlap.
    assert view._overlaps_entity(900, 100, (32, 32)) is True
    assert view._overlaps_entity(900 + 64, 100, (32, 32)) is False
    assert view._overlaps_entity(900, 100 + 53, (32, 32)) is False


def _patched_randint(candidates):
    """Patch random.randint to yield fixed (x_offset, y) pairs in order."""
    values = iter(candidates)
    current = [None]

    def fake(lo, hi):
        """Return x offset for x-range calls (lo>0), y for y-range calls (lo==0)."""
        if lo == 0:
            return current[0][1]
        current[0] = next(values)
        return current[0][0]

    return patch("quick_herbalist.game_scene.random.randint", side_effect=fake)


def test_spawn_flower_does_not_overlap_existing_entity():
    """spawn_flower must never place a flower on top of an existing entity."""
    view = _make_game_view()
    view.stones.append(Stone(_make_sprite_manager(), "lvl_stone", SCREEN_W + 120, 100))

    # First candidate lands on the stone; second candidate is free.
    with _patched_randint([(120, 100), (150, 200)]):
        view.spawn_flower(0)

    assert len(view.flowers) == 1
    assert view.flowers[0].pos == (SCREEN_W + 150, 200)


def test_spawn_stone_does_not_overlap_existing_entity():
    """spawn_stone must never place a stone on top of an existing entity."""
    view = _make_game_view()
    view.flowers.append(Flower(_make_sprite_manager(), "lvl_flower", SCREEN_W + 120, 100))

    with _patched_randint([(120, 100), (150, 200)]):
        view.spawn_stone(0)

    assert len(view.stones) == 1
    assert view.stones[0].pos == (SCREEN_W + 150, 200)


def test_spawn_skipped_when_all_candidates_overlap():
    """Spawning must skip (no widget, no crash) when every candidate overlaps."""
    candidates = [(120, 100)] * SPAWN_POSITION_RETRIES

    view = _make_game_view()
    view.stones.append(Stone(_make_sprite_manager(), "lvl_stone", SCREEN_W + 120, 100))
    with _patched_randint(candidates):
        view.spawn_flower(0)
    assert view.flowers == []

    view2 = _make_game_view()
    view2.flowers.append(Flower(_make_sprite_manager(), "lvl_flower", SCREEN_W + 120, 100))
    with _patched_randint(candidates):
        view2.spawn_stone(0)
    assert view2.stones == []


def _make_level(number, background="lvl_bg", flower="lvl_flower", stone="lvl_stone"):
    """Build a LevelDefinition for GameView wiring tests."""
    from quick_herbalist.core.level_config import (
        LevelDefinition,
        SpawnDefinition,
        StoneDefinition,
    )

    return LevelDefinition(
        name=f"level{number}",
        background=background,
        distance=1000.0,
        start_speed=3.0,
        max_speed=15.0,
        flower=SpawnDefinition(sprite=flower, interval=1.0),
        stone=StoneDefinition(sprite=stone, interval=3.0, ramp_to=0.05),
    )


def test_game_view_uses_level_sprite_names():
    """GameView must request the level's background/flower/stone sprites, not hardcoded ones."""
    levels = [_make_level(1, background="a_bg"), _make_level(2, background="b_bg")]
    profile_manager = MagicMock(active_character_name="herb", next_level_number=lambda: 2)
    sprite_manager = _make_sprite_manager()

    from quick_herbalist.game_scene import GameView

    view = GameView(profile_manager, sprite_manager, levels)

    requested = [call.args[0] for call in sprite_manager.get.call_args_list]
    assert "b_bg" in requested  # level 2 background
    assert "a_bg" not in requested

    view.spawn_flower(0)
    view.spawn_stone(0)
    requested = [call.args[0] for call in sprite_manager.get.call_args_list]
    assert "lvl_flower" in requested
    assert "lvl_stone" in requested
    assert "flower_sprite" not in requested
    assert "stone_sprite" not in requested
    assert "grass_sprite" not in requested


# --- Potion effects (run loadout hotkeys + magnet) ---


def _make_magnet_recipe():
    """Build a real magnetism recipe for effect wiring tests."""
    from quick_herbalist.potions import Recipe

    return Recipe(
        id="potion_magnetism",
        name_key="potion_magnetism_name",
        description_key="potion_magnetism_description",
        ingredients={"flower_sprite": 1},
        duration_seconds=30.0,
    )


def _make_effect_view():
    """Build a GameView with a mocked profile manager and the magnet recipe."""
    levels = [_make_level(1)]
    profile_manager = MagicMock(active_character_name="herb", next_level_number=lambda: 1)
    from quick_herbalist.game_scene import GameView

    return GameView(
        profile_manager, _make_sprite_manager(), levels, recipes=[_make_magnet_recipe()]
    )


def test_hotkey_uses_filled_slot_and_activates_effect():
    """Pressing 1 with a filled slot consumes it and starts the timed effect."""
    view = _make_effect_view()
    view.profile_manager.get_run_loadout.return_value = ["potion_magnetism", None, None]

    assert view.on_keyboard_down("1") is True
    view.profile_manager.use_run_slot.assert_called_once_with(0)
    assert view.active_effects == [["potion_magnetism", 30.0]]


def test_hotkey_with_empty_slot_is_noop():
    """Pressing a hotkey for an empty slot does nothing and raises nothing."""
    view = _make_effect_view()
    view.profile_manager.get_run_loadout.return_value = [None, None, None]

    assert view.on_keyboard_down("2") is True
    view.profile_manager.use_run_slot.assert_not_called()
    assert view.active_effects == []


def test_hotkey_unknown_potion_skips_effect():
    """A slot holding a potion without a recipe is not consumed and adds no effect."""
    view = _make_effect_view()
    view.profile_manager.get_run_loadout.return_value = ["potion_gone", None, None]

    assert view.on_keyboard_down("1") is True
    view.profile_manager.use_run_slot.assert_not_called()
    assert view.active_effects == []


def test_magnet_pulls_flower_at_edge_of_radius_slowly():
    """A flower 100 px from the player center is pulled ~1 px/tick toward the player."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    flower = Flower(_make_sprite_manager(), "lvl_flower", center_x + 100 - 16, center_y - 16)
    view.flowers = [flower]

    view._tick_magnet(1.0)
    # speed = 10 - 9 * 100/100 = 1 px/tick, straight left
    assert flower.pos == (pytest.approx(center_x + 100 - 1 - 16), pytest.approx(center_y - 16))


def test_magnet_pulls_near_flower_fast_and_vertically():
    """Pull speed scales up near the player and works along the vertical axis."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2

    near = Flower(_make_sprite_manager(), "lvl_flower", center_x + 50 - 16, center_y - 16)
    below = Flower(_make_sprite_manager(), "lvl_flower", center_x - 16, center_y + 60 - 16)
    view.flowers = [near, below]

    view._tick_magnet(1.0)
    # dist 50 -> speed 5.5 left; dist 60 -> speed 4.6 up
    assert near.pos[0] == pytest.approx(center_x + 50 - 5.5 - 16)
    assert below.pos[1] == pytest.approx(center_y + 60 - 4.6 - 16)


def test_magnet_ignores_flowers_outside_radius_and_stones():
    """Flowers beyond 100 px and all stones are untouched."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    far = Flower(_make_sprite_manager(), "lvl_flower", center_x + 150 - 16, center_y - 16)
    stone = Stone(_make_sprite_manager(), "lvl_stone", center_x + 50 - 32, center_y - 53)
    view.flowers = [far]
    view.stones = [stone]

    view._tick_magnet(1.0)
    assert far.pos == (center_x + 150 - 16, center_y - 16)
    assert stone.pos == (center_x + 50 - 32, center_y - 53)


def test_magnet_pull_scales_with_frame_factor():
    """Pull distance per call scales with the dt-based frame factor."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    flower = Flower(_make_sprite_manager(), "lvl_flower", center_x + 100 - 16, center_y - 16)
    view.flowers = [flower]

    view._tick_magnet(2.0)
    assert flower.pos == (pytest.approx(center_x + 100 - 2 - 16), pytest.approx(center_y - 16))


def test_effects_stack_across_slots():
    """Using two different slots starts two independent timed effects."""
    view = _make_effect_view()
    view.profile_manager.get_run_loadout.return_value = [
        "potion_magnetism",
        "potion_magnetism",
        None,
    ]

    view.on_keyboard_down("1")
    view.on_keyboard_down("2")
    assert view.active_effects == [
        ["potion_magnetism", 30.0],
        ["potion_magnetism", 30.0],
    ]


def test_effect_expires_and_label_cleared():
    """An effect dropped by the countdown is removed and the HUD label empties."""
    view = _make_effect_view()
    view.active_effects = [["potion_magnetism", 0.5]]

    view._step_effects(1.0, 1.0)
    assert view.active_effects == []
    assert view.effect_label.text == ""


def test_effect_label_shows_name_and_whole_seconds():
    """The HUD label lists each active effect with remaining seconds rounded up."""
    view = _make_effect_view()
    view.active_effects = [["potion_magnetism", 12.5]]

    view._step_effects(0.5, 1.0)
    assert view.active_effects == [["potion_magnetism", 12.0]]
    assert view.effect_label.text == "potion_magnetism_name 12"
