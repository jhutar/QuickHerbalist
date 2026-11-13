"""Regression tests for the game scene: entities, spawning, pacing, effects.

Covers the GameEntity contract (move/on_enter/hero_speed_factor/done) and
the MovingWidget-era regression: subclasses must forward sprite_manager as
the first positional argument (regression from commit 25a399b, which added
sprite_manager to Flower/Stone without updating their super().__init__
calls, crashing on first spawn).
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
        self.children = []

    def add_widget(self, child, *args, **kwargs):
        # Mirror Kivy: new child at index 0 (front of z-order).
        self.children.insert(0, child)

    def remove_widget(self, child, *args, **kwargs):
        if child in self.children:
            self.children.remove(child)

    def on_touch_down(self, touch):
        """Default propagation: most-recently-added child gets the touch first."""
        for child in self.children[:]:
            if hasattr(child, "on_touch_down") and child.on_touch_down(touch):
                return True
        return False

    def bind(self, *args, **kwargs):
        pass

    @property
    def x(self):
        """Left edge, mirroring Kivy's Widget.x."""
        return self.pos[0]

    @x.setter
    def x(self, value):
        self.pos = (value, self.pos[1])

    @property
    def y(self):
        """Bottom edge, mirroring Kivy's Widget.y."""
        return self.pos[1]

    @y.setter
    def y(self, value):
        self.pos = (self.pos[0], value)

    @property
    def width(self):
        """Width, mirroring Kivy's Widget.width."""
        return self.size[0]

    @property
    def height(self):
        """Height, mirroring Kivy's Widget.height."""
        return self.size[1]

    @property
    def center_x(self):
        """Center x, mirroring Kivy's Widget.center_x."""
        return self.pos[0] + self.size[0] / 2

    @property
    def center_y(self):
        """Center y, mirroring Kivy's Widget.center_y."""
        return self.pos[1] + self.size[1] / 2


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
kivy_graphics_module.Color = MagicMock()
kivy_graphics_module.Rectangle = MagicMock()
kivy_label_module.Label = MagicMock()

# Import the code under test
from quick_herbalist.core.level_config import EntityDefinition  # noqa: E402
from quick_herbalist.game import (  # noqa: E402
    ENTITY_TYPES,
    SCREEN_W,
    SPAWN_POSITION_RETRIES,
    EntitySpec,
    Flower,
    GameView,
    Hill,
    Rock,
    SpawnPacer,
    Spider,
    Stone,
)
from quick_herbalist.game.effects import ActiveEffect, MagnetEffect  # noqa: E402
from quick_herbalist.game.hints import _BG, ENTITY_HINTS, HintBox, hint_text  # noqa: E402


def _make_sprite_manager():
    sprite_manager = MagicMock()
    sprite_manager.get.return_value = MagicMock()
    return sprite_manager


def _make_level(number, background="lvl_bg", entities=None):
    """Build a LevelDefinition for GameView wiring tests."""
    from quick_herbalist.core.level_config import LevelDefinition

    if entities is None:
        entities = (
            EntityDefinition("flower", "lvl_flower", 1.0),
            EntityDefinition("stone", "lvl_stone", 3.0, 0.05),
        )
    return LevelDefinition(
        name=f"level{number}",
        background=background,
        distance=1000.0,
        start_speed=3.0,
        max_speed=15.0,
        entities=entities,
    )


def _make_game_view():
    """Build a GameView with mocked dependencies for spawn tests."""
    levels = [_make_level(1)]
    profile_manager = MagicMock(active_character_name="herb", next_level_number=lambda: 1)

    return GameView(profile_manager, _make_sprite_manager(), levels)


def _frame(view):
    """Build the per-frame state the scene hands to entities."""
    return view._frame_state(1.0 / 60)


def _always_overlap(view, overlap=True):
    """Force all hero/entity overlap checks on this view to a fixed answer."""
    view._rects_overlap = lambda a_pos, a_size, b: overlap
    return view


