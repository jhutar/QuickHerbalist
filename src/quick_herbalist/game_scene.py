"""Game scene widgets: background, player, obstacles, and the GameView."""

import logging
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Rectangle
from kivy.uix.label import Label
from kivy.uix.widget import Widget

from quick_herbalist.core.level_config import level_for
from quick_herbalist.game_rules import GameRules
from quick_herbalist.localization import _

logger = logging.getLogger(__name__)

SCREEN_W = 800
SCREEN_H = 600
SPAWN_POSITION_RETRIES = 10


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


class MovingWidget(Widget):
    """Base class for moving game objects."""

    def __init__(self, sprite_manager, sprite_name, size, x, y, **kwargs):
        """Initialize moving widget with a sprite from the given SpriteManager."""
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

    SIZE = (32, 32)
    SPAWN_X_MIN = 50
    SPAWN_X_MAX = 200

    def __init__(self, sprite_manager, sprite_name, x, y, **kwargs):
        """Initialize flower at the given position using the level's flower sprite."""
        super().__init__(sprite_manager, sprite_name, self.SIZE, x, y, **kwargs)


class Stone(MovingWidget):
    """Stone object that causes game over."""

    SIZE = (64, 53)
    SPAWN_X_MIN = 100
    SPAWN_X_MAX = 300

    def __init__(self, sprite_manager, sprite_name, x, y, **kwargs):
        """Initialize stone at the given position using the level's stone sprite."""
        super().__init__(sprite_manager, sprite_name, self.SIZE, x, y, **kwargs)


class GameView(Widget):
    """Game view widget managing the game scene for one level definition."""

    def __init__(self, profile_manager, sprite_manager, levels, level_number=None, **kwargs):
        """Initialize game view with widgets, labels, and the level definition."""
        super().__init__(**kwargs)
        self.active = True
        self.profile_manager = profile_manager
        self.sprite_manager = sprite_manager
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

        self.flowers = []
        self.stones = []

        self.moving_up = False
        self.moving_down = False
        self.touch_active = False
        self.target_y = 0

        self.background = Background(self.sprite_manager, self.level.background)
        self.add_widget(self.background)

        self.hero = Player(self.sprite_manager)
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
        Clock.schedule_interval(self.spawn_flower, self.level.flower.interval)
        self.schedule_next_stone()

    def stop_game(self):
        """Stop the game loop and all timers."""
        self.active = False
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_flower)
        Clock.unschedule(self.spawn_stone)

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
        """Return True if the given rectangle overlaps any live flower or stone."""
        for entity in self.flowers + self.stones:
            ex, ey = entity.pos
            ew, eh = entity.size
            if x < ex + ew and x + size[0] > ex and y < ey + eh and y + size[1] > ey:
                return True
        return False

    def spawn_flower(self, dt):
        """Spawn a flower at a random position that does not overlap existing entities."""
        if not self.active:
            return
        position = self._spawn_position(Flower)
        if position is None:
            logger.warning("No free spawn position for flower, skipping spawn")
            return
        flower = Flower(self.sprite_manager, self.level.flower.sprite, *position)
        self.add_widget(flower)
        self.flowers.append(flower)

    def schedule_next_stone(self):
        """Schedule the next stone spawn using the rules' pacing."""
        Clock.schedule_once(self.spawn_stone, self.rules.next_stone_interval())

    def spawn_stone(self, dt):
        """Spawn a stone at a free position and schedule the next one."""
        if not self.active:
            return
        position = self._spawn_position(Stone)
        if position is None:
            logger.warning("No free spawn position for stone, skipping spawn")
        else:
            stone = Stone(self.sprite_manager, self.level.stone.sprite, *position)
            self.add_widget(stone)
            self.stones.append(stone)

        self.schedule_next_stone()

    def update_labels(self):
        """Update score, distance, level, and character name labels."""
        active_name = self.profile_manager.active_character_name
        name = active_name if active_name else _("No Active Character")
        self.char_label.text = f"{name}  {_('Level: ')}{self.level_number}"
        self.score_label.text = _("Collected: ") + str(self.rules.score)
        self.distance_label.text = _("Distance: ") + str(int(self.rules.distance))

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
            alive = flower.update(self.rules.game_speed * frame_factor)
            if not alive:
                self.remove_widget(flower)
                self.flowers.remove(flower)
            elif self.hero.collide_widget(flower):
                self.rules.on_flower_hit()
                self.remove_widget(flower)
                self.flowers.remove(flower)

        for stone in self.stones[:]:
            alive = stone.update(self.rules.game_speed * frame_factor)
            if not alive:
                self.remove_widget(stone)
                self.stones.remove(stone)
            elif self.hero.collide_widget(stone):
                self.rules.on_stone_hit()
                self.game_over()

        self.update_labels()

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
