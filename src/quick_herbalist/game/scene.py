"""Game scene: GameView orchestrating background, hero, entities, HUD, effects."""

import logging
import math
import random
from dataclasses import dataclass, field
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget

from quick_herbalist.core.level_config import level_for
from quick_herbalist.game.effects import EFFECT_FACTORIES, ActiveEffect
from quick_herbalist.game.entities import ENTITY_TYPES, FrameState, GameEntity
from quick_herbalist.game.hints import HintBox, hint_text
from quick_herbalist.game.hud import GameHud
from quick_herbalist.game.widgets import SCREEN_W, Background, Player
from quick_herbalist.game_rules import GameRules
from quick_herbalist.localization import _

logger = logging.getLogger(__name__)

# Max random spawn retries before a spawn is skipped.
SPAWN_POSITION_RETRIES = 10
# Random per-spawn decay step (seconds) applied while an interval ramps
# down toward its level's floor.
RAMP_STEP = 0.05
# How many px an entity must be inside the right viewport edge before its
# first-seen tutorial hint fires.
HINT_TRIGGER_DEPTH = 100
# Keys that dismiss an open hint box (Kivy key names, see kivy.core.window
# keycodes: Esc is 'escape', Space is 'spacebar').
HINT_CLOSE_KEYS = ("escape", "enter", "spacebar")
# Poll interval (seconds) a spawn waits in while a hint box pauses the run.
HINT_SPAWN_POLL = 0.1


class SpawnPacer:
    """Current spawn interval for one entity type, with an optional ramp.

    Each next_delay() call returns the current interval and, when a ramp
    floor is set, shrinks it by a random 0..RAMP_STEP seconds toward the
    floor. A pacer without a floor yields a constant interval.
    """

    def __init__(self, interval, ramp_to=None):
        """Create a pacer; ramp_to None means the interval never changes."""
        self.interval = interval
        self.ramp_to = ramp_to

    def next_delay(self):
        """Return the current interval, then shrink it toward the floor if set."""
        delay = self.interval
        if self.ramp_to is not None:
            self.interval = max(
                self.interval - random.uniform(0.0, RAMP_STEP),
                self.ramp_to,
            )
        return delay


