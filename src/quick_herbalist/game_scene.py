"""Game scene widgets: background, player, obstacles, and the GameView."""

import logging
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Rectangle
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from quick_herbalist.core.sprite_manager import SpriteManager
from quick_herbalist.localization import _

logger = logging.getLogger(__name__)

sprite_manager = SpriteManager()


class Background(Widget):
    """Animated background with scrolling tiles."""

    def __init__(self, **kwargs):
        """Initialize background with grass tiles."""
        super().__init__(**kwargs)
        self.tile_width = 128
        self.tile_height = 128
        self.cols = int(800 / self.tile_width) + 2
        self.rows = int(600 / self.tile_height) + 1

        self.tiles = []

        # Retrieve grass texture region from SpriteManager
        grass_sprite = sprite_manager.get("grass_sprite")
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
                same_row_tiles = [
                    t for t in self.tiles if abs(t["pos"][1] - tile["pos"][1]) < 1
                ]
                max_x = max(t["pos"][0] for t in same_row_tiles)
                tile["pos"][0] = max_x + self.tile_width

        for tile in self.tiles:
            tile["rect"].pos = (tile["pos"][0], tile["pos"][1])


class Player(Widget):
    """Player character widget."""

    def __init__(self, **kwargs):
        """Initialize player with hero sprite."""
        super().__init__(**kwargs)
        self.size = (64, 64)
        self.pos = (800 // 8 - 32, 600 // 2 - 32)

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
        elif new_y + self.height > 600:
            new_y = 600 - self.height
        self.y = new_y


class MovingWidget(Widget):
    """Base class for moving game objects."""

    def __init__(self, sprite_name, size, x, y, **kwargs):
        """Initialize moving widget with sprite."""
        super().__init__(**kwargs)
        self.size = size
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

    def __init__(self, **kwargs):
        """Initialize flower at random position."""
        x = 800 + random.randint(50, 200)
        y = random.randint(0, 600 - 32)
        super().__init__("flower_sprite", (32, 32), x, y, **kwargs)


class Stone(MovingWidget):
    """Stone object that causes game over."""

    def __init__(self, **kwargs):
        """Initialize stone at random position."""
        x = 800 + random.randint(100, 300)
        y = random.randint(0, 600 - 64)
        super().__init__("stone_sprite", (64, 53), x, y, **kwargs)


class GameView(Widget):
    """Game view widget managing the game scene."""

    def __init__(self, **kwargs):
        """Initialize game view with widgets and labels."""
        super().__init__(**kwargs)
        self.active = True

        app = App.get_running_app()
        if app and hasattr(app, "profile_manager") and app.profile_manager:
            self.win_distance = app.profile_manager.settings.get("win_distance", 1000.0)
            self.game_speed = app.profile_manager.settings.get("game_speed_start", 3.0)
        else:
            self.win_distance = 1000.0
            self.game_speed = 3.0

        self.max_speed = 15.0  # Cap game speed to prevent unbounded growth
        self.score = 0
        self.distance = 0.0
        self.stone_interval = 3.0

        self.flowers = []
        self.stones = []

        self.moving_up = False
        self.moving_down = False
        self.touch_active = False
        self.target_y = 0

        self.background = Background()
        self.add_widget(self.background)

        self.hero = Player()
        self.add_widget(self.hero)

        self.score_label = Label(
            text="",
            font_size=24,
            color=(0, 0, 0, 1),
            pos=(10, 560),
            size=(200, 30),
            halign="left",
            valign="middle",
        )
        self.score_label.bind(size=self.score_label.setter("text_size"))
        self.add_widget(self.score_label)

        self.distance_label = Label(
            text="",
            font_size=24,
            color=(0, 0, 0, 1),
            pos=(10, 520),
            size=(200, 30),
            halign="left",
            valign="middle",
        )
        self.distance_label.bind(size=self.distance_label.setter("text_size"))
        self.add_widget(self.distance_label)

        # HUD Active Character Name Label
        self.char_label = Label(
            text="",
            font_size=24,
            color=(0, 0, 0, 1),
            pos=(590, 560),
            size=(200, 30),
            halign="right",
            valign="middle",
        )
        self.char_label.bind(size=self.char_label.setter("text_size"))
        self.add_widget(self.char_label)

        self.update_labels()

    def start_game(self):
        """Start the game loop and spawning timers."""
        Clock.schedule_interval(self.update, 1.0 / 60)
        Clock.schedule_interval(self.spawn_flower, 1.0)
        self.schedule_next_stone()

    def stop_game(self):
        """Stop the game loop and all timers."""
        self.active = False
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_flower)
        Clock.unschedule(self.spawn_stone)

    def spawn_flower(self, dt):
        """Spawn a flower at a random position."""
        if not self.active:
            return
        flower = Flower()
        self.add_widget(flower)
        self.flowers.append(flower)

    def schedule_next_stone(self):
        """Schedule the next stone spawn."""
        Clock.schedule_once(self.spawn_stone, self.stone_interval)

    def spawn_stone(self, dt):
        """Spawn a stone and schedule the next one."""
        if not self.active:
            return
        stone = Stone()
        self.add_widget(stone)
        self.stones.append(stone)

        if self.stone_interval > 0.05:
            self.stone_interval -= random.randint(0, 50) / 1000.0
            if self.stone_interval < 0.05:
                self.stone_interval = 0.05

        self.schedule_next_stone()

    def update_labels(self):
        """Update score, distance, and character name labels."""
        app = App.get_running_app()
        active_name = (
            app.profile_manager.active_character_name
            if app and hasattr(app, "profile_manager") and app.profile_manager
            else None
        )
        self.char_label.text = (
            str(active_name) if active_name else _("No Active Character")
        )
        self.score_label.text = _("Collected: ") + str(self.score)
        self.distance_label.text = _("Distance: ") + str(int(self.distance))

    def update(self, dt):
        """Update game state each frame."""
        if not self.active:
            return

        frame_factor = dt * 60
        self.hero.animate(dt)

        self.game_speed = min(self.game_speed + 0.001 * frame_factor, self.max_speed)
        self.distance += (self.game_speed / 10) * frame_factor

        # Check Win Condition
        if self.distance >= self.win_distance:
            self.game_won()
            return

        self.background.update(self.game_speed * frame_factor)

        # Player Movement Y
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

        for flower in self.flowers[:]:
            alive = flower.update(self.game_speed * frame_factor)
            if not alive:
                self.remove_widget(flower)
                self.flowers.remove(flower)
            elif self.hero.collide_widget(flower):
                self.score += 1
                self.remove_widget(flower)
                self.flowers.remove(flower)

        for stone in self.stones[:]:
            alive = stone.update(self.game_speed * frame_factor)
            if not alive:
                self.remove_widget(stone)
                self.stones.remove(stone)
            elif self.hero.collide_widget(stone):
                self.game_over()

        self.update_labels()

    def game_over(self):
        """Handle game over: stop game and show game over screen."""
        self.stop_game()
        app = App.get_running_app()
        go_screen = app.root.get_screen("game_over")
        go_screen.score = self.score
        go_screen.distance = self.distance
        app.root.current = "game_over"

    def game_won(self):
        """Handle win: stop game, update profile, show win screen."""
        self.stop_game()
        app = App.get_running_app()
        if app and hasattr(app, "profile_manager") and app.profile_manager:
            try:
                app.profile_manager.complete_level()
                app.profile_manager.add_flowers(self.score)
            except Exception as e:
                logger.error("Failed to save profile on win: %s", e)
        won_screen = app.root.get_screen("game_won")
        won_screen.score = self.score
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
        """Handle keyboard key down for player movement."""
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


