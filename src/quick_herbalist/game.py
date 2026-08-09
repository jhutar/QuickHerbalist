import gettext
import logging
import os
import random

# Kivy setup (force window size before other imports)
from kivy.config import Config

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "600")
Config.set("graphics", "resizable", "0")

from kivy.app import App  # noqa: E402
from kivy.uix.screenmanager import ScreenManager, Screen  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.uix.button import Button  # noqa: E402
from quick_herbalist.profiles import ProfileManager  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.graphics import Rectangle  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.lang import Builder  # noqa: E402

logger = logging.getLogger(__name__)

# --- Správa cest k prostředkům (assets / locales) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


from quick_herbalist.core.sprite_manager import SpriteManager  # noqa: E402

sprite_manager = SpriteManager()


def get_asset_path(filename):
    """Return absolute path to an asset file."""
    return os.path.join(BASE_DIR, "assets", filename)


def get_locales_dir():
    """Return absolute path to the locales directory."""
    return os.path.join(BASE_DIR, "locales")


# --- Inicializace lokalizace
gettext.bindtextdomain("base", get_locales_dir())
gettext.textdomain("base")
_ = gettext.gettext


class KeyboardScreen(Screen):
    """Base screen class with keyboard support."""

    def on_enter(self):
        """Handle screen entry and request keyboard."""
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(
            on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
        )

    def on_leave(self):
        """Handle screen exit and unbind keyboard."""
        if self._keyboard:
            self._keyboard.unbind(
                on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
            )
            self._keyboard = None

    def _keyboard_closed(self):
        """Callback when keyboard is closed."""
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle key down event."""
        return False

    def _on_keyboard_up(self, keyboard, keycode):
        """Handle key up event."""
        return False


class MenuScreen(KeyboardScreen):
    """Main menu screen."""

    def on_pre_enter(self):
        """Initialize menu labels and buttons before entering."""
        app = App.get_running_app()
        self.ids.title.text = _("Quick Herbalist")
        self.ids.subtitle.text = _("Press 's' to start")
        active_name = app.profile_manager.active_character_name
        self.ids.active_char_lbl.text = _("Active Character: ") + (
            active_name if active_name else _("None")
        )
        self.ids.start_btn.text = _("Start Game")
        self.ids.new_btn.text = _("New Character")
        self.ids.load_btn.text = _("Load Character")
        self.ids.potions_btn.text = _("Create Potions")
        self.ids.quit_btn.text = _("Quit")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle menu keyboard shortcuts."""
        key = keycode[1]
        if key == "s":
            self.start_game()
            return True
        elif key == "n":
            self.manager.current = "new_character"
            return True
        elif key == "l":
            self.manager.current = "load_character"
            return True
        elif key == "c":
            self.manager.current = "potions"
            return True
        elif key in ("escape", "q"):
            App.get_running_app().stop()
            return True
        return False

    def start_game(self):
        """Switch to game screen."""
        self.manager.current = "game"


class NewCharacterScreen(Screen):
    """Screen for creating a new character."""

    def on_pre_enter(self):
        """Initialize character creation UI."""
        self.ids.title.text = _("Enter Character Name")
        self.ids.name_input.text = ""
        self.ids.error_label.text = ""
        self.ids.confirm_btn.text = _("Confirm")

        app = App.get_running_app()
        if app.profile_manager.active_character_name is None:
            self.ids.back_btn.opacity = 0
            self.ids.back_btn.disabled = True
            self.ids.back_btn.text = ""
        else:
            self.ids.back_btn.opacity = 1
            self.ids.back_btn.disabled = False
            self.ids.back_btn.text = _("Back to Menu")

    def confirm(self):
        """Create new character with input name."""
        app = App.get_running_app()
        name = self.ids.name_input.text
        try:
            app.profile_manager.create_character(name)
            self.manager.current = "menu"
        except ValueError as e:
            err_msg = str(e)
            if "Name cannot be empty" in err_msg:
                self.ids.error_label.text = _("Name cannot be empty.")
            elif "Character already exists" in err_msg:
                self.ids.error_label.text = _("Character already exists.")
            else:
                self.ids.error_label.text = _(err_msg)

    def back_to_menu(self):
        """Return to main menu."""
        self.manager.current = "menu"