@dataclass(frozen=True)
class EntitySpec:
    """One spawnable entity type of a level: widget class, sprite, pacing."""

    cls: type[GameEntity]
    sprite: str
    pacer: SpawnPacer = field(compare=False)


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
        )

        self._specs = self._build_specs()
        self.entities: list[GameEntity] = []
        self._spawn_events: list = []

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

        self._hint_queue: list[tuple[str, str]] = []
        self._hint_box: HintBox | None = None

        self._update_hud()

    def _build_specs(self):
        """Resolve the level's entity definitions into spawnable specs.

        Raises ValueError on an entity type missing from ENTITY_TYPES.
        """
        specs = []
        for definition in self.level.entities:
            cls = ENTITY_TYPES.get(definition.type)
            if cls is None:
                raise ValueError(
                    f"unknown entity type '{definition.type}' in level '{self.level.name}'; "
                    f"registered types: {sorted(ENTITY_TYPES)}"
                )
            specs.append(
                EntitySpec(
                    cls=cls,
                    sprite=definition.sprite,
                    pacer=SpawnPacer(definition.interval, definition.ramp_to),
                )
            )
        return tuple(specs)

    @property
    def hint_active(self):
        """True while a tutorial hint box is on screen (run paused)."""
        return self._hint_box is not None

    @property
    def active_effects(self):
        """Active potion effects as (potion_id, remaining) pairs."""
        return [(effect.potion_id, effect.remaining) for effect in self._active_effects]

    def _schedule_spawn(self, spec):
        """Schedule the next spawn for one spec; returns the clock event.

        Kivy's schedule_once does not forward extra callback arguments, so
        the spec is bound via functools.partial.
        """
        return Clock.schedule_once(partial(self._spawn, spec=spec), spec.pacer.next_delay())

    def start_game(self):
        """Start the game loop and all entity spawn timers."""
        self._spawn_events = [self._schedule_spawn(spec) for spec in self._specs]
        Clock.schedule_interval(self.update, 1.0 / 60)

    def stop_game(self):
        """Stop the game loop, all spawn timers, and any open hint box."""
        self.active = False
        self._close_hint_box()
        self._hint_queue = []
        Clock.unschedule(self.update)
        for event in self._spawn_events:
            Clock.unschedule(event.callback)
        self._spawn_events = []

    def _spawn_position(self, cls):
        """Pick a random spawn position that does not overlap live entities.

        Returns (x, y) or None if no free spot is found after retries.
        """
        for _attempt in range(SPAWN_POSITION_RETRIES):
            x = SCREEN_W + random.randint(cls.SPAWN_X_MIN, cls.SPAWN_X_MAX)
            y = cls.random_spawn_y()
            if not self._overlaps_entity(x, y, cls.SIZE):
                return x, y
        return None

    def _overlaps_entity(self, x, y, size):
        """Return True if the given rectangle overlaps any live entity."""
        for entity in self.entities:
            if self._rects_overlap((x, y), size, entity):
                return True
        return False

    @staticmethod
    def _rects_overlap(a_pos, a_size, b):
        """Return True if the (pos, size) rectangle overlaps widget b's rectangle."""
        ax, ay = a_pos
        bx, by = b.pos
        return (
            ax < bx + b.size[0]
            and ax + a_size[0] > bx
            and ay < by + b.size[1]
            and ay + a_size[1] > by
        )

    def _spawn(self, dt, spec):
        """Spawn one entity of the given type at a free position, then reschedule.

        A spawn due while a hint box pauses the run is deferred (re-polled
        until the box closes), never dropped: dropping it would kill the
        whole spawn chain for that entity type for the rest of the run.
        """
        if not self.active:
            return
        if self.hint_active:
            self._spawn_events.append(
                Clock.schedule_once(partial(self._spawn, spec=spec), HINT_SPAWN_POLL)
            )
            return
        position = self._spawn_position(spec.cls)
        if position is None:
            logger.warning("No free spawn position for %s, skipping spawn", spec.cls.__name__)
        else:
            entity = spec.cls(self.sprite_manager, spec.sprite, *position)
            self.add_widget(entity)
            self.entities.append(entity)

        if self.active and not self.hint_active:
            self._spawn_events.append(self._schedule_spawn(spec))

    def _frame_state(self, dt):
        """Build the per-frame data handed to entities."""
        return FrameState(
            game_speed=self.rules.game_speed * dt * 60,
            frame_factor=dt * 60,
            hero=self.hero,
            rules=self.rules,
        )

    def _step_entities(self, frame):
        """Advance all live entities: move, detect overlap, resolve, cull."""
        for entity in self.entities[:]:
            entity.move(frame)
            now = self._rects_overlap(self.hero.pos, self.hero.size, entity)
            if now and not entity.overlapping:
                entity.on_enter(frame)
            entity.overlapping = now
            if entity.done or entity.is_offscreen:
                self.remove_widget(entity)
                self.entities.remove(entity)

    def _move_hero(self, frame):
        """Move the hero from the keyboard state or the touch target.

        Movement speed is scaled by the min hero_speed_factor of all
        overlapping entities (e.g. a hill the hero is standing in).
        """
        factor = min(
            (entity.hero_speed_factor() for entity in self.entities if entity.overlapping),
            default=1.0,
        )
        step = 0.01 * 600 * frame.frame_factor * factor
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

    def _check_hints(self):
        """Queue hints for every unseen entity type that crossed the trigger line.

        An instance crosses once its left edge is HINT_TRIGGER_DEPTH px inside
        the right viewport edge. Seen types (and already-triggered instances)
        are skipped. The profile is marked at queue time, never at close time.
        """
        if not self.profile_manager.hints_enabled():
            return
        seen = set(self.profile_manager.get_seen_entities())
        queue = []
        for entity in self.entities:
            if entity.hint_triggered or entity.x > SCREEN_W - HINT_TRIGGER_DEPTH:
                continue
            entity.hint_triggered = True
            if entity.TYPE in seen:
                continue
            seen.add(entity.TYPE)
            queue.append((entity.TYPE, entity.sprite_name))
        if not queue:
            return
        for entity_type, _sprite in queue:
            self.profile_manager.mark_entity_seen(entity_type)
        self._hint_queue = queue
        self._open_hint_box()

    def _open_hint_box(self):
        """Pop the next queued hint and show it, pausing the run."""
        if not self._hint_queue:
            return
        entity_type, sprite_name = self._hint_queue.pop(0)
        title, description = hint_text(entity_type)
        box = HintBox(
            self.sprite_manager, sprite_name, title, description, on_close=self._close_hint_box
        )
        self.add_widget(box)
        self._hint_box = box

    def _close_hint_box(self):
        """Dismiss the open hint box; open the next queued one or resume the run."""
        if self._hint_box is None:
            return
        self.remove_widget(self._hint_box)
        self._hint_box = None
        self._open_hint_box()

    def update(self, dt):
        """Update game state each frame."""
        if not self.active or self.hint_active:
            return

        self.hero.animate(dt)

        # Check Win Condition
        if self.rules.step(dt):
            self.game_won()
            return

        frame = self._frame_state(dt)

        self._step_entities(frame)
        if self.rules.dead:
            self.game_over()
            return

        self._check_hints()

        self.background.update(frame.game_speed)

        self._move_hero(frame)

        self._step_effects(dt, frame.frame_factor)

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
        """Handle win: stop game, persist the per-sprite harvest, show win screen."""
        self.stop_game()
        try:
            self.profile_manager.complete_level()
            for sprite, count in self.rules.harvest.items():
                self.profile_manager.add_flowers(sprite, count)
        except Exception as e:
            logger.error("Failed to save profile on win: %s", e)
        app = App.get_running_app()
        won_screen = app.root.get_screen("game_won")
        won_screen.score = self.rules.score
        won_screen.harvest = dict(self.rules.harvest)
        app.root.current = "game_won"

    def on_touch_down(self, touch):
        """Propagate touch to children first; handle movement only if no child consumed it.

        Calling super() is required: without it this override starves the whole
        child subtree (hud, HintBox, ...) of all touches, because Kivy's child
        dispatch loop lives in the default Widget.on_touch_down.
        """
        if super().on_touch_down(touch):
            return True
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
        if self.hint_active:
            if key in HINT_CLOSE_KEYS:
                self._close_hint_box()
            return True  # all game input is dead while a hint is on screen
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
