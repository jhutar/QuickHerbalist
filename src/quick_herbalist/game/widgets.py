"""Scene widgets: scrolling background and the player hero."""

from kivy.graphics import Rectangle
from kivy.uix.widget import Widget

# Fixed logical playfield size (window is non-resizable, see app.py).
SCREEN_W = 800
SCREEN_H = 600


class Background(Widget):
    """Animated background with scrolling tiles."""

    def __init__(self, sprite_manager, background_sprite, **kwargs):
        """Initialize background with the level's grass tile sprite."""
        super().__init__(**kwargs)
        self.tile_width = 128
        self.tile_height = 128
        self.cols = int(SCREEN_W / self.tile_width) + 2
        self.rows = int(SCREEN_H / self.tile_height) + 1

        self.tiles = []

        # Retrieve grass texture region from SpriteManager
        grass_sprite = sprite_manager.get(background_sprite)
        grass_texture = grass_sprite.rect.texture

        with self.canvas:
            for r in range(self.rows):
                for c in range(self.cols):
                    x = c * self.tile_width
                    y = r * self.tile_height
                    rect = Rectangle(
                        texture=grass_texture,
                        pos=(x, y),
                        size=(self.tile_width, self.tile_height),
                    )
                    self.tiles.append({"pos": [x, y], "rect": rect})

    def update(self, game_speed):
        """Update tile positions for scrolling effect."""
        for tile in self.tiles:
            tile["pos"][0] -= game_speed

        for tile in self.tiles:
            if tile["pos"][0] <= -self.tile_width:
                same_row_tiles = [t for t in self.tiles if abs(t["pos"][1] - tile["pos"][1]) < 1]
                max_x = max(t["pos"][0] for t in same_row_tiles)
                tile["pos"][0] = max_x + self.tile_width

        for tile in self.tiles:
            tile["rect"].pos = (tile["pos"][0], tile["pos"][1])


class Player(Widget):
    """Player character widget."""

    def __init__(self, sprite_manager, **kwargs):
        """Initialize player with hero sprite from the given SpriteManager."""
        super().__init__(**kwargs)
        self.size = (64, 64)
        self.pos = (SCREEN_W // 8 - 32, SCREEN_H // 2 - 32)

        self.sprite = sprite_manager.get("hero_sprite")
        self.sprite.pos = self.pos
        self.sprite.size = self.size
        self.add_widget(self.sprite)

        self.bind(pos=self.update_sprite_pos)

    def update_sprite_pos(self, *args):
        """Sync sprite position with widget position."""
        self.sprite.pos = self.pos

    def animate(self, dt):
        """Handle player animation (stub)."""
        # Frame animation is handled autonomously by AnimatedSprite
        pass

    def move_by(self, dy):
        """Move player vertically within bounds."""
        new_y = self.y + dy
        if new_y < 0:
            new_y = 0
        elif new_y + self.height > SCREEN_H:
            new_y = SCREEN_H - self.height
        self.y = new_y
