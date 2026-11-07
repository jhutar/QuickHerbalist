"""Pure game rules: distance, speed growth, score, stone pacing, win/lose outcomes."""

import random

# Rates converted from the original 60 fps per-frame constants (0.001 and
# speed/10 per frame) to per-second rates, so behavior is identical at any fps.
SPEED_GROWTH_PER_SECOND = 0.06
DISTANCE_PER_SPEED_SECOND = 6.0
# Random per-spawn decay step (seconds) applied while a stone interval ramps
# down toward its level's floor.
STONE_RAMP_STEP = 0.05


class GameRules:
    """Stateful run rules: distance, speed, score, and win/lose outcomes.

    Pure Python with no Kivy imports so the logic is testable headless.
    A fresh instance is a fresh run; there is no explicit reset method.
    """

    def __init__(
        self,
        win_distance,
        start_speed,
        max_speed=15.0,
        stone_interval=3.0,
        stone_interval_min=None,
    ):
        """Create a run with win distance, starting speed, speed cap, and stone pacing.

        stone_interval_min is the interval floor for the in-level stone ramp;
        None means no ramp (interval stays constant at stone_interval).
        """
        self.win_distance = win_distance
        self.max_speed = max_speed
        self.game_speed = start_speed
        self.distance = 0.0
        self.score = 0
        self.dead = False
        self.stone_interval = stone_interval
        self.stone_interval_min = (
            stone_interval_min if stone_interval_min is not None else stone_interval
        )

    def step(self, dt):
        """Advance the run by dt seconds; return True once win distance is reached."""
        self.game_speed = min(self.game_speed + SPEED_GROWTH_PER_SECOND * dt, self.max_speed)
        self.distance += self.game_speed * DISTANCE_PER_SPEED_SECOND * dt
        return self.distance >= self.win_distance

    def next_stone_interval(self):
        """Return the delay before the next stone, then decay the interval.

        Each call shrinks the interval by a random 0..STONE_RAMP_STEP seconds,
        clamped to stone_interval_min; a floor equal to the start value means
        the interval never changes.
        """
        delay = self.stone_interval
        self.stone_interval = max(
            self.stone_interval - random.uniform(0.0, STONE_RAMP_STEP),
            self.stone_interval_min,
        )
        return delay

    def on_flower_hit(self):
        """Register a collected flower and return the new score."""
        self.score += 1
        return self.score

    def on_stone_hit(self):
        """Register a stone collision; the run is lost."""
        self.dead = True