def test_flower_forwards_sprite_manager_and_sprite_name():
    """Flower must pass sprite_manager through to GameEntity unchanged."""
    sprite_manager = _make_sprite_manager()

    flower = Flower(sprite_manager, "dandelion_sprite", SCREEN_W + 50, 10)

    sprite_manager.get.assert_called_once_with("dandelion_sprite")
    assert flower.sprite is sprite_manager.get.return_value
    assert flower.size == (32, 32)
    assert flower.pos == (SCREEN_W + 50, 10)
    assert flower.MAGNETIC is True


def test_stone_forwards_sprite_manager_and_sprite_name():
    """Stone must pass sprite_manager through to GameEntity unchanged."""
    sprite_manager = _make_sprite_manager()

    stone = Stone(sprite_manager, "stone_sprite", SCREEN_W + 100, 20)

    sprite_manager.get.assert_called_once_with("stone_sprite")
    assert stone.sprite is sprite_manager.get.return_value
    assert stone.size == (64, 53)
    assert stone.pos == (SCREEN_W + 100, 20)
    assert stone.MAGNETIC is False


def test_entity_scrolls_with_world_by_default():
    """The default move() scrolls the entity left by the frame's game_speed."""
    view = _make_game_view()
    flower = Flower(_make_sprite_manager(), "lvl_flower", 100, 10)
    view.entities.append(flower)

    view._step_entities(_frame(view))

    # game_speed 3.0 px/frame at start_speed 3.0; entity stays on screen.
    assert flower.x == 100 - 3.0
    assert view.entities == [flower]


# --- Spawning: free-position retries, per-spec widget/sprite ---


def test_spawn_position_rejects_overlapping_spot():
    """_overlaps_entity must detect AABB overlap with a live entity."""
    view = _make_game_view()
    view.entities.append(Stone(_make_sprite_manager(), "lvl_stone", 900, 100))

    # Same spot -> overlap. Shifted just past the stone's edge -> no overlap.
    assert view._overlaps_entity(900, 100, (32, 32)) is True
    assert view._overlaps_entity(900 + 64, 100, (32, 32)) is False
    assert view._overlaps_entity(900, 100 + 53, (32, 32)) is False


def _patched_positions(xs, ys):
    """Patch random.randint: x candidates (lo>0) and y candidates (lo==0)."""
    it_x = iter(xs)
    it_y = iter(ys)

    def fake(lo, hi):
        """Y-range calls always start at 0; x-range calls start at SPAWN_X_MIN > 0."""
        if lo == 0:
            return next(it_y)
        return next(it_x)

    return patch("random.randint", side_effect=fake)


def _spec_for(view, type_name):
    """Return the EntitySpec on the view for the given entity class name."""
    return next(s for s in view._specs if s.cls.__name__.lower() == type_name)


def test_spawn_entity_does_not_overlap_existing_entity():
    """spawning must never place a new entity on top of an existing one."""
    view = _make_game_view()
    view.entities.append(Stone(_make_sprite_manager(), "lvl_stone", SCREEN_W + 120, 100))

    # First candidate lands on the stone; second candidate is free.
    with _patched_positions([120, 150], [100, 200]):
        view._spawn(0, _spec_for(view, "flower"))

    assert len(view.entities) == 2
    flower = view.entities[-1]
    assert isinstance(flower, Flower)
    assert flower.pos == (SCREEN_W + 150, 200)


def test_spawn_skipped_when_all_candidates_overlap():
    """Spawning must skip (no widget, no crash) when every candidate overlaps."""
    xs = [120] * SPAWN_POSITION_RETRIES
    ys = [100] * SPAWN_POSITION_RETRIES

    view = _make_game_view()
    view.entities.append(Stone(_make_sprite_manager(), "lvl_stone", SCREEN_W + 120, 100))
    with _patched_positions(xs, ys):
        view._spawn(0, _spec_for(view, "flower"))
    assert len(view.entities) == 1


