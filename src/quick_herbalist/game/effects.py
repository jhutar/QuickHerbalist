"""In-run potion effects: base class, implementations, and the id registry.

Adding a new potion effect = one RunEffect subclass plus one entry in
EFFECT_FACTORIES keyed by the potion id from recipes.yaml.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass


class RunEffect:
    """Base class for a timed in-run potion effect; subclasses implement tick()."""

    def tick(self, frame_factor):
        """Advance the effect by one frame (frame_factor = dt * 60)."""


class MagnetEffect(RunEffect):
    """Pull live magnetic entities toward the player while within its radius."""

    RADIUS = 100.0
    MIN_SPEED = 1.0
    MAX_SPEED = 10.0

    def __init__(self, hero, entities):
        """Bind the effect to the hero widget and the live entity list."""
        self.hero = hero
        self.entities = entities

    def tick(self, frame_factor):
        """Pull each magnetic entity within RADIUS toward the hero center."""
        hx, hy = self.hero.pos
        hw, hh = self.hero.size
        px, py = hx + hw / 2, hy + hh / 2
        for entity in self.entities:
            if not entity.MAGNETIC:
                continue
            ex, ey = entity.pos
            ew, eh = entity.size
            dx = px - (ex + ew / 2)
            dy = py - (ey + eh / 2)
            dist = math.hypot(dx, dy)
            if dist == 0 or dist > self.RADIUS:
                continue
            speed = self.MAX_SPEED - (self.MAX_SPEED - self.MIN_SPEED) * dist / self.RADIUS
            entity.pos = (
                ex + dx / dist * speed * frame_factor,
                ey + dy / dist * speed * frame_factor,
            )


@dataclass
class ActiveEffect:
    """One running potion effect: id, seconds left, and its tick object (or None)."""

    potion_id: str
    remaining: float
    effect: RunEffect | None


def _make_magnet(view):
    """Create the magnetism effect bound to the given GameView."""
    return MagnetEffect(view.hero, view.entities)


# Registry: potion id -> factory(GameView) -> RunEffect.
EFFECT_FACTORIES: dict[str, Callable] = {"potion_magnetism": _make_magnet}
