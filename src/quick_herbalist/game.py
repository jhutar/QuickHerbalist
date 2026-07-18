import os
import random
import gettext

# Kivy setup (force window size before other imports)
from kivy.config import Config

Config.set("graphics", "width", "800")
Config.set("graphics", "height", "600")
Config.set("graphics", "resizable", "0")

from kivy.app import App  # noqa: E402
from kivy.uix.screenmanager import ScreenManager, Screen  # noqa: E402
from kivy.uix.widget import Widget  # noqa: E402
from kivy.uix.label import Label  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.graphics import Rectangle  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.lang import Builder  # noqa: E402

# --- Správa cest k prostředkům (assets / locales) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_asset_path(filename):
    return os.path.join(BASE_DIR, "assets", filename)


def get_locales_dir():
    return os.path.join(BASE_DIR, "locales")


# --- Inicializace lokalizace
gettext.bindtextdomain("base", get_locales_dir())
gettext.textdomain("base")
_ = gettext.gettext


class KeyboardScreen(Screen):
    def on_enter(self):
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def on_leave(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None

    def _keyboard_closed(self):
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        return False


class MenuScreen(KeyboardScreen):
    def on_pre_enter(self):
        self.ids.title.text = _("Quick Herbalist")
        self.ids.subtitle.text = _("Press 's' for start")
        self.ids.start_btn.text = _("Start Game")
        self.ids.quit_btn.text = _("Quit")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key == "s":
            self.start_game()
            return True
        elif key in ("escape", "q"):
            App.get_running_app().stop()
            return True
        return False

    def start_game(self):
        self.manager.current = "game"


class QuitScreen(KeyboardScreen):
    def on_pre_enter(self):
        self.ids.title.text = _("Do you want to quit?")
        self.ids.cont_lbl.text = _("Press 's' to continue")
        self.ids.quit_lbl.text = _("Press 'q' to quit")
        self.ids.resume_btn.text = _("Continue")
        self.ids.quit_btn.text = _("Quit")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key == "s":
            self.resume_game()
            return True
        elif key in ("escape", "q"):
            App.get_running_app().stop()
            return True
        return False

    def resume_game(self):
        self.manager.current = "game"


class GameOverScreen(KeyboardScreen):
    score = 0
    distance = 0

    def on_pre_enter(self):
        self.ids.title.text = _("GAME OVER!")
        self.ids.score_lbl.text = _("Collected: ") + str(self.score)
        self.ids.distance_lbl.text = _("Distance: ") + str(int(self.distance))
        self.ids.restart_btn.text = _("Play Again")
        self.ids.menu_btn.text = _("Main Menu")

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key in ("escape", "q"):
            App.get_running_app().stop()
            return True
        return False

    def restart_game(self):
        self.manager.current = "game"

    def goto_menu(self):
        self.manager.current = "menu"


class Background(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tile_width = 128
        self.tile_height = 128
        self.cols = int(800 / self.tile_width) + 2
        self.rows = int(600 / self.tile_height) + 1

        self.tiles = []

        with self.canvas:
            for r in range(self.rows):
                for c in range(self.cols):
                    x = c * self.tile_width
                    y = r * self.tile_height
                    rect = Rectangle(
                        source=get_asset_path("grass.png"),
                        pos=(x, y),
                        size=(self.tile_width, self.tile_height),
                    )
                    self.tiles.append({"pos": [x, y], "rect": rect})

    def update(self, game_speed):
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = (64, 64)
        self.pos = (800 // 8 - 32, 600 // 2 - 32)

        self.sprites = [
            get_asset_path("hero1.png"),
            get_asset_path("hero2.png"),
            get_asset_path("hero1.png"),
            get_asset_path("hero3.png"),
        ]
        self.index = 0
        self.animation_speed = 0.1
        self.anim_time = 0.0

        with self.canvas:
            self.rect = Rectangle(
                source=self.sprites[self.index], pos=self.pos, size=self.size
            )
        self.bind(pos=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos

    def animate(self, dt):
        self.anim_time += dt
        if self.anim_time >= self.animation_speed:
            self.anim_time = 0.0
            self.index = (self.index + 1) % len(self.sprites)
            self.rect.source = self.sprites[self.index]

    def move_up(self):
        step = 0.05 * 600
        new_y = self.y + step
        if new_y + self.height > 600:
            new_y = 600 - self.height
        self.y = new_y

    def move_down(self):
        step = 0.05 * 600
        new_y = self.y - step
        if new_y < 0:
            new_y = 0
        self.y = new_y


class MovingWidget(Widget):
    def __init__(self, image_path, size, x, y, **kwargs):
        super().__init__(**kwargs)
        self.size = size
        self.pos = (x, y)
        with self.canvas:
            self.rect = Rectangle(source=image_path, pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos

    def update(self, game_speed):
        self.x -= game_speed
        if self.x + self.width < 0:
            return False
        return True


class Flower(MovingWidget):
    def __init__(self, **kwargs):
        image = get_asset_path("flower1.png")
        x = 800 + random.randint(50, 200)
        y = random.randint(0, 600 - 32)
        super().__init__(image, (32, 32), x, y, **kwargs)


class Stone(MovingWidget):
    def __init__(self, **kwargs):
        image = get_asset_path("stone.png")
        x = 800 + random.randint(100, 300)
        y = random.randint(0, 600 - 64)
        super().__init__(image, (64, 64), x, y, **kwargs)


class GameView(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active = True
        self.game_speed = 3.0
        self.score = 0
        self.distance = 0.0
        self.stone_interval = 3.0

        self.flowers = []
        self.stones = []

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

        self.update_labels()

    def start_game(self):
        Clock.schedule_interval(self.update, 1.0 / 60)
        Clock.schedule_interval(self.spawn_flower, 1.0)
        self.schedule_next_stone()

    def stop_game(self):
        self.active = False
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_flower)
        Clock.unschedule(self.spawn_stone)

    def spawn_flower(self, dt):
        if not self.active:
            return
        flower = Flower()
        self.add_widget(flower)
        self.flowers.append(flower)

    def schedule_next_stone(self):
        Clock.schedule_once(self.spawn_stone, self.stone_interval)

    def spawn_stone(self, dt):
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
        self.score_label.text = _("Collected: ") + str(self.score)
        self.distance_label.text = _("Distance: ") + str(int(self.distance))

    def update(self, dt):
        if not self.active:
            return

        frame_factor = dt * 60
        self.hero.animate(dt)

        self.game_speed += 0.001 * frame_factor
        self.distance += (self.game_speed / 10) * frame_factor

        self.background.update(self.game_speed * frame_factor)

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
        self.stop_game()
        app = App.get_running_app()
        go_screen = app.root.get_screen("game_over")
        go_screen.score = self.score
        go_screen.distance = self.distance
        app.root.current = "game_over"

    def on_touch_down(self, touch):
        touch.ud["start_y"] = touch.y
        touch.ud["start_x"] = touch.x
        return True

    def on_touch_up(self, touch):
        if "start_y" in touch.ud:
            dy = touch.y - touch.ud["start_y"]
            dx = touch.x - touch.ud["start_x"]
            if abs(dy) > abs(dx) and abs(dy) > 30:
                if dy > 0:
                    self.hero.move_up()
                else:
                    self.hero.move_down()
        return True

    def on_keyboard_down(self, key):
        if key in ("up", "w"):
            self.hero.move_up()
            return True
        elif key in ("down", "s"):
            self.hero.move_down()
            return True
        return False


class GameScreen(Screen):
    def on_enter(self):
        self.game_view = GameView()
        self.add_widget(self.game_view)
        self.game_view.start_game()

        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def on_leave(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None
        self.game_view.stop_game()
        self.remove_widget(self.game_view)

    def _keyboard_closed(self):
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        key = keycode[1]
        if key in ("escape", "q"):
            self.manager.current = "quit"
            return True
        return self.game_view.on_keyboard_down(key)


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
        padding: 50
        spacing: 20
        Label:
            id: title
            font_size: 40
            color: 1, 1, 1, 1
        Label:
            id: subtitle
            font_size: 24
            color: 1, 1, 1, 1
        Button:
            id: start_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: root.start_game()
        Button:
            id: quit_btn
            size_hint: (0.4, 0.15)
            pos_hint: {'center_x': 0.5}
            font_size: 20
            on_release: app.stop()

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
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(QuitScreen(name="quit"))
        sm.add_widget(GameOverScreen(name="game_over"))
        return sm


def main():
    QuickHerbalistApp().run()


if __name__ == "__main__":
    main()