def test_unknown_entity_type_raises():
    """A levels.yaml type missing from ENTITY_TYPES fails fast at view build."""
    level = _make_level(1, entities=(EntityDefinition("ghost", "lvl_flower", 1.0),))
    profile_manager = MagicMock(active_character_name="herb", next_level_number=lambda: 1)

    with pytest.raises(ValueError, match="unknown entity type 'ghost'"):
        GameView(profile_manager, _make_sprite_manager(), [level])


# --- Collision outcomes via on_enter ---


def test_collect_hit_adds_score_and_removes_entity():
    """A collected (colliding) flower adds score and harvest, then despawns."""
    view = _make_game_view()
    _always_overlap(view)
    flower = Flower(_make_sprite_manager(), "lvl_flower", 10, 10)
    view.entities.append(flower)

    view._step_entities(_frame(view))

    assert view.rules.score == 1
    assert view.rules.harvest == {"lvl_flower": 1}
    assert view.entities == []


def test_damage_hit_ends_run():
    """A colliding damaging entity ends the run and despawns."""
    view = _make_game_view()
    _always_overlap(view)
    stone = Stone(_make_sprite_manager(), "lvl_stone", 10, 10)
    view.entities.append(stone)

    view._step_entities(_frame(view))

    assert view.rules.dead is True
    assert view.entities == []


def test_offscreen_entity_is_culled():
    """An entity that scrolled off-screen is removed without a collision."""
    view = _make_game_view()
    _always_overlap(view, overlap=False)
    flower = Flower(_make_sprite_manager(), "lvl_flower", -100, 10)
    view.entities.append(flower)

    view._step_entities(_frame(view))

    assert view.entities == []


def test_enter_fires_only_on_overlap_transition():
    """on_enter fires once when overlap starts, not on continuing frames."""
    view = _make_game_view()
    _always_overlap(view)
    flower = Flower(_make_sprite_manager(), "lvl_flower", 10, 10)
    view.entities.append(flower)

    view._step_entities(_frame(view))
    assert view.rules.score == 1

    # Second frame while still overlapping: no second collection.
    flower.done = False
    view.entities.append(flower)
    view._step_entities(_frame(view))
    assert view.rules.score == 1


def test_game_view_uses_level_sprite_names():
    """GameView must request the level's background and entity sprites."""
    levels = [_make_level(1, background="b_bg"), _make_level(2, background="c_bg")]
    profile_manager = MagicMock(active_character_name="herb", next_level_number=lambda: 2)
    sprite_manager = _make_sprite_manager()

    view = GameView(profile_manager, sprite_manager, levels)

    requested = [call.args[0] for call in sprite_manager.get.call_args_list]
    assert "c_bg" in requested  # level 2 background
    assert "b_bg" not in requested

    view._spawn(0, _spec_for(view, "flower"))
    view._spawn(0, _spec_for(view, "stone"))
    requested = [call.args[0] for call in sprite_manager.get.call_args_list]
    assert "lvl_flower" in requested
    assert "lvl_stone" in requested
    assert "dandelion_sprite" not in requested
    assert "stone_sprite" not in requested
    assert "grass_sprite" not in requested


def test_start_game_schedules_spawn_with_bound_spec():
    """start_game must schedule spawns with spec bound, not as extra args.

    Kivy's Clock.schedule_once accepts exactly (callback, delay); passing
    extra positional or keyword args raises TypeError at startup
    (regression test).
    """
    view = _make_game_view()
    kivy_clock_module.Clock.reset_mock()

    view.start_game()

    assert view.active is True
    spawn_calls = kivy_clock_module.Clock.schedule_once.call_args_list
    assert len(spawn_calls) == len(view._specs)
    for call in spawn_calls:
        args, kwargs = call
        assert len(args) == 2
        assert not kwargs
        callback = args[0]
        assert callback.func == view._spawn
        assert set(callback.keywords) == {"spec"}
        assert isinstance(callback.keywords["spec"], EntitySpec)


