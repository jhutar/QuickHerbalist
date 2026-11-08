"""Moving entity widgets for the game scene.

A new entity type (e.g. a moving hazard or bonus pickup) is a MovingWidget
subclass with its own SIZE and SPAWN_X window; the scene spawns and updates
any such class generically through EntitySpec in game.scene.
"""

from kivy.uix.widget import Widget


class MovingWidget(Widget):
    """Base class for moving game objects.

    Subclasses define SIZE and the SPAWN_X_MIN/SPAWN_X_MAX horizontal spawn
    window in pixels beyond the right screen edge.
    """

    SIZE = (32, 32)
    SPAWN_X_MIN = 0
    SPAWN_X_MAX = 100

    def __init__(self, sprite_manager, sprite_name, x, y, **kwargs):
        """Initialize moving widget with a sprite from the given SpriteManager."""
        super().__init__(**kwargs)
        self.size = self.SIZE
        self.pos = (x, y)

        self.sprite = sprite_manager.get(sprite_name)
        self.sprite.pos = self.pos
        self.sprite.size = self.size
        self.add_widget(self.sprite)

        self.bind(pos=self.update_sprite_pos)

    def update_sprite_pos(self, *args):
        """Sync sprite position with widget position."""
        self.sprite.pos = self.pos

    def update(self, game_speed):
        """Update horizontal position and check if off-screen."""
        self.x -= game_speed
        if self.x + self.width < 0:
            return False
        return True


class Flower(MovingWidget):
    """Flower object to be collected."""

    SIZE = (32, 32)
    SPAWN_X_MIN = 50
    SPAWN_X_MAX = 200


class Stone(MovingWidget):
    """Stone object that causes game over."""

    SIZE = (64, 53)
    SPAWN_X_MIN = 100
    SPAWN_X_MAX = 300