class LoadCharacterScreen(KeyboardScreen):
    """Screen for loading existing characters."""

    def on_pre_enter(self):
        """Populate character list before entering."""
        self.ids.title.text = _("Select Character")
        self.ids.back_btn.text = _("Back to Menu")

        self.ids.list_layout.clear_widgets()

        app = App.get_running_app()
        for name in app.profile_manager.characters.keys():
            btn = Button(text=name, size_hint_y=None, height=50, font_size=18)
            btn.bind(on_release=self.select_and_return)
            self.ids.list_layout.add_widget(btn)

    def select_and_return(self, btn):
        """Select character and return to menu."""
        app = App.get_running_app()
        app.profile_manager.select_character(btn.text)
        self.manager.current = "menu"

    def back_to_menu(self):
        """Return to main menu."""
        self.manager.current = "menu"

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for load screen."""
        key = keycode[1]
        if key in ("escape", "q"):
            self.back_to_menu()
            return True
        return False


class GameWonScreen(KeyboardScreen):
    """Screen shown when level is completed."""

    score = 0

    def on_pre_enter(self):
        """Initialize level completion UI."""
        self.ids.title.text = _("LEVEL COMPLETED!")
        self.ids.score_lbl.text = _("Collected Flowers: ") + str(self.score)
        self.ids.restart_btn.text = _("Play Again")
        self.ids.menu_btn.text = _("Main Menu")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for win screen."""
        key = keycode[1]
        if key in ("escape", "q"):
            self.manager.current = "menu"
            return True
        return False

    def restart_game(self):
        """Restart game."""
        self.manager.current = "game"

    def goto_menu(self):
        """Go to main menu."""
        self.manager.current = "menu"


class PotionsScreen(KeyboardScreen):
    """Screen for potion crafting (placeholder)."""

    def on_pre_enter(self):
        """Initialize potions screen UI."""
        self.ids.title.text = _("Potion Crafting")
        self.ids.desc.text = _(
            "Placeholder Screen: Future crafting system will be here!"
        )
        self.ids.back_btn.text = _("Back to Menu")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for potions screen."""
        key = keycode[1]
        if key in ("escape", "q"):
            self.manager.current = "menu"
            return True
        return False


class QuitScreen(KeyboardScreen):
    """Screen asking user if they want to quit."""

    def on_pre_enter(self):
        """Initialize quit confirmation UI."""
        self.ids.title.text = _("Do you want to quit?")
        self.ids.cont_lbl.text = _("Press 's' to continue")
        self.ids.quit_lbl.text = _("Press 'q' to quit")
        self.ids.resume_btn.text = _("Continue")
        self.ids.quit_btn.text = _("Quit")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for quit screen."""
        key = keycode[1]
        if key == "s":
            self.resume_game()
            return True
        elif key in ("escape", "q"):
            App.get_running_app().stop()
            return True
        return False

    def resume_game(self):
        """Return to game."""
        self.manager.current = "game"


class GameOverScreen(KeyboardScreen):
    """Screen shown when player hits a stone."""

    score = 0
    distance = 0

    def on_pre_enter(self):
        """Initialize game over UI."""
        self.ids.title.text = _("GAME OVER!")
        self.ids.score_lbl.text = _("Collected: ") + str(self.score)
        self.ids.distance_lbl.text = _("Distance: ") + str(int(self.distance))
        self.ids.restart_btn.text = _("Play Again")
        self.ids.menu_btn.text = _("Main Menu")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for game over screen."""
        key = keycode[1]
        if key in ("escape", "q"):
            App.get_running_app().stop()
            return True
        return False

    def restart_game(self):
        """Restart game."""
        self.manager.current = "game"

    def goto_menu(self):
        """Go to main menu."""
        self.manager.current = "menu"


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


class GameScreen(Screen):
    """Screen displaying the game view."""

    def on_enter(self):
        """Initialize game view and request keyboard on entry."""
        self.game_view = GameView()
        self.add_widget(self.game_view)
        self.game_view.start_game()

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(
            on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
        )

    def on_leave(self):
        """Stop game and release keyboard on leave."""
        if self._keyboard:
            self._keyboard.unbind(
                on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up
            )
            self._keyboard = None
        self.game_view.stop_game()
        self.remove_widget(self.game_view)

    def _keyboard_closed(self):
        """Callback when keyboard is closed."""
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle keyboard shortcuts for the game screen."""
        key = keycode[1]
        if key in ("escape", "q"):
            self.manager.current = "quit"
            return True
        return self.game_view.on_keyboard_down(key)

    def _on_keyboard_up(self, keyboard, keycode):
        """Handle keyboard key up events."""
        key = keycode[1]
        return self.game_view.on_keyboard_up(key)


