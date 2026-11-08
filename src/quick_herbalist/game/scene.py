"""Game scene: GameView orchestrating background, hero, entities, HUD, effects."""

import logging
import math
import random
from dataclasses import dataclass

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from quick_herbalist.core.level_config import level_for
from quick_herbalist.game.entities import Flower, Stone
from quick_herbalist.game.effects import ActiveEffect, EFFECT_FACTORIES
from quick_herbalist.game.hud import GameHud
from quick_herbalist.game.widgets import Background, Player, SCREEN_H, SCREEN_W
from quick_herbalist.game_rules import GameRules
from quick_herbalist.localization import _

logger = logging.getLogger(__name__)

# Max random spawn retries before a spawn is skipped.
SPAWN_POSITION_RETRIES = 10


@dataclass(frozen=True)
class EntitySpec:
    """One spawnable entity type of a level: widget class, pacing, hit outcome.

    hit is "collect" (adds to the score) or "damage" (ends the run).
    Adding a new entity type = a MovingWidget subclass plus one EntitySpec
    built from the level definition in GameView.
    """

    key: str
    widget_cls: type
    sprite: str
    interval: float
    hit: str


class GameView(Widget):
    """Game view widget managing the game scene for one level definition."""

    def __init__(
        self, profile_manager, sprite_manager, levels, level_number=None, recipes=None, **kwargs
    ):
        """Initialize game view with widgets, labels, and the level definition."""
        super().__init__(**kwargs)
        self.active = True
        self.profile_manager = profile_manager
        self.sprite_manager = sprite_manager
        self.recipes = list(recipes or [])
        if level_number is None:
            level_number = profile_manager.next_level_number()
        self.level_number = level_number
        self.level = level_for(levels, self.level_number)
        self.rules = GameRules(
            win_distance=self.level.distance,
            start_speed=self.level.start_speed,
            max_speed=self.level.max_speed,
            stone_interval=self.level.stone.interval,
            stone_interval_min=self.level.stone.ramp_to,
        )

        self._specs = (
            EntitySpec(
                key="flower",
                widget_cls=Flower,
                sprite=self.level.flower.sprite,
                interval=self.level.flower.interval,
                hit="collect",
            ),
            EntitySpec(
                key="stone",
                widget_cls=Stone,
                sprite=self.level.stone.sprite,
                interval=self.level.stone.interval,
                hit="damage",
            ),
        )
        # One stable list per entity key; run effects may hold list references.
        self.entities = {spec.key: [] for spec in self._specs}

        self.moving_up = False
        self.moving_down = False
        self.touch_active = False
        self.target_y = 0
        self._active_effects: list[ActiveEffect] = []

        self.background = Background(self.sprite_manager, self.level.background)
        self.add_widget(self.background)

        self.hero = Player(self.sprite_manager)
        self.add_widget(self.hero)

        self.hud = GameHud()
        self.add_widget(self.hud)

        self._update_hud()

    @property
    def active_effects(self):
        """Active potion effects as (potion_id, remaining) pairs."""
        return [(effect.potion_id, effect.remaining) for effect in self._active_effects]

    def start_game(self):
        """Start the game loop and all entity spawn timers."""
        Clock.schedule_interval(self.update, 1.0 / 60)
        for spec in self._specs:
            Clock.schedule_once(self._spawn, self._next_spawn_delay(spec), spec)

    def stop_game(self):
        """Stop the game loop and all spawn timers."""
        self.active = False
        Clock.unschedule(self.update)
        Clock.unschedule(self._spawn)

    def _next_spawn_delay(self, spec):
        """Return the delay before the next spawn of this entity type.

        Stones ramp their interval down through the rules; other types keep
        a fixed interval.
        """
        if spec.key == "stone":
            return self.rules.next_stone_interval()
        return spec.interval

    def _spawn_position(self, cls):
        """Pick a random spawn position that does not overlap live entities.

        Returns (x, y) or None if no free spot is found after retries.
        """
        for _attempt in range(SPAWN_POSITION_RETRIES):
            x = SCREEN_W + random.randint(cls.SPAWN_X_MIN, cls.SPAWN_X_MAX)
            y = random.randint(0, SCREEN_H - cls.SIZE[1])
            if not self._overlaps_entity(x, y, cls.SIZE):
                return x, y
        return None

    def _overlaps_entity(self, x, y, size):
        """Return True if the given rectangle overlaps any live entity."""
        for entity in (e for entities in self.entities.values() for e in entities):
            ex, ey = entity.pos
            ew, eh = entity.size
            if x < ex + ew and x + size[0] > ex and y < ey + eh and y + size[1] > ey:
                return True
        return False

    def _spawn(self, dt, spec):
        """Spawn one entity of the given type at a free position, then reschedule."""
        if not self.active:
            return
        position = self._spawn_position(spec.widget_cls)
        if position is None:
            logger.warning("No free spawn position for %s, skipping spawn", spec.key)
        else:
            entity = spec.widget_cls(self.sprite_manager, spec.sprite, *position)
            self.add_widget(entity)
            self.entities[spec.key].append(entity)

        Clock.schedule_once(self._spawn, self._next_spawn_delay(spec), spec)

    def _update_entities(self, spec, speed):
        """Advance one entity type: move, cull off-screen, resolve collisions."""
        for entity in self.entities[spec.key][:]:
            if not entity.update(speed):
                self.remove_widget(entity)
                self.entities[spec.key].remove(entity)
                continue
            if self.hero.collide_widget(entity):
                self._on_entity_hit(spec)
                self.remove_widget(entity)
                self.entities[spec.key].remove(entity)

    def _on_entity_hit(self, spec):
        """Apply the entity's hit outcome: collect adds score, damage ends the run."""
        if spec.hit == "collect":
            self.rules.on_flower_hit()
        else:
            self.rules.on_stone_hit()
            self.game_over()

    def _move_hero(self, frame_factor):
        """Move the hero from the keyboard state or the touch target."""
        step = 0.01 * 600 * frame_factor
        if self.touch_active:
            diff_y = self.target_y - self.hero.center_y
            if abs(diff_y) > 2:
                if diff_y > 0:
                    self.hero.move_by(min(step, diff_y))
                else:
                    self.hero.move_by(-min(step, abs(diff_y)))
        else:
            if self.moving_up:
                self.hero.move_by(step)
            elif self.moving_down:
                self.hero.move_by(-step)

    def _use_slot(self, slot_index):
        """Use the potion in the given run slot, activating its timed effect."""
        loadout = self.profile_manager.get_run_loadout()
        potion_id = loadout[slot_index]
        if potion_id is None:
            return
        recipe = next((r for r in self.recipes if r.id == potion_id), None)
        if recipe is None:
            logger.warning("No recipe found for potion '%s', effect skipped", potion_id)
            return
        factory = EFFECT_FACTORIES.get(potion_id)
        if factory is None:
            logger.warning("No effect registered for potion '%s', no in-run effect", potion_id)
        self.profile_manager.use_run_slot(slot_index)
        self._active_effects.append(
            ActiveEffect(
                potion_id=potion_id,
                remaining=recipe.duration_seconds,
                effect=factory(self) if factory is not None else None,
            )
        )

    def _step_effects(self, dt, frame_factor):
        """Advance active potion effects: countdown, tick handlers, drop expired."""
        for effect in self._active_effects:
            effect.remaining -= dt
        self._active_effects = [effect for effect in self._active_effects if effect.remaining > 0]
        for effect in self._active_effects:
            if effect.effect is not None:
                effect.effect.tick(frame_factor)
        self.hud.set_effects(self._effect_lines())

    def _effect_lines(self):
        """Build HUD effect lines: each active effect with whole seconds left."""
        lines = []
        for effect in self._active_effects:
            recipe = next((r for r in self.recipes if r.id == effect.potion_id), None)
            name = _(recipe.name_key) if recipe else effect.potion_id
            lines.append(f"{name} {math.ceil(effect.remaining)}")
        return lines

    def _update_hud(self):
        """Refresh all HUD labels from the current run state."""
        self.hud.set_character(self.profile_manager.active_character_name, self.level_number)
        self.hud.set_score(self.rules.score)
        self.hud.set_distance(self.rules.distance)

    def update(self, dt):
        """Update game state each frame."""
        if not self.active:
            return

        frame_factor = dt * 60
        self.hero.animate(dt)

        # Check Win Condition
        if self.rules.step(dt):
            self.game_won()
            return

        self.background.update(self.rules.game_speed * frame_factor)

        self._move_hero(frame_factor)

        self._step_effects(dt, frame_factor)

        for spec in self._specs:
            self._update_entities(spec, self.rules.game_speed * frame_factor)

        self._update_hud()

    def game_over(self):
        """Handle game over: stop game and show game over screen."""
        self.stop_game()
        app = App.get_running_app()
        go_screen = app.root.get_screen("game_over")
        go_screen.score = self.rules.score
        go_screen.distance = self.rules.distance
        app.root.current = "game_over"

    def game_won(self):
        """Handle win: stop game, update profile, show win screen."""
        self.stop_game()
        try:
            self.profile_manager.complete_level()
            self.profile_manager.add_flowers(self.level.flower.sprite, self.rules.score)
        except Exception as e:
            logger.error("Failed to save profile on win: %s", e)
        app = App.get_running_app()
        won_screen = app.root.get_screen("game_won")
        won_screen.score = self.rules.score
        won_screen.harvest = {self.level.flower.sprite: self.rules.score}
        app.root.current = "game_won"

    def on_touch_down(self, touch):
        """Handle touch down for touch-based movement."""
        self.touch_active = True
        self.target_y = touch.y
        return True

    def on_touch_move(self, touch):
        """Handle touch move for touch-based movement."""
        if self.touch_active:
            self.target_y = touch.y
        return True

    def on_touch_up(self, touch):
        """Handle touch up to stop touch-based movement."""
        self.touch_active = False
        return True

    def on_keyboard_down(self, key):
        """Handle keyboard key down for player movement and potion slots."""
        if key in ("1", "2", "3"):
            self._use_slot(int(key) - 1)
            return True
        if key in ("up", "w"):
            self.moving_up = True
            return True
        elif key in ("down", "s"):
            self.moving_down = True
            return True
        return False

    def on_keyboard_up(self, key):
        """Handle keyboard key up for player movement."""
        if key in ("up", "w"):
            self.moving_up = False
            return True
        elif key in ("down", "s"):
            self.moving_down = False
            return True
        return False