# --- Spawn pacing (ramp moved from GameRules to SpawnPacer) ---


def test_pacer_constant_without_floor():
    """Without a ramp floor the interval stays constant."""
    pacer = SpawnPacer(2.5)
    for _ in range(50):
        assert pacer.next_delay() == 2.5
    assert pacer.interval == 2.5


def test_pacer_first_delay_is_start_interval():
    """The first spawn waits the full starting interval."""
    pacer = SpawnPacer(3.0, ramp_to=0.05)
    assert pacer.next_delay() == 3.0


def test_pacer_ramps_down_to_floor():
    """Repeated calls decay the interval toward the floor, never below."""
    pacer = SpawnPacer(3.0, ramp_to=0.05)
    for _ in range(1000):
        delay = pacer.next_delay()
        assert delay >= 0.05
    assert pacer.interval == 0.05


def test_pacer_never_increases():
    """Ramping only shrinks the interval; it never grows back."""
    pacer = SpawnPacer(3.0, ramp_to=0.05)
    previous = 3.0
    for _ in range(200):
        delay = pacer.next_delay()
        assert delay <= previous
        previous = delay


# --- Entity types: rock, spider, hill ---


def test_registry_covers_shipped_level_types():
    """Every type used in levels.yaml resolves to a widget class."""
    assert {"flower", "stone", "rock", "spider", "hill"} <= set(ENTITY_TYPES)


def test_rock_is_bigger_stone_that_damages():
    """Rock inherits stone damage but renders pillar-sized."""
    rock = Rock(_make_sprite_manager(), "lvl_stone", 10, 0)
    assert rock.size == (96, 128)

    view = _make_game_view()
    _always_overlap(view)
    view.entities.append(rock)
    view._step_entities(_frame(view))

    assert view.rules.dead is True
    assert view.entities == []


def test_spider_chases_hero_vertically():
    """Spider scrolls at half world speed and steers toward the hero center."""
    view = _make_game_view()
    _always_overlap(view, overlap=False)
    spider = Spider(_make_sprite_manager(), "lvl_stone", 400, view.hero.center_y - 50)
    view.entities.append(spider)

    view._step_entities(_frame(view))

    # world speed 3.0 px/frame * 0.5 scroll factor; chase step 3.0 px/frame
    assert spider.x == 400 - 1.5
    assert spider.y == view.hero.center_y - 50 + 3.0

    # From below the hero it steers upward instead.
    below = Spider(_make_sprite_manager(), "lvl_stone", 400, view.hero.center_y + 100)
    view.entities.append(below)
    view._step_entities(_frame(view))
    assert below.y < view.hero.center_y + 100


def test_spider_stings_on_contact():
    """A spider reaching the hero ends the run and despawns."""
    view = _make_game_view()
    _always_overlap(view)
    spider = Spider(_make_sprite_manager(), "lvl_stone", 10, 10)
    view.entities.append(spider)

    view._step_entities(_frame(view))

    assert view.rules.dead is True
    assert view.entities == []


def test_hill_halves_hero_step_and_survives_overlap():
    """A hill slows the hero while inside it and keeps scrolling, undamaged."""
    view = _make_game_view()
    hill = Hill(_make_sprite_manager(), "lvl_bg", 100, 100)
    hill.overlapping = True
    view.entities.append(hill)
    view.moving_up = True
    start_y = view.hero.y

    view._move_hero(view._frame_state(1.0 / 60))
    assert view.hero.y == start_y + 3.0  # 6 px step halved

    # An overlapping frame does not despawn the hill or damage the hero.
    _always_overlap(view)
    view._step_entities(_frame(view))
    assert view.entities == [hill]
    assert view.rules.dead is False


