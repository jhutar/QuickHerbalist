"""Spawnable game entities and the registry mapping level types to classes.

Adding a new entity kind (bigger rocks, chasing spiders, slowing hills) is:
  1. a GameEntity subclass overriding whatever it needs (size, spawn window,
     move(), on_enter(), hero_speed_factor(), MAGNETIC)
  2. one entry in ENTITY_TYPES
  3. entries in a level's entities list in levels.yaml

The scene spawns and steps every registered type the same way.
"""

import random
from dataclasses import dataclass

from kivy.uix.widget import Widget

from quick_herbalist.game.widgets import SCREEN_H
from quick_herbalist.game_rules import GameRules


@dataclass(frozen=True)
class FrameState:
    """Per-frame data the scene hands to entities so they need no view access."""

    game_speed: float  # world scroll distance for this frame, in px
    frame_factor: float  # dt * 60, for fps-independent custom motion
    hero: Widget
    rules: GameRules


class GameEntity(Widget):
    """Base class for all spawnable entities: size, spawn window, and hooks.

    Subclass overrides:
      SIZE, SPAWN_X_MIN, SPAWN_X_MAX   size and horizontal spawn window (px past the right edge)
      random_spawn_y()                 vertical spawn placement (full-height pillars return 0)
      move(frame)                      per-frame motion (default: scroll left with the world)
      on_enter(frame)                  one-shot reaction when overlap with the hero starts
      hero_speed_factor()              hero movement multiplier while overlapping (default 1.0)
      MAGNETIC                         pulled toward the hero by the magnetism potion
      done                             set True to be removed after the interaction
    """

    TYPE = None  # entity type name used in levels.yaml and the hint system
    SIZE = (32, 32)
    SPAWN_X_MIN = 0
    SPAWN_X_MAX = 100
    MAGNETIC = False

    def __init__(self, sprite_manager, sprite_name, x, y, **kwargs):
        """Create the entity at (x, y) with the named sprite."""
        super().__init__(**kwargs)
        self.size = self.SIZE
        self.pos = (x, y)
        self.sprite_name = sprite_name
        self.done = False
        self.overlapping = False
        self.hint_triggered = False  # one-shot tutorial-hint trigger, per instance

        self.sprite = sprite_manager.get(sprite_name)
        self.sprite.pos = self.pos
        self.sprite.size = self.size
        self.add_widget(self.sprite)

        self.bind(pos=self.update_sprite_pos)

    @classmethod
    def random_spawn_y(cls):
        """Pick a random y for a spawn; override for fixed vertical placement."""
        return random.randint(0, SCREEN_H - cls.SIZE[1])

    def move(self, frame):
        """Advance one frame; default scrolls left with the world."""
        self.x -= frame.game_speed

    def on_enter(self, frame):
        """React once when overlap with the hero starts; default: nothing."""

    def hero_speed_factor(self):
        """Multiplier on hero movement speed while this entity overlaps; default: none."""
        return 1.0

    @property
    def is_offscreen(self):
        """True once the entity has fully left the playfield."""
        return self.x + self.width < 0

    def update_sprite_pos(self, *args):
        """Sync sprite position with widget position."""
        self.sprite.pos = self.pos


class Flower(GameEntity):
    """Flower object collected for score and the run harvest."""

    TYPE = "flower"
    SIZE = (32, 32)
    SPAWN_X_MIN = 50
    SPAWN_X_MAX = 200
    MAGNETIC = True

    def on_enter(self, frame):
        """Score the flower, add it to the harvest, and despawn it."""
        frame.rules.on_collected(self.sprite_name)
        self.done = True


class Stone(GameEntity):
    """Stone object that ends the run on contact."""

    TYPE = "stone"
    SIZE = (64, 53)
    SPAWN_X_MIN = 100
    SPAWN_X_MAX = 300

    def on_enter(self, frame):
        """Damage the hero: end the run and despawn the stone."""
        frame.rules.on_damaged()
        self.done = True


class Rock(Stone):
    """Bigger stone (pillar-sized) that ends the run on contact."""

    TYPE = "rock"
    SIZE = (96, 128)


class Spider(GameEntity):
    """Crawling hazard: scrolls at a quarter of world speed and chases the
    hero vertically; stings (ends the run) on contact."""

    TYPE = "spider"
    SIZE = (32, 32)
    SPAWN_X_MIN = 50
    SPAWN_X_MAX = 200
    CHASE_SPEED = 2.0  # px/frame at 60 fps; hero can outrun it
    SCROLL_FACTOR = 0.25  # scrolls at a share of the world speed

    def move(self, frame):
        """Scroll with the world and steer vertically toward the hero."""
        self.x -= frame.game_speed * self.SCROLL_FACTOR
        dy = frame.hero.center_y - self.center_y
        step = self.CHASE_SPEED * frame.frame_factor
        self.y += max(-step, min(step, dy))

    def on_enter(self, frame):
        """Sting the hero: end the run and despawn the spider."""
        frame.rules.on_damaged()
        self.done = True


class Hill(GameEntity):
    """Large mound the hero passes through; slows hero movement while inside.

    Non-lethal: it never despawns on contact and scrolls off-screen like
    any other entity.
    """

    TYPE = "hill"
    SIZE = (64, 32)
    SPAWN_X_MIN = 100
    SPAWN_X_MAX = 300
    SPEED_FACTOR = 0.5

    def hero_speed_factor(self):
        """Halve the hero's movement speed while overlapping the hill."""
        return self.SPEED_FACTOR


# Entity type names usable in levels.yaml -> widget class.
ENTITY_TYPES: dict[str, type[GameEntity]] = {
    "flower": Flower,
    "stone": Stone,
    "rock": Rock,
    "spider": Spider,
    "hill": Hill,
}
