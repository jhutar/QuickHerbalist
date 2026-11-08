"""Regression tests for the game scene: entities, spawning, and potion effects.

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

    def remove_widget(self, widget):
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
from quick_herbalist.game import (  # noqa: E402
    SCREEN_W,
    SPAWN_POSITION_RETRIES,
    Flower,
    GameView,  # noqa: E402
    Stone,
)
from quick_herbalist.game.effects import ActiveEffect, MagnetEffect  # noqa: E402
from quick_herbalist.game.scene import EntitySpec  # noqa: E402


def _make_sprite_manager():
    sprite_manager = MagicMock()
    sprite_manager.get.return_value = MagicMock()
    return sprite_manager


def _spec(view, key):
    """Return the EntitySpec on the view for the given entity key."""
    return next(s for s in view._specs if s.key == key)


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

    return GameView(profile_manager, _make_sprite_manager(), levels)


def test_spawn_position_rejects_overlapping_spot():
    """_overlaps_entity must detect AABB overlap with a live entity."""
    view = _make_game_view()
    view.entities["stone"].append(Stone(_make_sprite_manager(), "lvl_stone", 900, 100))

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

    return patch("quick_herbalist.game.scene.random.randint", side_effect=fake)


def test_spawn_flower_does_not_overlap_existing_entity():
    """spawning a flower must never place it on top of an existing entity."""
    view = _make_game_view()
    view.entities["stone"].append(Stone(_make_sprite_manager(), "lvl_stone", SCREEN_W + 120, 100))

    # First candidate lands on the stone; second candidate is free.
    with _patched_randint([(120, 100), (150, 200)]):
        view._spawn(0, _spec(view, "flower"))

    assert len(view.entities["flower"]) == 1
    assert view.entities["flower"][0].pos == (SCREEN_W + 150, 200)


def test_spawn_stone_does_not_overlap_existing_entity():
    """spawning a stone must never place it on top of an existing entity."""
    view = _make_game_view()
    view.entities["flower"].append(
        Flower(_make_sprite_manager(), "lvl_flower", SCREEN_W + 120, 100)
    )

    with _patched_randint([(120, 100), (150, 200)]):
        view._spawn(0, _spec(view, "stone"))

    assert len(view.entities["stone"]) == 1
    assert view.entities["stone"][0].pos == (SCREEN_W + 150, 200)


def test_spawn_skipped_when_all_candidates_overlap():
    """Spawning must skip (no widget, no crash) when every candidate overlaps."""
    candidates = [(120, 100)] * SPAWN_POSITION_RETRIES

    view = _make_game_view()
    view.entities["stone"].append(Stone(_make_sprite_manager(), "lvl_stone", SCREEN_W + 120, 100))
    with _patched_randint(candidates):
        view._spawn(0, _spec(view, "flower"))
    assert view.entities["flower"] == []

    view2 = _make_game_view()
    view2.entities["flower"].append(
        Flower(_make_sprite_manager(), "lvl_flower", SCREEN_W + 120, 100)
    )
    with _patched_randint(candidates):
        view2._spawn(0, _spec(view2, "stone"))
    assert view2.entities["stone"] == []


def test_new_entity_type_spawns_into_its_own_list():
    """A custom MovingWidget subclass can be spawned via its own EntitySpec."""
    from quick_herbalist.game.entities import MovingWidget

    view = _make_game_view()

    class Ghost(MovingWidget):
        """Test-only entity type."""

        SIZE = (16, 16)
        SPAWN_X_MIN = 0
        SPAWN_X_MAX = 10

    spec = EntitySpec(
        key="ghost", widget_cls=Ghost, sprite="lvl_flower", interval=1.0, hit="collect"
    )
    view._specs = (spec,)
    view.entities = {spec.key: []}

    view._spawn(0, spec)

    assert len(view.entities["ghost"]) == 1
    assert view.entities["ghost"][0].size == (16, 16)


def test_collect_hit_adds_score_and_removes_entity():
    """A collected (colliding) flower adds score and is removed from the scene."""
    view = _make_game_view()
    flower = Flower(_make_sprite_manager(), "lvl_flower", 10, 10)
    flower.update = lambda speed: True
    view.entities["flower"].append(flower)
    view.hero.collide_widget = lambda entity: True

    view._update_entities(_spec(view, "flower"), 1.0)

    assert view.rules.score == 1
    assert view.entities["flower"] == []


def test_damage_hit_ends_run():
    """A colliding damage entity ends the run and is removed from the scene."""
    view = _make_game_view()
    stone = Stone(_make_sprite_manager(), "lvl_stone", 10, 10)
    stone.update = lambda speed: True
    view.entities["stone"].append(stone)
    view.hero.collide_widget = lambda entity: True

    view._update_entities(_spec(view, "stone"), 1.0)

    assert view.rules.dead is True
    assert view.entities["stone"] == []


def test_offscreen_entity_is_culled():
    """An entity that reports off-screen is removed without a collision."""
    view = _make_game_view()
    flower = Flower(_make_sprite_manager(), "lvl_flower", -100, 10)
    flower.update = lambda speed: False
    view.entities["flower"].append(flower)

    view._update_entities(_spec(view, "flower"), 1.0)

    assert view.entities["flower"] == []


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

    view = GameView(profile_manager, sprite_manager, levels)

    requested = [call.args[0] for call in sprite_manager.get.call_args_list]
    assert "b_bg" in requested  # level 2 background
    assert "a_bg" not in requested

    view._spawn(0, _spec(view, "flower"))
    view._spawn(0, _spec(view, "stone"))
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

    return GameView(
        profile_manager, _make_sprite_manager(), levels, recipes=[_make_magnet_recipe()]
    )


def test_hotkey_uses_filled_slot_and_activates_effect():
    """Pressing 1 with a filled slot consumes it and starts the timed effect."""
    view = _make_effect_view()
    view.profile_manager.get_run_loadout.return_value = ["potion_magnetism", None, None]

    assert view.on_keyboard_down("1") is True
    view.profile_manager.use_run_slot.assert_called_once_with(0)
    assert view.active_effects == [("potion_magnetism", 30.0)]
    assert view.active_effects and isinstance(view._active_effects[0].effect, MagnetEffect)


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


def test_potion_without_registered_effect_is_consumed_and_listed():
    """A potion with a recipe but no effect factory is consumed, listed, and inert."""
    from quick_herbalist.potions import Recipe

    view = _make_effect_view()
    view.recipes.append(
        Recipe(
            id="potion_bubble",
            name_key="potion_bubble_name",
            description_key="potion_bubble_description",
            ingredients={"flower_sprite": 1},
            duration_seconds=10.0,
        )
    )
    view.profile_manager.get_run_loadout.return_value = ["potion_bubble", None, None]

    view.on_keyboard_down("1")

    view.profile_manager.use_run_slot.assert_called_once_with(0)
    assert view.active_effects == [("potion_bubble", 10.0)]
    view._step_effects(1.0, 1.0)
    assert view.active_effects == [("potion_bubble", 9.0)]


def _magnet(view):
    """Create the magnet effect bound to the view's hero and live flowers."""
    return MagnetEffect(view.hero, view.entities["flower"])