def test_hero_moves_full_step_without_slowing_entity():
    """Baseline: with no overlapping entity the hero takes the full step."""
    view = _make_game_view()
    view.moving_up = True
    start_y = view.hero.y

    view._move_hero(view._frame_state(1.0 / 60))

    assert view.hero.y == start_y + 6.0


# --- Potion effects (run loadout hotkeys + magnet) ---


def _make_magnet_recipe():
    """Build a real magnetism recipe for effect wiring tests."""
    from quick_herbalist.potions import Recipe

    return Recipe(
        id="potion_magnetism",
        name_key="potion_magnetism_name",
        description_key="potion_magnetism_description",
        ingredients={"dandelion_sprite": 1},
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
    assert isinstance(view._active_effects[0].effect, MagnetEffect)


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
            ingredients={"dandelion_sprite": 1},
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
    """Create the magnet effect bound to the view's hero and live entities."""
    return MagnetEffect(view.hero, view.entities)


def test_magnet_pulls_magnetic_entity_at_edge_of_radius_slowly():
    """A flower 100 px from the player center is pulled ~1 px/tick toward it."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    flower = Flower(_make_sprite_manager(), "lvl_flower", center_x + 100 - 16, center_y - 16)
    view.entities = [flower]

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
    view.entities = [near, below]

    _magnet(view).tick(1.0)
    # dist 50 -> speed 5.5 left; dist 60 -> speed 4.6 up
    assert near.pos[0] == pytest.approx(center_x + 50 - 5.5 - 16)
    assert below.pos[1] == pytest.approx(center_y + 60 - 4.6 - 16)


def test_magnet_ignores_non_magnetic_entities_and_far_flowers():
    """Flowers beyond 100 px and non-magnetic entities (stones) are untouched."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    far = Flower(_make_sprite_manager(), "lvl_flower", center_x + 150 - 16, center_y - 16)
    stone = Stone(_make_sprite_manager(), "lvl_stone", center_x + 50 - 32, center_y - 53)
    view.entities = [far, stone]

    _magnet(view).tick(1.0)
    assert far.pos == (center_x + 150 - 16, center_y - 16)
    assert stone.pos == (center_x + 50 - 32, center_y - 53)


def test_magnet_pull_scales_with_frame_factor():
    """Pull distance per call scales with the dt-based frame factor."""
    view = _make_effect_view()
    px, py = view.hero.pos
    center_x, center_y = px + view.hero.size[0] / 2, py + view.hero.size[1] / 2
    flower = Flower(_make_sprite_manager(), "lvl_flower", center_x + 100 - 16, center_y - 16)
    view.entities = [flower]

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


# --- First-seen tutorial hints ---


def _view_with_hint_mocks():
    """Build a GameView whose profile manager behaves like the real hint API."""
    view = _make_game_view()
    view.profile_manager.hints_enabled.return_value = True
    view.profile_manager.get_seen_entities.return_value = []
    return view


def test_entity_type_names_match_registry():
    """Every registered entity class carries the TYPE name used in levels.yaml."""
    assert {cls.TYPE for cls in ENTITY_TYPES.values()} == set(ENTITY_TYPES)


def test_new_entities_start_untriggered():
    """Each spawned instance gets its own one-shot hint trigger flag, off."""
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W + 100, 10)
    assert stone.hint_triggered is False


def test_hint_triggers_at_100px_into_viewport():
    """An unseen entity past the trigger line queues, shows, and is marked seen."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)

    view._check_hints()

    assert view.hint_active is True
    assert view._hint_queue == []
    view.profile_manager.mark_entity_seen.assert_called_once_with("stone")
    assert stone.hint_triggered is True


def test_hint_not_triggered_before_line():
    """An entity still inside the HINT_TRIGGER_DEPTH band shows no hint."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 99, 10)
    view.entities.append(stone)

    view._check_hints()

    assert view.hint_active is False
    view.profile_manager.mark_entity_seen.assert_not_called()
    assert stone.hint_triggered is False


