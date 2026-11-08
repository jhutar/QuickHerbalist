"""In-run potion effects: base class, implementations, and the id registry.

Adding a new potion effect = one RunEffect subclass plus one entry in
EFFECT_FACTORIES keyed by the potion id from recipes.yaml.
"""

import math
from dataclasses import dataclass
from typing import Callable


class RunEffect:
    """Base class for a timed in-run potion effect; subclasses implement tick()."""

    def tick(self, frame_factor):
        """Advance the effect by one frame (frame_factor = dt * 60)."""


class MagnetEffect(RunEffect):
    """Pull live flowers toward the player while within its radius."""

    RADIUS = 100.0
    MIN_SPEED = 1.0
    MAX_SPEED = 10.0

    def __init__(self, hero, flowers):
        """Bind the effect to the hero widget and the live flower list."""
        self.hero = hero
        self.flowers = flowers

    def tick(self, frame_factor):
        """Pull each flower within RADIUS toward the hero center."""
        hx, hy = self.hero.pos
        hw, hh = self.hero.size
        px, py = hx + hw / 2, hy + hh / 2
        for flower in self.flowers:
            fx, fy = flower.pos
            fw, fh = flower.size
            dx = px - (fx + fw / 2)
            dy = py - (fy + fh / 2)
            dist = math.hypot(dx, dy)
            if dist == 0 or dist > self.RADIUS:
                continue
            speed = self.MAX_SPEED - (self.MAX_SPEED - self.MIN_SPEED) * dist / self.RADIUS
            flower.pos = (
                fx + dx / dist * speed * frame_factor,
                fy + dy / dist * speed * frame_factor,
            )


@dataclass
class ActiveEffect:
    """One running potion effect: id, seconds left, and its tick object (or None)."""

    potion_id: str
    remaining: float
    effect: RunEffect | None


def _make_magnet(view):
    """Create the magnetism effect bound to the given GameView."""
    return MagnetEffect(view.hero, view.entities["flower"])


# Registry: potion id -> factory(GameView) -> RunEffect.
EFFECT_FACTORIES: dict[str, Callable] = {"potion_magnetism": _make_magnet}