def test_magnet_pulls_flower_at_edge_of_radius_slowly():
    """A flower 100 px from the player center is pulled ~1 px/tick toward the player."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    flower = Flower(_make_sprite_manager(), "lvl_flower", center_x + 100 - 16, center_y - 16)
    view.entities["flower"] = [flower]

    _magnet(view).tick(1.0)
    # speed = 10 - 9 * 100/100 = 1 px/tick, straight left
    assert flower.pos == (pytest.approx(center_x + 100 - 1 - 16), pytest.approx(center_y - 16))


def test_magnet_pulls_near_flower_fast_and_vertically():
    """Pull speed scales up near the player and works along the vertical axis."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2

    near = Flower(_make_sprite_manager(), "lvl_flower", center_x + 50 - 16, center_y - 16)
    below = Flower(_make_sprite_manager(), "lvl_flower", center_x - 16, center_y + 60 - 16)
    view.entities["flower"] = [near, below]

    _magnet(view).tick(1.0)
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
    view.entities["flower"] = [far]
    view.entities["stone"] = [stone]

    _magnet(view).tick(1.0)
    assert far.pos == (center_x + 150 - 16, center_y - 16)
    assert stone.pos == (center_x + 50 - 32, center_y - 53)


def test_magnet_pull_scales_with_frame_factor():
    """Pull distance per call scales with the dt-based frame factor."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    flower = Flower(_make_sprite_manager(), "lvl_flower", center_x + 100 - 16, center_y - 16)
    view.entities["flower"] = [flower]

    _magnet(view).tick(2.0)
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
        ("potion_magnetism", 30.0),
        ("potion_magnetism", 30.0),
    ]


def test_effect_expires_and_label_cleared():
    """An effect dropped by the countdown is removed and the HUD label empties."""
    view = _make_effect_view()
    view._active_effects = [ActiveEffect("potion_magnetism", 0.5, None)]

    view._step_effects(1.0, 1.0)
    assert view.active_effects == []
    assert view.hud.effect_label.text == ""


def test_effect_label_shows_name_and_whole_seconds():
    """The HUD label lists each active effect with remaining seconds rounded up."""
    view = _make_effect_view()
    view._active_effects = [ActiveEffect("potion_magnetism", 12.5, None)]

    view._step_effects(0.5, 1.0)
    assert view.active_effects == [("potion_magnetism", 12.0)]
    assert view.hud.effect_label.text == "potion_magnetism_name 12"