def test_hint_is_one_shot_per_instance():
    """A triggered instance never re-queues, even if it re-enters the band."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)

    view._check_hints()
    view._close_hint_box()
    stone.pos = (SCREEN_W - 100, 10)
    view._check_hints()

    assert view.profile_manager.mark_entity_seen.call_count == 1
    assert view.hint_active is False


def test_hint_skipped_for_seen_type():
    """A type already in the character's seen-set never shows its hint."""
    view = _view_with_hint_mocks()
    view.profile_manager.get_seen_entities.return_value = ["stone"]
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)

    view._check_hints()

    assert view.hint_active is False
    view.profile_manager.mark_entity_seen.assert_not_called()


def test_hints_disabled_shows_nothing():
    """show_hints=False short-circuits the whole hint check."""
    view = _view_with_hint_mocks()
    view.profile_manager.hints_enabled.return_value = False
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)

    view._check_hints()

    assert view.hint_active is False
    view.profile_manager.mark_entity_seen.assert_not_called()
    assert stone.hint_triggered is False


def test_same_frame_batch_shows_hints_in_sequence():
    """Two unseen types crossing in one frame queue both, shown one after the other."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    hill = Hill(_make_sprite_manager(), "hill_sprite", SCREEN_W - 100, 200)
    view.entities.extend([stone, hill])

    view._check_hints()

    assert view.hint_active is True
    assert view._hint_queue == [("hill", "hill_sprite")]  # stone box open, hill queued
    assert view.profile_manager.mark_entity_seen.call_count == 2

    view._close_hint_box()  # opens the queued hill box
    assert view.hint_active is True
    assert view._hint_queue == []

    view._close_hint_box()  # queue drained, run resumes
    assert view.hint_active is False


def test_update_skipped_while_hint_open():
    """The run is fully paused while a hint box is on screen."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)
    view._check_hints()
    assert view.hint_active is True

    stone.pos = (stone.x - 5, stone.y)
    x_before = stone.x
    view.update(1.0 / 60)

    assert stone.x == x_before  # entity did not move
    assert view.hint_active is True


def test_spawn_deferred_while_hint_open():
    """A spawn due while a hint box pauses the run is deferred, not dropped.

    Dropping it killed the spawn chain for that entity type forever (empty
    levels after the first hint). Deferring keeps the chain alive and the
    spawn fires on the next poll after the box closes.
    """
    view = _view_with_hint_mocks()
    view._hint_box = object()

    view._spawn(1.0 / 60, view._specs[0])

    assert view.entities == []
    # Chain alive: one deferred poll scheduled, not a dead chain.
    assert len(view._spawn_events) == 1

    view._hint_box = None  # hint closed
    view._spawn(1.0 / 60, view._specs[0])

    assert len(view.entities) == 1  # deferred spawn fired
    assert len(view._spawn_events) == 2  # normal next spawn also scheduled


