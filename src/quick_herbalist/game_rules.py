"""Pure game rules: distance, speed growth, score, and win/lose outcomes."""

# Rates converted from the original 60 fps per-frame constants (0.001 and
# speed/10 per frame) to per-second rates, so behavior is identical at any fps.
SPEED_GROWTH_PER_SECOND = 0.06
DISTANCE_PER_SPEED_SECOND = 6.0


class GameRules:
    """Stateful run rules: distance, speed, score, and win/lose outcomes.

    Pure Python with no Kivy imports so the logic is testable headless.
    A fresh instance is a fresh run; there is no explicit reset method.
    """

    def __init__(self, win_distance, start_speed, max_speed=15.0):
        """Create a run with win distance, starting speed, and speed cap."""
        self.win_distance = win_distance
        self.max_speed = max_speed
        self.game_speed = start_speed
        self.distance = 0.0
        self.score = 0
        self.dead = False

    def step(self, dt):
        """Advance the run by dt seconds; return True once win distance is reached."""
        self.game_speed = min(self.game_speed + SPEED_GROWTH_PER_SECOND * dt, self.max_speed)
        self.distance += self.game_speed * DISTANCE_PER_SPEED_SECOND * dt
        return self.distance >= self.win_distance

    def on_flower_hit(self):
        """Register a collected flower and return the new score."""
        self.score += 1
        return self.score

    def on_stone_hit(self):
        """Register a stone collision; the run is lost."""
        self.dead = True