Builder.load_string("""
<MenuScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 40
        spacing: 15
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: active_char_lbl
            font_size: 22
            color: 0.8, 0.8, 0.2, 1
        Label:
            id: subtitle
            font_size: 20
            color: 1, 1, 1, 1
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.15
            Button:
                id: start_btn
                font_size: 18
                on_release: root.start_game()
            Button:
                id: potions_btn
                font_size: 18
                on_release: root.manager.current = 'potions'
        BoxLayout:
            orientation: 'horizontal'
            spacing: 10
            size_hint_y: 0.15
            Button:
                id: new_btn
                font_size: 18
                on_release: root.manager.current = 'new_character'
            Button:
                id: load_btn
                font_size: 18
                on_release: root.manager.current = 'load_character'
        Button:
            id: quit_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 18
            on_release: app.stop()

<NewCharacterScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 32
            color: 1, 1, 1, 1
        TextInput:
            id: name_input
            multiline: False
            font_size: 24
            size_hint: (0.6, 0.25)
            pos_hint: {'center_x': 0.5}
        Label:
            id: error_label
            font_size: 20
            color: 1, 0, 0, 1
        Button:
            id: confirm_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.confirm()
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.back_to_menu()

<LoadCharacterScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 32
            color: 1, 1, 1, 1
            size_hint_y: 0.2
        ScrollView:
            size_hint_y: 0.6
            BoxLayout:
                id: list_layout
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 10
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.back_to_menu()

<GameWonScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 50
            color: 0.2, 0.8, 0.2, 1
        Label:
            id: score_lbl
            font_size: 28
            color: 1, 1, 1, 1
        Button:
            id: restart_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.restart_game()
        Button:
            id: menu_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.goto_menu()

<PotionsScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: desc
            font_size: 24
            color: 0.7, 0.7, 0.7, 1
        Button:
            id: back_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.manager.current = 'menu'

<QuitScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: cont_lbl
            font_size: 24
            color: 1, 1, 1, 1
        Label:
            id: quit_lbl
            font_size: 24
            color: 1, 1, 1, 1
        Button:
            id: resume_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.resume_game()
        Button:
            id: quit_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: app.stop()

<GameOverScreen>:
    canvas.before:
        Color:
            rgb: 0, 0, 0
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 50
            color: 1, 1, 1, 1
        Label:
            id: score_lbl
            font_size: 28
            color: 1, 1, 1, 1
        Label:
            id: distance_lbl
            font_size: 28
            color: 1, 1, 1, 1
        Button:
            id: restart_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.restart_game()
        Button:
            id: menu_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.goto_menu()
""")


class QuickHerbalistApp(App):
    """Main application for Quick Herbalist game."""

    def build(self):
        """Build the app with screen manager and all screens."""
        self.profile_manager = ProfileManager()

        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(NewCharacterScreen(name="new_character"))
        sm.add_widget(LoadCharacterScreen(name="load_character"))
        sm.add_widget(PotionsScreen(name="potions"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(GameWonScreen(name="game_won"))
        sm.add_widget(QuitScreen(name="quit"))
        sm.add_widget(GameOverScreen(name="game_over"))

        # Skip main menu and redirect directly to "new_character" if no active character exists
        if self.profile_manager.active_character_name is None:
            sm.current = "new_character"
        else:
            sm.current = "menu"

        return sm


def main():
    """Entry point: run the Quick Herbalist app."""
    QuickHerbalistApp().run()


if __name__ == "__main__":
    main()
