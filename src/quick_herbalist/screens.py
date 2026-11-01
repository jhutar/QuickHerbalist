"""All menu/flow screens plus their KV definitions."""

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from quick_herbalist.game_scene import GameView
from quick_herbalist.localization import _


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

    def on_back(self):
        """Default back behaviour: return to the main menu."""
        self.manager.current = "menu"

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """Handle escape/q as back; return True when the key was handled."""
        if keycode[1] in ("escape", "q"):
            self.on_back()
            return True
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
        return super()._on_keyboard_down(keyboard, keycode, text, modifiers)

    def on_back(self):
        """Quit the app when leaving the main menu."""
        App.get_running_app().stop()

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


class GameWonScreen(KeyboardScreen):
    """Screen shown when level is completed."""

    score = 0

    def on_pre_enter(self):
        """Initialize level completion UI."""
        self.ids.title.text = _("LEVEL COMPLETED!")
        self.ids.score_lbl.text = _("Collected Flowers: ") + str(self.score)
        self.ids.restart_btn.text = _("Play Again")
        self.ids.menu_btn.text = _("Main Menu")

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
        """Handle 's' to resume the game; leave escape/q to the base class."""
        if keycode[1] == "s":
            self.resume_game()
            return True
        return super()._on_keyboard_down(keyboard, keycode, text, modifiers)

    def on_back(self):
        """Quit the app from the quit screen."""
        App.get_running_app().stop()

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

    def on_back(self):
        """Quit the app from the game over screen."""
        App.get_running_app().stop()

    def restart_game(self):
        """Restart game."""
        self.manager.current = "game"

    def goto_menu(self):
        """Go to main menu."""
        self.manager.current = "menu"


class GameScreen(Screen):
    """Screen displaying the game view."""

    def on_enter(self):
        """Initialize game view and request keyboard on entry."""
        app = App.get_running_app()
        self.game_view = GameView(app.profile_manager, app.sprite_manager)
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