def test_keyboard_closes_hint_box():
    """Esc/Enter/Space dismiss the box; other keys are swallowed while it is open."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)
    view._check_hints()

    assert view.on_keyboard_down("w") is True  # movement dead, box stays
    assert view.hint_active is True
    assert view.moving_up is False

    assert view.on_keyboard_down("spacebar") is True
    assert view.hint_active is False


def test_keyboard_escape_closes_hint_box():
    """Kivy names the Esc key 'escape'; it must dismiss the hint box."""
    view = _view_with_hint_mocks()
    stone = Stone(_make_sprite_manager(), "stone_sprite", SCREEN_W - 100, 10)
    view.entities.append(stone)
    view._check_hints()
    assert view.hint_active is True

    assert view.on_keyboard_down("escape") is True
    assert view.hint_active is False


def test_stop_game_closes_open_hint():
    """Leaving the run clears any open hint box and its queue."""
    view = _view_with_hint_mocks()
    view._hint_queue = [("hill", "hill_sprite")]
    view._open_hint_box()
    assert view.hint_active is True

    view.stop_game()

    assert view.hint_active is False
    assert view._hint_queue == []


def test_hint_box_has_solid_background():
    """Hint box must paint a solid background covering the whole box rect."""
    box = HintBox(_make_sprite_manager(), "stone_sprite", "Stone", "desc", on_close=lambda: None)

    assert box.bg_rect == box.box_rect
    assert _BG[3] == 1.0  # solid, not translucent


def test_hint_box_outside_touch_swallowed():
    """A touch outside the box is consumed without dismissing (cross only)."""
    from types import SimpleNamespace

    closed = []
    box = HintBox(
        _make_sprite_manager(), "stone_sprite", "Stone", "desc", on_close=lambda: closed.append(1)
    )

    assert box.on_touch_down(SimpleNamespace(pos=(10, 10))) is True
    assert closed == []


def test_hint_box_closes_on_cross_touch():
    """A touch of the cross button in the upper-right corner dismisses the hint."""
    from types import SimpleNamespace

    closed = []
    box = HintBox(
        _make_sprite_manager(), "stone_sprite", "Stone", "desc", on_close=lambda: closed.append(1)
    )
    cx, cy = box.close_rect[0] + 10, box.close_rect[1] + 10

    assert box.on_touch_down(SimpleNamespace(pos=(cx, cy))) is True
    assert len(closed) == 1


def test_hint_box_inside_touch_swallowed():
    """A touch inside the box is consumed without dismissing."""
    from types import SimpleNamespace

    closed = []
    box = HintBox(
        _make_sprite_manager(), "stone_sprite", "Stone", "desc", on_close=lambda: closed.append(1)
    )
    mid = (box.box_rect[0] + 50, box.box_rect[1] + 50)

    assert box.on_touch_down(SimpleNamespace(pos=mid)) is True
    assert closed == []


def test_game_view_touch_goes_to_child_first():
    """GameView.on_touch_down must let a child consume the touch before movement.

    Regression: without the super() call the whole child subtree (HintBox
    included) is starved of touches, because Kivy dispatches to children only
    inside the default Widget.on_touch_down.
    """
    from types import SimpleNamespace

    view = _make_game_view()
    received = []

    class SwallowingChild(RealWidget):
        def on_touch_down(self, touch):
            received.append(touch.pos)
            return True

    view.add_widget(SwallowingChild())
    touch = SimpleNamespace(pos=(42, 42), y=42)

    assert view.on_touch_down(touch) is True
    assert received == [(42, 42)]
    assert view.touch_active is False


def test_game_view_touch_still_moves_without_child():
    """With no consuming child, GameView takes over for hero movement."""
    from types import SimpleNamespace

    view = _make_game_view()
    view.children.clear()
    touch = SimpleNamespace(pos=(7, 33), y=33)

    assert view.on_touch_down(touch) is True
    assert view.touch_active is True
    assert view.target_y == 33


def test_hint_text_covers_all_entity_types():
    """Every registered entity type has a title and a non-empty description."""
    for entity_type in ENTITY_TYPES:
        title, description = hint_text(entity_type)
        assert title and description
        assert hint_text(entity_type) == ENTITY_HINTS[entity_type]


def test_hud_labels_added_as_children():
    """All four HUD labels must be added as children of the hud widget.

    Kivy only renders widgets that are in the canvas tree. The labels used
    to be created without add_widget, leaving the whole HUD invisible during
    a run (blank score/distance/character counters).
    """
    from quick_herbalist.game.hud import GameHud

    hud = GameHud()

    assert len(hud.children) == 4
    assert hud.score_label in hud.children
    assert hud.distance_label in hud.children
    assert hud.effect_label in hud.children
    assert hud.char_label in hud.children
